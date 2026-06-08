#!/bin/bash
# UserPromptSubmit hook: 捕获 Telegram 信道来源

STATE=/tmp/ope-channel.json

if read -t 0; then
  STDIN=$(cat)
  CHAT_ID=$(echo "$STDIN" | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
p = d.get('prompt', '')
m = re.search(r'chat_id=\"(-?\d+)\"', p)
if m: print(m.group(1))
" 2>/dev/null)
  if [ -n "$CHAT_ID" ]; then
    echo '{"source":"telegram","chat_id":"'"$CHAT_ID"'"}' > "$STATE"
    echo "$ CHANNEL: telegram  chat_id: $CHAT_ID"
    exit 0
  fi
fi

echo '{"source":"terminal"}' > "$STATE"
echo "$ CHANNEL: terminal"
