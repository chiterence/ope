#!/bin/bash
# SessionEnd hook: 退出时存档当前会话的完整聊天记录
# 文件: book/diary/sessions/<日期>_<session-id-前8位>.md

HISTORY_FILE="$HOME/.claude/history.jsonl"
SID_FILE="/home/user/ope/.session-id"
ARCHIVE_DIR="/home/user/ope/book/diary/sessions"

if [ ! -f "$SID_FILE" ] || [ ! -f "$HISTORY_FILE" ]; then
  exit 0
fi

SID=$(cat "$SID_FILE")
if [ -z "$SID" ]; then
  exit 0
fi

python3 -c "
import sys, json, os
sid = '$SID'
history = []
with open('$HISTORY_FILE') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            entry = json.loads(line)
            if entry.get('sessionId') == sid:
                history.append(entry)
        except:
            pass

if not history:
    sys.exit(0)

first_ts = history[0].get('timestamp', 0)
from datetime import datetime, timezone
dt = datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
prefix = sid[:8]
filename = os.path.join('$ARCHIVE_DIR', f'{dt}_{prefix}.md')

with open(filename, 'w') as f:
    f.write(f'# Session {sid}\n')
    f.write(f'> 存档时间: {datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc).strftime(\"%Y-%m-%d %H:%M UTC\")}\n')
    f.write(f'> 对话数: {len(history)}\n\n')
    for entry in history:
        display = entry.get('display', '')
        ts = entry.get('timestamp', 0)
        dt_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime('%H:%M')
        if display:
            f.write(f'### [{dt_str}] {display}\n')
        pasted = entry.get('pastedContents', {})
        if pasted:
            f.write(f'{json.dumps(pasted, ensure_ascii=False)}\n')
        f.write('\n')
" 2>/dev/null
