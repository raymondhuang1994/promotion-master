# -*- coding: utf-8 -*-
"""quant_tools.py —— 深度报告里反复用到的“独立复算”工具。
全部是确定性的算术，输入来自用户材料或公开披露；输出用于“本报告测算”并须在注释里写明方法与输入。"""

def concentration(weights, tops=(1, 3, 5, 10)):
    """集中度：前 N 大合计、赫芬达尔指数、有效数量（1/HHI）。weights 为百分数列表，降序与否均可。"""
    w = sorted(weights, reverse=True); tot = sum(w)
    hhi = sum((x / tot) ** 2 for x in w)
    out = {f"top{n}": round(sum(w[:n]), 2) for n in tops if n <= len(w)}
    out.update({"n": len(w), "sum": round(tot, 2), "hhi": round(hhi, 4), "effective_n": round(1 / hhi, 1)})
    return out

def group_sum(items, key):
    """分组加总，用于核对材料宣称的地区或行业分布。items: [{'w':权重, 'region':..., ...}]。"""
    out = {}
    for it in items: out[it[key]] = round(out.get(it[key], 0) + it["w"], 2)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))

def check_claim(computed, claimed, tol=1.0):
    """把逐项加总的结果与材料宣称值对比，返回超出容差（百分点）的条目。"""
    return {k: {"computed": computed.get(k), "claimed": v, "diff": round((computed.get(k) or 0) - v, 2)}
            for k, v in claimed.items() if abs((computed.get(k) or 0) - v) > tol}

def overlap(a, b):
    """两个组合的近似重叠度：共同持仓按较小权重加总。a、b: {代码: 权重%}。同时返回各自独有部分。"""
    common = set(a) & set(b)
    return {"overlap": round(sum(min(a[k], b[k]) for k in common), 2), "n_common": len(common),
            "only_a_weight": round(sum(v for k, v in a.items() if k not in b), 2), "only_a_n": len(set(a) - set(b)),
            "only_b_weight": round(sum(v for k, v in b.items() if k not in a), 2), "only_b_n": len(set(b) - set(a))}

def fee_drag(fee_pct, years=5, start=100.0):
    """费用的独立影响：V = start × (1 − f)^t，毛回报假设为零。返回逐年数值。"""
    return [round(start * (1 - fee_pct / 100) ** t, 2) for t in range(years + 1)]

def tilt_value(tilt_pp, relative_perf_pp):
    """权重倾斜的静态贡献（百分点）= 多配权重 × 相对表现。用于和费用差比较数量级。"""
    return round(tilt_pp * relative_perf_pp / 100, 2)

def sensitivity(weight_pct, move_pct):
    """某部分权重变动对整体的机械影响（百分点），其余不变。"""
    return round(weight_pct * move_pct / 100, 2)

def price_return(eps_growth_pct, multiple_change_pct):
    """价格回报 ≈ (1+盈利增速)×(1+估值倍数变化) − 1。用来说明“盈利兑现不等于股价上涨”。"""
    return round(((1 + eps_growth_pct / 100) * (1 + multiple_change_pct / 100) - 1) * 100, 2)

def session_overlap(home, others, step_min=1):
    """交易时段重合：home 与 others 均为 [(开始小时, 结束小时)...]，同一时区。返回本市场开市时长、至少一个与全部其他市场同时开市的时长与占比。"""
    def is_open(t, spans): return any(a <= t < b for a, b in spans)
    tot = any_ = all_ = 0
    for m in range(0, 24 * 60, step_min):
        t = m / 60
        if not is_open(t, home): continue
        tot += 1; flags = [is_open(t, o) for o in others]; any_ += any(flags); all_ += all(flags)
    h = step_min / 60
    return {"home_hours": round(tot * h, 2), "any_open_hours": round(any_ * h, 2), "all_open_hours": round(all_ * h, 2),
            "any_open_pct": round(any_ / tot * 100, 1), "all_open_pct": round(all_ / tot * 100, 1)}

def lot_cost(rows, fx=1.0):
    """按整手买齐一组证券的成本。rows: [(名称, 单价, 每手股数)]，fx 为折算到目标币种的汇率。"""
    detail = [(n, p, l, round(p * l * fx)) for n, p, l in rows]
    return {"detail": detail, "total": sum(d[3] for d in detail)}

if __name__ == "__main__":  # 冒烟测试（示例数字，非任何真实产品）
    w = [21.0, 18.6, 16.4, 5.3, 3.7, 3.6, 3.4, 3.4, 2.8, 1.8] + [1.0] * 20
    print(concentration(w)); print(fee_drag(1.8), fee_drag(0.68)); print(tilt_value(15.41, 10), sensitivity(56.0, -30), price_return(20, -20))
    print(overlap({"A": 20, "B": 10, "C": 5}, {"A": 15, "B": 12, "D": 8}))
    print(session_overlap([(9.5, 12), (13, 16)], [[(8, 14.5)], [(8, 10.5), (11.5, 14.5)], [(9, 13.5)]]))
    print(check_claim({"甲": 39.5, "乙": 34.5, "丙": 26.0}, {"甲": 36, "乙": 43, "丙": 20}))
