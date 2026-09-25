# -*- coding: utf-8 -*-
"""structure_qa.py —— 对 report.json 做结构检查，把技能里的硬规则变成可执行的检查。
用法：python3 structure_qa.py report.json [--pdf 报告.pdf] [--example]
  --pdf      传入 render_qa 生成的 PDF，可实测执行摘要页数
  --example  允许样例标记词（只在检查 examples/ 时使用）
JSON 可声明 qa.requiredModules: ["qa", "suitability", "battlecard"]；
表对象的 module 可显式标记模块，battlecard 的 acknowledgementColumn 可指定承认栏（从 0 起）。
qa.profile: "short" 用于短材料，免封面/目录、章内图表和重要提示框要求；旧 JSON 默认 report。
短材料可用 qa.minQuestions 指定问答条数；默认 10，完整报告至少 10。
退出码：有 FAIL 为 1，否则 0。WARN 需要人工判断，不影响退出码。
检查的规则（编号与输出对应）：
  F1 封面口径声明与目录存在            F6 适配矩阵至少两行“不适合/优势不充分/匹配度有限”
  F2 每张图有来源（src）               F7 攻防表“需要先承认的”一列无空格
  F3 含外部数据的表后两项内有资料来源行（自编工具表降为 WARN）   F8 情景目标表附近标注“建议值”
  F4 每个 h1 章至少一张表或图（附录/结语降为 WARN）   F9 存在“重要提示”提示框
  F5 质疑问答表不少于 10 行            F10 无占位符、样例标记词、过程性字眼
  W1 h1 标题过短，可能不是结论句       W2 执行摘要疑似超过两页（无 PDF 时按字数估）
"""
import sys, re, json, subprocess, shutil, argparse, os, unicodedata

PLACEHOLDER = ["TODO", "XXX", "【】", "……。", "〔示例"]
EXAMPLE_MARK = ["北极星", "样例机构", "样例指数公司", "样例交易所", "样例数据商"]
PROCESS = ["上一版", "另一个AI", "另一个 AI", "其他AI", "其他 AI", "作为AI", "作为 AI"]

def has_source(value):
    return isinstance(value, str) and bool(re.sub(r"^\s*资料来源\s*[:：]?", "", value).strip(" \t\r\n。；;—-"))

def strings(x):  # 递归取出所有字符串
    if isinstance(x, str): return [x]
    if isinstance(x, dict): return [s for v in x.values() for s in strings(v)]
    if isinstance(x, list): return [s for v in x for s in strings(v)]
    return []

def table_is(head, *pats):
    h = "｜".join(str(c) for c in head)
    return all(re.search(p, h) for p in pats)

def normalize_title(text):
    return re.sub(r"\s|\u200b", "", unicodedata.normalize("NFKC", text))

def title_at(lines, title, start=0):
    """完整标题须由连续整行组成；可换行，不匹配正文中的短前缀或子串。"""
    target = normalize_title(title)
    if not target: return False
    joined = ""
    for line in lines[start:]:
        joined += line
        if joined == target: return True
        if not target.startswith(joined): return False
    return False

