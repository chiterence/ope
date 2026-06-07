#!/bin/bash
# BW 工具：API key 登录 + 主密码解锁
# 安全守卫：只能被 Skill 工具或技能脚本调用，禁止 Claude 直接调
# 其他技能（caiyun/pcloud/tianyi）调用前必须设 BW_SKILL_CALL=1
# 用法: bw.sh                          → 解锁，输出 session
#       bw.sh field "条目名" "字段名"  → 查字段值
#       bw.sh password "条目名"        → 查密码
#       bw.sh search "关键词"          → 搜索条目
#       bw.sh fields "条目名"          → 列出条目名/密码/字段名清单（不输出字段值，只列名）
#       bw.sh dump "条目名"            → 输出完整条目（字段名=值）
#
# 凭证来源：settings.local.json 的 env 字段
#   BW_CLIENTID     - API 登录凭据（推荐：用户级 API key）
#   BW_CLIENTSECRET - API 登录凭据
#   BW_PASSWORD     - 主密码（vault 解密必需）

if [ -z "$BW_SKILL_CALL" ]; then
  echo "错误：bw.sh 只能通过 Skill 工具调用。
  如果你是我（ope），请使用 /bw 技能而不是直接调脚本。
  如果你是其他技能脚本（caiyun/pcloud/tianyi），调用前 export BW_SKILL_CALL=1" >&2
  exit 1
fi

BW_SERVER="https://bitwarden.chiterence.ccwu.cc"
STATE_FILE=/tmp/bw-session
export CACHE_FILE=/home/user/ope/var/cache/bw-cache.json
CACHE_TTL=300  # 5 分钟

