import streamlit as st

st.set_page_config(
    page_title="Auto QCA Tool",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── 全局样式 ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* 主背景 */
.stApp { background-color: #0f1117; color: #e8e8e8; }

/* 顶部标题栏 */
.top-bar {
    background: linear-gradient(90deg, #1a1f2e 0%, #16213e 100%);
    border-bottom: 1px solid #2a3a5c;
    padding: 16px 32px;
    margin: -1rem -1rem 2rem -1rem;
    display: flex;
    align-items: center;
    gap: 16px;
}
.top-bar h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.3rem;
    font-weight: 600;
    color: #5b9bd5;
    margin: 0;
    letter-spacing: 0.05em;
}
.top-bar .subtitle {
    font-size: 0.8rem;
    color: #6b7a99;
    font-family: 'IBM Plex Mono', monospace;
}

/* 阶段进度条 */
.stage-indicator {
    display: flex;
    gap: 0;
    margin-bottom: 2rem;
    border: 1px solid #2a3a5c;
    border-radius: 4px;
    overflow: hidden;
}
.stage-item {
    flex: 1;
    padding: 10px 16px;
    text-align: center;
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
    color: #4a5a7a;
    background: #141824;
    border-right: 1px solid #2a3a5c;
    transition: all 0.2s;
}
.stage-item:last-child { border-right: none; }
.stage-item.active {
    background: #1a2a4a;
    color: #5b9bd5;
    font-weight: 600;
}
.stage-item.done {
    background: #0d2a1a;
    color: #3dba6f;
}

/* 卡片容器 */
.card {
    background: #141824;
    border: 1px solid #2a3a5c;
    border-radius: 6px;
    padding: 24px;
    margin-bottom: 16px;
}
.card-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #5b9bd5;
    margin-bottom: 12px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* 按钮 */
.stButton > button {
    background: #1a2a4a !important;
    color: #5b9bd5 !important;
    border: 1px solid #2a3a5c !important;
    border-radius: 3px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.05em !important;
    padding: 8px 20px !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #243a6a !important;
    border-color: #5b9bd5 !important;
    color: #7ab3e8 !important;
}

/* 主确认按钮 */
.primary-btn > button {
    background: #1a3a2a !important;
    color: #3dba6f !important;
    border-color: #2a6a4a !important;
}
.primary-btn > button:hover {
    background: #1e4a34 !important;
    border-color: #3dba6f !important;
}

/* 输入框 */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: #0f1117 !important;
    border: 1px solid #2a3a5c !important;
    color: #e8e8e8 !important;
    border-radius: 3px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #5b9bd5 !important;
    box-shadow: 0 0 0 1px #5b9bd5 !important;
}

/* 数据表格 */
.stDataFrame { border: 1px solid #2a3a5c; border-radius: 4px; }

/* 单选按钮 */
.stRadio > div { gap: 16px; }
.stRadio label { color: #b0bec5 !important; font-size: 0.9rem !important; }

/* 成功/警告提示 */
.stSuccess { background: #0d2a1a !important; border-color: #3dba6f !important; }
.stWarning { background: #2a1a0a !important; border-color: #e8a23a !important; }
.stInfo { background: #0d1a2a !important; border-color: #5b9bd5 !important; }

/* 分割线 */
hr { border-color: #2a3a5c !important; }

/* selectbox */
.stSelectbox > div > div {
    background: #0f1117 !important;
    border-color: #2a3a5c !important;
    color: #e8e8e8 !important;
}

/* metric */
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    color: #5b9bd5;
}
</style>
""", unsafe_allow_html=True)

# ── 顶部标题 ──────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
    <div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1.3rem;font-weight:600;color:#5b9bd5;letter-spacing:0.05em;">
            ◈ AUTO-QCA
        </div>
        <div style="font-size:0.75rem;color:#6b7a99;font-family:'IBM Plex Mono',monospace;margin-top:2px;">
            Qualitative Comparative Analysis · Automated Scoring System
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Session State 初始化 ──────────────────────────────────
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "cases" not in st.session_state:
    st.session_state.cases = []
if "confirmed_cases" not in st.session_state:
    st.session_state.confirmed_cases = False
if "qca_type" not in st.session_state:
    st.session_state.qca_type = "fsQCA"
if "indicators" not in st.session_state:
    st.session_state.indicators = [
        {"name": "", "description": "", "criteria_high": "", "criteria_mid": "", "criteria_low": ""},
        {"name": "", "description": "", "criteria_high": "", "criteria_mid": "", "criteria_low": ""},
        {"name": "", "description": "", "criteria_high": "", "criteria_mid": "", "criteria_low": ""},
    ]
if "calibration_done" not in st.session_state:
    st.session_state.calibration_done = False
if "calibrated_scores" not in st.session_state:
    st.session_state.calibrated_scores = {}
if "edit_scores" not in st.session_state:
    st.session_state.edit_scores = {}
if "final_scores" not in st.session_state:
    st.session_state.final_scores = {}
if "anchor_full_in" not in st.session_state:
    st.session_state.anchor_full_in = 0.95
if "anchor_crossover" not in st.session_state:
    st.session_state.anchor_crossover = 0.50
if "anchor_full_out" not in st.session_state:
    st.session_state.anchor_full_out = 0.05
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "reasoning" not in st.session_state:
    st.session_state.reasoning = {}
if "scores_confirmed" not in st.session_state:
    st.session_state.scores_confirmed = False
if "necessity_done" not in st.session_state:
    st.session_state.necessity_done = False
if "necessity_threshold" not in st.session_state:
    st.session_state.necessity_threshold = 0.90
if "truth_table_done" not in st.session_state:
    st.session_state.truth_table_done = False
if "minimization_done" not in st.session_state:
    st.session_state.minimization_done = False
if "ai_names_done" not in st.session_state:
    st.session_state.ai_names_done = False
if "freq_threshold" not in st.session_state:
    st.session_state.freq_threshold = 1
if "consist_threshold" not in st.session_state:
    st.session_state.consist_threshold = 0.80
if "pri_threshold" not in st.session_state:
    st.session_state.pri_threshold = 0.75

# ── 阶段指示器 ────────────────────────────────────────────
stages = ["① 数据上传", "② 模型配置", "③ AI评分&确认", "④ 校准",
          "⑤ 必要条件", "⑥ 组态分析", "⑦ 汇总导出"]
cols_stage = st.columns(7)
for i, (col, label) in enumerate(zip(cols_stage, stages)):
    s = i + 1
    cls = "active" if s == st.session_state.stage else ("done" if s < st.session_state.stage else "")
    col.markdown(f'<div class="stage-item {cls}">{label}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── 导入各阶段页面 ────────────────────────────────────────
from stages.stage1 import render_stage1
from stages.stage2 import render_stage2
from stages.stage3 import render_stage3
from stages.stage4 import render_stage4
from stages.stage5 import render_stage5
from stages.stage6 import render_stage6
from stages.stage7 import render_stage7

if st.session_state.stage == 1:
    render_stage1()
elif st.session_state.stage == 2:
    render_stage2()
elif st.session_state.stage == 3:
    render_stage3()
elif st.session_state.stage == 4:
    render_stage4()
elif st.session_state.stage == 5:
    render_stage5()
elif st.session_state.stage == 6:
    render_stage6()
elif st.session_state.stage == 7:
    render_stage7()
