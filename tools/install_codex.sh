#!/usr/bin/env bash
# 默认只装自包含主技能；--all 额外安装卫星。既有同名目录/无关链接必须由用户自行处理。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
DEST="$HOME/.agents/skills"
INSTALL_ALL=0
DEST_SET=0

usage() {
  echo "用法：tools/install_codex.sh [--all] [--dest 目标目录 | 目标目录]"
  echo "  默认：只安装自包含的 promotion-master，保留已安装的旧技能。"
  echo "  --all：同时安装仓库内卫星；同名目录或其他仓库的链接冲突时停止。"
  echo "  --dest：指定安装目录，默认 ~/.agents/skills；也接受一个位置参数。"
  echo "  --help：查看说明，不执行安装。"
}
set_destination() {
  if [ "$DEST_SET" -eq 1 ]; then echo "目标目录只能指定一次。" >&2; exit 2; fi
  if [ -z "$1" ]; then echo "目标目录不能为空。" >&2; exit 2; fi
  DEST="$1"
  DEST_SET=1
}
while [ "$#" -gt 0 ]; do
  case "$1" in
    --all) INSTALL_ALL=1; shift ;;
    --dest)
      if [ "$#" -lt 2 ]; then echo "--dest 后需要目标目录。" >&2; exit 2; fi
      case "$2" in --*) echo "--dest 后需要目标目录，不能是选项。" >&2; exit 2 ;; esac
      set_destination "$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    --)
      shift
      if [ "$#" -ne 1 ]; then usage >&2; exit 2; fi
      set_destination "$1"; shift ;;
    -*) echo "未知选项：$1" >&2; usage >&2; exit 2 ;;
    *) set_destination "$1"; shift ;;
  esac
done

for tool in node npm python3; do
  if ! command -v "$tool" >/dev/null; then echo "缺少 ${tool}，请先安装；尚未创建技能链接。" >&2; exit 1; fi
done
DEST="$(python3 -c 'import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$DEST")"
if { [ -e "$DEST" ] || [ -L "$DEST" ]; } && [ ! -d "$DEST" ]; then
  echo "目标不是可用目录：$DEST" >&2; exit 1
fi
if [ ! -f "$ROOT/skills/promotion-master/SKILL.md" ]; then
  echo "缺少主技能：$ROOT/skills/promotion-master/SKILL.md" >&2; exit 1
fi
if [ ! -f "$ROOT/skills/promotion-master/scripts/package.json" ] || [ ! -f "$ROOT/skills/promotion-master/scripts/build.js" ]; then
  echo "主技能缺少自包含的渲染入口或依赖清单；请重新下载完整仓库。" >&2; exit 1
fi
SKILLS=("$ROOT/skills/promotion-master")
if [ "$INSTALL_ALL" -eq 1 ]; then
  SKILLS=()
  for skill in "$ROOT"/skills/*/; do
    if [ -f "$skill/SKILL.md" ]; then SKILLS+=("${skill%/}"); fi
  done
fi

check_target() {
  local source="$1" target="$2"
  if [ -L "$target" ]; then
    if ! [ "$target" -ef "$source" ]; then
      echo "安装冲突：${target} 已链接到 $(readlink "$target")。" >&2
      echo "未替换旧链接。可使用默认主技能安装，或 --dest 指定独立目录；--all 不会覆盖旧版卫星。" >&2
      return 1
    fi
  elif [ -e "$target" ]; then
    echo "安装冲突：${target} 已有文件或目录，未覆盖；请用 --dest 指定独立目录。" >&2
    return 1
  fi
}

# 所有所选目标先检查，冲突时不装依赖、不创建任何链接。
for skill in "${SKILLS[@]}"; do
  check_target "$skill" "$DEST/$(basename "$skill")"
done
SCRIPT_DIRS=("$ROOT/shared/scripts")
for skill in "${SKILLS[@]}"; do
  if [ -f "$skill/scripts/package.json" ]; then SCRIPT_DIRS+=("$skill/scripts"); fi
done
for scripts in "${SCRIPT_DIRS[@]}"; do
  if [ -f "$scripts/package.json" ]; then
    echo "安装依赖：$scripts"
    env -u NODE_PATH npm install --prefix "$scripts" --ignore-scripts --no-audit --no-fund --package-lock=false
  fi
done
echo "检查系统依赖；缺失项需按 doctor 提示安装，检查未通过不会创建技能链接。"
env -u NODE_PATH python3 "$ROOT/shared/scripts/doctor.py"
for scripts in "${SCRIPT_DIRS[@]}"; do
  if [ -f "$scripts/package.json" ]; then
    env -u NODE_PATH node -e 'const path=require("path"); const req=require("module").createRequire(path.join(process.argv[1],"build.js")); const resolved=req.resolve("docx"); req("docx"); console.log("依赖 OK："+resolved);' "$scripts"
  fi
done
mkdir -p "$DEST"
for skill in "${SKILLS[@]}"; do
  target="$DEST/$(basename "$skill")"
  check_target "$skill" "$target"
  if [ -L "$target" ]; then echo "已安装：$target"; else ln -s "$skill" "$target"; echo "linked $target"; fi
done
echo "完成：安装 ${#SKILLS[@]} 个技能到 ${DEST}。使用 \$promotion-master 调用主技能。"
echo "旧 exec-deep-report 不会被本安装器替换或创建别名。版式交付仍须逐页目视检查。"
