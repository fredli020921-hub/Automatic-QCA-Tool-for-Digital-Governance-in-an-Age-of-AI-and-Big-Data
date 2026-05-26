import streamlit as st
import time
from core.llm_scorer import score_cases
import pandas as pd


def render_stage3():
    st.markdown('<div class="card-title">// 阶段三 · AI 评分 & 结果确认</div>', unsafe_allow_html=True)

    if st.button("← 返回第二阶段", key="back_to_2"):
        st.session_state.stage = 2
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    cases      = st.session_state.cases
    indicators = st.session_state.indicators
    qca_type   = st.session_state.qca_type
    n_cases      = len(cases)
    n_indicators = len(indicators)
    total_calls  = n_cases * n_indicators
    ind_names    = [ind["name"] for ind in indicators]

    # ════════════════════════════════════════════════════
    # 3.1 AI 评分
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">3.1</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">AI 自动评分</div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("案例数", n_cases)
    c2.metric("理论指标数", n_indicators)
    c3.metric("评分类型", qca_type)
    c4.metric("预估 API 请求次数", total_calls)

    already_scored = bool(st.session_state.get("scores"))

    if not already_scored:
        st.markdown("""
        <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #5b9bd5;
                    border-radius:4px;padding:12px 18px;margin:16px 0;font-size:0.82rem;color:#8ba8c8;line-height:1.7;">
            大模型将结合理论说明与水平操作化标准，逐案例对每个指标打分。<br>
            <b style="color:#5b9bd5;">fsQCA</b>：输出 0.00~1.00 之间的连续小数得分（AI 自由判定）。<br>
            <b style="color:#5b9bd5;">csQCA</b>：输出 0 或 1 的二元值。
        </div>
        """, unsafe_allow_html=True)

        col_start, _ = st.columns([2, 4])
        with col_start:
            start_scoring = st.button("▶ 开始 AI 评分", key="start_scoring")

        if start_scoring:
            progress_bar = st.progress(0)
            status_text  = st.empty()
            scores    = {}
            reasoning = {}
            errors    = []

            for case_idx, case in enumerate(cases):
                scores[case_idx]    = {}
                reasoning[case_idx] = {}

                for ind_idx, indicator in enumerate(indicators):
                    ind_name = indicator["name"]
                    progress = (case_idx * n_indicators + ind_idx) / total_calls
                    status_text.markdown(
                        f'<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:#6b7a99;">'
                        f'评分中 · Case {case_idx+1}/{n_cases} · 指标「{ind_name}」</div>',
                        unsafe_allow_html=True
                    )
                    progress_bar.progress(progress)

                    try:
                        score, reason = score_cases(
                            case_text      = case["案例文本"],
                            indicator_name = ind_name,
                            indicator_desc = indicator.get("description", ""),
                            qca_type       = qca_type,
                            api_key        = st.session_state.api_key,
                            model          = st.session_state.get("model_choice", "gpt-4o"),
                            base_url       = st.session_state.get("base_url", "https://api.openai.com/v1"),
                            criteria_high  = indicator.get("criteria_high", ""),
                            criteria_mid   = indicator.get("criteria_mid", ""),
                            criteria_low   = indicator.get("criteria_low", ""),
                        )
                        scores[case_idx][ind_name]    = score
                        reasoning[case_idx][ind_name] = reason
                    except Exception as e:
                        scores[case_idx][ind_name]    = None
                        reasoning[case_idx][ind_name] = f"[错误] {e}"
                        errors.append(f"Case {case_idx+1} · {ind_name}：{e}")

            progress_bar.progress(1.0)
            status_text.markdown(
                '<div style="font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:#3dba6f;">✓ 评分完成</div>',
                unsafe_allow_html=True
            )

            st.session_state.scores    = scores
            st.session_state.reasoning = reasoning
            st.session_state.edit_scores = {
                ci: {name: scores[ci].get(name) for name in ind_names}
                for ci in range(n_cases)
            }
            st.session_state.calibration_done  = False
            st.session_state.calibrated_scores = {}

            if errors:
                st.warning(f"⚠️ {len(errors)} 条评分出现错误，可在下方手动填写")

            time.sleep(0.3)
            st.rerun()
        return   # 未评分时，只显示上方内容

    # ── 已完成评分：显示重新评分按钮 ─────────────────────
    col_re, col_tip = st.columns([1, 4])
    with col_re:
        if st.button("🔄 重新评分", key="rescore"):
            st.session_state.scores            = {}
            st.session_state.reasoning         = {}
            st.session_state.edit_scores       = {}
            st.session_state.calibrated_scores = {}
            st.session_state.calibration_done  = False
            st.rerun()
    with col_tip:
        st.markdown(
            '<span style="font-size:0.75rem;color:#4a5a7a;line-height:2.8;'
            'font-family:\'IBM Plex Mono\',monospace;">✓ AI 评分已完成，请在下方核查并确认得分</span>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 3.2 结果核查与人工调整
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">3.2</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
            核查 AI 评分 · 人工调整
        </div>
    </div>
    """, unsafe_allow_html=True)

    score_hint = "0.00~1.00 连续值" if qca_type == "fsQCA" else "0 或 1"
    st.markdown(f"""
    <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #e8a23a;
                border-radius:4px;padding:10px 16px;margin-bottom:16px;font-size:0.8rem;color:#8ba8c8;">
        查看每个案例的 AI 评分理由，如有不准确可直接修改得分（{score_hint}）。
        确认无误后点击底部「确认评分，进入下一步」。
    </div>
    """, unsafe_allow_html=True)

    # 初始化 edit_scores
    if not st.session_state.get("edit_scores"):
        st.session_state.edit_scores = {
            ci: {name: st.session_state.scores[ci].get(name) for name in ind_names}
            for ci in range(n_cases)
        }

    scores    = st.session_state.scores
    reasoning = st.session_state.reasoning

    # 视图切换
    view_mode = st.radio(
        "查看方式",
        ["📋 逐案例详细查看（含 AI 评分理由）", "📊 汇总表格"],
        horizontal=True, label_visibility="collapsed"
    )
    st.markdown("<br>", unsafe_allow_html=True)

    # ── 逐案例视图 ────────────────────────────────────────
    if "逐案例" in view_mode:
        for ci, case in enumerate(cases):
            case_text = case["案例文本"]
            outcome   = case["结果变量"]

            with st.expander(
                f"Case {ci+1}  ·  结果变量={outcome}  ·  {case_text[:45]}{'...' if len(case_text)>45 else ''}",
                expanded=(ci == 0)
            ):
                # 案例全文
                st.markdown(f"""
                <div style="background:#0f1117;border:1px solid #2a3a5c;border-radius:4px;
                            padding:12px 16px;margin-bottom:16px;font-size:0.85rem;
                            color:#b0c4d8;line-height:1.7;">
                    <span style="font-size:0.7rem;color:#4a5a7a;font-family:'IBM Plex Mono',monospace;
                                 display:block;margin-bottom:6px;">案例全文</span>
                    {case_text}
                </div>
                """, unsafe_allow_html=True)

                # 列表头
                h_name, h_score, h_flag = st.columns([3, 2, 1])
                h_name.markdown('<div style="font-size:0.72rem;color:#4a5a7a;font-family:\'IBM Plex Mono\',monospace;">指标</div>', unsafe_allow_html=True)
                h_score.markdown('<div style="font-size:0.72rem;color:#4a5a7a;font-family:\'IBM Plex Mono\',monospace;">得分（可直接修改）</div>', unsafe_allow_html=True)

                for ind_name in ind_names:
                    current_score = st.session_state.edit_scores[ci].get(ind_name)
                    reason_text   = reasoning.get(ci, {}).get(ind_name, "")

                    col_name, col_score, col_flag = st.columns([3, 2, 1])

                    with col_name:
                        st.markdown(
                            f'<div style="font-size:0.85rem;color:#c8d8e8;padding:8px 0;'
                            f'font-family:\'IBM Plex Mono\',monospace;">{ind_name}</div>',
                            unsafe_allow_html=True
                        )

                    with col_score:
                        if qca_type == "fsQCA":
                            new_score = st.number_input(
                                f"s_{ci}_{ind_name}",
                                min_value=0.0, max_value=1.0, step=0.01,
                                value=float(current_score) if current_score is not None else 0.5,
                                format="%.2f",
                                label_visibility="collapsed",
                                key=f"edit_{ci}_{ind_name}"
                            )
                        else:
                            # csQCA：0 或 1，用 number_input step=1
                            new_score = st.number_input(
                                f"s_{ci}_{ind_name}",
                                min_value=0, max_value=1, step=1,
                                value=int(current_score) if current_score is not None else 0,
                                label_visibility="collapsed",
                                key=f"edit_{ci}_{ind_name}"
                            )
                        st.session_state.edit_scores[ci][ind_name] = new_score

                    with col_flag:
                        if current_score is None:
                            st.markdown(
                                '<div style="font-size:0.72rem;color:#e8a23a;padding-top:10px;">⚠ 缺失</div>',
                                unsafe_allow_html=True
                            )

                    # AI 评分理由
                    if reason_text and not reason_text.startswith("[错误]"):
                        st.markdown(f"""
                        <div style="background:#0a1520;border-left:2px solid #2a4a6a;
                                    border-radius:0 3px 3px 0;padding:8px 14px;
                                    margin:4px 0 12px 0;font-size:0.78rem;color:#6b8aaa;line-height:1.6;">
                            <span style="color:#4a6a8a;font-family:'IBM Plex Mono',monospace;
                                         font-size:0.7rem;">AI 评分理由 ·</span>
                            {reason_text}
                        </div>
                        """, unsafe_allow_html=True)
                    elif reason_text.startswith("[错误]"):
                        st.markdown(f"""
                        <div style="background:#1a0a0a;border-left:2px solid #6a2a2a;
                                    border-radius:0 3px 3px 0;padding:6px 14px;
                                    margin:4px 0 12px 0;font-size:0.75rem;color:#c06060;">
                            {reason_text}
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown('<hr style="margin:4px 0;border-color:#1a2a3a;">', unsafe_allow_html=True)

    # ── 汇总表格视图 ──────────────────────────────────────
    else:
        rows = []
        for ci, case in enumerate(cases):
            row = {
                "Case": f"Case {ci+1}",
                "结果变量": case["结果变量"],
                "文本摘要": case["案例文本"][:40] + "..." if len(case["案例文本"]) > 40 else case["案例文本"],
            }
            for name in ind_names:
                v = st.session_state.edit_scores.get(ci, {}).get(name)
                row[name] = f"{v:.2f}" if v is not None else "—"
            rows.append(row)
        st.dataframe(pd.DataFrame(rows), use_container_width=True, height=400)
        st.markdown(
            '<div style="font-size:0.78rem;color:#4a5a7a;margin-top:8px;'
            'font-family:\'IBM Plex Mono\',monospace;">切换到「逐案例」视图可查看 AI 理由并修改得分</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ── 得分分布图 ──────────────────────────────────────
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">图</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
            各指标 AI 评分分布图
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        from core.visualizer import plot_score_distribution
        import streamlit as _st
        fig_dist, img_dist = plot_score_distribution(
            st.session_state.edit_scores, ind_names, n_cases
        )
        st.pyplot(fig_dist, use_container_width=True)
        st.session_state["img_score_dist"] = img_dist
        st.download_button(
            "⬇ 下载得分分布图 PNG", img_dist,
            file_name="score_distribution.png", mime="image/png",
            key="dl_dist_stage3"
        )
    except Exception as e:
        st.caption(f"图表生成失败：{e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # ════════════════════════════════════════════════════
    # 确认按钮
    # ════════════════════════════════════════════════════
    next_label = "✓ 确认评分，进入校准 →" if qca_type == "fsQCA" else "✓ 确认评分，导出结果 →"
    hint_text  = "确认后将进入 → 阶段四：模糊集校准" if qca_type == "fsQCA" else "确认后将进入 → 阶段四：导出结果"

    col_btn, col_hint = st.columns([2, 4])
    with col_btn:
        if st.button(next_label, key="confirm_and_next"):
            st.session_state.calibration_done  = False
            st.session_state.calibrated_scores = {}
            st.session_state.stage = 4
            st.rerun()
    with col_hint:
        st.markdown(
            f'<span style="font-size:0.75rem;color:#4a5a7a;line-height:2.8;'
            f'font-family:\'IBM Plex Mono\',monospace;">{hint_text}</span>',
            unsafe_allow_html=True
        )
