# -*- coding: utf-8 -*-
"""Word 转 PDF 与逐页缩略图。输出目录下每次新建 run-*，不删除已有文件。
用法：python3 render_qa.py 报告.docx [输出目录] [--zoom 9,16,21]
stdout 的 pdf: 和 output: 给出本次真实路径；图片仍须逐页目视检查。
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def conversion_env(soffice):
    """部分 macOS headless 包未自动加载字体配置；只为本次进程补充已存在的配置。"""
    env = dict(os.environ)
    if sys.platform == "darwin" and not env.get("FONTCONFIG_FILE") and soffice:
        binary = Path(shutil.which(soffice) or soffice).resolve()
        candidates = [
            binary.parent.parent / "Resources/fontconfig/fonts.conf",
            binary.parent / "../../native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fontconfig/fonts.conf",
            Path("/opt/homebrew/etc/fonts/fonts.conf"),
            Path("/usr/local/etc/fonts/fonts.conf"),
        ]
        config = next((p.resolve() for p in candidates if p.is_file()), None)
        if config:
            env["FONTCONFIG_FILE"] = str(config)
    return env


def to_pdf(docx, outdir):
    wrapper = "/mnt/skills/public/docx/scripts/office/soffice.py"
    soffice = next((c for c in ["soffice", "/Applications/LibreOffice.app/Contents/MacOS/soffice", "/usr/local/bin/soffice"] if shutil.which(c) or os.path.isfile(c)), None)
    if not os.path.isfile(wrapper) and not soffice:
        raise RuntimeError("未找到 LibreOffice，无法转 PDF；运行 scripts/doctor.py 查看安装方法")
    cmd = ([sys.executable, wrapper] if os.path.isfile(wrapper) else [soffice]) + ["--headless", "--convert-to", "pdf", "--outdir", outdir, docx]
    env = conversion_env(soffice)
    if env.get("FONTCONFIG_FILE"):
        print("fontconfig:", env["FONTCONFIG_FILE"], flush=True)
    subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=True, env=env)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(docx))[0] + ".pdf")
    if not os.path.isfile(pdf) or not os.path.getsize(pdf):
        raise RuntimeError("LibreOffice 未生成有效 PDF，请检查输入文件与转换环境")
    return pdf


def zoom_pages(value):
    try:
        pages = [int(n.strip()) for n in value.split(",")]
        if not pages or any(n < 1 for n in pages):
            raise ValueError
        return list(dict.fromkeys(pages))
    except ValueError:
        raise argparse.ArgumentTypeError("--zoom 应为从 1 开始的页码，例如 1,3,5")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx")
    parser.add_argument("outdir", nargs="?")
    parser.add_argument("--zoom", type=zoom_pages, default=[])
    args = parser.parse_args(argv)
    docx = os.path.abspath(args.docx)
    if not os.path.isfile(docx):
        parser.error("输入文件不存在：" + docx)
    if not shutil.which("pdftoppm"):
        raise RuntimeError("未找到 pdftoppm；运行 scripts/doctor.py 查看安装方法")
    from PIL import Image
    base = os.path.abspath(args.outdir) if args.outdir else os.path.join(os.path.dirname(docx), "render_qa")
    os.makedirs(base, exist_ok=True)
    outdir = tempfile.mkdtemp(prefix="run-", dir=base)
    print("output:", outdir, flush=True)
    work = os.path.join(outdir, "in.docx")
    shutil.copy2(docx, work)
    pdf = to_pdf(work, outdir)
    print("pdf:", pdf, flush=True)
    subprocess.run(["pdftoppm", "-r", "55", "-png", pdf, os.path.join(outdir, "p")], check=True)
    pages = sorted(glob.glob(os.path.join(outdir, "p-*.png")))
    if not pages:
        raise RuntimeError("PDF 未生成任何页面图片，版式检查未完成")
    print("pages:", len(pages))
    if any(n > len(pages) for n in args.zoom):
        raise RuntimeError(f"--zoom 页码超出报告页数 {len(pages)}")
    for k in range(0, len(pages), 8):
        ims = [Image.open(f) for f in pages[k:k + 8]]
        try:
            w, h = ims[0].size
            sheet = Image.new("RGB", (w * 4, h * ((len(ims) + 3) // 4)), "white")
            for i, im in enumerate(ims):
                sheet.paste(im, ((i % 4) * w, (i // 4) * h))
            name = os.path.join(outdir, f"sheet_{k // 8 + 1}.png")
            sheet.save(name)
            sheet.close()
            print("sheet:", name, f"(第 {k + 1}–{k + len(ims)} 页)")
        finally:
            for im in ims:
                im.close()
    for n in args.zoom:
        subprocess.run(["pdftoppm", "-r", "85", "-f", str(n), "-l", str(n), "-png", pdf, os.path.join(outdir, "zoom")], check=True)
    for path in sorted(glob.glob(os.path.join(outdir, "zoom-*.png"))):
        print("zoom:", path)
    print("渲染完成；版式仍需逐页目视检查。")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, "stderr", "") or ""
        print(f"FAIL 版式渲染未完成：{exc}\n{detail[:1500]}", file=sys.stderr)
        sys.exit(1)
