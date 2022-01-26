#! /usr/bin/env python3

import argparse
import re
import subprocess, os
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
import json
import sys
import csv, math

from git import Repo, GitCommandError
from lizard import analyze
from perceval.backends.core.git import Git
from perceval.backends.core.github import GitHub
from perceval.backends.core.github import GitHubClient
from graal.backends.core.cocom import CoCom

default_entries_per_page = 1
repo_metadata = dict()

def make_github_get_query(owner, repository, token, resource, params=''):
  github_client = GitHubClient(owner=owner, repository=repository, tokens=token)
  resource_url = "https://api.github.com/repos/" + owner + "/" + repository + "/" + resource + "?per_page=" + str(default_entries_per_page) + params
  if args.debug:
    print("Asking for URL:", resource_url)
  response = github_client.fetch(url=resource_url)
  #print(response.headers)
  return response

def get_num_github_commits(owner, repo, token):
  response = make_github_get_query(owner, repo, token, "commits")
  # Response header contains something like '<https://api.github.com/repositories/392565553/commits?page=2>; 
  # rel="next"', '<https://api.github.com/repositories/392565553/commits?page=200>; rel="last"'
  _, _, last = response.headers['Link'].partition(',')
  # Get last page number from something like: <https://api.github.com/repositories/392565553/commits?page=200>; rel="last"
  _,_,last_page_number = re.search("&page=[0-9]+", last).group(0).partition('=')
  return (int(last_page_number) - 1) * default_entries_per_page

def get_num_github_contributors(owner, repo, token):
  response = make_github_get_query(owner, repo, token, "contributors")
  # Response header contains something like '<https://api.github.com/repositories/392565553/commits?page=2>; 
  # rel="next"', '<https://api.github.com/repositories/392565553/commits?page=200>; rel="last"'
  _, _, last = response.headers['Link'].partition(',')
  # Get last page number from something like: <https://api.github.com/repositories/392565553/commits?page=200>; rel="last"
  _,_,last_page_number = re.search("&page=[0-9]+", last).group(0).partition('=')
  return (int(last_page_number) - 1) * default_entries_per_page

def get_number_of_issues_over_period(owner, repository, token, state, from_date, to_date):
  # GitHub API for issues requires time in ISO-861 format. https://docs.github.com/en/rest/reference/issues
  if state == 'closed':
    response = make_github_get_query(owner, repository, token, "issues", "&state=" + state + "&since=" + from_date.isoformat(timespec='seconds') + 'Z') 
  else:
    response = make_github_get_query(owner, repository, token, "issues", "") 
  
  if 'Link' in response.headers:
    _, _, last = response.headers['Link'].partition(',')
    _,_,last_page_number = re.search("&page=[0-9]+", last).group(0).partition('=')
    return (int(last_page_number)) * default_entries_per_page
  else:
    return 0
  #for item in repo.fetch(category='issue', from_date=from_date, to_date=to_date):
  #  if 'pull_request' not in item['data']:
  #    if item['data']['state'] == 'closed':
  #      closed_issues = closed_issues + 1
  #    elif item['data']['state'] == 'open':
  #      open_issues = open_issues + 1
  #    else:
  #      print('Unhandled state of an issue:', item['data']['state'])
  #return (open_issues, closed_issues)

def report_number_of_issues_over_period(owner, repository, token):
  current_date = datetime.utcnow()
  # obtain 2 year prior date
  two_year_ago_date = current_date - timedelta(days=365*2)
  # obtain one year prior date
  one_year_ago_date = current_date - timedelta(days=365)
  # obtain 6 months prior date
  six_months_ago_date = current_date - timedelta(days=180)
  # obtain 1 month prior date
  one_month_ago_date = current_date - timedelta(days=30)  
  closed_issues_and_pr_over_two_year = get_number_of_issues_over_period(owner, repository, token, state="closed", from_date=two_year_ago_date, to_date=current_date)
  closed_issues_and_pr_over_one_year = get_number_of_issues_over_period(owner, repository, token, state="closed", from_date=one_year_ago_date, to_date=current_date)
  closed_issues_and_pr_over_six_months = get_number_of_issues_over_period(owner, repository, token, state="closed", from_date=six_months_ago_date, to_date=current_date)
  closed_issues_and_pr_over_one_month = get_number_of_issues_over_period(owner, repository, token, state="closed", from_date=one_month_ago_date, to_date=current_date)
  open_issues_and_pr_now = get_number_of_issues_over_period(owner, repository, token, state="open", from_date=current_date, to_date=current_date)   
  repo_metadata['open_issues_and_pr_now'] = open_issues_and_pr_now
  repo_metadata['closed_issues_and_pr_over_two_year'] = closed_issues_and_pr_over_two_year
  repo_metadata['closed_issues_and_pr_over_one_year'] = closed_issues_and_pr_over_one_year
  repo_metadata['closed_issues_and_pr_over_six_months'] = closed_issues_and_pr_over_six_months
  repo_metadata['closed_issues_and_pr_over_one_month'] = closed_issues_and_pr_over_one_month

