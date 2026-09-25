# -*- coding: utf-8 -*-
"""doctor.py —— 运行环境预检。用法：python3 doctor.py
在 Claude 沙箱以外（本机、Codex、CI）首次使用前运行；全部 OK 后再构建报告。
检查：node ≥ 18、docx 模块、Python 库、LibreOffice、poppler、pandoc、中文字体。缺什么给安装命令。
退出码：必需项缺失为 1。"""
import os, sys, shutil, subprocess, importlib, glob, re, shlex

HERE = os.path.dirname(os.path.abspath(__file__))
SOFFICE = ["soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice", "/usr/bin/soffice", "/usr/local/bin/soffice"]
CJK = ["Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK HK", "Noto Sans CJK TC", "Source Han Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", "SimHei"]
rows, bad = [], False

def add(name, ok, detail, hint, required=True):
    global bad
    if not ok and required: bad = True
    rows.append((("OK " if ok else ("MISS" if required else "OPT ")), name, detail if ok else hint))

def run(cmd, **kw):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=60, **kw)
    except Exception: return None

# node 与 docx
r = run(["node", "-v"]); ver = (r.stdout.strip() if r and r.returncode == 0 else "")
major = re.match(r"v?(\d+)", ver)
add("node", bool(major) and int(major.group(1)) >= 18, ver, "安装 Node.js 18 以上：https://nodejs.org 或 brew install node")
env = dict(os.environ)
# 与 build.js 使用同一目录及当前环境；不偷偷添加只在预检时有效的全局 NODE_PATH。
r = run(["node", "-e", "const fs=require('fs'),path=require('path');let d=path.dirname(require.resolve('docx'));for(;;){const p=path.join(d,'package.json');if(fs.existsSync(p)){const v=JSON.parse(fs.readFileSync(p,'utf8'));if(v.name==='docx'){console.log(v.version);break;}}const next=path.dirname(d);if(next===d)throw Error('docx package metadata not found');d=next;}"], cwd=HERE, env=env)
add("docx (npm)", bool(r) and r.returncode == 0, "docx " + (r.stdout.strip() if r else ""), "在此技能安装依赖：npm install --prefix " + shlex.quote(HERE) + "（仓库用户可运行 tools/install_codex.sh）")

# Python 库
for mod, hint, req in [("matplotlib", "pip install matplotlib", True), ("PIL", "pip install pillow", True), ("openpyxl", "pip install openpyxl（生成 Excel 取数单用）", False)]:
    try: m = importlib.import_module(mod); add(mod, True, getattr(m, "__version__", ""), hint, req)
    except Exception: add(mod, False, "", hint, req)

# 外部工具
add("LibreOffice (soffice)", any(shutil.which(c) or os.path.exists(c) for c in SOFFICE), next((c for c in SOFFICE if shutil.which(c) or os.path.exists(c)), ""), "brew install --cask libreoffice 或 apt install libreoffice；render_qa 转 PDF 需要")
for tool, hint in [("pdftoppm", "brew install poppler 或 apt install poppler-utils；render_qa 出缩略图需要"), ("pdftotext", "同上（poppler）；structure_qa --pdf 需要"), ("pdfinfo", "同上（poppler）；structure_qa --pdf 需要"), ("pandoc", "brew install pandoc 或 apt install pandoc；text_qa 需要")]:
    add(tool, bool(shutil.which(tool)), shutil.which(tool) or "", hint)

# 中文字体
found = ""
try:
    from matplotlib import font_manager as fm
    for f in glob.glob("/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc"):
        try: fm.fontManager.addfont(f)
        except Exception: pass
    names = {f.name for f in fm.fontManager.ttflist}; found = next((c for c in CJK if c in names), "")
except Exception: pass
if not found and shutil.which("fc-list"):
    out = run(["fc-list", ":lang=zh", "family"]); fam = out.stdout if out else ""
    found = next((c for c in CJK if c in fam), "")
add("中文字体", bool(found), found, "brew install --cask font-noto-sans-cjk-sc 或 apt install fonts-noto-cjk；否则图表中文显示为方框")

w = max(len(n) for _, n, _ in rows)
for st, n, d in rows: print(f"[{st}] {n.ljust(w)}  {d}")
print("\n结论：" + ("必需项齐全，可以构建。" if not bad else "有必需项缺失，按上面的提示安装后重跑。"))
sys.exit(1 if bad else 0)
