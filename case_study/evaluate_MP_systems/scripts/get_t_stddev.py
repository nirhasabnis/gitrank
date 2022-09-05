# Input to the script is the trie dump of controlflag of format: 
# <pattern>,<num_occurrences>,<num_repos_contributing_to_pattern>,<repo1;contri>,...,<repoN;contri>
from statistics import pstdev
import sys, csv

with open(sys.argv[1], 'r') as f:
  lines = csv.reader(f)
  
  sum_stdev = 0
  num_lines = 0
  min_stdev = 0
  max_stdev = 0
  for line in lines:
    i = 0
    field_pct_array = []
    for field in line:
      i += 1
      if i == 2:
        total_contributions = float(field)
      if i <= 3:
        continue
      value = field.split(";")[1].rstrip(')')
      field_pct_array.append((float(value) / total_contributions) * 100)
    if len(field_pct_array) > 0:
      line_stdev = pstdev(field_pct_array)
      #print(num_lines, line_stdev)
      sum_stdev += line_stdev
      num_lines += 1

      if line_stdev < min_stdev:
        min_stdev = line_stdev
      if line_stdev > max_stdev:
        max_stdev = line_stdev
  print('avg pstdev:', round(sum_stdev / num_lines, 2))
  print('min pstdev:', round(min_stdev, 2))
  print('max pstdev:', round(max_stdev, 2))