def get_repo_code_complexity(repo_directory):
  #cc = CoCom(uri=repo_url, git_path=repo_directory)
  # Use Lizard's cpp language to check for code complexity
  file_infos = list(analyze(paths=[repo_directory], lans=["cpp"]))
  total_cyclomatic_complexity_for_repo = 0
  total_maintainability_index_for_repo = 0
  total_number_of_files_with_valid_info = 0

  # Determine average cyclomatic complexity per file using function-level cyclomatic complexity
  def get_avg_cyclomatic_complexity_per_file(file_info):
    total_cyclomatic_complexity = 0
    function_info_list = file_info.__dict__["function_list"]
    total_number_of_functions = len(function_info_list)
    for function_info in function_info_list:
      total_cyclomatic_complexity += function_info.__dict__["cyclomatic_complexity"]
    return total_cyclomatic_complexity / total_number_of_functions

  def get_halstead_volume_for_function(func_name, file_name, start_line, end_line):
    try:
      output_json = subprocess.check_output("halstead_volume/bin/get_halstead_volume -f " + file_name + " -l 2 -s " + str(start_line) + " -e " + str(end_line) + " 2> /dev/null", shell=True).decode("utf-8")
      #print('json:', output_json)
      halstead_volumes_for_funcs = json.loads(output_json)["halstead_volumes"]
      if len(halstead_volumes_for_funcs) < 1:
        raise Exception("No volume found for " + func_name)
      elif len(halstead_volumes_for_funcs) == 1:
        return halstead_volumes_for_funcs[0]["halstead_volume"]
      else:
        for halstead_volume_for_func in halstead_volumes_for_funcs:
          if halstead_volume_for_func["function_name"] == func_name:
            return halstead_volume_for_func["halstead_volume"]
          else:
            raise Exception("No volume found for " + func_name)
    except subprocess.CalledProcessError as err:
      return -1
    except Exception as exp:
      return -1
    finally:
      subprocess._cleanup()

  def get_maintainability_index_per_file(file_info):
    file_name = file_info.__dict__["filename"]
    # determine maintainability index of file using function-level info.
    #func_mi = 0
    #functions_without_err_in_halstead_vol = 0
    #function_info_list = file_info.__dict__["function_list"]
    #for function_info in function_info_list:
      #print(function_info.__dict__)
    #  func_name = function_info.__dict__["name"]
    #  start_line = function_info.__dict__["start_line"]
    #  end_line = function_info.__dict__["end_line"]
    #  cyclomatic_complexity = float(function_info.__dict__["cyclomatic_complexity"])
    #  nloc = function_info.__dict__["nloc"]
    #  halstead_volume_for_func = get_halstead_volume_for_function(func_name, file_name, start_line, end_line)
    #  if halstead_volume_for_func != -1:
    #    func_mi += 171 - 5.2 * math.log(halstead_volume_for_func) - 0.23 * cyclomatic_complexity - 16.2 * math.log(nloc)
    #    functions_without_err_in_halstead_vol += 1
    #if functions_without_err_in_halstead_vol > 0:
    #  return func_mi / len(function_info_list)
    #else:
    #  return -1
    avg_maintainability_index = -1
    try:
      output = subprocess.check_output("lizard -Emaintainabilityindex -i -1 " + file_name + " 2> /dev/null", shell=True).decode("utf-8")
      output_lines = output.split('\n')
      if len(output_lines) >= 2:
        for line in output_lines[len(output_lines) - 2 : len(output_lines)]:
          # Expected output line: "avg_maintainability_index: <index>"
          if line.startswith("avg_maintainability_index:"):
            avg_maintainability_index = float(line.split(' ')[-1])
            break
    except subprocess.CalledProcessError as err:
      print('filename:', file_name)
      print('error:', err)
      return -1
    finally:
      subprocess._cleanup()
      return avg_maintainability_index

  for file_info in file_infos:
    # Skip files having no function list info
    if 'function_list' in file_info.__dict__ and len(file_info.__dict__['function_list']) > 0:
      mi = get_maintainability_index_per_file(file_info)
      if mi != -1:
        total_cyclomatic_complexity_for_repo += get_avg_cyclomatic_complexity_per_file(file_info)
        total_maintainability_index_for_repo += mi
        total_number_of_files_with_valid_info += 1
    if args.debug:
      print(file_info.__dict__["filename"], file_info.__dict__["nloc"],
            get_avg_cyclomatic_complexity_per_file(file_info))    
      for function_info in file_info.__dict__["function_list"]:
        print(function_info.__dict__)
  
  if total_number_of_files_with_valid_info == 0:
    #raise Exception("lizard found no files in ", repo_directory)
    # Do not fail as we should continue with next repo.
    average_cyclomatic_complexity_for_repo = -1
    average_maintainability_index_for_repo = -1
  else:
    average_cyclomatic_complexity_for_repo = round(total_cyclomatic_complexity_for_repo / total_number_of_files_with_valid_info, 2)
    average_maintainability_index_for_repo = round(total_maintainability_index_for_repo / total_number_of_files_with_valid_info, 2)

  repo_metadata['average_cyclomatic_complexity_for_repo'] = average_cyclomatic_complexity_for_repo
  repo_metadata['average_maintainability_index_for_repo'] = average_maintainability_index_for_repo

