"""
真值表构建
算法参考：Dușa, A. (2019). QCA with R: A Comprehensive Resource. Springer.
- 案例按校准后分数 >0.5 → 1, <0.5 → 0 归入组态行
- 恰好 =0.5 的案例被排除（交叉点处模糊性最大，无法归类）
- 每行一致性 = Σmin(Xi*, Yi) / ΣXi*  （Xi* = 条件取交的模糊隶属度）
- PRI = 1（当结果为清晰集 0/1 时恒为 1，详见 Schneider & Wagemann 2012）
"""
import numpy as np
import pandas as pd
from itertools import product


def build_truth_table(calibrated_scores, cases, ind_names,
                      freq_threshold=1, consist_threshold=0.80, pri_threshold=0.75):
    """
    构建 fsQCA 真值表。

    Returns
    -------
    df_observed   : pd.DataFrame  仅含有观察案例的行（不含逻辑余项）
    row_info      : dict  {config_tuple: {...}}  供布尔最小化使用
    n_excluded    : int   因交叉点排除的案例数
    all_configs   : list  所有 2^n 组态（含逻辑余项），供完整真值表展示
    """
    n      = len(cases)
    n_vars = len(ind_names)

    Y = np.array([float(cases[i]["结果变量"]) for i in range(n)])
    X = np.zeros((n, n_vars))
    for i in range(n):
        for j, name in enumerate(ind_names):
            X[i, j] = float(calibrated_scores.get(i, {}).get(name, 0.5))

    # ── 案例分配 ──────────────────────────────────────────
    excluded = 0
    config_to_cases = {}  # config_tuple → [case_idx]

    for i in range(n):
        crisp = []
        valid = True
        for j in range(n_vars):
            v = X[i, j]
            if abs(v - 0.5) < 1e-9:
                valid = False
                excluded += 1
                break
            crisp.append(1 if v > 0.5 else 0)
        if valid:
            key = tuple(crisp)
            config_to_cases.setdefault(key, []).append(i)

    # ── 遍历所有 2^n 组态 ─────────────────────────────────
    all_possible = list(product([0, 1], repeat=n_vars))
    row_info = {}
    observed_rows = []

    for config in all_possible:
        case_idx_list = config_to_cases.get(config, [])
        n_cases = len(case_idx_list)

        if n_cases == 0:
            row_info[config] = {"outcome": "R", "n_cases": 0, "type": "逻辑余项"}
            continue

        # 计算每个案例在该组态下的模糊隶属度
        memberships = np.array([
            min(
                X[ci, j] if config[j] == 1 else (1.0 - X[ci, j])
                for j in range(n_vars)
            )
            for ci in case_idx_list
        ])
        y_vals = Y[case_idx_list]

        sum_m = float(np.sum(memberships))
        if sum_m > 1e-9:
            consistency = float(np.sum(np.minimum(memberships, y_vals)) / sum_m)
            # PRI（清晰结果时恒为 1，仍计算以保持通用性）
            sum_not_y = float(np.sum(np.minimum(memberships, 1.0 - y_vals)))
            denom_pri = sum_m - sum_not_y
            pri = float(np.sum(np.minimum(memberships, y_vals)) / denom_pri) if denom_pri > 1e-9 else 1.0
        else:
            consistency = 0.0
            pri = 0.0

        # 按阈值确定结果赋值
        if n_cases >= freq_threshold and consistency >= consist_threshold:
            outcome = 1
            row_type = "✓ 充分条件组态"
        elif n_cases < freq_threshold:
            outcome = "R*"
            row_type = f"频数不足（n={n_cases}）"
        else:
            outcome = 0
            row_type = "✗ 不充分"

        # 覆盖度 = Σmin(Xi*, Yi) / ΣYi（该组态对结果的解释比例）
        sum_Y_global = float(np.sum(Y))
        if sum_Y_global > 1e-9:
            coverage = float(np.sum(np.minimum(memberships, y_vals)) / sum_Y_global)
        else:
            coverage = 0.0

        row_dict = {name: config[j] for j, name in enumerate(ind_names)}
        row_dict.update({
            "案例数":  n_cases,
            "一致性":  round(consistency, 4),
            "覆盖度":  round(coverage, 4),
            "PRI":    round(pri, 4),
            "结果":   outcome,
            "类型":   row_type,
        })
        observed_rows.append(row_dict)
        row_info[config] = {
            "outcome": outcome,
            "n_cases": n_cases,
            "consistency": consistency,
            "pri": pri,
            "case_indices": case_idx_list,
            "type": "observed",
        }

    df_observed = pd.DataFrame(observed_rows) if observed_rows else pd.DataFrame()
    return df_observed, row_info, excluded
