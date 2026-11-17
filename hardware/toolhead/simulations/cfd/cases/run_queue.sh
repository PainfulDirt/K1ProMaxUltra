#!/bin/bash
# Sequential CFD queue: pops the first line of QUEUE (args for run_cases.py) until the file is empty.
# Lines can be appended while it runs. Usage: run_queue.sh QUEUE LOGDIR
Q=$1; L=$2
source /opt/k1th/env.sh
cd "$(dirname "$0")"
while true; do
  line=$(head -n 1 "$Q" 2>/dev/null)
  [ -z "$line" ] && break
  sed -i '1d' "$Q"
  tag=$(echo "$line" | tr ' :=/{}",' '_______' | cut -c1-60)
  echo "$(date -u +%FT%T) START $line" >> "$L/queue.log"
  case "$line" in
    repost*) $K1_PY repost.py ${line#repost} > "$L/q_$tag.log" 2>&1 ;;
    *)       $K1_PY run_cases.py $line > "$L/q_$tag.log" 2>&1 ;;
  esac
  echo "$(date -u +%FT%T) END   $line rc=$?" >> "$L/queue.log"
done
echo "$(date -u +%FT%T) QUEUE EMPTY" >> "$L/queue.log"