def get_repo_code_license_compliance(repo_directory):
  #cc = CoLic(uri=repo_url, git_path=repo_directory)
  is_valid_license = 0
  try:
    # Check type of LICENSE file. If such a file does not exist, return code will be non-zero, in which case we set test score to 0.
    output_json = subprocess.check_output("scancode -l --quiet --json - " + repo_directory + "/LICENSE 2> /dev/null", shell=True).decode("utf-8")
    output_dict = json.loads(output_json)

    # check that license is not a generic-cla, but a known one such as Apache, MIT, etc.
    if 'files' in output_dict:
      license_file_record = output_dict['files'][0]
      if 'license_expressions' in license_file_record and 'generic-cla' not in license_file_record['license_expressions']:
        is_valid_license = 1      
  except subprocess.CalledProcessError as err:
    is_valid_license = 0
  finally:
    subprocess._cleanup()
    repo_metadata['is_valid_license'] = is_valid_license

def get_repo_code_formatting_report(repo_directory):
  cpplint_errors = -1
  cpplint_loc = 1
  try:
    # Run cpplint at top-level with most confident verbosity level. If return code is 0, there are no style issues.
    # If return code is 1, there are some issues. In that case, issue count is in last but one line.
    output = subprocess.check_output("cpplint --recursive --verbose=5 --counting=total " + repo_directory + " 2>&1", shell=True).decode("utf-8")
    # Since there is no exception, set number of style issues to 0.
    cpplint_errors = 0
  except subprocess.CalledProcessError as err:
    if err.returncode == 1:
       decoded_output = err.output.decode('utf-8')
       decoded_output_lines = decoded_output.split('\n')
       if len(decoded_output_lines) >= 2:
         for line in decoded_output_lines[len(decoded_output_lines) - 2 : len(decoded_output_lines)]:
           # Expected output line: "Total errors found: <issues_count>"
           if line.startswith("Total errors found:"):
              cpplint_errors = line.split(' ')[-1]
              break
       else:
        raise err
    else:
      raise err
  finally:
    subprocess._cleanup()

  # Get lines of code scanned by cpplint. cpplint output does not contain this info, so we use a simple
  # shell script for it.
  try:
    cpplint_loc = subprocess.check_output(os.path.dirname(sys.argv[0]) + "/get_loc_for_cpplint.sh " + repo_directory, shell=True)
  except subprocess.CalledProcessError as err:
    raise err
  finally:
    subprocess._cleanup()

  repo_metadata['style_errors'] = cpplint_errors
  # avoid divide by 0
  if float(cpplint_loc) == 0:
    cpplint_loc = 1

  repo_metadata['style_errors_per_nloc'] = round(float(cpplint_errors) / float(cpplint_loc), 3)

