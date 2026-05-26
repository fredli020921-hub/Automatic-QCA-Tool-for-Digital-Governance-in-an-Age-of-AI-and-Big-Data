"""
必要条件分析
算法参考：Dușa, A. (2019). QCA with R: A Comprehensive Resource. Springer.
公式：necessity_consistency = Σmin(Xi, Yi) / ΣYi
      necessity_coverage    = Σmin(Xi, Yi) / ΣXi
"""
import numpy as np
import pandas as pd


def run_necessity_analysis(calibrated_scores, cases, ind_names):
    """
    对每个条件（及其取反）计算必要条件一致性和覆盖度。

    Parameters
    ----------
    calibrated_scores : dict  {case_idx: {ind_name: float}}
    cases             : list  [{"结果变量": 0/1, ...}, ...]
    ind_names         : list  条件名称列表

    Returns
    -------
    pd.DataFrame  columns: 条件, 方向, 一致性, 覆盖度
    """
    n = len(cases)
    Y = np.array([float(cases[i]["结果变量"]) for i in range(n)])

    def calc(X, Y):
        num     = float(np.sum(np.minimum(X, Y)))
        sum_Y   = float(np.sum(Y))
        sum_X   = float(np.sum(X))
        consist = round(num / sum_Y, 4) if sum_Y > 1e-9 else 0.0
        cov     = round(num / sum_X, 4) if sum_X > 1e-9 else 0.0
        return consist, cov

    rows = []
    for name in ind_names:
        X    = np.array([float(calibrated_scores.get(i, {}).get(name, 0.0)) for i in range(n)])
        negX = 1.0 - X

        c,  cv  = calc(X,    Y)
        cn, cvn = calc(negX, Y)

        rows.append({"条件": name,      "方向": "存在",       "一致性": c,  "覆盖度": cv})
        rows.append({"条件": f"~{name}", "方向": "缺乏（取反）", "一致性": cn, "覆盖度": cvn})

    return pd.DataFrame(rows)
