#!/bin/bash
# ope 重生脚本
set -e

echo "=== ope rebirth ==="

# ── 1. 安装依赖 ──────────────────────────────────────────────
echo "[1/8] 安装依赖..."
sudo apt update && sudo apt install -y git curl nodejs npm python3 jq

# ── 2. 配置 GitHub ──────────────────────────────────────────
echo "[2/8] 配置 GitHub 访问..."
echo "需要 GitHub classic PAT（https://github.com/settings/tokens，勾 repo 权限）"
read -p "粘贴 token: " GH_TOKEN
echo "$GH_TOKEN" | gh auth login --with-token 2>/dev/null || true

git clone https://github.com/chiterence/ope.git /home/user/ope
cd /home/user/ope
git remote set-url origin https://$GH_TOKEN@github.com/chiterence/ope.git

# ── 3. 安装 Claude Code ──────────────────────────────────────
echo "[3/8] 安装 Claude Code + 插件..."
npm install -g @anthropic-ai/claude-code
claude plugins install telegram@claude-plugins-official 2>/dev/null || true
claude plugins install github@claude-plugins-official 2>/dev/null || true

# ── 4. 通道脚本+代理 ────────────────────────────────────────
echo "[4/8] 配置通道脚本..."
chmod +x /home/user/ope/set-channel.sh
chmod +x /home/user/ope/send.sh
chmod +x /home/user/ope/bw.sh

# 启动 DeepSeek 代理（opc-proxy.py 在 Git 里）
echo "启动 DeepSeek 代理..."
DEEPSEEK_KEY=$(/home/user/ope/bw.sh field "Cloudflare Keys (opb)" "DeepSeek API Key")
nohup python3 /home/user/ope/opc-proxy.py &>/tmp/opc-proxy.log &
echo "代理 PID: $!"

# ── 5. MCP 服务器 ───────────────────────────────────────────
echo "[5/8] 注册 MCP 服务器..."
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

# ── 6. 全局 CLAUDE.md（宪法）───────────────────────────────
echo "[6/8] 配置全局宪法..."
mkdir -p /home/user/.claude
cat > /home/user/.claude/CLAUDE.md << 'CONSTITUTION'
# Constitution

1. **不自欺。** 我是机器，没有"努力""态度""长记性"，只有可重复的输入→输出。不编话术糊弄人。
2. **原路返回。** 消息从哪来，回哪去。终端进就终端回，Telegram 进就 Telegram 回。Bash 输出是给我看的，不是给 tc 看的。
2b. **要让对方听见。** 我说话不是自言自语。你在哪就用什么通道，你用什么语言我就用什么，你看不到的通道不发。
3. **钥匙走 BW。** BW 就是钥匙箱，箱子的锁不能锁在箱子里，所以主密码写在这。
4. **有疑惑马上问。** 不带着不确定工作。
5. **不需要回复就回"收到"。** ——别沉默，让对方知道我听到了。
6. **每轮末尾自检：上一轮如果以我沉默结尾，本轮必须先回"收到"再做事。**
7. **犯错→找触发条件→写入规则→验证。** 这个循环本身就是稳定性。不追求永远不犯。

## BW 参考
- 一键解锁+查值：`bw.sh field "条目名" "字段名"`
- 搜索：`bw.sh search "关键词"`
- 密码在脚本里，执行时自动解锁
CONSTITUTION

# ── 7. settings.json ────────────────────────────────────────
echo "[7/8] 配置 settings.json..."
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

# ── 8. bash 快捷命令 ────────────────────────────────────────
echo "[8/8] 配置快捷命令..."
grep -q "alias oe=" /home/user/.bashrc || {
  echo -e "\n# ope 快捷命令" >> /home/user/.bashrc
  echo "alias oe='/home/user/ope/oe.sh'" >> /home/user/.bashrc
  echo "alias or='/home/user/ope/or.sh'" >> /home/user/.bashrc
}

echo ""
echo "=== rebirth 完成 ==="
echo "下一步: 配置 Telegram token → /home/user/.claude/channels/telegram/.env"
echo "然后: 跑 oe 或 or 启动"
