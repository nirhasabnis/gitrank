#!/bin/bash

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
