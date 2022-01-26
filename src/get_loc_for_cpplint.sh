#!/bin/sh

if [ $# -ne 1 ];
then
  echo $0 "<directory_to_scan>"
  exit 0
fi

TMP_FILE=`mktemp`
sum=0
cpplint --recursive $1 2>&1 | grep "Done processing" | cut -d ' ' -f 3- > ${TMP_FILE}
while IFS= read -r file
do
  loc=`wc -l "${file}" | awk '{print $1}'`
  sum=$(( sum + loc ))
done < "${TMP_FILE}"

rm ${TMP_FILE}
echo -n $sum