def get_repo_code_security_report(repo_directory):
  security_notes = 0
  security_warnings = 0
  security_errors = 0
  flawfinder_loc = 1
  try:
    # Run flawfinder to get security report. Before that set LANG to ISO-8859-1 encoding to handle Python3 encoding/decoding errors.
    myenv = os.environ.copy()
    myenv["LANG"] = "en_US.ISO-8859-1"
    output_sarif = subprocess.check_output("flawfinder --sarif --falsepositive " + repo_directory + " 2> /dev/null", env=myenv, shell=True).decode("utf-8")
    output_json = json.loads(output_sarif)
    if "runs" in output_json and 'results' in output_json['runs'][0]:
      for result in output_json['runs'][0]['results']:
        if result['level'] == 'note':
          security_notes += 1
        elif result['level'] == 'warning':
          security_warnings += 1
        elif result['level'] == 'error':
          security_errors += 1
        else:
          print("Unhandled security level:", result['level'])
    else:
      # "runs" should be present in valid output, so scanning error.
      security_notes = -1
      security_warnings = -1
      security_errors = -1
  except subprocess.CalledProcessError as err:
    raise err
  finally:
    subprocess._cleanup()

  try:
    loc_scanned_output = subprocess.check_output("flawfinder -S --falsepositive " + repo_directory + " 2>&1 | tail -n 20", env=myenv, shell=True).decode("utf-8")
    decoded_output_lines = loc_scanned_output.split('\n')
    if len(decoded_output_lines) >= 20:
      for line in decoded_output_lines:
        # Expected output line: "Physical Source Lines of Code (SLOC) = <loc>"
        if line.startswith("Physical Source Lines of Code (SLOC)"):
          flawfinder_loc = float(line.split(' ')[-1])
          break
    else:
      raise subprocess.CalledProcessError
  except subprocess.CalledProcessError as err:
    raise err
  finally:
    subprocess._cleanup()

  repo_metadata['security_notes'] = security_notes
  repo_metadata['security_warnings'] = security_warnings
  repo_metadata['security_errors'] = security_errors

  # avoid div by 0
  if flawfinder_loc == 0:
    flawfinder_loc = 1

  repo_metadata['security_notes_per_nloc'] = round(float(security_notes) / flawfinder_loc, 3)
  repo_metadata['security_warnings_per_nloc'] = round(float(security_warnings) / flawfinder_loc, 3)
  repo_metadata['security_errors_per_nloc'] = round(float(security_errors) / flawfinder_loc, 3)
 
def print_report():
  writer = csv.DictWriter(sys.stdout, fieldnames=list(repo_metadata))
  if args.dont_print_csv_header == False:
    writer.writeheader()
  writer.writerow(repo_metadata)

# Parse command line arguments
parser = argparse.ArgumentParser(
    description = "Script to get repository metadata"
    )
parser.add_argument("-t", "--token",
                    '--nargs', nargs='+', required=True,
                    help = "GitHub token")
parser.add_argument("-r", "--repo-url", required=True,
                    help = "GitHub repository, as 'https://github.com/...'")
parser.add_argument("-g", "--debug", action='store_true',
                    help = "Debug this script")
parser.add_argument("-p", "--dont-print-csv-header", action='store_true', help = "Don't print header for csv")
parser.add_argument("-d", "--repo-dir", required=True,
                    help = "Directory to store cloned repository")
args = parser.parse_args()

#print('Calling with', args)

# Owner and repository names from https://github.com/<owner>/<repo_name>
owner = args.repo_url.split('/')[3]
repository = args.repo_url.split('/')[4]
repo_metadata['repository_owner'] = owner + "_" + repository
repo_metadata['repository_uri'] = args.repo_url

# First clone git repo
Repo.clone_from(url=args.repo_url, to_path=args.repo_dir)

# create a Git object, pointing to repo_url, using repo_dir for cloning
github_repo = GitHub(owner=owner, repository=repository, api_token=args.token)

for item in github_repo.fetch(category='repository'):
  for field in ['stargazers_count', 'subscribers_count', 'forks_count', 'open_issues', 'created_at']:
    if field == 'created_at':
      created_at_time_delta = datetime.now(timezone.utc) - isoparse(item['data'][field])
      repo_metadata['repo_age_in_days'] = created_at_time_delta.days
    repo_metadata[field] = item['data'][field]

repo_metadata['num_commits'] = get_num_github_commits(owner=owner, repo=repository, token=args.token)

report_number_of_issues_over_period(owner=owner, repository=repository, token=args.token)
# contributors API does not work for repositories having high number of contributors.
#print(get_num_github_contributors(owner=owner, repo=repo, token=args.token))

# Get complexity of code in the repository
get_repo_code_complexity(repo_directory=args.repo_dir)

# Get cpplint warnings - can use Graal Coqua for Python.
get_repo_code_formatting_report(repo_directory=args.repo_dir)

# Get code license compliance
get_repo_code_license_compliance(repo_directory=args.repo_dir)

# Get security analysis report
get_repo_code_security_report(repo_directory=args.repo_dir)

print_report()


