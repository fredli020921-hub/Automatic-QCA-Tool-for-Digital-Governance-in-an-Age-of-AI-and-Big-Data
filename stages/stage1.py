import streamlit as st
import pandas as pd
import io


def render_stage1():
    st.markdown('<div class="card-title">// 阶段一 · 数据上传</div>', unsafe_allow_html=True)

    # ── 说明 ──────────────────────────────────────────────
    st.markdown("""
    <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-left:3px solid #5b9bd5;
                border-radius:4px;padding:14px 18px;margin-bottom:20px;font-size:0.85rem;color:#8ba8c8;line-height:1.7;">
        <b style="color:#5b9bd5;">数据格式要求</b><br>
        请上传 <code style="color:#e8a23a;">.csv</code> 文件，或直接在下方粘贴文本。<br>
        格式：每行代表一个 Case，包含两列：<br>
        &nbsp;&nbsp;• <b>第一列</b>：案例描述文本<br>
        &nbsp;&nbsp;• <b>第二列</b>：结果变量（0 或 1）
    </div>
    """, unsafe_allow_html=True)

    # ── 输入方式选择 ──────────────────────────────────────
    input_mode = st.radio(
        "选择输入方式",
        ["📁 上传 CSV 文件", "✏️ 手动输入 / 粘贴文本"],
        horizontal=True,
        label_visibility="collapsed"
    )

    cases = []

    if input_mode == "📁 上传 CSV 文件":
        uploaded = st.file_uploader(
            "上传 CSV",
            type=["csv"],
            label_visibility="collapsed"
        )
        if uploaded:
            try:
                df = pd.read_csv(uploaded, header=None)
                if df.shape[1] < 2:
                    st.error("❌ CSV 至少需要两列：案例文本 + 结果变量")
                else:
                    df.columns = ["案例文本", "结果变量"] + [f"col_{i}" for i in range(df.shape[1] - 2)]
                    df = df[["案例文本", "结果变量"]]
                    cases = df.to_dict("records")
                    st.success(f"✅ 已读取 {len(cases)} 条记录")
            except Exception as e:
                st.error(f"❌ 文件读取失败：{e}")

    else:
        st.markdown("""
        <div style="font-size:0.78rem;color:#6b7a99;margin-bottom:6px;font-family:'IBM Plex Mono',monospace;">
            格式示例（每行：案例文本,结果变量）
        </div>
        """, unsafe_allow_html=True)

        default_example = (
            "市民张某投诉称小区附近工厂排放大量黑烟，严重影响其家人健康，要求立即处理,1\n"
            "某居委会反映辖区内多条街道存在严重扬尘问题，影响居民出行和生活质量,1\n"
            "用户匿名反映某化工园区气味刺鼻，附近居民多次出现呼吸道不适症状,0\n"
        )

        raw_text = st.text_area(
            "粘贴数据",
            value=default_example,
            height=200,
            label_visibility="collapsed",
            placeholder="案例文本,结果变量\n案例文本,结果变量\n..."
        )

        if raw_text.strip():
            lines = [l.strip() for l in raw_text.strip().split("\n") if l.strip()]
            errors = []
            for i, line in enumerate(lines):
                # 最后一个逗号分割，避免文本中有逗号
                parts = line.rsplit(",", 1)
                if len(parts) != 2:
                    errors.append(f"第 {i+1} 行格式错误：无法识别两列")
                    continue
                text, outcome = parts[0].strip(), parts[1].strip()
                if outcome not in ["0", "1"]:
                    errors.append(f"第 {i+1} 行结果变量必须是 0 或 1，当前值：'{outcome}'")
                    continue
                cases.append({"案例文本": text, "结果变量": int(outcome)})

            if errors:
                for e in errors:
                    st.warning(f"⚠️ {e}")

    # ── 数据预览 & Overview ───────────────────────────────
    if cases:
        st.markdown("---")
        st.markdown('<div class="card-title">// 数据概览</div>', unsafe_allow_html=True)

        df_preview = pd.DataFrame(cases)

        # 指标卡
        c1, c2, c3, c4 = st.columns(4)
        total = len(cases)
        outcome_1 = sum(1 for c in cases if c["结果变量"] == 1)
        outcome_0 = total - outcome_1
        avg_len = int(sum(len(c["案例文本"]) for c in cases) / total)

        c1.metric("总案例数", total)
        c2.metric("结果=1", outcome_1, f"{outcome_1/total*100:.0f}%")
        c3.metric("结果=0", outcome_0, f"{outcome_0/total*100:.0f}%")
        c4.metric("平均文本长度", f"{avg_len} 字")

        st.markdown("<br>", unsafe_allow_html=True)

        # 数据表格预览（最多显示前10行）
        st.markdown(f"""
        <div style="font-size:0.78rem;color:#6b7a99;margin-bottom:8px;font-family:'IBM Plex Mono',monospace;">
            数据预览（共 {total} 条，显示前 {min(10, total)} 条）
        </div>
        """, unsafe_allow_html=True)

        df_show = df_preview.head(10).copy()
        df_show.index = range(1, len(df_show) + 1)
        df_show["案例文本"] = df_show["案例文本"].apply(
            lambda x: x[:60] + "..." if len(x) > 60 else x
        )
        st.dataframe(df_show, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 确认按钮 ──────────────────────────────────────
        st.markdown("""
        <div style="background:#0d2a1a;border:1px solid #2a6a4a;border-radius:4px;
                    padding:12px 18px;margin-bottom:16px;font-size:0.85rem;color:#6bba8f;">
            ✓ 确认数据无误后，点击下方按钮进入第二阶段
        </div>
        """, unsafe_allow_html=True)

        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("✓ 确认，进入下一步", key="confirm_stage1"):
                st.session_state.cases = cases
                st.session_state.confirmed_cases = True
                st.session_state.stage = 2
                st.rerun()
        with col_btn2:
            st.markdown("""
            <span style="font-size:0.75rem;color:#4a5a7a;line-height:2.5;font-family:'IBM Plex Mono',monospace;">
                确认后将进入 → 阶段二：选择 QCA 类型 & 配置理论指标
            </span>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:40px;color:#3a4a6a;
                    font-family:'IBM Plex Mono',monospace;font-size:0.85rem;">
            ↑ 请上传数据或粘贴文本以开始
        </div>
        """, unsafe_allow_html=True)
