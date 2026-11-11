#!/usr/bin/env bash
# Fetch the roll calls found by fetch.py that are not yet in the transportation votes dataset,
# using the PA Housing Votes roll call fetcher. Run from anywhere: bash fetch-rollcalls.sh
# Output goes to ~/projects/pa-housing-votes/pipeline/data/rollcalls/.
set -u
cd ~/projects/pa-housing-votes/pipeline || exit 1
f() { uv run python scripts/fetch_rollcall.py "$@"; sleep 1.5; }

echo "== SB 509 (Senate passed 49-1 on Oct 20, 2026) =="
f --session 2025 --chamber senate --rc-num 567
f --session 2025 --chamber senate --committee-code 3  --committee-rc-id 1126
f --session 2025 --chamber senate --committee-code 19 --committee-rc-id 1072
f --session 2025 --chamber senate --committee-code 19 --committee-rc-id 1090

echo "== HB 291 House Transportation (26-0) =="
f --session 2025 --chamber house --committee-code 38 --committee-rc-id 7

echo "== HB 1085 committee =="
f --session 2025 --chamber house --committee-code 38 --committee-rc-id 241

echo "== SB 121, 2023 session (Senate passed 28-21) =="
f --session 2023 --chamber senate --rc-num 33
f --session 2023 --chamber senate --committee-code 3  --committee-rc-id 28
f --session 2023 --chamber senate --committee-code 19 --committee-rc-id 2

echo "== HB 1364 and HB 1788 committee votes =="
f --session 2025 --chamber house --committee-code 38 --committee-rc-id 402
f --session 2025 --chamber house --committee-code 38 --committee-rc-id 1094
f --session 2025 --chamber house --committee-code 67 --committee-rc-id 1096
f --session 2025 --chamber house --committee-code 62 --committee-rc-id 1097
echo "Done."
