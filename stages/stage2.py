import streamlit as st


def render_stage2():
    st.markdown('<div class="card-title">// 阶段二 · 模型配置</div>', unsafe_allow_html=True)

    if st.button("← 返回第一阶段", key="back_to_1"):
        st.session_state.stage = 1
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2.1 选择 QCA 类型
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;flex-shrink:0;">2.1</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">选择 QCA 分析类型</div>
    </div>
    """, unsafe_allow_html=True)

    col_qca1, col_qca2 = st.columns(2)
    with col_qca1:
        st.markdown("""
        <div style="background:#0f1117;border:1px solid #2a3a5c;border-radius:6px;padding:14px 18px;margin-bottom:8px;">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#e8e8e8;margin-bottom:6px;">fsQCA · 模糊集</div>
            <div style="font-size:0.78rem;color:#6b7a99;line-height:1.6;">
                得分 <b style="color:#e8a23a;">0.00 ~ 1.00</b>（连续值）<br>
                概念边界模糊，允许部分隶属度。<br>
                <span style="color:#5b9bd5;">→ 包含校准阶段</span>
            </div>
        </div>""", unsafe_allow_html=True)
    with col_qca2:
        st.markdown("""
        <div style="background:#0f1117;border:1px solid #2a3a5c;border-radius:6px;padding:14px 18px;margin-bottom:8px;">
            <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#e8e8e8;margin-bottom:6px;">csQCA · 清晰集</div>
            <div style="font-size:0.78rem;color:#6b7a99;line-height:1.6;">
                得分 <b style="color:#e8a23a;">0 或 1</b>（二元值）<br>
                非此即彼，要求明确归类。<br>
                <span style="color:#6b7a99;">→ 无需校准，直接导出</span>
            </div>
        </div>""", unsafe_allow_html=True)

    qca_choice = st.radio(
        "QCA 类型",
        ["fsQCA（模糊集，0~1连续值）", "csQCA（清晰集，0或1二元值）"],
        index=0 if st.session_state.qca_type == "fsQCA" else 1,
        label_visibility="collapsed"
    )
    st.session_state.qca_type = "fsQCA" if "fsQCA" in qca_choice else "csQCA"

    st.markdown(f"""
    <div style="background:#0d1a2a;border:1px solid #2a3a5c;border-radius:3px;
                padding:8px 14px;margin-top:6px;font-size:0.78rem;
                font-family:'IBM Plex Mono',monospace;color:#5b9bd5;">
        ✓ 已选择：{st.session_state.qca_type}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2.2 理论指标配置（三列布局）
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;flex-shrink:0;">2.2</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">配置理论指标</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.8rem;color:#6b7a99;margin-bottom:18px;line-height:1.8;">
        每个指标填写三列：<b style="color:#c8d8e8;">①指标名称</b>、
        <b style="color:#c8d8e8;">②理论说明</b>（文献来源、核心定义）、
        <b style="color:#c8d8e8;">③评价标准</b>（高 / 中 / 低 的具体判断依据）。<br>
        评价标准将作为提示词传递给 AI，指导文本赋值评分，填写越具体越准确。
    </div>
    """, unsafe_allow_html=True)

    # ── 列表头 ────────────────────────────────────────────
    h1, h2, h3, h_del = st.columns([1.8, 3.2, 3.8, 0.4])
    h1.markdown(
        '<div style="font-size:0.72rem;color:#4a5a7a;font-family:\'IBM Plex Mono\',monospace;'
        'padding:4px 0;border-bottom:1px solid #2a3a5c;">① 指标名称</div>',
        unsafe_allow_html=True
    )
    h2.markdown(
        '<div style="font-size:0.72rem;color:#4a5a7a;font-family:\'IBM Plex Mono\',monospace;'
        'padding:4px 0;border-bottom:1px solid #2a3a5c;">② 理论说明（来源 / 定义）</div>',
        unsafe_allow_html=True
    )
    h3.markdown(
        '<div style="font-size:0.72rem;color:#4a5a7a;font-family:\'IBM Plex Mono\',monospace;'
        'padding:4px 0;border-bottom:1px solid #2a3a5c;">③ 评价标准（高 / 中 / 低）→ 传入 AI 提示词</div>',
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── 确保旧数据兼容新字段 ──────────────────────────────
    for ind in st.session_state.indicators:
        for field in ["criteria_high", "criteria_mid", "criteria_low"]:
            if field not in ind:
                ind[field] = ""

    indicators = st.session_state.indicators
    to_delete  = None

    for i, ind in enumerate(indicators):
        col1, col2, col3, col_del = st.columns([1.8, 3.2, 3.8, 0.4])

        # ── 第一列：指标名称 ──────────────────────────────
        with col1:
            indicators[i]["name"] = st.text_input(
                f"名称{i}",
                value=ind["name"],
                key=f"ind_name_{i}",
                placeholder="例：个人利益框架",
                label_visibility="collapsed"
            )

        # ── 第二列：理论说明 ──────────────────────────────
        with col2:
            indicators[i]["description"] = st.text_area(
                f"说明{i}",
                value=ind["description"],
                key=f"ind_desc_{i}",
                height=158,
                placeholder="例：出自 Yuan & Shen (2024)，指投诉中将受害者或获益者限定为自身（而非集体），与集体利益框架相对。",
                label_visibility="collapsed"
            )

        # ── 第三列：评价标准 高/中/低 ─────────────────────
        with col3:
            # 高
            st.markdown(
                '<div style="font-size:0.7rem;color:#3dba6f;font-family:\'IBM Plex Mono\',monospace;'
                'margin-bottom:3px;letter-spacing:0.04em;">▲ 高（得分趋近 1.00）</div>',
                unsafe_allow_html=True
            )
            indicators[i]["criteria_high"] = st.text_input(
                f"高{i}",
                value=ind.get("criteria_high", ""),
                key=f"ind_high_{i}",
                placeholder="例：投诉中明确将受害者 / 获益者指向自身或家庭成员",
                label_visibility="collapsed"
            )
            # 中
            st.markdown(
                '<div style="font-size:0.7rem;color:#e8a23a;font-family:\'IBM Plex Mono\',monospace;'
                'margin-top:8px;margin-bottom:3px;letter-spacing:0.04em;">◆ 中（得分约 0.50）</div>',
                unsafe_allow_html=True
            )
            indicators[i]["criteria_mid"] = st.text_input(
                f"中{i}",
                value=ind.get("criteria_mid", ""),
                key=f"ind_mid_{i}",
                placeholder="例：投诉中无明确受害者指向，描述较为模糊",
                label_visibility="collapsed"
            )
            # 低
            st.markdown(
                '<div style="font-size:0.7rem;color:#c06060;font-family:\'IBM Plex Mono\',monospace;'
                'margin-top:8px;margin-bottom:3px;letter-spacing:0.04em;">▼ 低（得分趋近 0.00）</div>',
                unsafe_allow_html=True
            )
            indicators[i]["criteria_low"] = st.text_input(
                f"低{i}",
                value=ind.get("criteria_low", ""),
                key=f"ind_low_{i}",
                placeholder="例：投诉中明确将受害者 / 获益者指向集体或公众",
                label_visibility="collapsed"
            )

        # ── 删除按钮 ──────────────────────────────────────
        with col_del:
            if len(indicators) > 1:
                st.markdown("<div style='height:52px'></div>", unsafe_allow_html=True)
                if st.button("✕", key=f"del_ind_{i}", help="删除此行"):
                    to_delete = i

        st.markdown('<hr style="margin:10px 0;border-color:#1e2a3a;">', unsafe_allow_html=True)

    if to_delete is not None:
        st.session_state.indicators.pop(to_delete)
        st.rerun()

    # ── 添加行按钮 ────────────────────────────────────────
    col_add, col_tip = st.columns([1.2, 5])
    with col_add:
        if st.button("＋ 添加指标行", key="add_indicator"):
            st.session_state.indicators.append(
                {"name": "", "description": "",
                 "criteria_high": "", "criteria_mid": "", "criteria_low": ""}
            )
            st.rerun()
    with col_tip:
        st.markdown(
            '<span style="font-size:0.75rem;color:#3a4a6a;line-height:2.8;'
            'font-family:\'IBM Plex Mono\',monospace;">'
            '建议 3~8 个指标 · 评价标准越具体，AI 评分越准确</span>',
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # 2.3 API Key 输入
    # ════════════════════════════════════════════════════
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">
        <div style="width:24px;height:24px;background:#1a2a4a;border:1px solid #5b9bd5;border-radius:3px;
                    display:flex;align-items:center;justify-content:center;
                    font-family:'IBM Plex Mono',monospace;font-size:0.75rem;color:#5b9bd5;flex-shrink:0;">2.3</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:0.9rem;color:#c8d8e8;">输入 API Key</div>
    </div>
    """, unsafe_allow_html=True)

    col_api, col_model = st.columns([3, 2])
    with col_api:
        st.session_state.api_key = st.text_input(
            "API Key",
            value=st.session_state.api_key,
            type="password",
            placeholder="sk-...",
            label_visibility="collapsed"
        )
    with col_model:
        model_options = [
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo",
            "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1",
            "claude-sonnet-4-20250514", "自定义"
        ]
        cur = st.session_state.get("model_choice", "gpt-4o")
        idx = model_options.index(cur) if cur in model_options else 0
        model_choice = st.selectbox(
            "模型", model_options, index=idx, label_visibility="collapsed"
        )
        st.session_state.model_choice = model_choice

    if model_choice == "自定义":
        st.session_state.model_choice = st.text_input(
            "自定义模型名",
            placeholder="例：deepseek-chat",
            label_visibility="collapsed"
        )

    with st.expander("⚙️ 高级设置（API Base URL）", expanded=False):
        st.session_state.base_url = st.text_input(
            "Base URL",
            value=st.session_state.get("base_url", "https://api.openai.com/v1"),
            placeholder="https://api.openai.com/v1",
            label_visibility="collapsed"
        )
        st.markdown("""
        <div style="font-size:0.75rem;color:#4a5a7a;margin-top:4px;line-height:1.8;">
            🇨🇳 硅基流动：https://api.siliconflow.cn/v1 &nbsp;·&nbsp;
            🌐 DeepSeek 官方：https://api.deepseek.com/v1
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── 校验 & 跳转 ────────────────────────────────────────
    valid_indicators = [ind for ind in st.session_state.indicators if ind["name"].strip()]
    all_ready = bool(st.session_state.api_key.strip()) and len(valid_indicators) >= 1

    if not all_ready:
        missing = []
        if not st.session_state.api_key.strip():
            missing.append("API Key")
        if not valid_indicators:
            missing.append("至少一个理论指标名称")
        st.markdown(f"""
        <div style="background:#2a1a0a;border:1px solid #6a3a1a;border-radius:3px;
                    padding:8px 14px;font-size:0.8rem;color:#e8a23a;
                    font-family:'IBM Plex Mono',monospace;margin-bottom:12px;">
            ⚠ 尚缺：{" · ".join(missing)}
        </div>
        """, unsafe_allow_html=True)

    col_btn, col_hint = st.columns([2, 4])
    with col_btn:
        if st.button("▶ 开始 AI 评分 →", key="go_to_stage3", disabled=not all_ready):
            st.session_state.indicators = valid_indicators
            st.session_state.stage = 3
            st.rerun()
    with col_hint:
        st.markdown(
            '<span style="font-size:0.75rem;color:#4a5a7a;line-height:2.8;'
            'font-family:\'IBM Plex Mono\',monospace;">'
            '确认后将进入 → 阶段三：AI 评分 & 结果确认</span>',
            unsafe_allow_html=True
        )
