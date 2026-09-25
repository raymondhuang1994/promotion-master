# -*- coding: utf-8 -*-
"""生成样例图 fig_weights.png（全部数字为虚构）。用法：python3 make_figures.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from chart_style import weights_cumulative

def example_weights():
    """纯数据函数，供图表与独立算术回归共用；导入本模块不生成图片。"""
    core = [18.9, 15.7, 14.0]                               # 三家核心，合计 48.6%
    raw = [3.2 - 2.5 * i / 26 for i in range(27)]            # 归一前的相对数，不是最终最大权重
    sat = [round(w * 51.4 / sum(raw), 2) for w in raw]
    sat[-1] = round(51.4 - sum(sat[:-1]), 2)
    names = ["核心A", "核心B", "核心C"] + [f"卫星{i+1:02d}" for i in range(27)]
    return names, core + sat, ["核心"] * 3 + ["卫星"] * 27


if __name__ == "__main__":
    names, weights, groups = example_weights()
    print(weights_cumulative(names, weights, groups, os.path.join(HERE, "fig_weights.png"), marks=(3, 10)))
