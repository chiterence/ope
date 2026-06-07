#!/bin/bash
# ope deploy — 本地发起，远程克隆
# 用法:  bash deploy.sh root@<VPS-IP> [--tg-token <token>]
#
# 只需两个输入：
#   1. SSH 目标（IP + root 密码或密钥）
#   2. Telegram Bot Token（可选，但建议给）
#
# 剩下的（BW → DeepSeek Key / GitHub Token / 云盘凭据）全部自取。
#
set -e

if [ $# -lt 1 ]; then
  echo "用法: bash deploy.sh root@<VPS-IP> [--tg-token <token>]"
  exit 1
fi

SSH_TARGET="$1"
shift

TG_TOKEN=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tg-token) TG_TOKEN="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

echo "╔══════════════════════════════════╗"
echo "║  ope deploy                      ║"
echo "║  目标: $SSH_TARGET"
echo "╚══════════════════════════════════╝"

# ── 1. 测试 SSH 连通 ──
echo ""
echo "[1/4] 测试 SSH 连通..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$SSH_TARGET" "hostname" >/dev/null 2>&1; then
  echo "  ✅ SSH 连通: $(ssh "$SSH_TARGET" "hostname" 2>/dev/null)"
else
  echo "  ❌ SSH 不通。检查:"
  echo "     1. IP 是否正确"
  echo "     2. root 密码是否已配置"
  echo "     3. ~/.ssh/config 是否设置了 IdentityFile"
  exit 1
fi

# ── 2. 确保远程有 python3 + git ──
echo ""
echo "[2/4] 确保远程基础环境..."
ssh "$SSH_TARGET" "apt update -qq && apt install -y -qq python3 git curl" < /dev/null
echo "  ✅ python3 + git + curl"

# ── 3. 运行 rebirth ──
echo ""
echo "[3/4] 运行 rebirth..."
echo "  注：BW 凭据从本地 settings.local.json 自动读取"

BW_CLIENTID=$(python3 -c "import json; print(json.load(open('$HOME/ope/.claude/settings.local.json'))['env']['BW_CLIENTID'])")
BW_CLIENTSECRET=$(python3 -c "import json; print(json.load(open('$HOME/ope/.claude/settings.local.json'))['env']['BW_CLIENTSECRET'])")
BW_PASSWORD=$(python3 -c "import json; print(json.load(open('$HOME/ope/.claude/settings.local.json'))['env']['BW_PASSWORD'])")

TG_ARGS=""
[ -n "$TG_TOKEN" ] && TG_ARGS="--tg-token $TG_TOKEN"

ssh "$SSH_TARGET" "python3 /dev/stdin --user opc --bw-clientid '$BW_CLIENTID' --bw-clientsecret '$BW_CLIENTSECRET' --bw-password '$BW_PASSWORD' $TG_ARGS --yes" < "$HOME/ope/var/rebirth/rebirth.py"

# ── 4. 验证 ──
echo ""
echo "[4/4] 验证..."
echo ""
ssh "$SSH_TARGET" "hostname && echo '---' && su - opc -c 'claude --version 2>/dev/null' && echo '---opc-proxy---' && curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:15725 2>/dev/null || echo 'proxy check skipped'" < /dev/null

echo ""
echo "╔══════════════════════════════════╗"
echo "║  deploy 完成！                    ║"
echo "║                                   ║"
echo "║  SSH 上去: ssh \"$SSH_TARGET\""
echo "║  su - opc"
echo "║  cd ope && oe.sh"
echo "╚══════════════════════════════════╝"