def locate_summary_pages(pdf, summary_title, next_title, headers=()):
    info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, check=True).stdout
    match = re.search(r"Pages:\s+(\d+)", info)
    if not match: raise RuntimeError("pdfinfo 未返回有效页数，摘要页数未实测")
    total = int(match.group(1))
    header_parts = [normalize_title(h) for h in headers if h]
    ignored = set(header_parts) | {"".join(header_parts), "".join(reversed(header_parts))}
    summary_page = None
    for page in range(1, total + 1):
        out = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), pdf, "-"], capture_output=True, text=True, check=True).stdout
        lines = [normalize_title(line) for line in out.splitlines() if normalize_title(line)]
        lines = [line for line in lines if line not in ignored]
        # 封面长度可能变化，不能以固定第 3 页代替目录识别；兼容“目\n录”。
        if any(title_at(lines, "目录", start) for start in range(len(lines))):
            continue
        # report_lib 的 h1 另起页，因此去掉已知页眉后应从完整标题开始。
        if summary_page is None:
            if title_at(lines, summary_title): summary_page = page
        elif page > summary_page and next_title and title_at(lines, next_title):
            return summary_page, page
    return summary_page, None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--pdf")
    parser.add_argument("--example", action="store_true")
    args = parser.parse_args(); allow_example = args.example; pdf = args.pdf
    with open(args.report, encoding="utf-8") as source: spec = json.load(source)
    content = spec.get("content", []); doc = spec.get("doc", {}); qa = spec.get("qa", {})
    if not isinstance(qa, dict): parser.error("qa 必须为对象")
    required = qa.get("requiredModules", [])
    known = {"qa", "suitability", "battlecard"}
    if not isinstance(required, list) or any(not isinstance(m, str) or m not in known for m in required):
        parser.error("qa.requiredModules 仅支持 qa、suitability、battlecard 的数组")
    profile = qa.get("profile", "report")
    if profile not in ("report", "short"): parser.error("qa.profile 仅支持 report 或 short")
    min_questions = qa.get("minQuestions", 10)
    if type(min_questions) is not int or min_questions < 1 or (profile == "report" and min_questions < 10):
        parser.error("qa.minQuestions 须为正整数；完整报告至少 10，short 可按确认范围设置")
    if not isinstance(content, list) or any(not isinstance(x, list) or not x or (x[0] != "pb" and len(x) < 2) for x in content):
        parser.error("content 必须为有效的内容条目数组")
    if any(x[0] in ("t", "f", "c") and not isinstance(x[1], dict) for x in content):
        parser.error("表格、图片、提示框必须为对象")
    if any(x[0] == "t" and (not isinstance(x[1].get("head", []), list) or not isinstance(x[1].get("rows", []), list) or any(not isinstance(r, list) for r in x[1].get("rows", []))) for x in content):
        parser.error("表头与表格行必须为数组")
    fails, warns = [], []
    F = lambda code, msg: fails.append(f"FAIL {code} {msg}"); W = lambda code, msg: warns.append(f"WARN {code} {msg}")

    # F1
    if profile == "report":
        if not (doc.get("cover") or {}).get("disclaimer"): F("F1", "封面缺少口径声明 disclaimer")
        if not spec.get("toc"): F("F1", "缺少目录 toc")

    # 按 h1 分章
    chapters, cur = [], None
    for idx, item in enumerate(content):
        if item[0] == "h1": cur = {"title": item[1], "items": [], "idx": idx}; chapters.append(cur)
        elif cur is not None: cur["items"].append(item)

    seen = set()
    for i, item in enumerate(content):
        kind = item[0]; v = item[1] if len(item) > 1 else None
        nxt = [x[0] for x in content[i + 1:i + 3]]
        if kind == "f" and not has_source(v.get("src", "")): F("F2", f"第{i}项 图「{v.get('cap', '')[:30]}」缺少有效来源 src")
        if kind == "s" and not has_source(v): F("F3", f"第{i}项 资料来源行为空")
        if kind == "t":
            head = v.get("head", []); rows = v.get("rows", [])
            module = v.get("module")
            if module is not None and (not isinstance(module, str) or module not in known): F("F0", f"第{i}项 未知表格模块 {module}")
            modules = {module} if isinstance(module, str) and module in known else set()
            if table_is(head, r"怎么问|质疑|问题|疑问", r"答|回应"): modules.add("qa")
            if table_is(head, r"适配判断|适配结论|匹配判断|适合度"): modules.add("suitability")
            if table_is(head, r"需要先承认"): modules.add("battlecard")
            seen.update(modules)
            if "s" not in nxt:
                body = " ".join(strings(rows)); external = bool(re.search(r"\d[\d,.]*\s*(%|％|亿|万|bp|港元|美元|人民币|日元|韩元|新台币)|20[1-3]\d年|20[1-3]\d[/-]\d", body))
                tool = table_is(head, r"情景|KPI|阶段|动作|验收|风险|概率|表述|替代|候选|层次|客群|方向|需要的数据|观察对象|周次")
                (W if (tool or not external) else F)("F3", f"第{i}项 表「{'｜'.join(map(str, head))[:30]}」后两项内没有资料来源行 s" + ("（自编工具表，建议写“资料来源：本报告整理”）" if tool or not external else ""))
            if "qa" in modules and len(rows) < min_questions: F("F5", f"第{i}项 质疑问答表只有 {len(rows)} 行，要求不少于 {min_questions} 行")
            if "suitability" in modules:
                n = sum(1 for r in rows if any(re.search(r"不适合|优势不充分|匹配度有限", str(c)) for c in r))
                if n < 2: F("F6", f"第{i}项 适配矩阵只有 {n} 行“不适合/优势不充分/匹配度有限”，要求至少 2 行")
            if "battlecard" in modules:
                cols = [j for j, c in enumerate(head) if re.search(r"需要先承认|先承认|必须承认|局限|短板", str(c))]
                col = v.get("acknowledgementColumn", cols[0] if cols else None)
                if type(col) is not int or not 0 <= col < len(head):
                    F("F7", f"第{i}项 攻防表缺少可识别的承认栏；请指定 acknowledgementColumn")
                elif not rows:
                    F("F7", f"第{i}项 攻防表没有内容")
                else:
                    empty = [r[0] if r else "空行" for r in rows if len(r) <= col or r[col] is None or not str(r[col]).strip() or str(r[col]).strip() in ("—", "-", "无")]
                    if empty: F("F7", f"第{i}项 攻防表以下维度“需要先承认的”为空：{empty}")
            if table_is(head, r"情景") and table_is(head, r"目标|规模"):
                near = " ".join(strings(content[i + 1:i + 3])); before = " ".join(strings(content[max(0, i - 2):i]))
                if "建议值" not in near + before: F("F8", f"第{i}项 情景目标表附近没有“建议值”标注")

    for module in sorted(set(required) - seen): F("F0", f"缺少声明的必要模块：{module}；请补模块并用表对象 module 显式标记")

    # F4
    for ch in chapters:
        if profile == "report" and not any(x[0] in ("t", "f") for x in ch["items"]):
            (W if re.search(r"附录|结语", ch["title"]) else F)("F4", f"章「{ch['title'][:30]}」没有表或图")
        title = re.sub(r"^第[一二三四五六七八九十\d]+章[\s　]*", "", ch["title"]).strip()
        if title != "执行摘要" and len(title) < 8: W("W1", f"h1「{ch['title']}」只有 {len(title)} 字，可能不是结论句")

    # F9
    if profile == "report" and not any(x[0] == "c" and "重要提示" in str(x[1].get("title", "")) for x in content): F("F9", "缺少“重要提示”提示框")

    # F10
    alltext = strings(content) + strings(doc)
    for w in PLACEHOLDER + ([] if allow_example else EXAMPLE_MARK):
        hits = [s[:40] for s in alltext if w in s]
        if hits: F("F10", f"出现「{w}」{len(hits)} 处，例如：{hits[0]}")
    for w in PROCESS:
        hits = [s[:80] for s in alltext if w in s]
        if hits: W("W3", f"过程性字眼「{w}」{len(hits)} 处，需结合上下文判断，例如：{hits[0]}")

    # W2 执行摘要页数
    summ = next((c for c in chapters if "执行摘要" in c["title"]), None)
    pdf_ready = bool(pdf)
    if pdf and (not os.path.isfile(pdf) or not shutil.which("pdftotext") or not shutil.which("pdfinfo")):
        F("W2", "已请求 PDF 检查，但 PDF 文件、pdftotext 或 pdfinfo 缺失；未实测")
        pdf_ready = False
    if summ:
        if pdf_ready:
            k = chapters.index(summ)
            nxt_title = chapters[k + 1]["title"] if k + 1 < len(chapters) else ""
            s0, s1 = locate_summary_pages(pdf, summ["title"], nxt_title, [doc.get("headerLeft", ""), doc.get("headerRight", "")])
            if s0 is not None and s1 is not None and s1 > s0:
                pages = s1 - s0
                print(f"[执行摘要] 起于第 {s0} 页，下一章起于第 {s1} 页，占 {pages} 页")
                if pages > 2: F("W2", f"执行摘要占 {pages} 页，要求不超过 2 页")
            else: W("W2", "无法可靠定位执行摘要与其后下一章的完整标题，页数未实测；需人工核对")
        else:
            chars = sum(len(s) for s in strings([x for x in summ["items"] if x[0] in ("p", "n", "b", "c")]))
            tables = sum(1 for x in summ["items"] if x[0] in ("t", "f"))
            if chars > 1800 or tables > 3: W("W2", f"执行摘要正文约 {chars} 字、{tables} 张表图，可能超过两页；以 render_qa 为准")

    n_t = sum(1 for x in content if x[0] == "t"); n_f = sum(1 for x in content if x[0] == "f")
    print(f"章数 {len(chapters)}；表 {n_t}；图 {n_f}；来源行 {sum(1 for x in content if x[0] == 's')}")
    for m in fails + warns: print(m)
    print(f"结果：{len(fails)} FAIL，{len(warns)} WARN")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    try: main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"FAIL 检查未完成：{exc}", file=sys.stderr)
        sys.exit(1)
