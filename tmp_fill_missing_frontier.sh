#!/bin/sh
set -eu
for d in \
  2020-06-16 \
  2020-06-17 \
  2020-06-18 \
  2020-06-19 \
  2020-06-20 \
  2023-09-24 \
  2023-09-25 \
  2023-09-26 \
  2023-09-27 \
  2023-09-28
 do
  echo "===== $d ====="
  python3 scripts/fetch_press_releases.py --start "$d" --end "$d" --skip-existing --continue-on-error --sleep-seconds 0.8
  echo
 done
