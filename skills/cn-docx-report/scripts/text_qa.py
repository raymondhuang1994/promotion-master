# -*- coding: utf-8 -*-
"""交付前文字检查。硬错误或提取失败退出 1；慎用词按上下文人工判断。
用法：python3 text_qa.py 报告.docx [--extra 词1,词2] [--example]
“待核实、数据缺口、建议值”等有效披露不会被当成未填模板。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

CAUTION = ["首只", "唯一", "独家", "全面覆盖", "稳赚", "保本", "零风险", "低风险", "更安全", "持久定价权", "必然", "保证收益", "最佳", "第一名"]
PROCESS = ["上一版", "v1 ", "V1 ", "另一个AI", "另一个 AI", "其他AI", "其他 AI", "如前所述我", "作为AI", "作为 AI"]
PLACEHOLDER = ["TODO", "XXX", "【】", "……。"]
EXAMPLE_MARK = ["北极星", "样例机构", "样例指数公司", "样例交易所", "样例数据商"]


def check_text(txt, extra=(), allow_example=False):
    lines = txt.splitlines()
    print(f"字符数（含表格排版空白）：{len(txt)}；行数：{len(lines)}")
    fails, warns = 0, 0

    def scan(title, words, hard=False):
        nonlocal fails, warns
        hits = [(i + 1, word, line.strip()[:120]) for i, line in enumerate(lines) for word in words if word in line]
        if hard:
            fails += len(hits)
        else:
            warns += len(hits)
        print(f"\n[{'FAIL' if hard else 'WARN'} {title}] 命中 {len(hits)} 处")
        for n, word, context in hits[:25]:
            print(f"  行{n} 「{word}」 {context}")

    scan("残留标记", ["**"], hard=True)
    scan("占位符", PLACEHOLDER, hard=True)
    if not allow_example:
        scan("样例标记词", EXAMPLE_MARK, hard=True)
    scan("慎用词（须判断是否为承诺、否定句或风险提示）", CAUTION + list(extra))
    scan("过程性字眼", PROCESS)
    rare = sorted({c for c in txt if "\u3400" <= c <= "\u4dbf" or "\U00020000" <= c <= "\U0002ffff"})
    print(f"\n[疑似罕见字] {''.join(rare) or '无'}")
    for word in ["转引", "待核实", "待复核", "待校准", "待补", "数据缺口", "本报告测算", "建议值"]:
        print(f"[披露计数] {word}: {txt.count(word)}")
    empty_sources = [(i + 1, line) for i, line in enumerate(lines) if re.match(r"\s*资料来源[:：]\s*$", line)]
    fails += len(empty_sources)
    for n, _ in empty_sources:
        print(f"FAIL 空的资料来源行：行{n}")
    print(f"结果：{fails} FAIL，{warns} WARN；WARN 需人工结合上下文判断。")
    return 1 if fails else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx")
    parser.add_argument("--extra", default="")
    parser.add_argument("--example", action="store_true", help="仅用于虚构样例")
    args = parser.parse_args(argv)
    if not os.path.isfile(args.docx):
        parser.error("输入文件不存在：" + args.docx)
    if not shutil.which("pandoc"):
        raise RuntimeError("未找到 pandoc，文字未检查；运行 scripts/doctor.py 查看安装方法")
    result = subprocess.run(["pandoc", "-t", "plain", args.docx], capture_output=True, text=True, check=True, timeout=120)
    if not result.stdout.strip():
        raise RuntimeError("未提取到文字，不能判定文字检查通过")
    return check_text(result.stdout, [w.strip() for w in args.extra.split(",") if w.strip()], args.example)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        detail = getattr(exc, "stderr", "") or ""
        print(f"FAIL 文字检查未完成：{exc}\n{detail[:1500]}", file=sys.stderr)
        sys.exit(1)
