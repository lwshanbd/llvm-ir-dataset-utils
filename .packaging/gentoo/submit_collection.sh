#!/bin/bash
# Fan the package list out across N flux jobs, one disjoint [start,end) slice
# each. Resumable: a slice skips packages whose corpus already exists, so you can
# re-submit to continue after a time limit or failure.
#
#   ./submit_collection.sh [NUM_SLICES]
#
# Env (with defaults):
#   QUEUE      flux queue                 (pdebug)
#   TIME       per-job time limit         (12h)
#   LIST_FILE  list on the host           (<repo>/corpus_descriptions_test/portage_pkg.list)
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
QUEUE=${QUEUE:-pdebug}
TIME=${TIME:-12h}
LIST_FILE=${LIST_FILE:-/p/lustre2/shan4/llvm-ir-dataset-utils/corpus_descriptions_test/portage_pkg.list}
NUM_SLICES=${1:-24}

TOTAL=$(grep -c . "$LIST_FILE")
PER=$(( (TOTAL + NUM_SLICES - 1) / NUM_SLICES ))
echo "total=$TOTAL slices=$NUM_SLICES per=$PER queue=$QUEUE time=$TIME"

for (( s = 0; s < TOTAL; s += PER )); do
  e=$(( s + PER )); (( e > TOTAL )) && e=$TOTAL
  flux submit -q "$QUEUE" -N1 --exclusive -t "$TIME" \
    --job-name="corpus_${s}_${e}" \
    bash "$HERE/collect_slice.sh" "$s" "$e"
done
echo "submitted $NUM_SLICES jobs; watch with 'flux jobs' and tail \$LOGDIR/slice_*.log"
