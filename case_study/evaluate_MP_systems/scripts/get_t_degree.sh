#!/bin/sh

# Input to the script is the trie dump of controlflag of format: 
# <pattern>,<num_occurrences>,<num_repos_contributing_to_pattern>,<repo1;contri>,...,<repoN;contri>

# Script prints the percentage of repos contributing to every pattern first.
# Towards the end, the script prints the histogram of contributions.

AWK_SCRIPT=`mktemp`
cat > ${AWK_SCRIPT} <<- EOM
BEGINFILE {
 tdegree_sum=0;
}
{
 pattern_tdegree=(\$3/244);
 tdegree_sum += pattern_tdegree;
}
ENDFILE {
 print (tdegree_sum / NR);
}
EOM

awk -F "," -f ${AWK_SCRIPT} $1
