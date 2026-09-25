# Promotion Master

以研究为基础，制作有判断、有证据的中文产品分析与推广材料。

当前正式版本：**1.0.0**。默认分支：[main](https://github.com/raymondhuang1994/promotion-master/tree/main)。

## 能做什么

- 从资料中提炼核心判断，解释产品提供什么、适合什么需求，以及相比其他选择的代价。
- 先写准确定位，再比较标题与传播表达；保留候选及用户指定原句，不固定套用某个行业故事。
- 按真实决策障碍组织问答，直接回答、给依据和条件，重要异议继续追问。
- 按最终读者制作内部版、客户版或两版配套；支持完整分析、指定模块和现稿优化。
- 按需生成中文 Word，并做结构、文字与版式检查。

完整产品推广报告默认包含核心判断、一句话定位、十二问十二答及一分钟产品介绍。
只要三问就交三问；经营 KPI、渠道计划、多语言和 Word 都按需要选择。

## 安装到 Codex

以下两种安装方式择一使用。

### 方式一：克隆仓库安装

默认安装只准备文字工作流，需要基础 shell 和 Python 3；下载仓库另需 Git。

```bash
git clone --branch v1.0.0 --depth 1 https://github.com/raymondhuang1994/promotion-master.git
cd promotion-master
bash tools/install_codex.sh
```

默认只安装自包含的 `promotion-master`，目标为 `~/.agents/skills/promotion-master`。
安装采用软链接，安装后请保留仓库目录。同名目录或指向其他位置的链接存在时，安装器会停止，不覆盖现有内容。

需要 Word 排版时，在同一仓库准备可选工具链：

```bash
bash tools/install_codex.sh --with-word
```

这一步准备项目的排版依赖并检查 Node.js/npm、Python 库、文档转换工具和中文字体；
缺少的系统软件按提示补齐，不把未完成的检查当作通过。文字研究和 Markdown 交付不要求这些工具。
已经由同一仓库建立的技能链接可重复执行安装以补齐 Word 准备。

需要四个专项入口时显式选择：

```bash
bash tools/install_codex.sh --all
```

`--all` 与 `--with-word` 可以组合。验证安装位置时可用 `--dest /path/to/isolated-skills`；
自定义目录不会自动成为 Codex 扫描入口，是否启用须由宿主配置决定。

### 方式二：请 Codex 从 GitHub 安装技能

在 Codex 中提出明确安装请求：

> 请从 GitHub 仓库 `raymondhuang1994/promotion-master` 的 `v1.0.0` 版本安装 `skills/promotion-master`，
> 目标为 `~/.agents/skills`。暂不准备 Word 工具；如果目标有同名内容，请保留并告知冲突。

技能安装 helper 采用复制安装，与方式一的软链接不同。复制安装后，克隆脚本不会覆盖同名目录；
需要更换安装方式时，先备份已有内容并明确目标。预计要使用 Word 时，可优先采用方式一。

Codex 会发现用户技能目录中的技能；安装后在新对话中用 `$promotion-master` 调用，
若仍未出现，可重启 Codex。用户技能目录与软链接规则见 [Codex 官方技能文档](https://learn.chatgpt.com/docs/build-skills)。

## 开始使用

还没确定范围时：

> 用 $promotion-master 根据附件推荐成品版本、范围和叙事，给方向小样与取舍，等我确认后再写。

已经确定范围时：

> 用 $promotion-master 给客户写完整产品分析，直接执行，仅依据附件，不联网、不发送。
> 保留核心判断、定位、十二问和产品要点；正文与简短制作说明分开。

> 用 $promotion-master 只做内部培训的三条费用问答，不扩成完整报告。

> 用 $promotion-master 做两版配套：内部培训说明和客户阅读说明，各自成稿，事实与口径一致。

已有读者、范围和方向就沿用，不重复问卷。遇到会改变主张或范围的缺项，再集中说明。

## 成品给谁看

| 版本 | 交付内容 |
|---|---|
| 内部版 | 支持管理层研判或同事培训，可保留依据、候选取舍与讲解提示 |
| 客户版 | 直接解释产品角色、考虑理由、证据和代价；制作说明与正文分开 |
| 两版配套 | 共用研究事实，分别交付；数字、日期和重要条件一致 |

按最终读者判断版本：销售让它写给客户，就是客户版。客户版可以深入研究，也可以只答指定问题，
不会自动变成短宣传单；制作客户稿不等于授权发送、发布或代替机构审批。

## 先看实际示例

[示例导航](docs/examples.md)提供两类虚构产品的完整分析、客户阅读稿、三问、配套说明及资料不足时的回复。
原始输入、作者制作说明、原始回放与后续评审分开保存；这些是有明确边界的写作记录，
不是真实投资建议、无历史盲测或营销效果保证。

## 可选专项技能

| 入口 | 用途 |
|---|---|
| `promotion-master` | 自包含的研究与推广主入口 |
| `product-slogan` | 定位、标题与传播候选 |
| `sales-qa-battlecard` | 问答、追问、竞品比较与客户适配 |
| `material-factcheck` | 事实、数字与口径核查 |
| `cn-docx-report` | 中文 Word 构建及结构、文字、版式检查 |

## 维护与验证

共享规则和脚本在 `shared/` 维护，再同步到各独立技能包：

```bash
python3 tools/sync_shared.py
python3 tools/package_skills.py --check
python3 tools/package_skills.py --prompt-pack
```

完整 Word 回归需要先准备排版工具链，再运行 `bash tools/selftest.sh --all`。
验证方法见 [Codex 检查清单](docs/codex-smoke-test.md)，本版实际执行结果见
[1.0.0 验证记录](docs/validation-v1.0.0.md)。平台结论限于记录中的 macOS 本机与 Linux CI 实测范围；
未宣称 Windows、Claude 或纯 ChatGPT 环境的完整工具链已通过验证。

自动检查、模型内容审阅和真实使用者试用分别记录。材料质量、研究证据与使用者判断仍影响结果；
脚本通过不等于研究结论、合规或沟通效果获得批准。真实附件、客户资料与凭据不得加入公共仓库。

## 许可证

本项目使用 [MIT 许可证](LICENSE)。第三方组件说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
