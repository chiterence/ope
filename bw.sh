#!/bin/bash
# BW 工具：一键解锁 + 查条目
# 用法: bw.sh                          → 解锁，输出 session（缓存到 /tmp/bw-session）
#       bw.sh get "条目名"             → 查条目 .json 输出
#       bw.sh field "条目名" "字段名"  → 查指定字段值
#       bw.sh search "关键词"          → 搜索条目名

STATE_FILE=/tmp/bw-session

# ── 解锁 ────────────────────────────────────────────────────
do_unlock() {
  if [ -f "$STATE_FILE" ]; then
    SESSION=$(cat "$STATE_FILE")
    # 验证 session 是否有效
    if bw list items --session "$SESSION" &>/dev/null; then
      echo "$SESSION"
      return 0
    fi
  fi

  unset BW_SESSION
  export BW_PASSWORD='Yi3801900600.'
  SESSION=$(bw unlock --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')

  if [ -z "$SESSION" ]; then
    echo "BW unlock failed" >&2
    exit 1
  fi

  echo "$SESSION" > "$STATE_FILE"
  echo "$SESSION"
}

# ── 子命令 ──────────────────────────────────────────────────
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
