# -*- coding: utf-8 -*-
"""Validate and build self-contained skill archives and optional text-only prompts.

Default: dist/<name>.skill, identical <name>.zip, and SHA256SUMS.
--prompt-pack also merges Markdown under references/ and assets/ recursively.
dist/release/ contains flat release assets and their own SHA256SUMS.
--check validates without writing; --output-dir selects a distribution directory.
"""
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import zipfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS, DIST = os.path.join(ROOT, "skills"), os.path.join(ROOT, "dist")
EXCLUDE = {
    "node_modules", "__pycache__", ".ds_store", ".git", ".env", ".venv", "venv",
    "private", ".private", "docs", "evals", "gold", "work", "dist", "replay-log.md",
}
RESOURCE_DIRS = {"references", "assets", "scripts", "examples", "agents"}
ROOT_FILES = {"SKILL.md", "LICENSE", "NOTICE", "CHANGELOG.md", "README.md", "shared.txt"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".py", ".js", ".mjs", ".cjs", ".sh", ".toml"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ttf", ".otf"}
RESOURCE_PATH = re.compile(r"(?<![\w./])(?:references|assets|scripts|examples)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+")
LOCAL_PATH = re.compile(r"/(?:Users|home)/[^/\s]+|/(?:private/var|var/folders)(?:/|\b)|[A-Za-z]:[\\/]Users[\\/][^\\/\s]+", re.I)
PROMPT_NOTICE = (
    "> 能力边界：这是纯文本提示包，只合并技能说明与 Markdown 参考/模板；"
    "不含可执行脚本、依赖、图片或其他非文本资源，不代表宿主具备完整技能能力。\n"
    "> Word 渲染、QA、PPTX 抽取等脚本任务仍需下载完整 .skill 或 .zip 技能目录，"
    "在具备代码执行能力且依赖齐全的环境中运行。仅粘贴本文件不会安装或运行这些能力。\n"
)


def frontmatter(path):
    with open(path, encoding="utf-8") as source:
        text = source.read()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise ValueError("缺少 frontmatter")
    fields = dict(re.findall(r"^(\w+):\s*(.*)$", match.group(1), re.M))
    return fields, text[match.end():]


def package_files(skill):
    """Return only distributable resources; reject symlinks and private host paths."""
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill):
        raise ValueError("非法技能目录名")
    base = Path(SKILLS) / skill
    if base.is_symlink() or not base.is_dir():
        raise ValueError(f"技能目录缺失或为符号链接：{skill}")
    files = []
    for directory, dirs, names in os.walk(base, followlinks=False):
        relative_dir = Path(directory).relative_to(base)
        dirs[:] = sorted(name for name in dirs
                         if name.lower() not in EXCLUDE and not name.startswith(".")
                         and (relative_dir.parts or name in RESOURCE_DIRS))
        for name in dirs:
            if (Path(directory) / name).is_symlink():
                raise ValueError(f"分发资源不能为符号链接：{relative_dir / name}")
        for name in sorted(names):
            if name.lower() in EXCLUDE or name.startswith("."):
                continue
            path = Path(directory) / name
            relative = path.relative_to(base)
            if not relative_dir.parts and name not in ROOT_FILES:
                continue
            if relative_dir.parts and path.suffix.lower() not in TEXT_SUFFIXES | ASSET_SUFFIXES:
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"分发资源必须为普通文件：{relative}")
            if path.suffix.lower() in TEXT_SUFFIXES | {".svg"} or name in {"LICENSE", "NOTICE"}:
                content = path.read_text(encoding="utf-8")
                if LOCAL_PATH.search(content):
                    raise ValueError(f"分发资源含本机绝对路径：{relative}")
            files.append((relative.as_posix(), path))
    return sorted(files)


def check(skill):
    errors = []
    try:
        files = dict(package_files(skill))
        fields, body = frontmatter(Path(SKILLS) / skill / "SKILL.md")
        if fields.get("name") != skill:
            errors.append(f"name「{fields.get('name')}」与目录名不一致")
        description = fields.get("description", "")
        if not description:
            errors.append("description 为空")
        if len(description) > 1024:
            errors.append(f"description {len(description)} 字符，超过 1024")
        for required in ("SKILL.md", "LICENSE", "agents/openai.yaml", "shared.txt"):
            if required not in files or not files[required].read_bytes().strip():
                errors.append(f"缺少或为空的分发资源：{required}")
        references = set(RESOURCE_PATH.findall(body))
        if "shared.txt" in files:
            references.update(line.strip() for line in files["shared.txt"].read_text(encoding="utf-8").splitlines()
                              if line.strip() and not line.lstrip().startswith("#"))
        for relative in sorted(references):
            parsed = PurePosixPath(relative)
            if parsed.is_absolute() or ".." in parsed.parts or relative not in files:
                errors.append(f"引用资源未包含在技能包内：{relative}")
    except (OSError, ValueError, UnicodeError) as error:
        errors.append(str(error))
    return errors


def _validated_files(skill):
    errors = check(skill)
    if errors:
        raise ValueError(f"{skill}: " + "；".join(errors))
    return package_files(skill)


