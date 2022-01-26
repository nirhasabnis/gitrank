#!/bin/sh

# MIT License
# 
# Copyright (c) 2022 Niranjan Hasabnis
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
