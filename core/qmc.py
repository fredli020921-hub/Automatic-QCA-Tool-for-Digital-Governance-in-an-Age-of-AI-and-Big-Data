"""
Quine-McCluskey 布尔最小化 + 解的指标计算
算法参考：Dușa, A. (2019). QCA with R: A Comprehensive Resource. Springer.
          Thiem, A., & Dușa, A. (2013). QCA with R. Springer.
"""
import numpy as np
from collections import defaultdict


# ── 基础工具 ──────────────────────────────────────────────

def _to_bits(n, n_vars):
    return tuple((n >> (n_vars - 1 - i)) & 1 for i in range(n_vars))


def _config_to_int(config, n_vars):
    result = 0
    for b in config:
        result = (result << 1) | int(b)
    return result


def _can_combine(t1, t2):
    """若两项仅在一个非'-'位上不同，返回合并结果，否则返回 None。"""
    diffs = []
    for i, (a, b) in enumerate(zip(t1, t2)):
        if a != b:
            if a == '-' or b == '-':
                return None
            diffs.append(i)
    if len(diffs) == 1:
        r = list(t1)
        r[diffs[0]] = '-'
        return tuple(r)
    return None


def _term_covers(term, config):
    """判断 term（含'-'）是否覆盖某个具体组态。"""
    return all(t == '-' or t == c for t, c in zip(term, config))


# ── Quine-McCluskey 主算法 ────────────────────────────────

def _get_prime_implicants(minterms_set, dont_cares_set, n_vars):
    """
    返回所有质蕴含项：list of (term_tuple, covered_minterms_frozenset)
    使用分组 QMC，按非'-'位中1的数量分组，比较相邻组。
    """
    # 初始化
    current = {}
    for m in minterms_set:
        t = _to_bits(m, n_vars)
        current[t] = (False, frozenset([m]))
    for d in dont_cares_set:
        t = _to_bits(d, n_vars)
        if t not in current:
            current[t] = (True, frozenset())

    prime_implicants = []

    while current:
        # 按非'-'位中1的数量分组
        groups = defaultdict(list)
        for term, (is_dc, covered) in current.items():
            n_ones = sum(1 for x in term if x == 1)
            groups[n_ones].append((term, is_dc, covered))

        used = set()
        new_current = {}

        for k in sorted(groups.keys()):
            if k + 1 not in groups:
                continue
            for t1, dc1, cov1 in groups[k]:
                for t2, dc2, cov2 in groups[k + 1]:
                    combined = _can_combine(t1, t2)
                    if combined is not None:
                        used.add(t1)
                        used.add(t2)
                        new_dc  = dc1 and dc2
                        new_cov = cov1 | cov2
                        if combined in new_current:
                            old_dc, old_cov = new_current[combined]
                            new_current[combined] = (old_dc and new_dc, old_cov | new_cov)
                        else:
                            new_current[combined] = (new_dc, new_cov)

        # 未被使用的非 don't-care 项 → 质蕴含项
        for term, (is_dc, covered) in current.items():
            if term not in used and not is_dc:
                prime_implicants.append((term, covered & minterms_set))

        current = new_current

    return prime_implicants


def _find_cover(minterms_list, prime_implicants):
    """贪心最小覆盖：先选必要质蕴含项，再贪心补充。"""
    if not prime_implicants or not minterms_list:
        return []

    minterms_set = set(minterms_list)

    # 必要质蕴含项（只被一个 PI 覆盖的 minterm 对应的 PI）
    m2pi = defaultdict(list)
    for i, (pi, cov) in enumerate(prime_implicants):
        for m in cov:
            if m in minterms_set:
                m2pi[m].append(i)

    selected = set()
    for m, covering in m2pi.items():
        if len(covering) == 1:
            selected.add(covering[0])

    covered = set()
    for idx in selected:
        covered |= prime_implicants[idx][1] & minterms_set

    remaining  = minterms_set - covered
    available  = [i for i in range(len(prime_implicants)) if i not in selected]

    while remaining and available:
        best = max(available, key=lambda i: len(prime_implicants[i][1] & remaining))
        if len(prime_implicants[best][1] & remaining) == 0:
            break
        selected.add(best)
        covered  |= prime_implicants[best][1] & minterms_set
        remaining = minterms_set - covered
        available = [i for i in available if i != best]

    return [prime_implicants[i] for i in sorted(selected)]


def _filter_blocking(pis, blocking_set, n_vars):
    """过滤掉覆盖 outcome=0 行的质蕴含项。"""
    valid = []
    for pi_term, covered in pis:
        if not any(_term_covers(pi_term, _to_bits(b, n_vars)) for b in blocking_set):
            valid.append((pi_term, covered))
    return valid