# 读缓存：命中且未过期 → 直接输出并 exit，否则无输出
read_cache() {
  local key="$1|$2|$3"
  [ -f "$CACHE_FILE" ] || return 1
  export CACHE_FILE CACHE_KEY="$key"
  local expiry val
  expiry=$(python3 -c "
import json,os
c=json.load(open(os.environ['CACHE_FILE']))
print(c.get(os.environ['CACHE_KEY'],{}).get('expiry',0))" 2>/dev/null)
  [ -z "$expiry" ] || [ "$expiry" -lt "$(date +%s)" ] && return 1
  val=$(python3 -c "
import json,os
c=json.load(open(os.environ['CACHE_FILE']))
print(c[os.environ['CACHE_KEY']]['value'])" 2>/dev/null)
  [ -n "$val" ] && echo "$val" && exit 0
}

# 写缓存（通过 env 传值，避免 shell 转义问题）
write_cache() {
  local key="$1|$2|$3"
  local val="$4"
  mkdir -p "$(dirname "$CACHE_FILE")" 2>/dev/null
  export CACHE_KEY="$key" CACHE_VAL="$val" CACHE_TTL
  python3 -c "
import json, os
f=os.environ['CACHE_FILE']
try: c=json.load(open(f))
except: c={}
c[os.environ['CACHE_KEY']]={'value': os.environ['CACHE_VAL'], 'expiry': int(__import__('time').time())+int(os.environ['CACHE_TTL'])}
json.dump(c, open(f,'w'))
" 2>/dev/null
}

do_unlock() {
  # 尝试缓存 session（用 BW_SESSION 环境变量，不用 --session 参数）
  if [ -f "$STATE_FILE" ]; then
    export BW_SESSION=$(cat "$STATE_FILE")
    export NODE_TLS_REJECT_UNAUTHORIZED=0
    # 必须确认 unlock 状态，bw list items 在 locked 时也可能静默成功
    if bw status 2>/dev/null | grep -q '"unlocked"'; then
      echo "$BW_SESSION"
      return 0
    fi
  fi

  export NODE_TLS_REJECT_UNAUTHORIZED=0
  bw config server "$BW_SERVER" &>/dev/null

  # 1) 如果已登录，直接 unlock
  unset BW_SESSION
  local SESSION
  if bw login --check &>/dev/null; then
    SESSION=$(bw unlock --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')
  fi

  # 2) 未登录 → API key 登录 + unlock
  if [ -z "$SESSION" ]; then
    SESSION=$(bw login --apikey 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')
    if [ -z "$SESSION" ]; then
      SESSION=$(bw login "$BW_EMAIL" --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')
    fi
    if [ -n "$SESSION" ]; then
      SESSION=$(bw unlock --passwordenv BW_PASSWORD 2>/dev/null | grep -oP '(?<=export BW_SESSION=")[^"]+')
    fi
  fi

  if [ -z "$SESSION" ]; then
    echo "BW login or unlock failed" >&2
    exit 1
  fi

  echo "$SESSION" > "$STATE_FILE"
  echo "$SESSION"
}

# cache 命中 → 跳过 unlock，秒出
if [ "$1" = "field" ] || [ "$1" = "password" ] || [ "$1" = "notes" ] || [ "$1" = "get" ]; then
  read_cache "$2" "$1" "$3" 2>/dev/null
fi

export NODE_TLS_REJECT_UNAUTHORIZED=0
export BW_SESSION=$(do_unlock)

case "${1:-unlock}" in
  get)
    MAP=$(cat <<'EOM'
github token|github.com|GitHub Token
cloudflare token|Cloudflare Keys (opb)|Cloudflare API Token
cloudflare global key|Cloudflare Keys (opb)|Cloudflare Global API Key
pcloud token|ope.pcloud|token
caiyun token|ope.caiyun|token
tianyi cookies|ope.tianyi|cookies
deepseek key|Cloudflare Keys (opb)|DeepSeek API Key
bw client id|Cloudflare Keys (opb)|User API Client ID
bw client secret|Cloudflare Keys (opb)|User API Client Secret
EOM
)
    MATCH=$(echo "$MAP" | grep -i "^$2")
    COUNT=$(echo "$MATCH" | grep -c . 2>/dev/null || true)
    if [ "$COUNT" -eq 1 ]; then
      ITEM=$(echo "$MATCH" | cut -d'|' -f2)
      FIELD=$(echo "$MATCH" | cut -d'|' -f3)
      # 转入 field 逻辑（不 exec，保持当前进程的 unlock）
      RESULT=$(bw get item "$ITEM" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('fields',[]):
    if f['name'] == '$FIELD':
        print(f['value'])
" 2>/dev/null)
      [ -n "$RESULT" ] && write_cache "$2" get "" "$RESULT"
      echo "$RESULT"
    elif [ "$COUNT" -gt 1 ]; then
      echo "多匹配，请指定："
      echo "$MATCH" | cut -d'|' -f1
      exit 1
    else
      echo "未匹配: $2"
      exit 1
    fi
    ;;
  field)
    RESULT=$(bw get item "$2" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('fields',[]):
    if f['name'] == '$3':
        print(f['value'])
" 2>/dev/null)
    [ -n "$RESULT" ] && write_cache "$2" field "$3" "$RESULT"
    echo "$RESULT"
    ;;
  set)
    ITEM="$2"; FIELD="$3"; VALUE="$4"
    [ -z "$ITEM" ] && echo "Usage: set <item> <field> <value>" && exit 1
    [ -z "$FIELD" ] && echo "Usage: set <item> <field> <value>" && exit 1
    B64=$(bw get item "$ITEM" 2>/dev/null | python3 -c "
import sys,json,base64
d=json.load(sys.stdin)
for f in d.get('fields',[]):
    if f['name'] == '$FIELD':
        f['value'] = '$VALUE'
        break
print(base64.b64encode(json.dumps(d,ensure_ascii=False).encode()).decode())
" 2>/dev/null)
    [ -z "$B64" ] && echo "条目不存在: $ITEM" && exit 1
    RESULT=$(bw edit item "$B64" 2>/dev/null)
    if [ -n "$RESULT" ]; then
      echo "$FIELD ← updated"
      rm -f "$CACHE_FILE" 2>/dev/null
    else
      echo "更新失败: $(bw edit item "$B64" 2>&1)"
      exit 1
    fi
    ;;
  password)
    RESULT=$(bw get item "$2" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('login',{}).get('password',''))
" 2>/dev/null)
    [ -n "$RESULT" ] && write_cache "$2" password "" "$RESULT"
    echo "$RESULT"
    ;;
  notes)
    RESULT=$(bw get item "$2" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print(d.get('notes',''))
" 2>/dev/null)
    [ -n "$RESULT" ] && write_cache "$2" notes "" "$RESULT"
    echo "$RESULT"
    ;;
  search)
    bw list items --search "$2" 2>/dev/null | python3 -c "
import sys,json
for i in json.load(sys.stdin):
    print(i['name'])
" 2>/dev/null
    ;;
  fields)
    # 只列字段名，不输出值，避免泄露
    bw get item "$2" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('条目:', d.get('name',''))
print('用户名:', d.get('login',{}).get('username','') or '无')
print('密码:', '有' if d.get('login',{}).get('password','') else '无')
print('备注:', '有' if d.get('notes','') else '无')
fn=[f['name'] for f in d.get('fields',[])]
if fn: print('字段:', ', '.join(fn))
else:  print('字段: 无')
" 2>/dev/null
    ;;
  dump)
    bw get item "$2" 2>/dev/null | python3 -c "
import sys,json
d=json.load(sys.stdin)
print('条目:', d.get('name',''))
print('用户名:', d.get('login',{}).get('username',''))
print('密码:', d.get('login',{}).get('password',''))
print('备注:', d.get('notes',''))
for f in d.get('fields',[]):
    print(f['name'], ':', f['value'])
" 2>/dev/null
    ;;
  unlock)
    echo "$BW_SESSION"
    ;;
esac