def _destination(relative):
    base = Path(DIST)
    output = base / relative
    if output.is_symlink() or not output.resolve().is_relative_to(base.resolve()):
        raise ValueError("输出路径不能通过符号链接离开分发目录")
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def zip_skill(skill):
    """Keep the existing .skill return API and create its byte-identical .zip twin."""
    files = _validated_files(skill)
    output = _destination(f"{skill}.skill")
    twin = _destination(f"{skill}.zip")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, source in files:
            info = zipfile.ZipInfo(f"{skill}/{relative}", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            mode = 0o100755 if source.stat().st_mode & 0o111 else 0o100644
            info.external_attr = mode << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes(), compresslevel=9)
    twin.write_bytes(output.read_bytes())
    return str(output)


def prompt_pack(skill):
    files = _validated_files(skill)
    fields, body = frontmatter(Path(SKILLS) / skill / "SKILL.md")
    parts = [f"# {skill} — 纯文本提示包\n\n", PROMPT_NOTICE,
             f"\n> {fields.get('description', '')}\n\n", body]
    for relative, source in files:
        if relative == "LICENSE" or (relative.startswith(("references/", "assets/")) and relative.endswith(".md")):
            parts.append(f"\n\n---\n\n<!-- {relative} -->\n\n" + source.read_text(encoding="utf-8"))
    output = _destination(f"prompts/{skill}.md")
    output.write_text("".join(parts), encoding="utf-8")
    return str(output)


def write_checksums(paths, directory=None):
    """Cover exactly the build outputs; stale or foreign files cannot join a release."""
    base = Path(directory if directory is not None else DIST).resolve()
    if not base.is_relative_to(Path(DIST).resolve()):
        raise ValueError("校验和目录必须位于分发目录")
    expected = set()
    for name in paths:
        path = Path(name)
        if path.is_symlink() or not path.is_file():
            raise ValueError("校验和输入必须是本次生成的普通文件")
        try:
            relative = path.resolve().relative_to(base).as_posix()
        except ValueError as error:
            raise ValueError("校验和输入必须位于分发目录") from error
        if relative == "SHA256SUMS":
            raise ValueError("SHA256SUMS 不能包含自身")
        expected.add(relative)
    actual = set()
    for path in base.rglob("*"):
        if path.is_symlink():
            raise ValueError("分发目录不能包含符号链接")
        relative = path.relative_to(base).as_posix()
        if path.is_file() and relative != "SHA256SUMS":
            actual.add(relative)
    if expected != actual:
        raise ValueError("分发目录包含旧文件或非本次产物，请使用空的 --output-dir；额外文件："
                         + ", ".join(sorted(actual - expected)))
    lines = [f"{hashlib.sha256((base / relative).read_bytes()).hexdigest()}  {relative}\n"
             for relative in sorted(expected)]
    output = _destination((base / "SHA256SUMS").relative_to(Path(DIST).resolve()).as_posix())
    output.write_text("".join(lines), encoding="utf-8")
    return str(output)


def release_bundle(paths):
    """Flatten the exact artifacts that GitHub Release users will download."""
    outputs = []
    names = set()
    for source_name in paths:
        source = Path(source_name)
        relative = source.resolve().relative_to(Path(DIST).resolve())
        name = f"{source.stem}-prompt.md" if relative.parts[0] == "prompts" else source.name
        if name in names:
            raise ValueError(f"发布文件名冲突：{name}")
        names.add(name)
        destination = _destination(f"release/{name}")
        destination.write_bytes(source.read_bytes())
        outputs.append(str(destination))
    outputs.append(write_checksums(outputs, Path(DIST) / "release"))
    return outputs


def main():
    global DIST
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--prompt-pack", action="store_true")
    parser.add_argument("--output-dir", default=DIST)
    args = parser.parse_args()
    DIST = args.output_dir
    sync = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_shared.py"), "--check"],
                          capture_output=True, text=True)
    if sync.returncode:
        print((sync.stdout + sync.stderr).strip())
        return 1
    skills = sorted(path.name for path in Path(SKILLS).iterdir() if (path / "SKILL.md").is_file())
    if not skills:
        print("[FAIL] 没有可分发的技能")
        return 1
    invalid = False
    for skill in skills:
        errors = check(skill)
        if errors:
            invalid = True
            print(f"[FAIL] {skill}: " + "；".join(errors))
        elif args.check:
            print(f"[OK]   {skill}")
    if invalid or args.check:
        return int(invalid)
    try:
        outputs = []
        for skill in skills:
            archive = zip_skill(skill)
            generated = [archive, str(Path(archive).with_suffix(".zip"))]
            if args.prompt_pack:
                generated.append(prompt_pack(skill))
            outputs.extend(generated)
            print(f"[OK]   {skill} → " + "，".join(os.path.relpath(path, DIST) for path in generated))
        outputs.extend(release_bundle(outputs))
        print("[OK]   release/ — 平面发布文件与 SHA256SUMS")
        print(f"[OK]   {os.path.basename(write_checksums(outputs))}")
    except (OSError, ValueError, UnicodeError) as error:
        print(f"[FAIL] {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
