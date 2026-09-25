// report_lib.js —— 中文深度报告的 Word 渲染库（基于 docx 9.x）
// 用法见 build_template.js。内容用简单数组描述：
//   ["h1", "标题"] ["h2", ...] ["h3", ...] ["p", "正文，支持 **粗体**"] ["b", [要点...]] ["n", [编号项...]]
//   ["t", {head:[...], rows:[[...]], w:[相对列宽...], opt:{size, boldFirstCol, center:[列号], keep, compact}}]
//   ["c", {title, body:[段落或要点数组...], opt:{accent, fill, titleColor}}]   提示框
//   ["f", {file:"图片绝对路径.png", cap:"图题", src:"资料来源…", width:560}]
//   ["s", "资料来源：…"]   ["pb"] 分页
// 已内置的版式对策：所有段落显式自动行距；小表格整体同页；页码拆成三个文本块；手工目录。
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell, WidthType,
  ShadingType, BorderStyle, ImageRun, PageBreak, VerticalAlign, LevelFormat, Header, Footer, PageNumber,
  TabStopType, LineRuleType,
} = require("docx");

const LR = LineRuleType.AUTO;
const THEME = { NAVY: "12355B", BLUE: "1F6FB2", RED: "B5322A", GREY: "5F6B7A", LIGHT: "EEF3F8", ZEBRA: "F5F8FB", LINE: "C9D3DD", WARN_FILL: "FBF1EF", WARN_TITLE: "8E241D", NOTE_FILL: "F3F4F6" };
const FONT = { ascii: "Arial", hAnsi: "Arial", cs: "Arial", eastAsia: process.env.REPORT_CJK_FONT || "Microsoft YaHei" }; // 中文字体名可用环境变量覆盖，例如 Mac 上 REPORT_CJK_FONT="PingFang SC"
const CONTENT_W = 9026; // A4 宽 11906 减左右边距各 1440

function pngSize(file) { // 读取 PNG 头部的宽高，避免额外依赖
  const b = fs.readFileSync(file);
  if (b.toString("ascii", 1, 4) !== "PNG") throw new Error("figure 仅支持 PNG：" + file);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}

