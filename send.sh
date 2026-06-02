#!/bin/bash
# 发送消息到当前通道
# 用法: send.sh "消息内容"
STATE_FILE=/tmp/ope-channel.json

if [ ! -f "$STATE_FILE" ]; then
  echo "错误：未设置通道，先运行 set-channel.sh"
  exit 1
fi

SOURCE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('source',''))" 2>/dev/null)
CHAT_ID=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('chat_id',''))" 2>/dev/null)

if [ "$SOURCE" = "telegram" ] && [ -n "$CHAT_ID" ]; then
  TOKEN=$(grep TELEGRAM_BOT_TOKEN /home/user/.claude/channels/telegram/.env | cut -d= -f2-)
  TEXT="$1"
  curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${CHAT_ID}" \
    --data-urlencode "text=${TEXT}" > /dev/null
else
  echo "[terminal]: $1"
fi
