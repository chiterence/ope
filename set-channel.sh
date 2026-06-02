#!/bin/bash
# 设置当前通道变量（写入 /tmp，tmpfs 即内存，非磁盘 IO）
if [ "$1" = "telegram" ] && [ -n "$2" ]; then
  echo "{\"source\":\"telegram\",\"chat_id\":\"$2\"}" > /tmp/ope-channel.json
else
  echo "{\"source\":\"terminal\"}" > /tmp/ope-channel.json
fi
