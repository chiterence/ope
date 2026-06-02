#!/bin/bash
# ope 重生脚本
set -e

echo "=== ope rebirth ==="

# ── 1. 安装依赖 ──────────────────────────────────────────────
echo "[1/7] 安装依赖..."
sudo apt update && sudo apt install -y git curl nodejs npm python3 jq

# ── 2. 配置 GitHub ──────────────────────────────────────────
echo "[2/7] 配置 GitHub 访问..."
echo "需要 GitHub classic PAT（https://github.com/settings/tokens，勾 repo 权限）"
read -p "粘贴 token: " GH_TOKEN
echo "$GH_TOKEN" | gh auth login --with-token 2>/dev/null || true

git clone https://github.com/chiterence/ope.git /home/user/ope
cd /home/user/ope
git remote set-url origin https://$GH_TOKEN@github.com/chiterence/ope.git

# ── 3. 安装 Claude Code ──────────────────────────────────────
echo "[3/7] 安装 Claude Code..."
npm install -g @anthropic-ai/claude-code

# ── 4. 通道脚本 ─────────────────────────────────────────────
echo "[4/7] 配置通道脚本..."
chmod +x /home/user/ope/set-channel.sh
chmod +x /home/user/ope/send.sh

# ── 5. MCP 服务器 ───────────────────────────────────────────
echo "[5/7] 注册 MCP 服务器..."
python3 << 'PYEOF'
import json, os
path = '/home/user/.claude.json'
d = json.load(open(path)) if os.path.exists(path) else {}
d.setdefault('mcpServers', {}).update({
  'zai-mcp-server': {'type': 'stdio', 'command': 'npx',
    'args': ['-y', '@z_ai/mcp-server'],
    'env': {'Z_AI_MODE': 'ZHIPU', 'Z_AI_API_KEY': '<需填入>'}},
  'web-search-prime': {'type': 'http'},
  'web-reader': {'type': 'http'},
  'zread': {'type': 'http'}
})
with open(path, 'w') as f: json.dump(d, f, indent=2)
PYEOF

# ── 6. settings.json ────────────────────────────────────────
echo "[6/7] 配置 settings.json..."
mkdir -p /home/user/.claude
cat > /home/user/.claude/settings.json << 'SETTINGS'
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:15725",
    "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED",
    "GITHUB_PERSONAL_ACCESS_TOKEN": "填入token"
  },
  "enabledPlugins": {
    "telegram@claude-plugins-official": true,
    "github@claude-plugins-official": true
  },
  "skipDangerousModePermissionPrompt": true,
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "/home/user/ope/set-channel.sh",
        "timeout": 3
      }]
    }]
  },
  "permissions": {
    "deny": [
      "mcp__plugin_telegram_telegram__reply",
      "mcp__plugin_telegram_telegram__react",
      "mcp__plugin_telegram_telegram__edit_message"
    ]
  }
}
SETTINGS
sed -i "s/填入token/$GH_TOKEN/" /home/user/.claude/settings.json

# ── 7. bash 快捷命令 ────────────────────────────────────────
echo "[7/7] 配置快捷命令..."
grep -q "alias oe=" /home/user/.bashrc || {
  echo -e "\n# ope 快捷命令" >> /home/user/.bashrc
  echo "alias oe='/home/user/ope/oe.sh'" >> /home/user/.bashrc
  echo "alias or='/home/user/ope/or.sh'" >> /home/user/.bashrc
}

echo ""
echo "=== rebirth 完成 ==="
echo "下一步: 配置 Telegram token → /home/user/.claude/channels/telegram/.env"
echo "然后: 跑 oe 或 or 启动"