# ── 主入口 ────────────────────────────────────────────────

def run_minimization(row_info, conditions, n_vars):
    """
    运行布尔最小化，返回复杂解和简约解，以及核心条件集合。

    Parameters
    ----------
    row_info   : {config_tuple: {"outcome": 1/0/"R"/"R*", ...}}
    conditions : list of str
    n_vars     : int

    Returns
    -------
    dict with keys: complex, parsimonious, core_cond_directions
      complex/parsimonious : list of (term_tuple, covered_minterms_frozenset)
      core_cond_directions : set of (cond_name, direction_int) — 出现在简约解中的条件
    """
    minterms  = set()
    blocking  = set()
    remainders = set()

    for config, info in row_info.items():
        ci = _config_to_int(config, n_vars)
        oc = info.get("outcome", "R")
        if oc == 1:
            minterms.add(ci)
        elif oc == 0:
            blocking.add(ci)
        else:
            remainders.add(ci)

    if not minterms:
        return {"complex": [], "parsimonious": [], "core_cond_directions": set()}

    # 复杂解（不使用余项）
    pis_c    = _get_prime_implicants(minterms, set(), n_vars)
    valid_c  = _filter_blocking(pis_c, blocking, n_vars)
    complex_sol = _find_cover(list(minterms), valid_c)

    # 简约解（所有余项作为 don't-care）
    pis_p    = _get_prime_implicants(minterms, remainders, n_vars)
    valid_p  = _filter_blocking(pis_p, blocking, n_vars)
    pars_sol = _find_cover(list(minterms), valid_p)

    # 核心条件 = 出现在简约解中的 (条件名, 方向) 对
    core_dirs = set()
    for term, _ in pars_sol:
        for j, cond in enumerate(conditions):
            if term[j] != '-':
                core_dirs.add((cond, term[j]))

    return {
        "complex":    complex_sol,
        "parsimonious": pars_sol,
        "core_cond_directions": core_dirs,
    }


# ── 解的指标计算 ──────────────────────────────────────────

def calc_solution_metrics(solution, calibrated_scores, cases, ind_names):
    """
    计算每条路径及整体解的一致性、覆盖度指标。

    Returns
    -------
    (path_metrics_list, solution_consistency, solution_coverage)

    path_metrics_list : list of dict
      keys: term, consistency, raw_coverage, unique_coverage
    """
    n      = len(cases)
    n_vars = len(ind_names)

    Y = np.array([float(cases[i]["结果变量"]) for i in range(n)])
    X = np.zeros((n, n_vars))
    for i in range(n):
        for j, name in enumerate(ind_names):
            X[i, j] = float(calibrated_scores.get(i, {}).get(name, 0.5))

    sum_Y = float(np.sum(Y))
    if not solution:
        return [], 0.0, 0.0

    def path_membership(term):
        pm = np.ones(n)
        for j in range(n_vars):
            if term[j] == '-':
                continue
            pm = np.minimum(pm, X[:, j] if term[j] == 1 else 1.0 - X[:, j])
        return pm

    pms = [path_membership(term) for term, _ in solution]

    # 解的隶属度 = 所有路径的最大值（OR）
    sol_mem = np.zeros(n)
    for pm in pms:
        sol_mem = np.maximum(sol_mem, pm)

    path_metrics = []
    for k, ((term, covered), pm) in enumerate(zip(solution, pms)):
        sum_pm = float(np.sum(pm))
        if sum_pm < 1e-9:
            continue
        consist   = float(np.sum(np.minimum(pm, Y)) / sum_pm)
        raw_cov   = float(np.sum(np.minimum(pm, Y)) / sum_Y) if sum_Y > 1e-9 else 0.0

        # 唯一覆盖：去掉本路径后，解覆盖的减少量
        other_mem = np.zeros(n)
        for k2, pm2 in enumerate(pms):
            if k2 != k:
                other_mem = np.maximum(other_mem, pm2)
        uniq_cov = max(0.0,
            float((np.sum(np.minimum(pm, Y)) - np.sum(np.minimum(other_mem, Y))) / sum_Y)
            if sum_Y > 1e-9 else 0.0
        )

        path_metrics.append({
            "term":           term,
            "consistency":    round(consist, 4),
            "raw_coverage":   round(raw_cov, 4),
            "unique_coverage": round(uniq_cov, 4),
        })

    sum_sol = float(np.sum(sol_mem))
    sol_consist = float(np.sum(np.minimum(sol_mem, Y)) / sum_sol) if sum_sol > 1e-9 else 0.0
    sol_cov     = float(np.sum(np.minimum(sol_mem, Y)) / sum_Y)   if sum_Y  > 1e-9 else 0.0

    return path_metrics, round(sol_consist, 4), round(sol_cov, 4)
