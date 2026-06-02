#!/bin/bash
export PATH="$HOME/.npm-global/bin:$PATH"
export ANTHROPIC_BASE_URL=http://127.0.0.1:15725
export ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED
cd /home/user/ope
# 新开会话，清除旧的 session-id 标记
rm -f /home/user/ope/.session-id
echo "起新 session..."
exec claude --model deepseek-v4-flash --add-dir /home/user/ope --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official
