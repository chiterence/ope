#!/bin/bash
# SessionStart hook: 保存当前 session ID 到 .session-id
# 供 or.sh 在下次启动时 resume 到同一会话
# $1 = optional PID (默认 $PPID = Claude Code 主进程)
PID="${1:-$PPID}"
SESSION_FILE="/home/user/.claude/sessions/${PID}.json"
SID_FILE="/home/user/ope/.session-id"

if [ -f "$SESSION_FILE" ]; then
  SID=$(python3 -c "
import sys, json
try:
    with open('$SESSION_FILE') as f:
        d = json.load(f)
        print(d.get('sessionId', ''))
except:
    pass
" 2>/dev/null)
  if [ -n "$SID" ]; then
    echo "$SID" > "$SID_FILE"
  fi
fi
