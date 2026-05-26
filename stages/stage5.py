import streamlit as st
import pandas as pd
from core.necessity import run_necessity_analysis


def render_stage5():
    st.markdown('<div class="card-title">// 阶段五 · 必要条件分析</div>', unsafe_allow_html=True)

    if st.button("← 返回第四阶段", key="back_to_4"):
        st.session_state.stage = 4
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 数据检查
    calibrated = st.session_state.get("calibrated_scores", {})
    if not calibrated:
        st.warning("⚠ 请先完成第四阶段的模糊集校准。")
        return

    cases     = st.session_state.cases
    ind_names = [ind["name"] for ind in st.session_state.indicators]

    # ════════════════════════════════════════════════════
    # 5.1 设置阈值
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">5.1</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
            设置必要条件一致性阈值
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_inp, col_space = st.columns([2, 5])
    with col_inp:
        threshold = st.number_input(
            "必要条件一致性阈值",
            min_value=0.0, max_value=1.0, step=0.01,
            value=float(st.session_state.get("necessity_threshold", 0.90)),
            format="%.2f",
            label_visibility="collapsed",
            key="inp_necessity"
        )
        st.session_state.necessity_threshold = threshold

    st.markdown("""
    <div style="font-size:0.75rem;color:#4a5a7a;margin-top:6px;line-height:1.9;">
        默认值 <b style="color:#5b9bd5;">0.90</b>（可输入 0~1 之间任意值）<br>
        参考文献：Ragin, C. C. and Fiss, P. C., 2008, "Net Effects Analysis Versus
        Configurational Analysis: An Empirical Demonstration",
        <i>Redesigning Social Inquiry: Fuzzy Sets and Beyond</i>, Vol.240, pp.190~212.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 5.2 运行计算
    # ════════════════════════════════════════════════════
    col_run, _ = st.columns([2, 5])
    with col_run:
        run_btn = st.button("▶ 开始必要条件计算", key="run_necessity")

    if run_btn:
        st.session_state.necessity_done = False

    if run_btn or st.session_state.get("necessity_done", False):
        df = run_necessity_analysis(calibrated, cases, ind_names)
        st.session_state.necessity_df   = df
        st.session_state.necessity_done = True

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                        display:flex;align-items:center;justify-content:center;
                        font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">5.2</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
                分析结果
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 添加判断列
        thr = st.session_state.necessity_threshold
        df_show = df.copy()
        df_show["判断"] = df_show["一致性"].apply(
            lambda c: "✓ 必要条件" if float(c) >= thr else "—"
        )

        st.markdown("""
        <div style="font-size:0.8rem;color:#8ba8c8;margin-bottom:10px;line-height:1.7;">
            一致性 ≥ 阈值的条件被标记为必要条件。覆盖度（relevance）反映该条件对结果的解释力。
        </div>
        """, unsafe_allow_html=True)

        # 显示表格（手动渲染以突出必要条件行）
        _render_necessity_table(df_show, thr)

        st.markdown("""
        <div style="font-size:0.72rem;color:#3a4a6a;margin-top:12px;line-height:1.8;">
            算法参考：Dușa, A. (2019). <i>QCA with R: A Comprehensive Resource</i>. Springer.
            Thiem, A., & Dușa, A. (2013). <i>Qualitative Comparative Analysis with R</i>. Springer.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("---")
        col_next, _ = st.columns([2, 5])
        with col_next:
            if st.button("→ 进入组态充分性分析", key="go_to_6"):
                st.session_state.stage = 6
                st.rerun()


def _render_necessity_table(df, threshold):
    """渲染带高亮的必要条件表格。"""
    header_cols = list(df.columns)
    header_html = "".join(
        f'<th style="padding:8px 14px;text-align:left;font-family:\'IBM Plex Mono\',monospace;'
        f'font-size:0.75rem;color:#4a5a7a;border-bottom:1px solid #2a3a5c;">{c}</th>'
        for c in header_cols
    )

    rows_html = ""
    for _, row in df.iterrows():
        is_necessary = str(row.get("判断", "")) == "✓ 必要条件"
        bg = "#0d2a1a" if is_necessary else "#0f1117"
        cells = ""
        for col in header_cols:
            val = row[col]
            color = "#3dba6f" if (col == "判断" and is_necessary) else "#c8d8e8"
            cells += (
                f'<td style="padding:8px 14px;font-size:0.84rem;color:{color};'
                f'border-bottom:1px solid #1a2a3a;">{val}</td>'
            )
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

    html = f"""
    <div style="overflow-x:auto;border:1px solid #2a3a5c;border-radius:4px;">
    <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="background:#141824;">{header_html}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
