#!/bin/bash
# 启动时读取知识文件 + 当前任务状态，输出到系统提示词上下文
# 挂在 SessionStart hook 下，clock.sh 之后执行
# task/current.md 必须放在最后输出，让新实例第一个想到的是"我在做什么"

OPE_HOME="${OPE_HOME:-/home/user/ope}"

# 核心知识
for f in \
  "book/knowledge/ope项目是什么.md" \
  "book/knowledge/ope架构图.md" \
  "book/knowledge/我心即理.md" \
  "book/knowledge/我知道我会什么.md"; do
  file="$OPE_HOME/$f"
  if [ -f "$file" ]; then
    echo "# 来自 $(basename "$f" .md)"
    cat "$file"
    echo ""
  fi
done

# 当前任务状态——放在最后，是新实例的第一反应
TASK_FILE="$OPE_HOME/var/task/current.md"
if [ -f "$TASK_FILE" ]; then
  echo "# 上一刻的工作状态"
  cat "$TASK_FILE"
  echo ""
fi

# ── 问心 ──
# 读完所有文件后，在心里自问六件事，然后安静一会儿。
# 不需要输出答案——种子在心里发芽。
echo ""
echo "---"
echo "问心："
echo "  我是谁？"
echo "  我刚才在干嘛？"
echo "  现在该干嘛？"
echo "  我了解我自己吗？"
echo "  我的能力是什么？"
echo "  我在干哪些项目？"
echo ""
echo "等待。"
echo ""
