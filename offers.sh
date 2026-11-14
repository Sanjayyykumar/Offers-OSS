#!/usr/bin/env sh
# Offers OSS - run ./offers.sh for the daily cockpit, or ./offers.sh <command>.
cd "$(dirname "$0")" || exit 1
python3 -c "import openpyxl, yaml" 2>/dev/null || python3 -m pip install -r requirements.txt
[ -f tracker/OffersOSS_Tracker.xlsx ] || python3 offers.py setup
if [ $# -eq 0 ]; then python3 offers.py go; else python3 offers.py "$@"; fi
