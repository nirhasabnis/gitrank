#!/bin/bash

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
  echo "Usage: $0 <csv_file>"
  exit 0
fi

CSV_FILE=$1

function print_prologue() {
  echo "<!DOCTYPE html>"
  echo "<html>"
  echo "<title>GitRank: A framework to rank open-source repositories</title>"
  echo "<meta charset=\"utf-8\">"
  echo "<script src=\"https://www.w3schools.com/lib/w3.js\"></script>"
  echo "<head>"
  echo "<style>"
  echo "table, th, td {"
  echo "border: 1px solid black;"
  echo "}"
  echo "</style>"
  echo "</head>"
  echo "<body>"
  echo ""
  echo "<h2>Ranked list of repositories</h2>"
  echo "<p>Click the table headers to sort the  table accordingly:</p>"
}

function print_table() {
  echo "<table id=\"myTable\">"
  # Print table header
  echo "<tr>"
    for field in `head -n 1 ${CSV_FILE} | tr -t "," " "`
    do
      echo -n "<th onclick=\"w3.sortHTML('#myTable', '.item', 'td:nth-child(1)')\" style=\"cursor:pointer\">"
      echo -n ${field}
      echo "</th>"
    done
  echo "</tr>"

  # Print table rows now.
  while IFS= read -r row
  do
    echo "<tr class=\"item\">"
    for cell in `echo ${row} | tr -t "," " "`
    do
      echo -n "<td>"
      echo -n ${cell}
      echo "</td>"
    done
    echo "</tr>"
  done < <(tail -n +2 ${CSV_FILE})
  echo "</table>"
}

function print_epilogue() {
  echo "</body>"
  echo "</html>"
}

print_prologue
print_table
print_epilogue
