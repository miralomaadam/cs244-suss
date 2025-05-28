#!/usr/bin/env bash
# run_curl_trace.sh
#
# Usage:  ./run_curl_trace.sh <download-file> <logfile>
# Example: ./run_curl_trace.sh 1G.bin myrun.log
#
# Notes
# -----
# * Valid DOWNLOAD targets are listed in ALLOWED array.
# * LOGFILE must end in ".log".
# * The script exits on first error (`set -euo pipefail`).

set -euo pipefail

# ---------- configuration ----------
ALLOWED=(1M.bin 1K.bin 1G.bin)   # add/remove entries as you wish
SERVER_IP="104.154.51.134"
ASSETS_PATH="/assets"

# ---------- helpers ----------
usage() {
  echo "Usage: $0 <download-file> <logfile>"
  echo "       download-file must be one of: ${ALLOWED[*]}"
  echo "       logfile must end in .log"
  exit 1
}

# ---------- argument parsing & validation ----------
[[ $# -eq 2 ]] || usage
DOWNLOAD="$1"
LOGFILE="$2"

# 1. validate DOWNLOAD
valid=false
for f in "${ALLOWED[@]}"; do
  [[ "$DOWNLOAD" == "$f" ]] && valid=true && break
done
if ! $valid; then
  echo "Error: \"$DOWNLOAD\" is not an allowed asset."
  echo "Allowed values: ${ALLOWED[*]}"
  exit 1
fi

# 2. validate LOGFILE suffix
if [[ "$LOGFILE" != *.log ]]; then
  echo "Error: logfile \"$LOGFILE\" must end with .log"
  exit 1
fi

# 3. run the command
echo "Fetching ${DOWNLOAD} … output to ${LOGFILE}"
curl --output /dev/null \
     --trace - \
     --trace-time \
     "http://${SERVER_IP}${ASSETS_PATH}/${DOWNLOAD}" |
  grep '^[0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}\.[0-9]\{6\}' > "$LOGFILE"

echo "Done. Log written to \"$LOGFILE\""
