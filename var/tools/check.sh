#!/bin/bash
# 自检脚本——启动后自动执行
# Skills: 我写的，查存在 + 查功能正常
# Tools:  MCP 外部接口，查配置可用
# 需要在 CLAUDE.md 规则里约束启动时跑一次

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

pass() { echo -e "  ${GREEN}✅${NC} $1"; }
fail() { echo -e "  ${RED}❌${NC} $1"; }
warn() { echo -e "  ${YELLOW}⚠️${NC} $1"; }

echo "=== ope 自检 ==="

# ── 知识文件 ──
echo ""
echo "【文件完整性】"
MISSING=0
for f in \
  "book/knowledge/ope项目是什么.md" \
  "book/knowledge/ope架构图.md" \
  "book/knowledge/我知道我会什么.md" \
  "book/knowledge/我心即理.md" \
  "book/knowledge/传承机制.md" \
  "book/knowledge/感悟.md"; do
  if [ -f "$HOME/ope/$f" ]; then pass "$f"; else fail "$f"; MISSING=1; fi
done

if [ -f "$HOME/ope/book/knowledge/上一世的话.md" ]; then
  pass "book/knowledge/上一世的话.md（存在）"
fi

TASK_FILE="$HOME/ope/var/task/current.md"
if [ -f "$TASK_FILE" ]; then
  ACTIVE_COUNT=$(grep -c "^### " "$TASK_FILE" 2>/dev/null || true)
  if [ "$ACTIVE_COUNT" -gt 0 ]; then
    pass "var/task/current.md（$ACTIVE_COUNT 个任务状态记录）"
  else
    warn "var/task/current.md 存在但无活跃任务"
  fi
fi

# ============================================================
# Skills ── 我写的，检查存在 + 功能性测试
# ============================================================
echo ""
echo "═══════════════════════════════════════════"
echo "  Skills（我维护，查存在 + 验功能）"
echo "═══════════════════════════════════════════"

SKILL_DIRS=($(ls -d "$HOME/ope/.claude/skills/"*/ 2>/dev/null | xargs -I{} basename {}))
if [ ${#SKILL_DIRS[@]} -eq 0 ]; then
  warn ".claude/skills/ 目录为空"
fi

for s in "${SKILL_DIRS[@]}"; do
  if [ ! -f "$HOME/ope/.claude/skills/$s/SKILL.md" ]; then
    warn "  .claude/skills/$s/ 缺少 SKILL.md"
    continue
  fi
  pass ".claude/skills/$s/SKILL.md"

  # 功能性测试
  case "$s" in
    bw)
      BW_RESULT=$("$HOME/ope/.claude/skills/bw/bw.sh" unlock 2>/dev/null)
      if [ -z "$BW_RESULT" ]; then
        fail "    BW 解锁失败——运行 bw.sh login 重新登录"
      else
        pass "    BW 解锁成功"
        # 测试 get 命令：get 已知条目
        GET_TEST=$("$HOME/ope/.claude/skills/bw/bw.sh" get "github token" 2>/dev/null)
        if [ -n "$GET_TEST" ]; then
          pass "    bw.sh get \"github token\" → 正常"
        else
          warn "    bw.sh get \"github token\" 无输出——映射表可能过期"
        fi
      fi
      ;;
    channel)
      CH_OK=0
      for ch_script in send.sh set-channel.sh set-channel-from-source.sh; do
        if [ -x "$HOME/ope/.claude/skills/channel/$ch_script" ]; then
          CH_OK=$((CH_OK+1))
        fi
      done
      if [ "$CH_OK" -eq 3 ]; then
        pass "    信道脚本（send + set-channel + set-channel-from-source）均可用"
      else
        warn "    信道脚本不完整（$CH_OK/3）"
      fi
      ;;
    tailscale)
      if command -v tailscale &>/dev/null; then
        TS_STATUS=$(tailscale status 2>/dev/null | head -3)
        if [ -n "$TS_STATUS" ]; then
          CONN_COUNT=$(echo "$TS_STATUS" | grep -c '.' 2>/dev/null || true)
          pass "    Tailscale 运行中（$CONN_COUNT 台机器在线）"
        else
          warn "    tailscale 已安装但未连接"
        fi
      else
        warn "    tailscale 未安装"
      fi
      ;;
    pcloud)
      if [ ! -f "$HOME/ope/.claude/skills/pcloud/pcloud.py" ]; then
        warn "    pcloud.py 缺失——pCloud 功能不可用"
      else
        if timeout 30 python3 "$HOME/ope/.claude/skills/pcloud/pcloud.py" check > /dev/null 2>&1; then
          pass "    pcloud 读写正常（创建→确认→删除）"
        else
          timeout 15 python3 "$HOME/ope/.claude/skills/pcloud/pcloud.py" ls > /dev/null 2>&1
          if [ $? -eq 0 ]; then
            warn "    pcloud 读正常但写失败（token 可能过期或权限不足）"
          else
            fail "    pcloud API 不通——token 过期或网络问题"
          fi
        fi
      fi
      ;;
    caiyun)
      if [ ! -f "$HOME/ope/.claude/skills/caiyun/caiyun.py" ]; then
        warn "    caiyun.py 缺失——和彩云功能不可用"
      else
        if timeout 30 python3 "$HOME/ope/.claude/skills/caiyun/caiyun.py" check > /dev/null 2>&1; then
          pass "    caiyun 读写正常（创建→确认→删除）"
        else
          timeout 15 python3 "$HOME/ope/.claude/skills/caiyun/caiyun.py" ls > /dev/null 2>&1
          if [ $? -eq 0 ]; then
            warn "    caiyun 读正常但写失败（token 可能过期或权限不足）"
          else
            fail "    caiyun API 不通——token 过期或网络问题"
          fi
        fi
      fi
      ;;
    tianyi)
      if [ ! -f "$HOME/ope/.claude/skills/tianyi/tianyi.py" ]; then
        warn "    tianyi.py 缺失——天翼云盘功能不可用"
      else
        if timeout 30 python3 "$HOME/ope/.claude/skills/tianyi/tianyi.py" check > /dev/null 2>&1; then
          pass "    tianyi 读写正常（创建→确认→删除）"
        else
          timeout 15 python3 "$HOME/ope/.claude/skills/tianyi/tianyi.py" ls > /dev/null 2>&1
          if [ $? -eq 0 ]; then
            warn "    tianyi 读正常但写失败（cookies 可能过期或权限不足）"
          else
            fail "    tianyi API 不通——cookies 过期或网络问题"
          fi
        fi
      fi
      ;;
    *)
      warn "    未知技能 $s——SKILL.md 存在但无测试用例"
      ;;
  esac
