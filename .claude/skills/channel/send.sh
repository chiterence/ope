#!/bin/bash
# 发送消息到当前通道或指定chat_id
# 用法: send.sh "消息内容" [chat_id]
# 第二个参数可选：指定chat_id发送（用于群聊）
STATE_FILE=/tmp/ope-channel.json

# 空消息自动替换为"收到"
if [ -z "$1" ]; then
  TEXT="收到"
else
  TEXT="$1"
fi

TOKEN=$(grep TELEGRAM_BOT_TOKEN /home/user/.claude/channels/telegram/.env | cut -d= -f2-)

send_msg() {
  local CID="$1"
  local RESPONSE
  RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${CID}" \
    --data-urlencode "text=${TEXT}")
  if echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('ok') else 1)" 2>/dev/null; then
    echo "[sent→$1]"
  else
    local DESC
    DESC=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('description','unknown'))" 2>/dev/null)
    echo "[失败] $DESC"
    return 1
  fi
}

if [ -n "$2" ]; then
  send_msg "$2"
  exit $?
fi

if [ ! -f "$STATE_FILE" ]; then
  echo "错误：未设置通道，先运行 set-channel.sh"
  exit 1
fi

SOURCE=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('source',''))" 2>/dev/null)
CHAT_ID=$(python3 -c "import json; print(json.load(open('$STATE_FILE')).get('chat_id',''))" 2>/dev/null)

if [ "$SOURCE" = "telegram" ]; then
  send_msg "$CHAT_ID"
else
  echo "[terminal]: $TEXT"
fi
