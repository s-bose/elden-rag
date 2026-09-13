#!/bin/sh
set -eu

for f in $(ls /migrations/*.sql | sort); do
  echo "applying $f"
  psql -v ON_ERROR_STOP=1 -f "$f"
done
