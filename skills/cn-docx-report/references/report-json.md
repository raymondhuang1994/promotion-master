# report.json 与可选模块

`node scripts/build.js report.json out.docx` 从 JSON 构建 Word。
图片路径相对 JSON 所在目录；内容与脚本分离。样例 examples/polaris-mini.json 全部虚构。

```json
{
  "doc": {
    "title": "标题", "headerLeft": "页眉左", "headerRight": "内部讨论稿",
    "cover": {"title": "标题", "disclaimer": "用途与口径声明"}
  },
  "toc": [["执行摘要", 0]],
  "qa": {"profile": "report", "requiredModules": ["qa", "suitability", "battlecard"]},
  "content": [
    ["p", "正文，支持 **粗体**"],
    ["t", {"module": "battlecard", "acknowledgementColumn": 2,
      "head": ["维度", "论据", "需要先承认的"], "rows": [], "w": [20, 40, 40]}],
    ["s", "资料来源：文件名，日期与口径"]
  ]
}
```

以上是结构示意，不是可交付样例（空 rows 应由实际内容填充）。
未写 qa 保留旧完整报告检查。短材料用 `qa.profile: "short"`，可省封面、目录和章内图表，
但不得省相关证据与风险说明。`qa.requiredModules` 只声明用户选择的 qa（问答）、
suitability（适配）、battlecard（攻防）；整张表缺失也要失败。
表格显式 module 可避免同义表头漏检；旧表头仍兼容。问答数量按实际任务声明，
不通过堆无关问答满足完整报告的数量。
例如只选三题：`"qa": {"profile": "short", "requiredModules": ["qa"], "minQuestions": 3}`；
完整报告保持至少十问。这些数字只是结构要求，不证明回答质量。

| 内容项 | 用法 |
|---|---|
| h1 / h2 / h3 | 标题；h1 另起页，短材料适当使用 h2 避免无必要分页 |
| p | 段落，支持 **粗体** |
| b / n | 无序/有序列表，值为字符串数组 |
| t | 表格：head、rows、列宽 w；opt 可设 boldFirstCol、size、compact 等 |
| c | 提示框：title、body；opt.kind 可为 warn 或 note |
| f | 图片：file、cap、src；相对路径从 JSON 目录解析，等比缩放 |
| s | 来源行：机构/文件、数据日期、口径；不能只留空的“资料来源：” |
| pb | 显式分页 |

完整报告末尾有重要提示框。含外部数据的表须有来源与日期，工具/建议表注明其性质；
声明模块、来源、占位符由结构检查；证据能否支持主张必须另做语义评审。

运行结构 → 构建 → render_qa → 目视检查 → text_qa；
render_qa 每次在指定输出父目录下创建独立子目录，不清空父目录。
把它打印的实际 PDF 路径传给 structure_qa --pdf，不假设 out/render/in.pdf。