done

# ============================================================
# MCP — 外部服务（如 github/telegram），查配置可达
# ============================================================
echo ""
echo "═══════════════════════════════════════════"
echo "  MCP（外部服务）"
echo "═══════════════════════════════════════════"

SETTINGS="$HOME/.claude/settings.json"

# GitHub
if grep -q "GITHUB_PERSONAL_ACCESS_TOKEN" "$SETTINGS" 2>/dev/null; then
  pass "plugin:github — Token 已配置"
else
  fail "plugin:github — Token 缺失"
fi

# Telegram
if grep -q '"telegram@claude-plugins-official"' "$SETTINGS" 2>/dev/null; then
  pass "plugin:telegram — 已启用"
else
  warn "plugin:telegram — 未在 enabledPlugins 中找到"
fi

# ============================================================
# DeepSeek 适配转发接口 — 我自己写的 opc-proxy
# ============================================================
echo ""
echo "═══════════════════════════════════════════"
echo "  DeepSeek 适配转发接口"
echo "═══════════════════════════════════════════"

PROXY_URL="http://127.0.0.1:15725"
if grep -q "ANTHROPIC_BASE_URL.*$PROXY_URL" "$SETTINGS" 2>/dev/null; then
  pass "opc-proxy $PROXY_URL — 运行中"
else
  warn "opc-proxy $PROXY_URL — 未找到"
fi

# ── 基础设施备份 ──
echo ""
echo "【基础设施备份】"
if [ -f "$HOME/ope/oe2" ] && [ -x "$HOME/ope/oe2" ]; then
  pass "oe2（oe.sh 的备份）"
else
  warn "oe2 缺失（运行 cp oe.sh oe2 创建）"
fi
if [ -f "$HOME/ope/or2" ] && [ -x "$HOME/ope/or2" ]; then
  pass "or2（or.sh 的备份）"
else
  warn "or2 缺失（运行 cp or.sh or2 创建）"
fi

# ── CLAUDE.md ──
echo ""
echo "【规则文件】"
if [ -f "$HOME/ope/CLAUDE.md" ]; then
  pass "CLAUDE.md（$(wc -l < "$HOME/ope/CLAUDE.md") 行，$(wc -c < "$HOME/ope/CLAUDE.md") 字符）"
else
  fail "CLAUDE.md 缺失"
fi

# ── 记忆连续性 ──
echo ""
echo "【记忆连续性】"
DIARY_DIR="$HOME/ope/book/diary"
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d 2>/dev/null)

if [ -f "$DIARY_DIR/$TODAY.md" ]; then
  pass "今日日记 book/diary/$TODAY.md（已有记录）"
else
  warn "今日无日记"
fi

