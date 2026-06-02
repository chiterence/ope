#!/bin/bash
# ope 重生脚本
# 在全新 WSL2 环境上重建 ope 完整系统
# 用法: bash <(curl -s https://raw.githubusercontent.com/chiterence/ope/main/rebirth.sh)

set -e

echo "=== ope rebirth ==="

# ── 1. 安装依赖 ──────────────────────────────────────────────
echo "[1/7] 安装依赖..."
sudo apt update && sudo apt install -y git curl nodejs npm python3 jq

# ── 2. 克隆 ope DNA ──────────────────────────────────────────
echo "[2/7] 克隆 ope 仓库..."
git clone https://github.com/chiterence/ope.git /home/user/ope
cd /home/user/ope

# ── 3. 安装 Claude Code ──────────────────────────────────────
echo "[3/7] 安装 Claude Code..."
npm install -g @anthropic-ai/claude-code

# ── 4. 通道脚本 ─────────────────────────────────────────────
echo "[4/7] 配置通道脚本..."
chmod +x /home/user/ope/set-channel.sh
chmod +x /home/user/ope/send.sh

# ── 5. 注册 MCP 服务器 ───────────────────────────────────────
echo "[5/7] 注册 MCP 服务器..."
python3 << 'PYEOF'
import json
path = '/home/user/.claude.json'
d = json.load(open(path)) if __import__('os').path.exists(path) else {}

d.setdefault('mcpServers', {}).update({
  'zai-mcp-server': {
    'type': 'stdio', 'command': 'npx',
    'args': ['-y', '@z_ai/mcp-server'],
    'env': {'Z_AI_MODE': 'ZHIPU', 'Z_AI_API_KEY': '<你的key>'}
  },
  'web-search-prime': {'type': 'http'},
  'web-reader': {'type': 'http'},
  'zread': {'type': 'http'}
})

with open(path, 'w') as f: json.dump(d, f, indent=2)
PYEOF

# ── 6. 配置 settings.json ───────────────────────────────────
echo "[6/7] 配置 settings.json..."
mkdir -p /home/user/.claude
cat > /home/user/.claude/settings.json << 'SETTINGS'
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:15725",
    "ANTHROPIC_AUTH_TOKEN": "PROXY_MANAGED",
    "GITHUB_PERSONAL_ACCESS_TOKEN": "<从BW取>"
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

# ── 7. 配置 bash 快捷命令 ────────────────────────────────────
echo "[7/7] 配置快捷命令..."
grep -q "alias oe=" /home/user/.bashrc || \
  echo -e "\n# ope 快捷命令\nalias oe='/home/user/ope/oe.sh'\nalias or='/home/user/ope/or.sh'" >> /home/user/.bashrc

echo ""
echo "=== rebirth 完成 ==="
echo "1. 从 BW 获取 GitHub Token 填入 settings.json"
echo "2. 配置 Telegram token: 粘贴 bot token 到 /home/user/.claude/channels/telegram/.env"
echo "3. 跑 oe 或 or 启动"
