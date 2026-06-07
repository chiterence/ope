#!/bin/bash
# 根据传入的 source 和 chat_id 自动设置 channel
# 用法: set-channel-from-source.sh telegram 942329001
#        set-channel-from-source.sh terminal
STATE_FILE=/tmp/ope-channel.json
if [ "$1" = "telegram" ] && [ -n "$2" ]; then
  echo "{\"source\":\"telegram\",\"chat_id\":\"$2\"}" > "$STATE_FILE"
elif [ "$1" = "terminal" ]; then
  echo "{\"source\":\"terminal\"}" > "$STATE_FILE"
fi
