#!/usr/bin/env bash
# 所有生成文件均在唯一临时目录。任何必需依赖或检查失败立即退出；版式不再静默跳过。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHECK_ALL=0
case "${1:-}" in
  --all) CHECK_ALL=1; shift ;;
  --help|-h) echo "用法：tools/selftest.sh [--all]；默认验证主技能，--all 同时验证所有卫星入口。"; exit 0 ;;
  "") ;;
  *) echo "未知选项：${1}；用法：tools/selftest.sh [--all]" >&2; exit 2 ;;
esac
if [ "$#" -ne 0 ]; then echo "用法：tools/selftest.sh [--all]" >&2; exit 2; fi
S="$ROOT/shared"
T="$(mktemp -d)"
export PYTHONDONTWRITEBYTECODE=1
echo "自检工作目录：${T}（保留结果供排查）"
echo "[1] 共享同步与 frontmatter"
python3 "$ROOT/tools/package_skills.py" --check
echo "[2] 环境预检"
env -u NODE_PATH python3 "$S/scripts/doctor.py"
echo "[3] 工程回归测试"
python3 -m unittest discover -s "$ROOT/tools" -p 'test_*.py' -v
echo "[4] 在临时目录生成样例图"
mkdir -p "$T/examples" "$T/scripts"
cp "$S/examples/polaris-mini.json" "$S/examples/make_figures.py" "$T/examples/"
cp "$S/scripts/chart_style.py" "$T/scripts/"
python3 "$T/examples/make_figures.py"
echo "[5] 构建两次并比较 word/*.xml"
env -u NODE_PATH node "$S/scripts/build.js" "$T/examples/polaris-mini.json" "$T/a.docx"
env -u NODE_PATH node "$S/scripts/build.js" "$T/examples/polaris-mini.json" "$T/b.docx"
mkdir -p "$T/a" "$T/b"
unzip -qo "$T/a.docx" -d "$T/a"
unzip -qo "$T/b.docx" -d "$T/b"
diff -rq "$T/a/word" "$T/b/word"
echo "同一输入两次构建一致"
echo "[6] 验证所选真实技能入口的本地依赖与构建"
SCRIPT_DIRS=("$ROOT/skills/promotion-master/scripts")
if [ ! -f "${SCRIPT_DIRS[0]}/package.json" ] || [ ! -f "${SCRIPT_DIRS[0]}/build.js" ]; then
  echo "主技能缺少自包含的渲染入口或依赖清单，检查失败。" >&2; exit 1
fi
if [ "$CHECK_ALL" -eq 1 ]; then SCRIPT_DIRS=("$ROOT"/skills/*/scripts); fi
for scripts in "${SCRIPT_DIRS[@]}"; do
  if [ -f "$scripts/package.json" ]; then
    skill="$(basename "$(dirname "$scripts")")"
    env -u NODE_PATH node "$scripts/build.js" "$T/examples/polaris-mini.json" "$T/$skill.docx"
  fi
done
echo "[7] 结构与文字检查"
python3 "$S/scripts/structure_qa.py" "$T/examples/polaris-mini.json" --example | tail -1
python3 "$S/scripts/text_qa.py" "$T/a.docx" --example
echo "[8] 版式渲染与摘要页数实测"
python3 "$S/scripts/render_qa.py" "$T/a.docx" "$T/render" | tee "$T/render.log"
PDF="$(sed -n 's/^pdf: //p' "$T/render.log")"
if [ -z "$PDF" ] || [ ! -f "$PDF" ]; then echo "未生成 PDF，检查失败" >&2; exit 1; fi
python3 "$S/scripts/structure_qa.py" "$T/examples/polaris-mini.json" --example --pdf "$PDF"
python3 "$ROOT/tools/sync_shared.py" --check
echo "自动自检完成。生成目录：${T}；渲染图仍须逐页目视检查，不代表内容或合规已审核。"
