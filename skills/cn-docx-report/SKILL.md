---
name: cn-docx-report
description: 用户要“排成 Word、生成 docx、中文报告排版、把 Markdown 或 JSON 变成 Word、版式检查、图片被压扁、目录空白、页眉页脚、封面”时使用。提供中文深度报告的 Word 渲染库（封面、目录、结论式标题、表格、图片、提示框、来源行）、图表样式，以及结构、文字、版式三道 QA 脚本；正文写在 report.json，`node scripts/build.js report.json out.docx` 一次渲染，同一份 JSON 重复构建结果一致。要写内容用 promotion-master，本技能只管排版与检查。Also use to render Chinese management reports to .docx with consistent layout and run layout QA.
---

# 中文 Word 报告排版与 QA（cn-docx-report）

## 什么时候用，什么时候不用

用：内容已经写好（或正在由其他技能产出），需要一份版式稳定的中文 Word 报告，并在交付前跑结构、文字、版式三道检查。也用于修版式问题：图片压扁、目录空白、表格溢出、中文方框。
不用：内容还没写（promotion-master 负责内容，其阶段 5 到 6 调用本技能的脚本）。

## 工作方式

1. **内容与版式分离。** 正文写进 `report.json`，结构见 `references/report-json.md`；版式全部由 `scripts/report_lib.js` 决定，改文字不碰脚本。图表先用 `scripts/chart_style.py` 生成 PNG，再在 JSON 里引用。
2. **先结构检查，再构建，再看图。** 顺序固定：`structure_qa.py` 零 FAIL → `build.js` 构建 → `render_qa.py` 转 PDF 出缩略图并逐页看 → `text_qa.py` 查残留标记、慎用词、过程性字眼 → 把 PDF 回传给 `structure_qa.py --pdf` 实测执行摘要页数。
3. **依赖与预检。** 首次先在当前技能的 `scripts/` 下执行 `npm install`，再跑 `python3 scripts/doctor.py`；仓库安装脚本会处理 Node 依赖。系统工具缺失时如实报告，不写 QA 通过。
4. **样例可构建。** `examples/polaris-mini.json` 是全部虚构的迷你报告，用来看版式效果和测试脚本；样例的名称与数字不得进入真实报告，QA 脚本会拦。

## 命令

```bash
python3 scripts/doctor.py                                  # 环境预检
python3 scripts/structure_qa.py work/report.json           # 结构检查（十条硬规则）
node scripts/build.js work/report.json out/report.docx     # 构建
python3 scripts/render_qa.py out/report.docx out/render    # 转 PDF、缩略图、总览图；逐页看
python3 scripts/text_qa.py out/report.docx                 # 文字检查
python3 scripts/structure_qa.py work/report.json --pdf 实际输出的PDF路径   # 使用 render_qa 打印路径
python3 scripts/make_datasheet.py 取数需求.json 取数单.xlsx   # Excel 取数单
```

## 版式约定（由渲染库固定，不需要每次决定）

短材料可设 `qa.profile: "short"`，按选择声明 `qa.requiredModules`；
不强加完整报告的封面、目录和每章图表。render_qa 在输出父目录下创建唯一子目录，
重复运行不清空原目录。脚本验结构和文字，不能替代对推论和可读性的人工判断。

A4、2.2 厘米页边距；中文字体默认微软雅黑（可用环境变量 `REPORT_CJK_FONT` 覆盖），英文 Arial；封面含口径声明；目录页；一级标题为结论式全句；表格斑马纹、表头深蓝、首列可加粗、列宽按百分比；图片按页宽等比缩放；提示框三种（说明、警示、结论）；每张图表下一行“资料来源：……，日期”；页眉左右文字、页脚页码。常见坑与对策见 `references/docx-pitfalls.md`。

## 与其他技能的关系

promotion-master 的阶段 5 到 6 直接调用本技能的脚本；material-factcheck、sales-qa-battlecard、product-slogan 的产出要进 Word 时，按 `references/report-json.md` 转成 JSON 后用本技能构建。四个技能可以单独用，也可以由 promotion-master 一次调用全部。

## 参考与脚本

| 文件 | 何时读 |
|---|---|
| `references/report-json.md` | 写 report.json 之前 |
| `references/docx-pitfalls.md` | 构建前与版式出问题时 |
| `scripts/` | 见上方命令；`build_template.js` 是直接调用渲染库的最小示例 |
| `examples/` | 看效果、跑测试 |

版本 1.0.0（2026-09-25）。脚本、样例及共享参考改 shared/ 后同步。
