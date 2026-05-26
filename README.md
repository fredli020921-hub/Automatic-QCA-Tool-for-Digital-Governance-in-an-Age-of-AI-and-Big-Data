# Auto-QCA Tool

面向社会科学研究者的自动化定性比较分析工具，通过大语言模型（LLM）实现从原始文本到完整 QCA 分析结果的端到端自动化流程。支持 **fsQCA（模糊集）** 与 **csQCA（清晰集）** 两种分析路径。

---

## 完整分析流程（7个阶段）

| 阶段 | 功能 |
|------|------|
| **① 数据上传** | 上传 CSV 或手动粘贴文本数据，预览数据概览 |
| **② 模型配置** | 选择 QCA 类型，配置理论指标（名称 / 理论说明 / 高中低评价标准），输入 API Key |
| **③ AI评分 & 确认** | 大模型逐案例自动评分，展示评分理由，支持人工核查与修改，生成得分分布图 |
| **④ 校准**（fsQCA） | 直接校准法，设置三个阈值将原始得分转为模糊集隶属分数，生成隶属度热力图 |
| **⑤ 必要条件分析** | 逐条件计算一致性与覆盖度，标注必要条件 |
| **⑥ 组态充分性分析** | 构建真值表 → 布尔最小化（复杂解 / 简约解）→ AI 路径命名，生成一致性-覆盖度散点图 |
| **⑦ 汇总导出** | 汇总所有结果，逐项下载 CSV 与图表 PNG |

---

## 快速开始

### 1. 克隆或下载项目

```bash
git clone https://github.com/fredli020921-hub/Automatic-QCA-Tool-for-Digital-Governance-in-an-Age-of-AI-and-Big-Data.git
cd Automatic-QCA-Tool-for-Digital-Governance-in-an-Age-of-AI-and-Big-Data
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动工具

```bash
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`

> **PyCharm 用户**：在底部 Terminal 面板中执行以上命令即可。

---

## 数据格式要求

CSV 文件（两列，无需表头）：

```
案例文本内容,结果变量
市民投诉工厂排放黑烟严重影响家人健康，要求立即处理,1
居委会反映辖区街道扬尘问题影响居民出行,0
```

- **第一列**：案例文本（中英文均可）
- **第二列**：结果变量（仅接受 0 或 1）

---

## API 配置

工具支持所有 OpenAI 兼容接口，在阶段二填写 API Key 及 Base URL：

| 服务商 | Base URL |
|--------|----------|
| OpenAI | `https://api.openai.com/v1` |
| 硅基流动（推荐国内） | `https://api.siliconflow.cn/v1` |
| DeepSeek 官方 | `https://api.deepseek.com/v1` |

---

## 导出文件说明

| 文件名 | 内容 |
|--------|------|
| `qca_scores.csv` | AI 原始评分（含案例文本、结果变量） |
| `qca_calibrated.csv` | 校准后模糊集隶属分数 |
| `qca_necessity.csv` | 必要条件一致性与覆盖度 |
| `qca_truth_table.csv` | 真值表（含组态、案例数、一致性、覆盖度、结果） |
| `qca_complex_solution.csv` | 复杂解路径表 |
| `qca_parsimonious_solution.csv` | 简约解路径表 |
| `score_distribution.png` | 各指标得分分布图 |
| `membership_heatmap.png` | 校准后隶属度热力图 |
| `consistency_coverage.png` | 一致性-覆盖度散点图 |

---

## 项目结构

```
auto-qca/
├── app.py                      # 主入口，7阶段路由
├── requirements.txt
├── stages/
│   ├── stage1.py               # 数据上传
│   ├── stage2.py               # 模型配置（指标三列布局）
│   ├── stage3.py               # AI 评分 & 人工确认 + 得分分布图
│   ├── stage4.py               # 模糊集校准 + 热力图
│   ├── stage5.py               # 必要条件分析
│   ├── stage6.py               # 真值表 + 布尔最小化 + AI命名 + 散点图
│   └── stage7.py               # 汇总导出
└── core/
    ├── llm_scorer.py           # LLM 评分（支持评价标准注入提示词）
    ├── necessity.py            # 必要条件一致性/覆盖度计算
    ├── truth_table.py          # 真值表构建
    ├── qmc.py                  # Quine-McCluskey 布尔最小化
    └── visualizer.py           # 三张可视化图表
```

---

## 算法参考文献

- **校准方法**：Ragin, C. C., & Fiss, P. C. (2008). Net Effects Analysis versus Configurational Analysis. *Redesigning Social Inquiry: Fuzzy Sets and Beyond*, Vol.240, pp.190–212.
- **布尔最小化 & QCA 计算**：Dușa, A. (2019). *QCA with R: A Comprehensive Resource*. Springer.
- **频数阈值建议**：Schneider, C. Q., & Wagemann, C. (2012). *Set-Theoretic Methods for the Social Sciences*. Cambridge University Press.

---

## 主要依赖

```
streamlit >= 1.35.0
pandas >= 2.0.0
numpy
matplotlib
requests
openpyxl
```

---

## 注意事项

1. **API Key 安全**：Key 仅在本地 session 中使用，不会被存储或上传
2. **样本量建议**：案例数至少为条件数的 3 倍以上，以保证组态分析的可靠性
3. **交叉点案例**：校准分数恰好等于 0.50 的案例会被真值表自动排除，建议调整校准阈值避免此情况
4. **AI 命名**：组态路径命名由 AI 生成，仅供参考，需研究者结合理论背景判断
