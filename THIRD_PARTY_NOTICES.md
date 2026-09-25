# 第三方组件说明

Promotion Master 的项目文件采用 [MIT License](LICENSE)。这不改变任何外部软件、字体、服务、数据或用户上传材料的授权条件。

## 可选依赖

- Word 构建会通过 npm 另行安装 `docx` 9.6.1 及其依赖。已核对该包自带的 MIT License，版权标记为 Copyright (c) 2016 Dolan；安装时保留 npm 包中的 LICENSE 和其他声明。
- Python 工具按所选操作使用 Matplotlib、Pillow、openpyxl 等；文档提取可能使用 python-pptx。它们通过各自发行渠道安装，适用各自许可证。
- Word/PDF 转换与检查可能使用 LibreOffice、Poppler、Pandoc 及本机中文字体，均不随本项目技能包分发，也不由项目 MIT 许可证重新授权。
- Codex、模型、联网服务以及其他宿主的使用条件由各自提供方规定。

## 分发边界

发布包不包含 `node_modules`、Python 环境、系统二进制、字体或第三方服务凭据。技能包随附本项目 LICENSE；若后续分发第三方代码或二进制，应先核对并随包保留对应许可与声明。

公开示例为虚构素材，不含用户提供的真实案例附件。用户上传的材料、客户资料与外部检索内容不因使用本项目而转为 MIT 授权。
