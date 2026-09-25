# 样例：「北极星」迷你报告（虚构）

这是证据不足、推论纠错与版式的虚构教学样例，不是成熟营销成品的文风标杆，也不是内容来源。
真实报告从原始材料重建。成熟判断与定位的转换见共享参考 insight-examples.md（主技能随包携带）。
本样例保留待核对事项与无效推论反例，不能据此让资料充分的任务也只输出“还需研究”。
不要照抄产品、数字、问题数量或固定比喻；这里的问答只供纠错与渲染测试，不是完整营销十二問模块。

- `polaris-mini.json`：可构建的迷你报告；最终页数由字体与渲染环境决定，必须看图。
- `make_figures.py`：生成样例用到的一张图，顺带检验 `chart_style.py` 的中文字体是否可用。

构建看效果：

```bash
cd examples && python3 make_figures.py
node ../scripts/build.js polaris-mini.json /tmp/polaris.docx
python3 ../scripts/structure_qa.py polaris-mini.json --example
```

防抄用：`text_qa.py` 与 `structure_qa.py` 都把“北极星”列为样例标记词，真实报告里出现即报错。
自动自检把素材复制到临时目录后生成图，不改源码PNG。make_figures.py 的
example_weights() 提供纯数据；test_example_math.py 复核报告表内的集中度、有效持股数与最大权重。
