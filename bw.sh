#!/bin/bash
# BW 工具：一键解锁 + 查条目
# 用法: bw.sh                          → 解锁，输出 session
#       bw.sh field "条目名" "字段名"  → 查字段值
#       bw.sh password "条目名"        → 查密码
#       bw.sh search "关键词"          → 搜索条目

BW_EMAIL="seven@pipisisi.top"
BW_PASSWORD='Yi3801900600.'
BW_SERVER="https://bitwarden.chiterence.ccwu.cc"
STATE_FILE=/tmp/bw-session

do_unlock() {
  if [ -f "$STATE_FILE" ]; then
    SESSION=$(cat "$STATE_FILE")
    unset BW_SESSION
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    if bw list items --session "$SESSION" &>/dev/null; then
      echo "$SESSION"
      return 0
    fi
  fi

  export NODE_TLS_REJECT_UNAUTHORIZED=0
  bw config server "$BW_SERVER" &>/dev/null

  # 尝试解锁
  unset BW_SESSION
  SESSION=$(BW_PASSWORD="$BW_PASSWORD" bw unlock --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')

  # 失败则重新登录
  if [ -z "$SESSION" ]; then
    SESSION=$(BW_PASSWORD="$BW_PASSWORD" bw login "$BW_EMAIL" --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')
  fi

  if [ -z "$SESSION" ]; then
    echo "BW unlock/login failed" >&2
    exit 1
  fi

  echo "$SESSION" > "$STATE_FILE"
  echo "$SESSION"
}

export NODE_TLS_REJECT_UNAUTHORIZED=0
SESSION=$(do_unlock)

case "${1:-unlock}" in
  get)
    bw get item "$2" --session "$SESSION" 2>/dev/null
    ;;
  field)
    bw get item "$2" --session "$SESSION" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('fields',[]):
    if f['name'] == '$3':
        print(f['value'])
" 2>/dev/null
    ;;
  password)
    bw get item "$2" --session "$SESSION" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('login',{}).get('password',''))
" 2>/dev/null
    ;;
  notes)
    bw get item "$2" --session "$SESSION" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('notes',''))
" 2>/dev/null
    ;;
  search)
    bw list items --search "$2" --session "$SESSION" 2>/dev/null | python3 -c "
import sys,json
for i in json.load(sys.stdin):
    print(i['name'])
" 2>/dev/null
    ;;
  unlock)
    echo "$SESSION"
    ;;
esac
