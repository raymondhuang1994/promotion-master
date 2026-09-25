// build.js —— 从 report.json 构建 Word。内容与渲染分离：正文写在 JSON 里，版式全部由 report_lib.js 决定。
// 用法：node build.js report.json out.docx
// JSON 结构：{ "doc": {title, headerLeft, headerRight, cover:{...}}, "toc": [["章标题",0],...], "content": [["h1","..."], ...] }
// content 的写法与 report_lib.js 文件头注释一致；"f" 的 file 若为相对路径，相对 JSON 所在目录解析。
// 依赖解析顺序：本目录 node_modules（在 scripts/ 下执行 npm install）→ NODE_PATH（全局安装）。
const fs = require("fs"), path = require("path");
const [, , jsonPath, outPath] = process.argv;
if (!jsonPath || !outPath) { console.error("用法：node build.js report.json out.docx"); process.exit(2); }

let L;
try { L = require("./report_lib.js"); }
catch (e) {
  if (e.code === "MODULE_NOT_FOUND" && /docx/.test(e.message)) {
    console.error("找不到 docx 模块。任选其一：\n  cd scripts && npm install\n  或 NODE_PATH=$(npm root -g) node build.js ...（需已全局安装 docx）");
    process.exit(3);
  }
  throw e;
}

const spec = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
const base = path.dirname(path.resolve(jsonPath));
const content = (spec.content || []).map((item) => {
  if (item[0] === "f" && item[1] && item[1].file && !path.isAbsolute(item[1].file)) {
    const f = path.resolve(base, item[1].file);
    if (!fs.existsSync(f)) { console.error("图片不存在：" + f); process.exit(4); }
    return ["f", { ...item[1], file: f }, item[2]];
  }
  return item;
});
const d = spec.doc || {};
L.buildDocument({ title: d.title, headerLeft: d.headerLeft, headerRight: d.headerRight, coverSpec: d.cover, toc: spec.toc, content, outPath: path.resolve(outPath) })
  .then((n) => console.log("written", path.resolve(outPath), n, "bytes"))
  .catch((e) => { console.error("构建失败：", e.message); process.exit(1); });
