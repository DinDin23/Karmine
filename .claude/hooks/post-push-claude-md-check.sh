#!/usr/bin/env bash
# PostToolUse hook (Bash, matcher "git push*"): after a successful push made
# through Claude Code, nudges Claude to check whether CLAUDE.md is stale given
# what changed since it was last touched. Per the user, when an update is
# warranted Claude edits + commits + pushes it automatically, no confirmation
# needed -- that's standing approval for this hook specifically.
#
# Uses python3 for JSON in/out (no jq on this machine).
set -euo pipefail

input="$(cat)"

success=$(python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    print("true")
    sys.exit()
resp = data.get("tool_response") or {}
if "success" in resp:
    print("true" if resp["success"] else "false")
elif "exitCode" in resp:
    print("true" if resp["exitCode"] == 0 else "false")
else:
    print("true")
' <<< "$input" 2>/dev/null || echo "true")

if [ "$success" != "true" ]; then
  exit 0
fi

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [ -z "$repo_root" ]; then
  exit 0
fi
cd "$repo_root"

last_touch=$(git log -1 --format=%H -- CLAUDE.md 2>/dev/null || true)
head=$(git rev-parse HEAD 2>/dev/null || true)

# No CLAUDE.md yet, or it's already as new as HEAD (e.g. the hook's own prior
# sync commit was the thing that just got pushed) -- nothing to check.
if [ -z "$last_touch" ] || [ -z "$head" ] || [ "$last_touch" = "$head" ]; then
  exit 0
fi

diff_stat=$(git diff --stat "$last_touch..$head" -- . ':!CLAUDE.md' 2>/dev/null || true)

if [ -z "$diff_stat" ]; then
  exit 0
fi

context="A git push just completed. Files changed since CLAUDE.md was last updated (commit $last_touch):
$diff_stat

Check whether CLAUDE.md's commands, architecture description, or workflow notes are now stale given these changes. If an update is warranted: edit CLAUDE.md, then commit and push that change yourself (git add CLAUDE.md && git commit -m \"docs: update CLAUDE.md\" && git push) without asking for confirmation first -- this is pre-approved standing behavior for this specific hook. If nothing is actually stale, don't make any change and don't bring it up."

CTX="$context" python3 -c '
import json, os
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": os.environ["CTX"],
    }
}))
'