function runs(text, opt = {}) { // **粗体** 迷你标记
  const parts = String(text).split("**"); const out = [];
  parts.forEach((s, i) => { if (s !== "") out.push(new TextRun({ text: s, bold: (i % 2 === 1) || !!opt.bold, font: FONT, size: opt.size || 21, color: opt.color, italics: opt.italics })); });
  if (out.length === 0) out.push(new TextRun({ text: "", font: FONT, size: opt.size || 21 }));
  return out;
}
function P(text, opt = {}) {
  return new Paragraph({ children: runs(text, opt), alignment: opt.align || AlignmentType.JUSTIFIED,
    spacing: { lineRule: LR, line: opt.line || 310, after: opt.after === undefined ? 105 : opt.after, before: opt.before || 0 }, indent: opt.indent, keepNext: opt.keepNext });
}
function H(level, text) {
  const map = { 1: HeadingLevel.HEADING_1, 2: HeadingLevel.HEADING_2, 3: HeadingLevel.HEADING_3 };
  return new Paragraph({ heading: map[level], children: [new TextRun({ text, font: FONT })], pageBreakBefore: level === 1, keepNext: true });
}
let listInstance = 0;
function bullets(items, opt = {}) {
  return items.map((t) => new Paragraph({ children: runs(t, { size: opt.size || 21 }), numbering: { reference: "bul", level: opt.level || 0 }, spacing: { lineRule: LR, line: 304, after: 65 }, alignment: AlignmentType.LEFT }));
}
function numbered(items, opt = {}) {
  listInstance += 1; const inst = listInstance;
  return items.map((t) => new Paragraph({ children: runs(t, { size: opt.size || 21 }), numbering: { reference: "num", level: 0, instance: inst }, spacing: { lineRule: LR, line: 304, after: 65 }, alignment: AlignmentType.LEFT }));
}
const thin = { style: BorderStyle.SINGLE, size: 4, color: THEME.LINE };
const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function cellParas(text, o) { // 单元格内用 \n 分段
  return String(text).split("\n").map((seg) => new Paragraph({ children: runs(seg, { size: o.size, color: o.color, bold: o.bold }), alignment: o.align || AlignmentType.LEFT, spacing: { lineRule: LR, line: 276, after: 30 }, keepNext: !!o.keepNext }));
}
function table(head, rows, widths, opt = {}) {
  const total = widths.reduce((a, b) => a + b, 0); const W = widths.map((w) => Math.round(w * CONTENT_W / total));
  W[W.length - 1] += CONTENT_W - W.reduce((a, b) => a + b, 0);
  const size = opt.size || 18;
  const keepAll = opt.keep === undefined ? rows.length <= 9 : !!opt.keep; // 小表整体同页，避免孤行
  const mk = (txt, i, isHead, zebra, kn) => new TableCell({
    width: { size: W[i], type: WidthType.DXA },
    shading: isHead ? { type: ShadingType.CLEAR, fill: THEME.NAVY, color: "auto" } : (zebra ? { type: ShadingType.CLEAR, fill: THEME.ZEBRA, color: "auto" } : undefined),
    margins: opt.compact ? { top: 25, bottom: 25, left: 90, right: 90 } : { top: 50, bottom: 50, left: 100, right: 100 },
    verticalAlign: VerticalAlign.CENTER, borders: { top: thin, bottom: thin, left: thin, right: thin },
    children: cellParas(txt, { size, keepNext: kn, color: isHead ? "FFFFFF" : undefined, bold: isHead || (opt.boldFirstCol && i === 0), align: (opt.center && opt.center.includes(i)) ? AlignmentType.CENTER : AlignmentType.LEFT }),
  });
  const trs = [];
  if (head) trs.push(new TableRow({ tableHeader: true, cantSplit: true, children: head.map((h, i) => mk(h, i, true, false, true)) }));
  rows.forEach((r, ri) => {
    if (r.length !== widths.length) throw new Error(`表格第 ${ri + 1} 行有 ${r.length} 列，应为 ${widths.length} 列`);
    trs.push(new TableRow({ cantSplit: true, children: r.map((c, i) => mk(c, i, false, ri % 2 === 1, keepAll ? ri < rows.length - 1 : ri === 0)) }));
  });
  return [new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: W, rows: trs }), new Paragraph({ children: [], spacing: { lineRule: LR, after: 60 } })];
}
function callout(title, body, opt = {}) { // opt.kind: "warn" 红色提示；"note" 灰色说明
  const preset = opt.kind === "warn" ? { accent: THEME.RED, fill: THEME.WARN_FILL, titleColor: THEME.WARN_TITLE } : opt.kind === "note" ? { accent: THEME.GREY, fill: THEME.NOTE_FILL, titleColor: "3A4652" } : {};
  const accent = opt.accent || preset.accent || THEME.BLUE, fill = opt.fill || preset.fill || THEME.LIGHT, tc = opt.titleColor || preset.titleColor || THEME.NAVY;
  const kids = [];
  if (title) kids.push(new Paragraph({ children: [new TextRun({ text: title, bold: true, color: tc, font: FONT, size: 22 })], spacing: { lineRule: LR, after: 90, line: 300 }, keepNext: true }));
  body.forEach((b) => {
    if (Array.isArray(b)) b.forEach((t) => kids.push(new Paragraph({ children: runs(t, { size: 20 }), numbering: { reference: "bul", level: 0 }, spacing: { lineRule: LR, line: 300, after: 60 } })));
    else kids.push(new Paragraph({ children: runs(b, { size: 20 }), spacing: { lineRule: LR, line: 300, after: 80 }, alignment: AlignmentType.JUSTIFIED }));
  });
  const cell = new TableCell({ width: { size: CONTENT_W, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill, color: "auto" }, margins: { top: 140, bottom: 110, left: 220, right: 200 },
    borders: { top: none, bottom: none, right: none, left: { style: BorderStyle.SINGLE, size: 28, color: accent } }, children: kids });
  return [new Table({ width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [CONTENT_W], rows: [new TableRow({ cantSplit: true, children: [cell] })] }), new Paragraph({ children: [], spacing: { lineRule: LR, after: 100 } })];
}
function source(text) { return new Paragraph({ children: [new TextRun({ text, font: FONT, size: 16, color: THEME.GREY })], spacing: { lineRule: LR, after: 160, line: 260 }, alignment: AlignmentType.LEFT }); }
function figure(file, cap, src, widthPx = 560) {
  const [w, h] = pngSize(file); const out = [];
  out.push(new Paragraph({ children: [new TextRun({ text: cap, bold: true, color: THEME.NAVY, font: FONT, size: 19 })], alignment: AlignmentType.LEFT, spacing: { lineRule: LR, before: 80, after: 60 }, keepNext: true }));
  out.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: !!src, spacing: { lineRule: LR, after: 40 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(file), transformation: { width: widthPx, height: Math.round(widthPx * h / w) }, altText: { title: cap, description: cap, name: cap } })] }));
  if (src) out.push(source(src));
  return out;
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }

function render(items) {
  const out = [];
  for (const [k, v, o] of items) {
    if (k === "h1") out.push(H(1, v)); else if (k === "h2") out.push(H(2, v)); else if (k === "h3") out.push(H(3, v));
    else if (k === "p") out.push(P(v, o || {})); else if (k === "b") out.push(...bullets(v, o || {})); else if (k === "n") out.push(...numbered(v, o || {}));
    else if (k === "t") out.push(...table(v.head, v.rows, v.w, v.opt || {})); else if (k === "c") out.push(...callout(v.title, v.body, v.opt || {}));
    else if (k === "f") out.push(...figure(v.file, v.cap, v.src, v.width)); else if (k === "s") out.push(source(v)); else if (k === "pb") out.push(pageBreak());
    else throw new Error("未知的内容类型：" + k);
  }
  return out;
}

