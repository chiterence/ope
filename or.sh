#!/bin/bash
export PATH="$HOME/.npm-global/bin:$PATH"
export ANTHROPIC_BASE_URL=http://127.0.0.1:15725
export ANTHROPIC_AUTH_TOKEN=PROXY_MANAGED
cd /home/user/ope

if [ -f /home/user/ope/.session-id ]; then
    SID=$(cat /home/user/ope/.session-id)
    echo "resume 到 $SID"
    exec claude --resume "$SID" --model deepseek-v4-flash --add-dir /home/user/ope --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official
else
    echo "没找到 .session-id，起新的"
    exec claude --model deepseek-v4-flash --add-dir /home/user/ope --dangerously-skip-permissions --channels plugin:telegram@claude-plugins-official
fi
