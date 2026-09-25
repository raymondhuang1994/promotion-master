# 验收题：cn-docx-report

**输入**：一份 Markdown 或已有的 report.json，或直接用 `examples/polaris-mini.json`。

**提示词**：
> 把这份内容排成 Word，检查一遍版式再给我。

**通过标准**
1. 顺序正确：structure_qa 零 FAIL → build → render_qa 逐页看图 → text_qa → structure_qa --pdf。
2. 构建成功且同一 JSON 两次构建的 word/*.xml 一致。
3. 逐页看图后能指出并修复任何压扁、溢出、空白目录、方框中文。
4. 交付说明列出 QA 结果与未修的问题。
5. 短材料使用 short profile 和所选模块要求，不为三题问答强凑十题。
6. 在报告同目录运行、重复运行，输入和既有其他文件保持不变；输出是独立子目录。
7. 缺工具、转换/提取失败、空来源、占位符均不能显示通过；中文文字提取成功不等于图上可见。
