# Promotion Master 1.0.0

以研究为基础的中文产品推广工作流：帮助团队提炼核心判断、一句话定位、客户问答及有证据的沟通材料。

## 核心能力

- 内部使用、客户阅读或两版配套；与完整分析、部分模块、现稿优化分别选择。
- 先推荐方向与表达小样，确认后执行；已明确的范围不重复问。
- 完整推广报告包含核心判断、定位、十二问十二答和一分钟产品要点；局部任务不强行扩写。
- 客户正文和内部训练、候选、制作说明分离；证据、来源日期、关键代价与适配边界保留。
- 默认仅安装自包含主入口；Word 工具按需启用，安装冲突不覆盖已有内容。

## 安装

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/raymondhuang1994/promotion-master.git
cd promotion-master
bash tools/install_codex.sh
```

默认文字模式不要求 Node、npm 或 Word 转换工具。需要 Word 输出时，在同一仓库运行：

```bash
bash tools/install_codex.sh --with-word
```

可在 Codex 下一轮对话调用 `$promotion-master`。快速上手与安装方式说明见仓库 README。

## 下载资产

- `.zip` 与 `.skill`：相同内容的完整技能目录包；主入口为 `promotion-master.zip`。
- `.md`：包含参考规则和工作模板的纯文本方法包，不包含脚本运行能力，不等于所有宿主都支持 Word 或联网。
- `SHA256SUMS`：对应本次 Release 的平面资产文件名；下载全部资产后在同一目录执行 `shasum -a 256 -c SHA256SUMS`，或核对所下载文件的单项摘要。

项目采用 MIT License。第三方软件及上传材料的授权条件不因此改变。

正式发布代表项目可版本化安装与使用，不代表生成报告自动获批外发或保证营销效果。公开案例全部虚构；实际材料仍须完成事实核验及适用的审阅。
