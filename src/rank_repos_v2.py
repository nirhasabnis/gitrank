import csv
import sys
import argparse

_popularity_metrics = ['subscribers_count', 'stargazers_count', 'forks_count']
_maintainability_metrics = ['num_commits']
_quality_metrics = ['style_errors', 'security_notes', 'security_warnings', 'security_errors']

_non_normalized_metrics = ['average_cyclomatic_complexity_for_repo', 'average_maintainability_index_for_repo',
                           'closed_issues_and_pr_over_two_year', 'closed_issues_and_pr_over_one_year',
                           'closed_issues_and_pr_over_six_months', 'closed_issues_and_pr_over_one_month']
_norm_popularity_metrics = [x + '_by_age' for x in _popularity_metrics]
_norm_maintainability_metrics = [x + '_by_age' for x in _maintainability_metrics]
_norm_quality_metrics = [x + '_per_nloc' for x in _quality_metrics]

def read_csv_file(csv_file_name, list_of_csv_rows):
  ''' Reads CSV file containing repository metadata and returns list of CSV rows in order '''
  with open(csv_file_name, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      list_of_csv_rows.append(row)

def normalize_repository_metrics(list_of_csv_rows):
  def normalize_for_key(candidate_repo, out_key, in_key, dividend):
    candidate_repo[out_key] = round(float(candidate_repo[in_key]) / dividend, 2)

  def normalize_popularity_metrics(candidate_repo):
    ''' Normalize popularity metrics by repository age '''
    candidate_repo_age = float(candidate_repo['repo_age_in_days'])
    for in_key in _popularity_metrics:
      normalize_for_key(candidate_repo, in_key + '_by_age', in_key, candidate_repo_age)

  def normalize_maintainability_metrics(candidate_repo):
    ''' Normalize maintainability metrics by repository age '''
    candidate_repo_age = float(candidate_repo['repo_age_in_days'])
    for in_key in _maintainability_metrics:
      normalize_for_key(candidate_repo, in_key + '_by_age', in_key, candidate_repo_age)

  def normalize_quality_metrics(candidate_repo):
    ''' Normalize quality metrics by number of lines of code '''
    for in_key in _quality_metrics:
      normalize_for_key(candidate_repo, in_key + '_per_nloc', in_key, candidate_repo_nloc)

  for candidate_repo in list_of_csv_rows:
    normalize_popularity_metrics(candidate_repo)
    normalize_maintainability_metrics(candidate_repo)
    #normalize_quality_metrics(candidate_repo)

def rank_repositories_v2(list_of_csv_rows):
  # Obtain min and max of popularity and quality metrics.
  min_count = dict()
  max_count = dict()
  for key in _norm_popularity_metrics + _norm_quality_metrics + _norm_maintainability_metrics + _non_normalized_metrics:
    # Initialize
    min_count[key] = float(list_of_csv_rows[1][key])
    max_count[key] = float(list_of_csv_rows[1][key])
    for candidate_repo in list_of_csv_rows:
      if float(candidate_repo[key]) < min_count[key]:
        min_count[key] = float(candidate_repo[key])
      if float(candidate_repo[key]) > max_count[key]:
        max_count[key] = float(candidate_repo[key])

  # Determine percentage of a candidate repo for a given metric using its min and max.
  for key in _norm_popularity_metrics + _norm_quality_metrics + _norm_maintainability_metrics + _non_normalized_metrics:
    for candidate_repo in list_of_csv_rows:
      if float(max_count[key]) - float(min_count[key]) == 0:
        candidate_repo[key + '_pct'] = 100
      else:
        candidate_repo[key + '_pct'] = round(((float(candidate_repo[key]) - min_count[key]) / (max_count[key] - min_count[key])) * 100, 2)

  def get_popularity_score(candidate_repo):
    ''' Equal weight for all 3 '''
    return (candidate_repo['subscribers_count_by_age' + '_pct'] \
          + candidate_repo['stargazers_count_by_age' + '_pct'] \
          + candidate_repo['forks_count_by_age' + '_pct']) / 3

  def get_maintainability_score(candidate_repo):
    ''' Higher weight for maintainability_index, lower for older PRs/issues '''
    return (0.51 * candidate_repo['average_maintainability_index_for_repo' + '_pct'] +
            0.09 * candidate_repo['closed_issues_and_pr_over_two_year' + '_pct'] +
            0.09 * candidate_repo['closed_issues_and_pr_over_one_year' + '_pct'] +
            0.09 * candidate_repo['closed_issues_and_pr_over_six_months' + '_pct'] +
            0.12 * candidate_repo['closed_issues_and_pr_over_one_month' + '_pct'] +
            0.12 * candidate_repo['num_commits_by_age' + '_pct'])

  def get_quality_score(candidate_repo):
    # Since these metrics indicate issues in percent, we subtract from 100%.
    return 100 - ((candidate_repo['average_cyclomatic_complexity_for_repo' + '_pct'] \
          + candidate_repo['style_errors_per_nloc' + '_pct'] \
          + candidate_repo['security_notes_per_nloc' + '_pct'] \
          + candidate_repo['security_warnings_per_nloc' + '_pct'] \
          + candidate_repo['security_errors_per_nloc' + '_pct']) / 5)

  for candidate_repo in list_of_csv_rows:
    quality_score = get_quality_score(candidate_repo)
    maintainability_score = get_maintainability_score(candidate_repo)
    popularity_score = get_popularity_score(candidate_repo)
    # Avg of 3 scores.
    overall_score_of_candidate_repo = round((quality_score + maintainability_score + popularity_score) / 3, 2)
    candidate_repo['quality_score'] = round(quality_score, 2)
    candidate_repo['maintainability_score'] = round(maintainability_score, 2)
    candidate_repo['popularity_score'] = round(popularity_score, 2)
    candidate_repo['overall_score'] = overall_score_of_candidate_repo
    #print(candidate_repo)

parser = argparse.ArgumentParser(
    description = "Script to rank repositories using metadata"
    )
parser.add_argument("-c", "--csv_file", required=True,
                    help="Name of csv file containing repository metadata")
parser.add_argument("-o", "--output_csv_file", required=True,
                    help="File to store list of ranked repositories")
parser.add_argument("-d", "--print_detailed", required=False, action='store_true', default=False)
args = parser.parse_args()

list_of_csv_rows = []
# Dictionary to store index of baseline repository for ranking purpose
read_csv_file(args.csv_file, list_of_csv_rows)

filtered_list_of_csv_rows = []
# Drop CSV rows that contain any field having value -1 (which indicates error).
for candidate_repo in list_of_csv_rows:
  if "-1" in list(candidate_repo.values()):
    print("Dropping:", candidate_repo)
    continue
  else:
    filtered_list_of_csv_rows.append(candidate_repo)

# Normalize repository metrics
normalize_repository_metrics(filtered_list_of_csv_rows)

rank_repositories_v2(filtered_list_of_csv_rows)

# Sort list by score in reverse order
filtered_list_of_csv_rows.sort(key=lambda repo: repo['overall_score'], reverse=True)

order_of_keys = ['repository_owner', 'repository_uri', 
                 'overall_score', 'quality_score', 'maintainability_score', 'popularity_score'] \
                + _norm_quality_metrics + _norm_popularity_metrics + ['average_cyclomatic_complexity_for_repo_pct']

if args.print_detailed:
  for key in list(filtered_list_of_csv_rows[0]):
    if key not in order_of_keys:
      order_of_keys.append(key)

# Write ranked repository list to output csv
with open(args.output_csv_file, 'w', newline='') as output_csvfile:
  if args.print_detailed:
    writer = csv.DictWriter(output_csvfile, fieldnames=order_of_keys)
  else:
    writer = csv.DictWriter(output_csvfile, fieldnames=order_of_keys, extrasaction='ignore')
  writer.writeheader()
  for candidate_repo in filtered_list_of_csv_rows:
    writer.writerow(candidate_repo)
