import streamlit as st
import pandas as pd
import requests
import json
import time

from core.truth_table import build_truth_table
from core.qmc import run_minimization, calc_solution_metrics


# ════════════════════════════════════════════════════════════
# 主渲染函数
# ════════════════════════════════════════════════════════════

def render_stage6():
    st.markdown('<div class="card-title">// 阶段六 · 组态充分性分析</div>', unsafe_allow_html=True)

    if st.button("← 返回第五阶段", key="back_to_5"):
        st.session_state.stage = 5
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    calibrated = st.session_state.get("calibrated_scores", {})
    if not calibrated:
        st.warning("⚠ 请先完成第四阶段的校准。")
        return

    cases     = st.session_state.cases
    ind_names = [ind["name"] for ind in st.session_state.indicators]
    n_vars    = len(ind_names)

    # ════════════════════════════════════════════════════
    # 6.1 真值表构建
    # ════════════════════════════════════════════════════
    st.markdown(_step_header("6.1", "真值表构建"), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div style="font-size:0.75rem;color:#4a5a7a;margin-bottom:4px;">频数阈值</div>', unsafe_allow_html=True)
        freq_thresh = st.number_input(
            "频数阈值", min_value=1, max_value=20, step=1,
            value=int(st.session_state.get("freq_threshold", 1)),
            label_visibility="collapsed", key="inp_freq"
        )
        st.markdown("""
        <div style="font-size:0.72rem;color:#3a4a6a;line-height:1.7;">
            参考：Schneider & Wagemann（2012）<br>
            小样本（&lt;30）→ 通常取 <b>1</b><br>
            中等样本（30~100）→ 取 <b>2~3</b><br>
            大样本（&gt;100）→ 取更大值<br>
            原则：保留至少 75% 的观察案例
        </div>""", unsafe_allow_html=True)
        st.session_state.freq_threshold = freq_thresh

    with col2:
        st.markdown('<div style="font-size:0.75rem;color:#4a5a7a;margin-bottom:4px;">真值表一致性阈值</div>', unsafe_allow_html=True)
        consist_thresh = st.number_input(
            "一致性阈值", min_value=0.0, max_value=1.0, step=0.01,
            value=float(st.session_state.get("consist_threshold", 0.80)),
            format="%.2f", label_visibility="collapsed", key="inp_consist"
        )
        st.markdown("""
        <div style="font-size:0.72rem;color:#3a4a6a;line-height:1.7;">
            Ragin（2008）推荐 ≥ <b>0.80</b><br>
            Fiss（2011）采用 <b>0.80</b><br>
            可根据研究实际调整，<br>
            原则上不应低于 0.75
        </div>""", unsafe_allow_html=True)
        st.session_state.consist_threshold = consist_thresh

    with col3:
        st.markdown('<div style="font-size:0.75rem;color:#4a5a7a;margin-bottom:4px;">PRI 一致性阈值</div>', unsafe_allow_html=True)
        pri_thresh = st.number_input(
            "PRI 阈值", min_value=0.0, max_value=1.0, step=0.01,
            value=float(st.session_state.get("pri_threshold", 0.75)),
            format="%.2f", label_visibility="collapsed", key="inp_pri"
        )
        st.markdown("""
        <div style="font-size:0.72rem;color:#3a4a6a;line-height:1.7;">
            学术界无定论<br>
            操作层面推荐至少 ≥ <b>0.50</b><br>
            <i>注：结果变量为清晰集（0/1）时<br>PRI 恒为 1.00</i>
        </div>""", unsafe_allow_html=True)
        st.session_state.pri_threshold = pri_thresh

    st.markdown("<br>", unsafe_allow_html=True)

    col_run_tt, _ = st.columns([2, 5])
    with col_run_tt:
        run_tt = st.button("▶ 生成真值表", key="run_truth_table")

    if run_tt:
        st.session_state.truth_table_done   = False
        st.session_state.minimization_done  = False
        st.session_state.ai_names_done      = False

    if run_tt or st.session_state.get("truth_table_done", False):
        df_tt, row_info, n_excl = build_truth_table(
            calibrated, cases, ind_names,
            freq_thresh, consist_thresh, pri_thresh
        )
        st.session_state.truth_table_df      = df_tt
        st.session_state.truth_table_row_info = row_info
        st.session_state.truth_table_done    = True

        st.markdown("<br>", unsafe_allow_html=True)
        if n_excl > 0:
            st.markdown(
                f'<div style="font-size:0.78rem;color:#e8a23a;margin-bottom:8px;">'
                f'⚠ {n_excl} 个案例因校准分数恰好等于 0.50（交叉点）而被排除。</div>',
                unsafe_allow_html=True
            )

        if df_tt.empty:
            st.warning("⚠ 没有观察到任何案例，请检查校准数据。")
        else:
            _render_truth_table(df_tt)
            st.markdown("""
            <div style="font-size:0.72rem;color:#3a4a6a;margin-top:10px;line-height:1.8;">
                算法参考：Dușa, A. (2019). <i>QCA with R: A Comprehensive Resource</i>. Springer.
                Thiem, A., & Dușa, A. (2013). <i>Qualitative Comparative Analysis with R</i>. Springer.
            </div>
            """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 6.2 布尔最小化
    # ════════════════════════════════════════════════════
    if not st.session_state.get("truth_table_done", False):
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(_step_header("6.2", "布尔最小化"), unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.8rem;color:#8ba8c8;margin-bottom:14px;line-height:1.7;">
        基于 Quine-McCluskey 算法化简真值表，输出组态路径。<br>
        <b style="color:#5b9bd5;">核心条件</b>（大符号）= 出现在简约解中；
        <b style="color:#7ab3e8;">边缘条件</b>（小符号）= 仅出现在复杂解中。
    </div>
    """, unsafe_allow_html=True)

    col_run_qmc, _ = st.columns([2, 5])
    with col_run_qmc:
        run_qmc = st.button("▶ 开始布尔最小化", key="run_qmc")

    if run_qmc:
        st.session_state.minimization_done = False
        st.session_state.ai_names_done     = False

    if run_qmc or st.session_state.get("minimization_done", False):
        row_info = st.session_state.truth_table_row_info

        result = run_minimization(row_info, ind_names, n_vars)
        complex_sol = result["complex"]
        pars_sol    = result["parsimonious"]
        core_dirs   = result["core_cond_directions"]

        metrics_c, sol_c_consist, sol_c_cov = calc_solution_metrics(
            complex_sol, calibrated, cases, ind_names)
        metrics_p, sol_p_consist, sol_p_cov = calc_solution_metrics(
            pars_sol, calibrated, cases, ind_names)

        st.session_state.minimization_done   = True
        st.session_state.complex_sol         = complex_sol
        st.session_state.pars_sol            = pars_sol
        st.session_state.core_dirs           = core_dirs
        st.session_state.metrics_complex     = (metrics_c, sol_c_consist, sol_c_cov)
        st.session_state.metrics_pars        = (metrics_p, sol_p_consist, sol_p_cov)

        if not complex_sol and not pars_sol:
            st.warning("⚠ 未找到有效的组态路径。请检查真值表阈值设置。")
            return

        # 显示复杂解
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#5b9bd5;
                    margin:16px 0 8px 0;letter-spacing:0.06em;">复杂解（Conservative Solution）</div>
        """, unsafe_allow_html=True)
        if complex_sol:
            _render_path_table(complex_sol, metrics_c, sol_c_consist, sol_c_cov,
                               ind_names, core_dirs)
        else:
            st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">无有效路径</div>', unsafe_allow_html=True)

        # 显示简约解
        st.markdown("""
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#e8a23a;
                    margin:20px 0 8px 0;letter-spacing:0.06em;">简约解（Parsimonious Solution）</div>
        """, unsafe_allow_html=True)
        if pars_sol:
            _render_path_table(pars_sol, metrics_p, sol_p_consist, sol_p_cov,
                               ind_names, core_dirs)
        else:
            st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">无有效路径</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.72rem;color:#3a4a6a;margin-top:14px;line-height:1.8;">
            算法参考：Dușa, A. (2019). <i>QCA with R: A Comprehensive Resource</i>. Springer.
            Thiem, A., & Dușa, A. (2013). <i>Qualitative Comparative Analysis with R</i>. Springer.
        </div>
        """, unsafe_allow_html=True)

    # ── 一致性-覆盖度散点图 ──────────────────────────────
    if st.session_state.get("minimization_done", False):
        metrics_c, sol_c_consist, sol_c_cov = st.session_state.get(
            "metrics_complex", ([], 0.0, 0.0))
        if metrics_c:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                            display:flex;align-items:center;justify-content:center;
                            font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">图</div>
                <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
                    组态路径一致性-覆盖度散点图
                </div>
            </div>
            """, unsafe_allow_html=True)
            try:
                from core.visualizer import plot_consistency_coverage
                consist_thr = st.session_state.get("consist_threshold", 0.80)
                fig_cc, img_cc = plot_consistency_coverage(
                    metrics_c, sol_c_consist, sol_c_cov, consist_thr
                )
                st.pyplot(fig_cc, use_container_width=True)
                st.session_state["img_consist_cov"] = img_cc
                st.download_button(
                    "⬇ 下载一致性-覆盖度图 PNG", img_cc,
                    file_name="consistency_coverage.png", mime="image/png",
                    key="dl_cc_stage6"
                )
            except Exception as e:
                st.caption(f"散点图生成失败：{e}")

    # ════════════════════════════════════════════════════
    # AI 组态命名
    # ════════════════════════════════════════════════════
    if not st.session_state.get("minimization_done", False):
        return

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(_step_header("6.3", "AI 组态路径命名"), unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.8rem;color:#8ba8c8;margin-bottom:14px;line-height:1.7;">
        结合案例内容和组态组合方式，由 AI 为每条路径建议学术性命名。
    </div>
    """, unsafe_allow_html=True)

    col_ai, _ = st.columns([2, 5])
    with col_ai:
        run_ai = st.button("▶ 生成 AI 组态命名", key="run_ai_naming")

    if run_ai:
        st.session_state.ai_names_done = False

    if run_ai or st.session_state.get("ai_names_done", False):
        if run_ai:
            ai_names = _get_ai_names(
                st.session_state.complex_sol,
                ind_names,
                cases,
                calibrated
            )
            st.session_state.ai_names      = ai_names
            st.session_state.ai_names_done = True
        else:
            ai_names = st.session_state.get("ai_names", {})

        if ai_names:
            for path_key, name_info in ai_names.items():
                st.markdown(f"""
                <div style="background:#0f1117;border:1px solid #2a3a5c;border-radius:4px;
                            padding:12px 16px;margin-bottom:8px;">
                    <div style="font-size:0.72rem;color:#4a5a7a;font-family:'IBM Plex Mono',monospace;
                                margin-bottom:4px;">{path_key}</div>
                    <div style="font-size:0.9rem;color:#c8d8e8;font-weight:500;">{name_info.get('name','—')}</div>
                    <div style="font-size:0.78rem;color:#6b8aaa;margin-top:4px;line-height:1.6;">
                        {name_info.get('rationale','')}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.72rem;color:#6a4a2a;margin-top:10px;
                    border:1px solid #4a3a1a;border-radius:3px;padding:6px 12px;background:#1a1006;">
            ⚠ 组态路径命名由 AI 生成，仅供建议参考，请结合理论背景判断。
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        col_next, _ = st.columns([2, 5])
        with col_next:
            if st.button("→ 进入结果汇总与导出", key="go_to_7"):
                st.session_state.stage = 7
                st.rerun()


# ════════════════════════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════════════════════════

def _step_header(num, title):
    return f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">{num}</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">{title}</div>
    </div>"""


def _render_truth_table(df):
    """渲染真值表，按结果赋值着色。"""
    color_map = {"✓ 充分条件组态": "#0d2a1a", "✗ 不充分": "#2a0a0a"}
    header = "".join(
        f'<th style="padding:7px 12px;text-align:center;font-family:\'IBM Plex Mono\',monospace;'
        f'font-size:0.72rem;color:#4a5a7a;border-bottom:1px solid #2a3a5c;">{c}</th>'
        for c in df.columns
    )
    rows_html = ""
    for _, row in df.iterrows():
        bg = color_map.get(str(row.get("类型", "")), "#0f1117")
        cells = ""
        for c in df.columns:
            v = row[c]
            color = "#e8e8e8"
            if c == "结果" and v == 1:
                color = "#3dba6f"
            elif c == "结果" and v == 0:
                color = "#c06060"
            elif c == "类型":
                color = "#3dba6f" if "充分" in str(v) else "#6b7a99"
            cells += (
                f'<td style="padding:7px 12px;text-align:center;font-size:0.82rem;'
                f'color:{color};border-bottom:1px solid #1a2a3a;">{v}</td>'
            )
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #2a3a5c;border-radius:4px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#141824;">{header}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True
    )


def _sym(cond_name, direction, core_dirs):
    """返回 Ragin & Fiss 符号 HTML。"""
    is_core = (cond_name, direction) in core_dirs
    if direction == 1:
        if is_core:
            return '<span style="font-size:1.5em;color:#5b9bd5;font-weight:bold;">●</span>'
        else:
            return '<span style="font-size:1.0em;color:#7ab3e8;">●</span>'
    else:
        if is_core:
            return '<span style="font-size:1.5em;color:#c06060;font-weight:bold;">⊗</span>'
        else:
            return '<span style="font-size:1.0em;color:#e0887a;">⊗</span>'


def _render_path_table(solution, metrics, sol_consist, sol_cov, ind_names, core_dirs):
    """渲染组态路径表（Ragin & Fiss 2008 符号体系）。"""
    n_paths = len(metrics)
    if n_paths == 0:
        return

    # 表头：条件名 + 路径列
    path_labels = [f"路径 {i+1}" for i in range(n_paths)]
    header_cells = (
        '<th style="padding:8px 14px;text-align:left;font-family:\'IBM Plex Mono\',monospace;'
        'font-size:0.75rem;color:#4a5a7a;border-bottom:1px solid #2a3a5c;">条件</th>'
    )
    for lbl in path_labels:
        header_cells += (
            f'<th style="padding:8px 14px;text-align:center;font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.75rem;color:#5b9bd5;border-bottom:1px solid #2a3a5c;">{lbl}</th>'
        )

    # 条件行
    cond_rows = ""
    for cond in ind_names:
        row_cells = (
            f'<td style="padding:8px 14px;font-size:0.84rem;color:#c8d8e8;'
            f'border-bottom:1px solid #1a2a3a;">{cond}</td>'
        )
        for m in metrics:
            term = m["term"]
            j    = ind_names.index(cond)
            if term[j] == '-':
                cell = ""
            else:
                cell = _sym(cond, term[j], core_dirs)
            row_cells += (
                f'<td style="padding:8px 14px;text-align:center;'
                f'border-bottom:1px solid #1a2a3a;">{cell}</td>'
            )
        cond_rows += f'<tr style="background:#0f1117;">{row_cells}</tr>'

    # 指标行
    def metric_row(label, values, highlight=False):
        color = "#5b9bd5" if highlight else "#8ba8c8"
        cells = (
            f'<td style="padding:6px 14px;font-family:\'IBM Plex Mono\',monospace;'
            f'font-size:0.75rem;color:{color};border-bottom:1px solid #1a2a3a;">{label}</td>'
        )
        for v in values:
            cells += (
                f'<td style="padding:6px 14px;text-align:center;'
                f'font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;'
                f'color:{color};border-bottom:1px solid #1a2a3a;">{v}</td>'
            )
        return f'<tr style="background:#141824;">{cells}</tr>'

    consist_vals   = [m["consistency"]    for m in metrics]
    raw_cov_vals   = [m["raw_coverage"]   for m in metrics]
    uniq_cov_vals  = [m["unique_coverage"] for m in metrics]
    # 解的指标只在最后一列合并显示
    sol_consist_vals = [""] * n_paths
    sol_cov_vals     = [""] * n_paths
    if n_paths > 0:
        sol_consist_vals[-1] = sol_consist
        sol_cov_vals[-1]     = sol_cov

    metric_rows = (
        metric_row("一致性",    consist_vals)
        + metric_row("原始覆盖度", raw_cov_vals)
        + metric_row("唯一覆盖度", uniq_cov_vals)
        + metric_row("解的一致性", sol_consist_vals, highlight=True)
        + metric_row("解的覆盖度", sol_cov_vals,     highlight=True)
    )

    # 符号说明
    legend = """
    <div style="font-size:0.72rem;color:#4a5a7a;margin-top:8px;line-height:2.0;">
        <span style="font-size:1.2em;color:#5b9bd5;font-weight:bold;">●</span> 核心条件存在 &nbsp;
        <span style="font-size:1.2em;color:#c06060;font-weight:bold;">⊗</span> 核心条件缺乏 &nbsp;
        <span style="font-size:0.9em;color:#7ab3e8;">●</span> 边缘条件存在 &nbsp;
        <span style="font-size:0.9em;color:#e0887a;">⊗</span> 边缘条件缺乏 &nbsp;
        空白 = 条件可有可无
    </div>
    """

    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid #2a3a5c;border-radius:4px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#141824;">{header_cells}</tr></thead>'
        f'<tbody>{cond_rows}{metric_rows}</tbody></table></div>'
        + legend,
        unsafe_allow_html=True
    )


def _get_ai_names(solution, ind_names, cases, calibrated_scores):
    """调用 API 为每条路径生成学术命名。"""
    if not solution:
        return {}

    api_key  = st.session_state.get("api_key", "")
    model    = st.session_state.get("model_choice", "gpt-4o")
    base_url = st.session_state.get("base_url", "https://api.openai.com/v1").rstrip("/")

    results = {}

    for k, (term, covered) in enumerate(solution):
        # 描述该路径的条件组合
        present  = [ind_names[j] for j in range(len(ind_names)) if term[j] == 1]
        absent   = [ind_names[j] for j in range(len(ind_names)) if term[j] == 0]
        irrelevant = [ind_names[j] for j in range(len(ind_names)) if term[j] == '-']

        cond_desc = ""
        if present:
            cond_desc += f"存在：{', '.join(present)}；"
        if absent:
            cond_desc += f"缺乏：{', '.join(absent)}；"
        if irrelevant:
            cond_desc += f"无关：{', '.join(irrelevant)}"

        # 取该路径覆盖的案例（最多3例）
        case_samples = []
        for ci in list(covered)[:3]:
            if ci < len(cases):
                txt = cases[ci]["案例文本"][:80]
                case_samples.append(f"案例{ci+1}：{txt}")
        sample_text = "\n".join(case_samples) if case_samples else "（无具体案例样本）"

        prompt = (
            f"在一项 fsQCA 定性比较分析中，以下是一条组态路径：\n\n"
            f"条件组合：{cond_desc}\n\n"
            f"该路径覆盖的部分案例示例：\n{sample_text}\n\n"
            f"请为这条组态路径建议一个简洁的学术命名（2~5个中文词，可参考已有 QCA 文献的命名惯例），"
            f"并用一句话说明命名理由。\n\n"
            f"请以 JSON 格式返回：\n"
            f'{{"name": "命名", "rationale": "理由"}}'
        )

        try:
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "你是一位 QCA 研究专家，擅长为组态路径提供学术命名。"},
                    {"role": "user",   "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 200
            }
            resp = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                import re
                content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
                name_info = json.loads(content)
            else:
                name_info = {"name": "（API 错误）", "rationale": resp.text[:100]}
        except Exception as e:
            name_info = {"name": "（生成失败）", "rationale": str(e)[:100]}

        results[f"路径 {k+1}"] = name_info

    return results