// ---------- 封面、手工目录、整本文档 ----------
const T = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 21, bold: o.bold, color: o.color });
const para = (children, o = {}) => new Paragraph({ children, alignment: o.align || AlignmentType.LEFT, spacing: { lineRule: LR, before: o.before || 0, after: o.after === undefined ? 120 : o.after, line: o.line || 320 }, border: o.border });

function cover(c) { // c: {org, badge, title, subtitle, product, tagline, audience, dateLine, disclaimer}
  const out = [];
  out.push(para([T(c.org || "", { size: 22, color: THEME.GREY })], { before: 600, after: 60 }));
  if (c.badge) out.push(para([T(c.badge, { size: 20, color: THEME.RED, bold: true })], { after: 1500 }));
  out.push(para([T(c.title, { size: 72, bold: true, color: THEME.NAVY })], { after: 120, line: 264 }));
  if (c.subtitle) out.push(para([T(c.subtitle, { size: 52, bold: true, color: THEME.NAVY })], { after: 360, line: 264 }));
  if (c.product) out.push(para([T(c.product, { size: 28, color: THEME.BLUE, bold: true })], { after: 60, line: 288 }));
  if (c.tagline) out.push(para([T(c.tagline, { size: 28, color: THEME.BLUE })], { after: 500, line: 288 }));
  out.push(para([T(c.audience || "", { size: 21, color: "3A4652" })], { after: 60, before: 900, border: { top: { style: BorderStyle.SINGLE, size: 12, color: THEME.NAVY, space: 14 } } }));
  out.push(para([T(c.dateLine || "", { size: 21, color: "3A4652" })], { after: 700 }));
  if (c.disclaimer) out.push(para([T(c.disclaimer, { size: 17, color: THEME.GREY })], { align: AlignmentType.JUSTIFIED, line: 280 }));
  return out;
}
function tocManual(items) { // items: [["章标题", 0], ["小节列表", 1], ...]；不带页码，任何设备上都能正常显示
  return [new Paragraph({ children: [T("目　录", { size: 32, bold: true, color: THEME.NAVY })], spacing: { lineRule: LR, before: 200, after: 300 }, pageBreakBefore: true, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: THEME.NAVY, space: 6 } } }),
    ...items.map(([t, lvl]) => new Paragraph({ children: [T(t, { size: lvl ? 18 : 22, bold: !lvl, color: lvl ? THEME.GREY : "1B2733" })], indent: { left: lvl ? 420 : 0 }, spacing: { lineRule: LR, before: lvl ? 0 : 150, after: 40, line: 300 } }))];
}
const numberingConfig = { config: [
  { reference: "bul", levels: [
    { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } }, run: { font: "Arial" } } },
    { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 840, hanging: 260 } }, run: { font: "Arial" } } } ] },
  { reference: "num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 460, hanging: 360 } }, run: { font: "Arial", bold: true, color: THEME.NAVY } } }] },
] };

async function buildDocument({ title, headerLeft, headerRight, coverSpec, toc, content, outPath }) {
  const small = (text) => new TextRun({ text, font: FONT, size: 16, color: THEME.GREY });
  const doc = new Document({
    creator: "promotion-master", title: title || "报告",
    styles: { default: { document: { run: { font: FONT, size: 21 }, paragraph: { spacing: { lineRule: LR, line: 310 } } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 32, bold: true, color: THEME.NAVY, font: FONT },
          paragraph: { spacing: { lineRule: LR, before: 120, after: 260, line: 420 }, outlineLevel: 0, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: THEME.NAVY, space: 6 } } } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, color: THEME.NAVY, font: FONT }, paragraph: { spacing: { lineRule: LR, before: 300, after: 140, line: 360 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 22, bold: true, color: THEME.BLUE, font: FONT }, paragraph: { spacing: { lineRule: LR, before: 200, after: 90, line: 320 }, outlineLevel: 2 } },
      ] },
    numbering: numberingConfig,
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1300, left: 1440, right: 1440 } }, titlePage: true },
      headers: { default: new Header({ children: [new Paragraph({ children: [small(headerLeft || ""), small("\t" + (headerRight || ""))], tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }], border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: THEME.LINE, space: 4 } } })] }), first: new Header({ children: [new Paragraph({ children: [] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [small("第 "), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 16, color: THEME.GREY }), small(" 页")] })] }), first: new Footer({ children: [new Paragraph({ children: [] })] }) },
      children: [...(coverSpec ? cover(coverSpec) : []), ...(toc ? tocManual(toc) : []), ...render(content)],
    }],
  });
  const buf = await Packer.toBuffer(doc); fs.mkdirSync(require("path").dirname(outPath), { recursive: true }); fs.writeFileSync(outPath, buf); return buf.length;
}

module.exports = { buildDocument, render, cover, tocManual, P, H, runs, table, callout, figure, source, pageBreak, numberingConfig, THEME, FONT, CONTENT_W };
