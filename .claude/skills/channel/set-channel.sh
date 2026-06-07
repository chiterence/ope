#!/bin/bash
# 设置当前通道变量（写入 /tmp，tmpfs 即内存，非磁盘 IO）
# 无参数时：如果已有 Telegram 信道则保留，否则设 terminal
# 有参数时：按参数设置
STATE_FILE=/tmp/ope-channel.json
if [ "$1" = "telegram" ] && [ -n "$2" ]; then
  echo "{\"source\":\"telegram\",\"chat_id\":\"$2\"}" > "$STATE_FILE"
elif [ -f "$STATE_FILE" ] && grep -q '"telegram"' "$STATE_FILE" 2>/dev/null; then
  # 已有 Telegram 信道，不覆写
  :
else
  echo "{\"source\":\"terminal\"}" > "$STATE_FILE"
fi
