# -*- coding: utf-8 -*-
"""chart_style.py —— 报告图表的统一样式与常用图形。
用法：from chart_style import *；每个函数返回保存的文件路径。宽 6.6 英寸、220dpi，适配 A4 正文宽度。"""
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

NAVY, BLUE, SKY, RED, GREY, GOLD, INK = "#12355B", "#1F6FB2", "#8DB8DE", "#C0392B", "#9AA5B1", "#D4A017", "#1B2733"

CJK_CANDIDATES = ["Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK HK", "Noto Sans CJK TC", "Source Han Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "WenQuanYi Micro Hei", "SimHei"]

def setup():
    """注册中文字体：先加载 Linux 的 Noto ttc（matplotlib 只读取 ttc 的第一个字形），再按名称在系统字体里回退（Mac 的 PingFang、Windows 的微软雅黑）。都没有时打印提示，文字会显示为方框，请运行 doctor.py。"""
    for f in glob.glob("/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc"):
        try: fm.fontManager.addfont(f)
        except Exception: pass
    names = {f.name for f in fm.fontManager.ttflist}
    found = [c for c in CJK_CANDIDATES if c in names]
    if not found: print("chart_style: 未找到中文字体，图表中文会显示为方框；运行 scripts/doctor.py 查看安装方法")
    plt.rcParams["font.family"] = found + ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color("#B8C2CC")
    ax.tick_params(colors="#3A4652", labelsize=8)

def _save(fig, path):
    fig.tight_layout(); fig.savefig(path); plt.close(fig); return path

def hbar(labels, values, path, xlabel="", colors=None, fmt="{:.1f}%", signed=False, height=2.6):
    """横向条形图。signed=True 时正值蓝、负值红，并画零线（用于敏感度、贡献度）。"""
    setup(); fig, ax = plt.subplots(figsize=(6.6, height), dpi=220)
    cols = colors or ([BLUE if v >= 0 else RED for v in values] if signed else [NAVY, BLUE, GOLD, SKY, "#5B8DB8", "#A9C4DC"][:len(values)])
    L, V, C = labels[::-1], values[::-1], cols[::-1]
    bars = ax.barh(L, V, color=C, height=0.6)
    span = (max(V) - min(min(V), 0)) or 1
    for r, v in zip(bars, V):
        ax.text(v + span * 0.015 * (1 if v >= 0 else -1), r.get_y() + r.get_height() / 2, fmt.format(v), va="center", ha="left" if v >= 0 else "right", fontsize=8.8, color=INK)
    if signed: ax.axvline(0, color="#3A4652", lw=0.8)
    ax.set_xlim(min(min(V), 0) * 1.25 - (span * 0.02 if min(V) < 0 else 0), max(max(V) * 1.18, span * 0.12)); ax.set_xlabel(xlabel, fontsize=8, color="#3A4652"); style(ax); ax.tick_params(axis="y", labelsize=8.5)
    return _save(fig, path)

def bar_highlight(labels, values, highlight, path, ylabel="", fmt="{:,.0f}", height=2.8):
    """柱状图，highlight 中的类别标红（用于“前十里有三家是我们的持仓”这类图）。"""
    setup(); fig, ax = plt.subplots(figsize=(6.6, height), dpi=220)
    bars = ax.bar(labels, values, color=[RED if l in highlight else "#5B7FA6" for l in labels], width=0.66)
    for r, v in zip(bars, values): ax.text(r.get_x() + r.get_width() / 2, v + max(values) * 0.015, fmt.format(v), ha="center", fontsize=8, color=INK)
    ax.set_ylabel(ylabel, fontsize=8, color="#3A4652"); ax.set_ylim(0, max(values) * 1.15); style(ax); ax.tick_params(axis="x", labelsize=8.2)
    return _save(fig, path)

def weights_cumulative(names, weights, groups, path, group_colors=None, marks=(3, 10)):
    """权重柱加累计线，按 groups 着色；marks 标注前 N 大累计值。用于展示“头重”结构。"""
    setup(); fig, ax = plt.subplots(figsize=(6.6, 3.3), dpi=220)
    uniq = list(dict.fromkeys(groups)); pal = group_colors or dict(zip(uniq, [NAVY, BLUE, SKY, GOLD, GREY]))
    n = len(names); ax.bar(range(n), weights, color=[pal[g] for g in groups], width=0.72)
    ax.set_xticks(range(n)); ax.set_xticklabels(names, rotation=60, ha="right", fontsize=6.3); ax.set_ylabel("权重（%）", fontsize=8, color="#3A4652"); style(ax)
    ax2 = ax.twinx(); cum = [sum(weights[:i + 1]) for i in range(n)]
    ax2.plot(range(n), cum, color=RED, lw=1.6, marker="o", ms=2.2); ax2.set_ylim(0, 105); ax2.set_ylabel("累计权重（%）", fontsize=8, color=RED); ax2.tick_params(colors=RED, labelsize=8); ax2.spines["top"].set_visible(False)
    for m in marks:
        if m <= n: ax2.annotate(f"前{m}大 {cum[m-1]:.1f}%", xy=(m - 1, cum[m - 1]), xytext=(m + 1.2, cum[m - 1] - 16), fontsize=8, color=RED, arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    from matplotlib.patches import Patch
    tot = {g: sum(w for w, gg in zip(weights, groups) if gg == g) for g in uniq}
    ax.legend(handles=[Patch(color=pal[g], label=f"{g} {tot[g]:.1f}%") for g in uniq], fontsize=7.5, frameon=False, loc="center right", bbox_to_anchor=(0.97, 0.42))
    return _save(fig, path)

def lines_compare(x_labels, series, path, ylabel="", ylim=None, end_labels=True):
    """多条折线对比。series: [(名称, 数值列表, 颜色)]，用于费用拖累、情景路径等。"""
    setup(); fig, ax = plt.subplots(figsize=(6.6, 2.6), dpi=220); xs = list(range(len(x_labels)))
    for name, vals, col in series:
        ax.plot(xs, vals, color=col, lw=2, marker="o", ms=4, label=name)
        if end_labels: ax.text(xs[-1] + 0.05, vals[-1], f"{vals[-1]:.2f}", va="center", fontsize=9, color=col)
    ax.set_xticks(xs); ax.set_xticklabels(x_labels); ax.set_xlim(0, xs[-1] + 0.6)
    if ylim: ax.set_ylim(*ylim)
    ax.set_ylabel(ylabel, fontsize=7.8, color="#3A4652"); style(ax); ax.legend(fontsize=7.8, frameon=False, loc="lower left")
    return _save(fig, path)

def sessions(rows, path, xlim=(7.5, 24), shade=None, xlabel="当地时间"):
    """交易时段或时间窗对比。rows: [(名称, [(开始小时, 结束小时)...], 颜色)]，自上而下绘制。"""
    setup(); fig, ax = plt.subplots(figsize=(6.6, 2.5), dpi=220); R = rows[::-1]
    for i, (name, spans, col) in enumerate(R):
        for a, b in spans: ax.barh(i, b - a, left=a, color=col, height=0.5)
    for a, b in (shade or []): ax.axvspan(a, b, color=RED, alpha=0.06)
    ax.set_yticks(range(len(R))); ax.set_yticklabels([r[0] for r in R], fontsize=8.5); ax.set_xlim(*xlim)
    ticks = list(range(int(xlim[0]) + 1, int(xlim[1]) + 1, 2)); ax.set_xticks(ticks); ax.set_xticklabels([f"{h}:00" for h in ticks])
    ax.set_xlabel(xlabel, fontsize=7.5, color="#3A4652"); style(ax)
    return _save(fig, path)

if __name__ == "__main__":  # 冒烟测试
    import sys; out = sys.argv[1] if len(sys.argv) > 1 else "/tmp"
    print(hbar(["环节甲", "环节乙", "环节丙"], [41.6, 25.1, 11.0], f"{out}/demo_hbar.png", xlabel="权重（%）"))
    print(hbar(["小权重故事翻倍", "前三大同跌 30%"], [0.6, -16.8], f"{out}/demo_sens.png", xlabel="对指数的机械影响（百分点）", signed=True, fmt="{:+.1f}"))
    print(lines_compare(["起点", "第1年", "第2年", "第3年"], [("低费率", [100, 99.3, 98.6, 98.0], GREY), ("高费率", [100, 98.2, 96.4, 94.7], NAVY)], f"{out}/demo_lines.png", ylim=(93, 100.5)))
