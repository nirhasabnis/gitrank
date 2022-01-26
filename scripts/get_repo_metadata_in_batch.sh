#!/bin/bash

function print_usage() {
  echo -n "Usage: $1 -f <file_containing_list_of_git_urls>"
  echo -n " -o <output_file_to_store_csv_data>"
  echo " -t <git_access_token>"
  echo "Optional:"
  if ! command -v nproc &> /dev/null
  then
    echo "[-n number_of_processes_to_use]  (default: 1)"
  else
    echo "[-n number_of_processes_to_use]  (default: num_cpus_on_system)"
  fi

  exit
}

# Default values
if ! command -v nproc &> /dev/null
then
  NUM_PROCS=1
else
  NUM_PROCS=`nproc`
fi

GIT_URL_FILE=""
OUTPUT_CSV_FILE=""
TOKEN=""

while getopts f:o:n:t: flag
do
  case "${flag}" in
    f) GIT_URL_FILE=${OPTARG};;
    o) OUTPUT_CSV_FILE=${OPTARG};;
    n) NUM_PROCS=${OPTARG};;
    t) TOKEN=${OPTARG}
  esac
done

if [ "${GIT_URL_FILE}" = "" ] || [ "${OUTPUT_CSV_FILE}" = "" ] || [ "${TOKEN}" = "" ];
then
  print_usage
fi

CURRENT_DIR=`dirname $0`

function get_metadata_of_single_repo() {
  repo_url=$1
  token=$2
  output_csv=$3
  tmp_dir_to_clone_repo=`mktemp -d`
  python3 ${CURRENT_DIR}/../src/get_metadata_of_single_repo.py -r ${repo_url} -t ${token} -d ${tmp_dir_to_clone_repo} -p >> ${output_csv}
  rm -rf ${tmp_dir_to_clone_repo}
}
export -f get_metadata_of_single_repo
export CURRENT_DIR

# Generate CSV header using a repo
python3 src/get_metadata_of_single_repo.py -t ${TOKEN} -r https://github.com/nirhasabnis/gitrank -d `mktemp -d` | head -n 1 > ${OUTPUT_CSV_FILE}

if ! command -v parallel &> /dev/null
then
  echo "GNU Parallel does not exist. Invoking serial dump.."
  for git_url in `cat $GIT_URL_FILE`;
  do
    echo "Processing " ${git_url}
    get_metadata_of_single_repo ${git_url} ${TOKEN} ${OUTPUT_CSV_FILE}
  done
else
  echo "GNU Parallel exists. Invoking parallel dump.."
  TMP_DIR=`mktemp -d`

  cat ${GIT_URL_FILE} | parallel --eta --bar --progress \
    -I% -j${NUM_PROCS} get_metadata_of_single_repo % ${TOKEN} ${TMP_DIR}/proc_{%}.csv

  for i in `seq 1 $NUM_PROCS`;
  do
    if [ -f ${TMP_DIR}/proc_${i}.csv ]
    then
      cat ${TMP_DIR}/proc_${i}.csv >> ${OUTPUT_CSV_FILE}
    fi
  done

  rm -rf {TMP_DIR}
fi