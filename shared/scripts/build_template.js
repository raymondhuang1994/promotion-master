// build_template.js —— 最小可运行示例。复制本文件，改 content 即可。
// 运行：NODE_PATH=$(npm root -g) node build_template.js [输出路径] [图片路径]
const path = require("path");
const L = require("./report_lib.js");
const out = process.argv[2] || "/tmp/report_sample.docx";
const fig = process.argv[3]; // 可选：一张 PNG，用来检查图片渲染

const content = [
  ["h1", `执行摘要`],
  ["p", `开场用两三个并置的事实引出核心问题。**粗体写结论**，后面跟数字与日期。`],
  ["c", { title: `本报告回答的核心问题`, body: [`用一句话写清整份报告要回答什么。`] }],
  ["h2", `三个核心判断`],
  ["n", [`**判断一的结论句。**三到四个承重数字，带来源与日期。`, `**判断二的结论句。**……`, `**判断三的结论句。**……`]],
  ["h2", `目标（建议值，非预测）`],
  ["t", { head: [`情景`, `目标值`, `核心假设`], w: [12, 22, 66], rows: [[`熊`, `—`, `—`], [`基准`, `—`, `—`], [`牛`, `—`, `—`]], opt: { boldFirstCol: true } }],
  ["s", `资料来源：目标为本报告建议值。`],
  ["h1", `第一章　主题：用结论句做标题`],
  ["p", `每章第一段给出本章结论，后文只做支撑。`],
  ["c", { title: `需要核对的数据点`, body: [`材料内部口径矛盾用红色提示框单独列出。`], opt: { kind: "warn" } }],
  ...(fig ? [["f", { file: path.resolve(fig), cap: `图 1　图题写清内容与日期`, src: `资料来源：机构或文件名，日期；口径说明。` }]] : []),
  ["b", [`要点一`, `要点二`]],
  ["c", { title: `重要提示`, body: [`用途、口径与合规审阅要求。`], opt: { kind: "note" } }],
];

L.buildDocument({
  title: "报告标题", headerLeft: "机构 · 报告简称", headerRight: "内部讨论稿 · 机密",
  coverSpec: { org: "机构名称 · 文件类型", badge: "内部讨论稿 v1.0 · 机密", title: "主标题", subtitle: "副标题写判断", product: "对象全称", tagline: "报告范围一句话", audience: "供：读者（分发限制）", dateLine: "日期 · 地点", disclaimer: "口径声明：数据截至日期；第三方数据均为转引并标注来源；目标为建议值，不构成预测或投资建议。" },
  toc: [["执行摘要", 0], ["第一章　主题：结论", 0], ["1.1 小节　1.2 小节", 1]],
  content, outPath: out,
}).then((n) => console.log("written", out, n));
