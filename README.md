# Promotion Master

**0.1.0-preview.1 · 开发预览，待使用者验收，尚未正式发布。**

以研究为基础，产出有判断、有证据、能用于沟通的中文产品推广材料。
不是固定口号生成器，也不是把每个任务扩成几十页报告。

## 怎么用

> 用 $promotion-master 根据附件推荐范围和叙事，给不同方向的小样与取舍。
> 我确认后再做。完整报告请提炼核心判断、一句话定位、十二问十二答和一分钟话术。
> 范例只作水准参考，不复制它的句子或观点。

可以选择完整分析、部分模块或优化现稿。已有明确确认不重问。
完整推广报告默认上述核心成品，渠道、KPI、路线图、多语言和Word按需选择。
只要三条问答就做三条，不为满足模板补一整份报告。

## 本轮优化

- 判断提炼：从事实与读者原有理解的差别出发，解释机制、产品实际敞口和选择含义。
- 定位：先写准确定位，再形成可传播的一句话；默认给三个候选与推荐，不强制比喻。
- 十二问十二答：按产品真实决策障碍重建问题，直接回答、给证据和条件，重要异议再追问。
- 成熟示范：普通摘要如何变成有解释力的判断，并自然进入定位和问答；与纠错/资料不足示例分开。
- 双重验收：基础正确与营销质量分开。判断、定位、问答的不足不能用排版或流程高分抵消。

材料与模型能力仍影响结果。通过自动检查不等于研究、合规或营销效果已获批准。

## 项目状态

开发在 [preview/quality-workflow](https://github.com/raymondhuang1994/promotion-master/tree/preview/quality-workflow)。
先提交实际测试成品和验证记录，使用者确认后再合并及正式发布。
当前没有自动发布Release；CI仅测试和提供预览构建产物。

原 [report-skills v1.3.0](https://github.com/raymondhuang1994/report-skills/releases/tag/v1.3.0)
和原Codex安装保持不变，仍可作为稳定版使用。来源与迁移说明见 [docs/provenance.md](docs/provenance.md)。

## 预览安装（自愿试用）

本轮不会自动执行以下真实安装。准备试用的同事可自行选择：
需要git、Node.js/npm、Python 3；完整Word工具依赖由doctor逐项检查，脚本不自动安装系统软件。

```bash
git clone --branch preview/quality-workflow https://github.com/raymondhuang1994/promotion-master.git
cd promotion-master
bash tools/install_codex.sh
```

默认只安装自包含的 `promotion-master`，不会动已有 `exec-deep-report` 或旧卫星。
在下一轮对话用 `$promotion-master` 调用。只复制方法写文本无需Word工具；安装脚本则验证完整工具链。

没有同名旧技能且确实想安装全部专项技能时：

```bash
bash tools/install_codex.sh --all
```

目标冲突会停止，不能用强制删除解决。可指定隔离测试目录：

```bash
bash tools/install_codex.sh --all --dest /path/to/isolated-skills
```

自定义目录只用于安装验证，宿主是否扫描该目录须另行配置；它不自动成为Codex可用入口。
安装是软链接，仓库目录不可随意删除。单个技能包有scripts/package.json时须在自己的scripts目录装Node依赖。

## 五个技能

| 入口 | 用途 |
|---|---|
| promotion-master | 完整研究与推广工作流；核心判断、定位、问答，自包含 |
| product-slogan | 定位和传播候选专项 |
| sales-qa-battlecard | 问答、追问、攻防与客户适配专项 |
| material-factcheck | 事实、数字与口径核查 |
| cn-docx-report | 中文Word构建与结构、文字、版式检查 |

主入口不因机器上有旧版卫星而被旧规则覆盖。其他宿主插件清单保留，但本轮不宣称已完成Claude环境实测。

## 开发与验证

```bash
python3 tools/sync_shared.py
bash tools/install_codex.sh --all --dest /path/to/isolated-skills
bash tools/selftest.sh --all
python3 tools/package_skills.py --prompt-pack
```

- shared/为共用文件唯一源，同步至技能目录后保证独立包完整。
- 自动测试输出在临时目录，不清空使用者材料目录。
- 脚本测试、独立模拟成品、真实同事试用分别记录，不能互相替代。
- 案例和评审分离：执行者得到原始资料，不得到终稿和期待结论；允许不同的好答案。
- 真实附件、客户资料、私有金标准不上传。公开示范与输入全部虚构。
- 新仓库Git提交使用隐藏邮箱。不得加入凭据或绝对本机路径。

正式发布前会提供本轮验证记录及可审阅的完整测试成品；未完成项如实列出。
