import streamlit as st
import pandas as pd
import io


def render_stage7():
    st.markdown('<div class="card-title">// 阶段七 · 结果汇总与导出</div>', unsafe_allow_html=True)

    if st.button("← 返回第六阶段", key="back_to_6"):
        st.session_state.stage = 6
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #5b9bd5;
                border-radius:4px;padding:14px 20px;margin-bottom:24px;font-size:0.84rem;
                color:#8ba8c8;line-height:1.8;">
        以下汇总本次 QCA 分析所有阶段的结果，可逐项下载为 CSV 文件。
    </div>
    """, unsafe_allow_html=True)

    ind_names = [ind["name"] for ind in st.session_state.get("indicators", [])]
    cases     = st.session_state.get("cases", [])

    # ── 1. 校准结果 ───────────────────────────────────────
    _section("① 校准结果（模糊集隶属分数）")
    calibrated = st.session_state.get("calibrated_scores", {})
    edit_scores = st.session_state.get("edit_scores", {})
    if calibrated:
        rows = []
        for ci, case in enumerate(cases):
            row = {"case_id": ci+1, "case_text": case["案例文本"][:60], "outcome": case["结果变量"]}
            for name in ind_names:
                row[f"{name}（原始）"]  = edit_scores.get(ci, {}).get(name, "")
                row[f"{name}（校准）"] = calibrated.get(ci, {}).get(name, "")
            rows.append(row)
        df_calib = pd.DataFrame(rows)
        st.dataframe(df_calib, use_container_width=True, height=250)
        _dl_btn(df_calib, "qca_calibrated.csv", "⬇ 下载校准数据", key="dl_calib")
    else:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">尚无校准数据</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 2. 必要条件分析 ───────────────────────────────────
    _section("② 必要条件分析结果")
    necessity_df = st.session_state.get("necessity_df")
    if necessity_df is not None and not necessity_df.empty:
        thr = st.session_state.get("necessity_threshold", 0.90)
        df_n = necessity_df.copy()
        df_n["判断"] = df_n["一致性"].apply(lambda c: "✓ 必要条件" if float(c) >= thr else "—")
        st.dataframe(df_n, use_container_width=True)
        _dl_btn(df_n, "qca_necessity.csv", "⬇ 下载必要条件结果", key="dl_necessity")
    else:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">尚无必要条件分析数据</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 3. 真值表 ─────────────────────────────────────────
    _section("③ 真值表")
    tt_df = st.session_state.get("truth_table_df")
    if tt_df is not None and not tt_df.empty:
        st.dataframe(tt_df, use_container_width=True, height=300)
        _dl_btn(tt_df, "qca_truth_table.csv", "⬇ 下载真值表", key="dl_tt")
    else:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">尚无真值表数据</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 4. 布尔最小化路径 ─────────────────────────────────
    _section("④ 布尔最小化路径")
    complex_sol = st.session_state.get("complex_sol", [])
    metrics_c   = st.session_state.get("metrics_complex", ([], 0.0, 0.0))
    pars_sol    = st.session_state.get("pars_sol", [])
    metrics_p   = st.session_state.get("metrics_pars", ([], 0.0, 0.0))

    if complex_sol:
        st.markdown('<div style="font-size:0.78rem;color:#5b9bd5;margin-bottom:6px;">复杂解</div>', unsafe_allow_html=True)
        df_c = _paths_to_df(complex_sol, metrics_c, ind_names)
        st.dataframe(df_c, use_container_width=True)
        _dl_btn(df_c, "qca_complex_solution.csv", "⬇ 下载复杂解", key="dl_complex")

    if pars_sol:
        st.markdown('<div style="font-size:0.78rem;color:#e8a23a;margin:10px 0 6px 0;">简约解</div>', unsafe_allow_html=True)
        df_p = _paths_to_df(pars_sol, metrics_p, ind_names)
        st.dataframe(df_p, use_container_width=True)
        _dl_btn(df_p, "qca_parsimonious_solution.csv", "⬇ 下载简约解", key="dl_pars")

    if not complex_sol and not pars_sol:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">尚无布尔最小化结果</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 5. AI 命名 ────────────────────────────────────────
    _section("⑤ AI 组态路径命名")
    ai_names = st.session_state.get("ai_names", {})
    if ai_names:
        rows_ai = [{"路径": k, "AI 建议命名": v.get("name",""), "命名理由": v.get("rationale","")}
                   for k, v in ai_names.items()]
        df_ai = pd.DataFrame(rows_ai)
        st.dataframe(df_ai, use_container_width=True)
        _dl_btn(df_ai, "qca_ai_names.csv", "⬇ 下载 AI 命名", key="dl_ai")
        st.markdown("""
        <div style="font-size:0.72rem;color:#6a4a2a;margin-top:6px;padding:5px 10px;
                    border:1px solid #4a3a1a;border-radius:3px;background:#1a1006;">
            ⚠ 组态路径命名由 AI 生成，仅供参考
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">尚无 AI 命名数据</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 6. 可视化图表 ─────────────────────────────────────
    _section("⑥ 可视化图表下载")

    img_map = {
        "得分分布图": ("img_score_dist",     "score_distribution.png",    "dl7_dist"),
        "隶属度热力图": ("img_heatmap",       "membership_heatmap.png",    "dl7_hm"),
        "一致性-覆盖度散点图": ("img_consist_cov", "consistency_coverage.png", "dl7_cc"),
    }
    any_img = False
    cols_img = st.columns(3)
    for ci_img, (label, (key, fname, dl_key)) in enumerate(img_map.items()):
        img_bytes = st.session_state.get(key)
        with cols_img[ci_img]:
            if img_bytes:
                any_img = True
                st.image(img_bytes, caption=label, use_container_width=True)
                st.download_button(
                    f"⬇ {label}", img_bytes,
                    file_name=fname, mime="image/png", key=dl_key
                )
            else:
                st.markdown(
                    f'<div style="color:#3a4a6a;font-size:0.78rem;text-align:center;'
                    f'padding:20px 0;">{label}<br>（尚未生成）</div>',
                    unsafe_allow_html=True
                )

    if not any_img:
        st.markdown('<div style="color:#4a5a7a;font-size:0.82rem;">请先完成各阶段分析以生成图表。</div>',
                    unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── 重置 ──────────────────────────────────────────────
    col_reset, _ = st.columns([1, 4])
    with col_reset:
        if st.button("↺ 全部重置，重新开始", key="full_reset"):
            keep = set()
            for k in list(st.session_state.keys()):
                if k not in keep:
                    del st.session_state[k]
            st.session_state.stage = 1
            st.rerun()


# ── 辅助函数 ──────────────────────────────────────────────

def _section(title):
    st.markdown(
        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.82rem;'
        f'color:#5b9bd5;margin:8px 0 10px 0;letter-spacing:0.05em;">{title}</div>',
        unsafe_allow_html=True
    )


def _dl_btn(df, filename, label, key):
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(label=label, data=csv_bytes, file_name=filename,
                       mime="text/csv", key=key)


def _paths_to_df(solution, metrics_tuple, ind_names):
    path_metrics, sol_consist, sol_cov = metrics_tuple
    rows = []
    for k, (m, (term, _)) in enumerate(zip(path_metrics, solution)):
        row = {"路径": f"路径 {k+1}"}
        for j, name in enumerate(ind_names):
            v = term[j]
            row[name] = "存在" if v == 1 else ("缺乏" if v == 0 else "—")
        row["一致性"]    = m["consistency"]
        row["原始覆盖度"] = m["raw_coverage"]
        row["唯一覆盖度"] = m["unique_coverage"]
        row["解的一致性"] = sol_consist if k == len(path_metrics)-1 else ""
        row["解的覆盖度"] = sol_cov     if k == len(path_metrics)-1 else ""
        rows.append(row)
    return pd.DataFrame(rows)
