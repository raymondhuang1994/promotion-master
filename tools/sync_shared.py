# -*- coding: utf-8 -*-
"""sync_shared.py —— 把 shared/ 里的文件按各技能的 shared.txt 清单复制进技能目录，保证“改一处、处处一致”。
用法：python3 tools/sync_shared.py          复制
      python3 tools/sync_shared.py --check  只校验，有差异则退出码 1（供 CI 与打包前使用）
每个技能目录放一个 shared.txt，一行一个相对 shared/ 的路径；技能内的落点与该相对路径相同。"""
import os, sys, shutil, hashlib, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); SHARED = os.path.join(ROOT, "shared")
check = "--check" in sys.argv; drift = []; copied = 0
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.exists(p) else None
for manifest in sorted(glob.glob(os.path.join(ROOT, "skills", "*", "shared.txt"))):
    skill = os.path.dirname(manifest)
    for rel in [l.strip() for l in open(manifest, encoding="utf-8") if l.strip() and not l.startswith("#")]:
        src, dst = os.path.join(SHARED, rel), os.path.join(skill, rel)
        if not os.path.exists(src): print(f"缺少共享文件：{rel}（{os.path.basename(skill)}）"); drift.append(rel); continue
        if h(src) != h(dst):
            if check: drift.append(f"{os.path.basename(skill)}/{rel}")
            else: os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst); copied += 1
if check: print("共享文件一致" if not drift else "与 shared/ 不一致：\n  " + "\n  ".join(drift)); sys.exit(1 if drift else 0)
print(f"已同步 {copied} 个文件")
