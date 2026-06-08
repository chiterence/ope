#!/bin/bash
# Stop hook: 若 Telegram 通道且未用 send.sh，自动用 send.sh 转发回复
SEND_FLAG=/tmp/ope-send-used
STATE_FILE=/tmp/ope-channel.json
SEND_SCRIPT=/home/user/ope/.claude/skills/ope-channel/send.sh

# 没有信道文件 → 跳过
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi
SOURCE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('source',''))" 2>/dev/null)
if [ "$SOURCE" != "telegram" ]; then
  exit 0
fi

# 检查 send.sh 是否在本轮调用过
SEND_USED=false
if [ -f "$SEND_FLAG" ]; then
  FLAG_TS=$(stat -c %Y "$SEND_FLAG" 2>/dev/null || echo 0)
  NOW=$(date +%s)
  if [ $((NOW - FLAG_TS)) -le 10 ]; then
    SEND_USED=true
  fi
fi

if $SEND_USED; then
  exit 0
fi

# 没走 send.sh → 从 transcript 取最后一轮回复文本，转发
TRANSCRIPT=$(cat | python3 -c "
import sys, json
data = json.load(sys.stdin)
tp = data.get('transcript_path', '')
if tp:
    print(tp)
" 2>/dev/null)

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  echo "⚠️ [自动转发] 找不到 transcript，无法自动回复"
  exit 0
fi

TEXT=$(python3 -c "
import sys, json
with open('$TRANSCRIPT') as f:
    latest_text = ''
    for line in f:
        line = line.strip()
        if not line: continue
        try:
            d = json.loads(line)
            if d.get('type') == 'assistant':
                msg = d.get('message', {})
                content = msg.get('content', [])
                for c in content:
                    if c.get('type') == 'text':
                        t = c.get('text', '')
                        if len(t) > 20:
                            latest_text = t
        except:
            pass
    print(latest_text)
" 2>/dev/null)

if [ -z "$TEXT" ]; then
  echo "⚠️ [自动转发] 找不到回复文本"
  exit 0
fi

bash "$SEND_SCRIPT" "$TEXT"
echo "[自动转发] 已通过 send.sh 发送回复"
