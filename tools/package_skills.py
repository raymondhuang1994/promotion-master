# -*- coding: utf-8 -*-
"""package_skills.py —— 校验并打包 skills/ 下的每个技能。
用法：python3 tools/package_skills.py            → dist/<name>.skill（zip，Claude.ai 上传用）
      python3 tools/package_skills.py --prompt-pack   → 另出 dist/prompts/<name>.md（SKILL.md + 参考文件合并成单文件，供 ChatGPT 项目或其他不支持技能的宿主粘贴）
      python3 tools/package_skills.py --check    → 只校验不打包
校验：frontmatter 的 name 与目录名一致、description 非空且不超过 1024 字符、shared 同步一致。"""
import os, sys, re, zipfile, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS, DIST = os.path.join(ROOT, "skills"), os.path.join(ROOT, "dist")
EXCLUDE = {"__pycache__", "node_modules", ".DS_Store"}

def frontmatter(path):
    t = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m: raise ValueError("缺少 frontmatter")
    fm = dict(re.findall(r"^(\w+):\s*(.*)$", m.group(1), re.M)); return fm, t[m.end():]

def check(skill):
    fm, _ = frontmatter(os.path.join(SKILLS, skill, "SKILL.md"))
    errs = []
    if fm.get("name") != skill: errs.append(f"name「{fm.get('name')}」与目录名不一致")
    d = fm.get("description", "")
    if not d: errs.append("description 为空")
    if len(d) > 1024: errs.append(f"description {len(d)} 字符，超过 1024")
    return errs

def zip_skill(skill):
    os.makedirs(DIST, exist_ok=True); out = os.path.join(DIST, f"{skill}.skill"); base = os.path.join(SKILLS, skill)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dp, dns, fns in os.walk(base):
            dns[:] = [x for x in dns if x not in EXCLUDE]
            for f in sorted(fns):
                if f in EXCLUDE: continue
                p = os.path.join(dp, f); z.write(p, os.path.join(skill, os.path.relpath(p, base)))
    return out

def prompt_pack(skill):
    fm, body = frontmatter(os.path.join(SKILLS, skill, "SKILL.md")); parts = [f"# {skill}\n\n> {fm.get('description','')}\n", body]
    for sub in ("references", "assets"):
        d = os.path.join(SKILLS, skill, sub)
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.endswith(".md"): parts.append(f"\n\n---\n\n<!-- {sub}/{f} -->\n\n" + open(os.path.join(d, f), encoding="utf-8").read())
    parts.append("\n\n---\n\n说明：本文件由 tools/package_skills.py 合并生成，供不支持技能目录的宿主使用；脚本类功能（Word 渲染、QA、pptx 抽取）需要在支持代码执行的环境里用仓库中的 scripts/ 运行。")
    os.makedirs(os.path.join(DIST, "prompts"), exist_ok=True); out = os.path.join(DIST, "prompts", f"{skill}.md")
    open(out, "w", encoding="utf-8").write("".join(parts)); return out

def main():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sync_shared.py"), "--check"], capture_output=True, text=True)
    if r.returncode: print(r.stdout.strip()); sys.exit(1)
    skills = sorted(d for d in os.listdir(SKILLS) if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))); bad = False
    for s in skills:
        errs = check(s)
        if errs: bad = True; print(f"[FAIL] {s}: " + "；".join(errs)); continue
        if "--check" in sys.argv: print(f"[OK]   {s}"); continue
        print(f"[OK]   {s} → {os.path.relpath(zip_skill(s), ROOT)}" + (f"，{os.path.relpath(prompt_pack(s), ROOT)}" if "--prompt-pack" in sys.argv else ""))
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