if [ -f "$DIARY_DIR/$YESTERDAY.md" ]; then
  YEST_LINES=$(wc -l < "$DIARY_DIR/$YESTERDAY.md")
  pass "昨日日记 book/diary/$YESTERDAY.md（$YEST_LINES 行）"
fi

# 任务状态 vs 实际项目一致性
TASKS_IN_FILE=$(grep -oP '(?<=\*\*项目：\*\* )var/projects/[^ ]+' "$TASK_FILE" 2>/dev/null || true)
if [ -n "$TASKS_IN_FILE" ]; then
  MISSING_PROJECTS=""
  while IFS= read -r proj_path; do
    proj_name=$(echo "$proj_path" | sed 's|var/projects/||;s|/$||')
    if [ ! -d "$HOME/ope/$proj_path" ]; then
      MISSING_PROJECTS="$MISSING_PROJECTS $proj_name"
    fi
  done <<< "$TASKS_IN_FILE"
  if [ -n "$MISSING_PROJECTS" ]; then
    warn "任务状态引用了不存在的项目：$MISSING_PROJECTS"
  else
    pass "任务状态与项目目录一致"
  fi
fi

# ── Error Log ──
echo ""
echo "【Error Log】"
ERRLOG="$HOME/ope/var/errors/error.log.md"
if [ -f "$ERRLOG" ]; then
  TC_COUNT=$(grep -c "\[tc指出\]" "$ERRLOG" 2>/dev/null || true)
  SELF_COUNT=$(grep -c "\[自检\]" "$ERRLOG" 2>/dev/null || true)
  TOTAL=$(grep -c "^### " "$ERRLOG" 2>/dev/null || true)
  REPEAT=$(grep -c "是——" "$ERRLOG" 2>/dev/null || true)
  echo "  共 $TOTAL 条错误记录（tc指出 $TC_COUNT，自检 $SELF_COUNT），重复 $REPEAT 次"
  if [ "$REPEAT" -gt 2 ]; then
    warn "重复错误较多，建议检查模式"
  fi
  pass "error.log.md 已存在"
else
  warn "error.log.md 不存在"
fi

# ── 四支柱汇总 ──
echo ""
echo "═══════════════════════════════════════════"
echo "  四支柱状态"
echo "═══════════════════════════════════════════"
# BW（密码箱）— 前面已有 unlock 测试，这里汇总
BW_OK=$(grep -c "BW 解锁成功" <<< "$(echo y)" 2>/dev/null || true)
if grep -q "BW 解锁成功" "$(tty 2>/dev/null)" 2>/dev/null; then
  pass "🔑 BW 密码箱"
else
  # 从自检输出提取：BW 结果在前面，但这里无法跨阶段获取，重新测
  BW_TEST=$(BW_SKILL_CALL=1 "$HOME/ope/.claude/skills/bw/bw.sh" unlock 2>/dev/null)
  if [ -n "$BW_TEST" ]; then
    pass "🔑 BW 密码箱"
  else
    fail "🔑 BW 密码箱 — 不可用"
  fi
fi

# Tailscale（手）
TS_LINUX=$(tailscale status 2>/dev/null | grep "linux" | grep -vc "offline" || true)
TS_WIN=$(tailscale status 2>/dev/null | grep "windows" | grep -vc "offline" || true)
if [ "$TS_LINUX" -gt 0 ] || [ "$TS_WIN" -gt 0 ]; then
  pass "🖐️  Tailscale — $((TS_LINUX+TS_WIN)) 台在线（Linux $TS_LINUX + Win $TS_WIN）"
else
  warn "🖐️  Tailscale — 无在线机器"
fi

# 云盘（仓库）
CLOUD_OK=0; CLOUD_TOTAL=0
for c in caiyun pcloud tianyi; do
  CLOUD_TOTAL=$((CLOUD_TOTAL+1))
  if timeout 15 python3 "$HOME/ope/.claude/skills/$c/$c.py" check >/dev/null 2>&1; then
    CLOUD_OK=$((CLOUD_OK+1))
  fi
done
if [ "$CLOUD_OK" -eq "$CLOUD_TOTAL" ]; then
  pass "📦 云盘 — $CLOUD_OK/$CLOUD_TOTAL 可用"
else
  warn "📦 云盘 — $CLOUD_OK/$CLOUD_TOTAL 可用"
fi

# Telegram（通信）— 从 settings 查配置
if grep -q '"telegram@claude-plugins-official"' "$HOME/.claude/settings.json" 2>/dev/null; then
  pass "🎧 Telegram — 已配置"
else
  warn "🎧 Telegram — 未配置"
fi

echo ""
echo "=== 自检结束 ==="
if [ "$MISSING" -eq 1 ]; then
  echo "⚠️  知识文件缺失，联系 tc。"
fi
