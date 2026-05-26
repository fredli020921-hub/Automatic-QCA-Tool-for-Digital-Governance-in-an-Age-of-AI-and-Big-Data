"""
阶段四：模糊集校准（仅 fsQCA）
参考：Ragin, C. C., & Fiss, P. C. (2008). Net Effects Analysis versus Configurational Analysis.
"""
import streamlit as st
import pandas as pd
import numpy as np


def render_stage4():
    qca_type = st.session_state.qca_type

    # ── csQCA 直接跳过 ────────────────────────────────────
    if qca_type == "csQCA":
        st.markdown('<div class="card-title">// 阶段四 · 结果导出（csQCA）</div>', unsafe_allow_html=True)
        if st.button("← 返回第三阶段", key="cs_back"):
            st.session_state.stage = 3
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #5b9bd5;
                    border-radius:4px;padding:14px 18px;margin-bottom:20px;font-size:0.85rem;color:#8ba8c8;line-height:1.7;">
            当前为 <b style="color:#5b9bd5;">csQCA（清晰集）</b>，无需模糊集校准。<br>
            已确认的 0/1 得分可直接导出用于后续 QCA 分析。
        </div>
        """, unsafe_allow_html=True)
        _render_cs_export()
        return

    # ════════════════════════════════════════════════════════
    # fsQCA 校准界面
    # ════════════════════════════════════════════════════════
    st.markdown('<div class="card-title">// 阶段四 · 模糊集校准（fsQCA）</div>', unsafe_allow_html=True)

    if st.button("← 返回第三阶段", key="back_to_3"):
        st.session_state.stage = 3
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 方法说明 ──────────────────────────────────────────
    st.markdown("""
    <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #5b9bd5;
                border-radius:4px;padding:18px 22px;margin-bottom:28px;line-height:2.0;">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.8rem;color:#5b9bd5;
                    margin-bottom:10px;letter-spacing:0.06em;">
            参考文献 · Ragin, C. C., & Fiss, P. C. (2008)
        </div>
        <div style="font-size:0.85rem;color:#c8d8e8;font-weight:500;margin-bottom:8px;">
            本工具采用直接校准法（Direct Method of Calibration）
        </div>
        <div style="font-size:0.82rem;color:#8ba8c8;line-height:1.9;">
            在模糊集定性比较分析（fsQCA）中，原始测量值需要通过校准转换为具有理论意义的
            集合隶属分数（0~1）。直接校准法需要预先设定三个关键阈值：<br><br>
            &nbsp;&nbsp;
            <span style="color:#3dba6f;font-weight:600;">● 完全隶属阈值</span>
            &nbsp;— 原始得分达到或超过此值的案例，被视为完全属于该集合（隶属分数趋近 1.00）<br>
            &nbsp;&nbsp;
            <span style="color:#e8a23a;font-weight:600;">● 交叉点（Crossover）</span>
            &nbsp;— 隶属与非隶属的临界点，模糊性最大，对应隶属分数恰好为 0.50<br>
            &nbsp;&nbsp;
            <span style="color:#c06060;font-weight:600;">● 完全不隶属阈值</span>
            &nbsp;— 原始得分低于此值的案例，被视为完全不属于该集合（隶属分数趋近 0.00）<br><br>
            默认阈值参考样本分布的分位数，遵循 Ragin & Fiss (2008) 推荐标准：
            <b style="color:#5b9bd5;">0.95 / 0.50 / 0.05</b>。
            你可以根据理论知识手动调整。
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 4.1 设置锚点阈值
    # ════════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">4.1</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
            设置三个关键阈值
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c, col_reset = st.columns([3, 3, 3, 1.5])

    with col_a:
        st.markdown("""
        <div style="background:#0a2a1a;border:1px solid #1a5a3a;border-radius:4px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-size:0.75rem;color:#3dba6f;font-family:'IBM Plex Mono',monospace;margin-bottom:4px;">
                ● 完全隶属阈值
            </div>
            <div style="font-size:0.72rem;color:#4a6a5a;line-height:1.5;">
                原始得分 ≥ 此值<br>→ 隶属分数趋近 1.00
            </div>
        </div>
        """, unsafe_allow_html=True)
        anchor_full_in = st.number_input(
            "完全隶属", min_value=0.01, max_value=1.0, step=0.01,
            value=float(st.session_state.get("anchor_full_in", 0.95)),
            format="%.2f", label_visibility="collapsed", key="inp_full_in"
        )

    with col_b:
        st.markdown("""
        <div style="background:#2a1a0a;border:1px solid #5a3a1a;border-radius:4px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-size:0.75rem;color:#e8a23a;font-family:'IBM Plex Mono',monospace;margin-bottom:4px;">
                ● 交叉点（Crossover）
            </div>
            <div style="font-size:0.72rem;color:#6a4a2a;line-height:1.5;">
                临界点，模糊性最大<br>→ 隶属分数 = 0.50
            </div>
        </div>
        """, unsafe_allow_html=True)
        anchor_crossover = st.number_input(
            "交叉点", min_value=0.01, max_value=0.99, step=0.01,
            value=float(st.session_state.get("anchor_crossover", 0.50)),
            format="%.2f", label_visibility="collapsed", key="inp_crossover"
        )

    with col_c:
        st.markdown("""
        <div style="background:#2a0a0a;border:1px solid #5a1a1a;border-radius:4px;padding:12px 14px;margin-bottom:8px;">
            <div style="font-size:0.75rem;color:#c06060;font-family:'IBM Plex Mono',monospace;margin-bottom:4px;">
                ● 完全不隶属阈值
            </div>
            <div style="font-size:0.72rem;color:#5a2a2a;line-height:1.5;">
                原始得分 ≤ 此值<br>→ 隶属分数趋近 0.00
            </div>
        </div>
        """, unsafe_allow_html=True)
        anchor_full_out = st.number_input(
            "完全不隶属", min_value=0.0, max_value=0.99, step=0.01,
            value=float(st.session_state.get("anchor_full_out", 0.05)),
            format="%.2f", label_visibility="collapsed", key="inp_full_out"
        )

    with col_reset:
        st.markdown("<div style='height:70px'></div>", unsafe_allow_html=True)
        if st.button("↺ 重置\n默认值", key="reset_anchors"):
            st.session_state.anchor_full_in   = 0.95
            st.session_state.anchor_crossover = 0.50
            st.session_state.anchor_full_out  = 0.05
            st.rerun()

    # 保存到 session
    st.session_state.anchor_full_in   = anchor_full_in
    st.session_state.anchor_crossover = anchor_crossover
    st.session_state.anchor_full_out  = anchor_full_out

    # 验证逻辑顺序
    if not (anchor_full_in > anchor_crossover > anchor_full_out):
        st.markdown("""
        <div style="background:#2a1a0a;border:1px solid #6a3a1a;border-radius:3px;
                    padding:10px 16px;margin-top:8px;font-size:0.82rem;color:#e8a23a;
                    font-family:'IBM Plex Mono',monospace;">
            ⚠ 阈值顺序错误，请确保：完全隶属 &gt; 交叉点 &gt; 完全不隶属
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown(f"""
    <div style="background:#0d1a0d;border:1px solid #2a4a2a;border-radius:3px;
                padding:8px 16px;margin-top:4px;font-size:0.78rem;
                font-family:'IBM Plex Mono',monospace;color:#5b9bd5;">
        当前阈值 &nbsp;·&nbsp;
        <span style="color:#3dba6f;">完全隶属 = {anchor_full_in:.2f}</span> &nbsp;|&nbsp;
        <span style="color:#e8a23a;">交叉点 = {anchor_crossover:.2f}</span> &nbsp;|&nbsp;
        <span style="color:#c06060;">完全不隶属 = {anchor_full_out:.2f}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════════
    # 4.2 执行校准计算
    # ════════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">4.2</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
            执行校准计算
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 检查是否有评分数据
    edit_scores = st.session_state.get("edit_scores", {})
    if not edit_scores:
        # 从 scores 初始化 edit_scores
        scores    = st.session_state.get("scores", {})
        indicators = st.session_state.get("indicators", [])
        ind_names  = [ind["name"] for ind in indicators]
        if scores:
            st.session_state.edit_scores = {
                ci: {name: scores[ci].get(name) for name in ind_names}
                for ci in range(len(st.session_state.get("cases", [])))
            }
            edit_scores = st.session_state.edit_scores

    col_run, _ = st.columns([2, 5])
    with col_run:
        run_btn = st.button("▶ 开始校准计算", key="run_calibration")

    if run_btn:
        st.session_state.calibration_done = False  # 强制重算

    if run_btn or st.session_state.get("calibration_done", False):
        cases      = st.session_state.get("cases", [])
        indicators = st.session_state.get("indicators", [])
        ind_names  = [ind["name"] for ind in indicators]

        # 执行校准
        calibrated = {}
        for ci in range(len(cases)):
            calibrated[ci] = {}
            for name in ind_names:
                raw = edit_scores.get(ci, {}).get(name)
                calibrated[ci][name] = _calibrate(raw, anchor_full_in, anchor_crossover, anchor_full_out)

        st.session_state.calibrated_scores = calibrated
        st.session_state.calibration_done  = True

        # ── 成功提示 ──────────────────────────────────────
        st.markdown("""
        <div style="background:#0d2a1a;border:1px solid #2a6a4a;border-radius:3px;
                    padding:8px 16px;font-size:0.82rem;color:#6bba8f;
                    font-family:'IBM Plex Mono',monospace;margin:12px 0;">
            ✓ 校准计算完成
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 4.3 校准结果表格 ──────────────────────────────
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                        display:flex;align-items:center;justify-content:center;
                        font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">4.3</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
                校准结果
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size:0.8rem;color:#6b7a99;margin-bottom:12px;line-height:1.7;">
            下表对比每个案例各指标的 <b style="color:#c8d8e8;">原始得分</b>（大模型输出）
            与校准后的 <b style="color:#5b9bd5;">模糊集隶属分数</b>（将用于 QCA 分析）。<br>
            交叉点处隶属分数精确为 <b style="color:#e8a23a;">0.5000</b>，高于交叉点趋近 1，低于交叉点趋近 0。
        </div>
        """, unsafe_allow_html=True)

        # 构建对比表格
        rows = []
        for ci, case in enumerate(cases):
            row = {
                "案例": f"Case {ci+1}",
                "结果变量": case["结果变量"],
                "文本摘要": case["案例文本"][:25] + "…" if len(case["案例文本"]) > 25 else case["案例文本"],
            }
            for name in ind_names:
                raw = edit_scores.get(ci, {}).get(name)
                cal = calibrated.get(ci, {}).get(name)
                row[f"{name} 原始"] = f"{raw:.2f}" if raw is not None else "—"
                row[f"{name} 隶属"] = f"{cal:.4f}" if cal is not None else "—"
            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, height=min(500, 80 + len(cases) * 38))

        # 统计摘要
        st.markdown("<br>", unsafe_allow_html=True)
        summary_cols = st.columns(len(ind_names))
        for ci_col, name in enumerate(ind_names):
            vals = [calibrated[ci].get(name) for ci in range(len(cases)) if calibrated.get(ci, {}).get(name) is not None]
            if vals:
                with summary_cols[ci_col]:
                    st.markdown(f"""
                    <div style="background:#0f1117;border:1px solid #2a3a5c;border-radius:4px;padding:10px 12px;text-align:center;">
                        <div style="font-size:0.7rem;color:#4a5a7a;font-family:'IBM Plex Mono',monospace;margin-bottom:4px;">
                            {name[:12]}{'…' if len(name)>12 else ''}
                        </div>
                        <div style="font-size:0.82rem;color:#5b9bd5;font-family:'IBM Plex Mono',monospace;">
                            均值 {np.mean(vals):.3f}
                        </div>
                        <div style="font-size:0.72rem;color:#4a5a7a;margin-top:2px;">
                            范围 {min(vals):.3f} ~ {max(vals):.3f}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # ── 隶属度热力图 ──────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                        display:flex;align-items:center;justify-content:center;
                        font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;">图</div>
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">
                校准后隶属度热力图
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            from core.visualizer import plot_membership_heatmap
            cases_s = st.session_state.get("cases", [])
            ind_ns  = [ind["name"] for ind in st.session_state.get("indicators", [])]
            fig_hm, img_hm = plot_membership_heatmap(calibrated, cases_s, ind_ns)
            st.pyplot(fig_hm, use_container_width=True)
            st.session_state["img_heatmap"] = img_hm
            st.download_button(
                "⬇ 下载热力图 PNG", img_hm,
                file_name="membership_heatmap.png", mime="image/png",
                key="dl_heatmap_stage4"
            )
        except Exception as e:
            st.caption(f"热力图生成失败：{e}")

        st.markdown("<br><br>", unsafe_allow_html=True)

        # ── 导航按钮 ──────────────────────────────────────
        col_next, col_redo = st.columns([2, 2])
        with col_next:
            if st.button("→ 进入必要条件分析", key="go_to_stage5"):
                st.session_state.stage = 5
                st.rerun()
        with col_redo:
            if st.button("🔄 修改阈值重新校准", key="redo_calib"):
                st.session_state.calibration_done  = False
                st.session_state.calibrated_scores = {}
                st.rerun()


# ── 校准核心算法 ──────────────────────────────────────────

def _calibrate(raw, full_in, crossover, full_out):
    """
    直接校准法（Ragin & Fiss 2008）
    使用分段线性函数将原始值映射至模糊集隶属分数。
    """
    if raw is None:
        return None
    raw = float(raw)

    if abs(raw - crossover) < 1e-9:
        return 0.5000

    if raw >= full_in:
        return 0.9999

    if raw <= full_out:
        return 0.0001

    if raw > crossover:
        # 交叉点到完全隶属：线性从 0.5 → ~1.0
        ratio = (raw - crossover) / (full_in - crossover)
        return round(0.5 + 0.4999 * ratio, 4)
    else:
        # 完全不隶属到交叉点：线性从 ~0.0 → 0.5
        ratio = (raw - full_out) / (crossover - full_out)
        return round(0.0001 + 0.4999 * ratio, 4)


# ── csQCA 导出函数 ────────────────────────────────────────

def _render_cs_export():
    import pandas as pd
    cases     = st.session_state.get("cases", [])
    indicators = st.session_state.get("indicators", [])
    ind_names  = [ind["name"] for ind in indicators]
    edit_scores = st.session_state.get("edit_scores", {})

    if not edit_scores:
        st.warning("尚无评分数据，请返回第三阶段。")
        return

    rows = []
    for ci, case in enumerate(cases):
        row = {
            "case_id": ci + 1,
            "case_text": case["案例文本"],
            "outcome": case["结果变量"],
        }
        for name in ind_names:
            v = edit_scores.get(ci, {}).get(name)
            row[name] = int(v) if v is not None else ""
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    csv_bytes = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    col1, col2 = st.columns([2, 4])
    with col1:
        st.download_button(
            label="⬇ 下载 qca_scores.csv",
            data=csv_bytes,
            file_name="qca_scores.csv",
            mime="text/csv",
            key="cs_download"
        )
    with col2:
        if st.button("↺ 全部重置", key="cs_reset"):
            for k in ["cases","scores","reasoning","edit_scores","indicators","confirmed_cases"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state.stage = 1
            st.rerun()
