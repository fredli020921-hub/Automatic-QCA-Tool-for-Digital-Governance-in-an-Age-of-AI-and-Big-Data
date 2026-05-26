"""
可视化模块
- 得分分布图（阶段三）
- 隶属度热力图（阶段四）
- 一致性-覆盖度散点图（阶段六）
"""
import io
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── 中文字体设置（Mac / Linux 通用）────────────────────────
matplotlib.rcParams['font.family'] = ['Arial Unicode MS',
                                       'Heiti TC', 'Heiti SC',
                                       'STHeiti', 'AppleGothic',
                                       'DejaVu Sans', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 全局配色（与工具深色主题一致）──────────────────────────
BG       = "#0f1117"
PANEL    = "#141824"
BORDER   = "#2a3a5c"
BLUE     = "#5b9bd5"
GREEN    = "#3dba6f"
ORANGE   = "#e8a23a"
RED      = "#c06060"
TEXT     = "#c8d8e8"
SUBTEXT  = "#6b7a99"


def _fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=BG, edgecolor="none")
    buf.seek(0)
    plt.close(fig)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════
# 图一：得分分布图
# ════════════════════════════════════════════════════════════

def plot_score_distribution(edit_scores, ind_names, n_cases):
    """
    小提琴图 + 散点叠加，展示每个指标的 AI 原始得分分布。
    """
    n = len(ind_names)
    data = []
    for name in ind_names:
        vals = [float(edit_scores.get(ci, {}).get(name, 0.5))
                for ci in range(n_cases)]
        data.append(vals)

    fig, ax = plt.subplots(figsize=(max(6, n * 1.6), 5), facecolor=BG)
    ax.set_facecolor(PANEL)

    # 小提琴图
    parts = ax.violinplot(data, positions=range(n), showmedians=True,
                          showextrema=True)
    for pc in parts['bodies']:
        pc.set_facecolor(BLUE)
        pc.set_alpha(0.35)
        pc.set_edgecolor(BLUE)
    for part in ['cmedians', 'cmins', 'cmaxes', 'cbars']:
        parts[part].set_color(BLUE)
        parts[part].set_linewidth(1.2)

    # 散点叠加（jitter）
    for i, vals in enumerate(data):
        jitter = np.random.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(np.full(len(vals), i) + jitter, vals,
                   color=ORANGE, alpha=0.75, s=22, zorder=3)

    ax.set_xticks(range(n))
    ax.set_xticklabels(
        [nm[:10] + "…" if len(nm) > 10 else nm for nm in ind_names],
        color=TEXT, fontsize=9
    )
    ax.set_ylabel("AI 原始得分", color=TEXT, fontsize=10)
    ax.set_ylim(-0.05, 1.05)
    ax.axhline(0.5, color=SUBTEXT, linewidth=0.8, linestyle="--", alpha=0.6)
    ax.tick_params(colors=SUBTEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    ax.set_title("各指标 AI 评分分布", color=TEXT, fontsize=12, pad=12)

    legend = [
        mpatches.Patch(color=BLUE, alpha=0.5, label="分布区间"),
        plt.scatter([], [], color=ORANGE, s=22, label="单个案例"),
    ]
    ax.legend(handles=legend, facecolor=PANEL, edgecolor=BORDER,
              labelcolor=TEXT, fontsize=8, loc="upper right")

    fig.tight_layout()
    return fig, _fig_to_bytes(fig)


# ════════════════════════════════════════════════════════════
# 图二：隶属度热力图
# ════════════════════════════════════════════════════════════

def plot_membership_heatmap(calibrated_scores, cases, ind_names):
    """
    行 = 案例，列 = 条件 + 结果变量，颜色 = 校准后隶属分数。
    """
    import matplotlib.colors as mcolors

    n_cases = len(cases)
    n_conds = len(ind_names)
    cols    = ind_names + ["结果变量"]

    matrix = np.zeros((n_cases, len(cols)))
    for i in range(n_cases):
        for j, name in enumerate(ind_names):
            matrix[i, j] = float(calibrated_scores.get(i, {}).get(name, 0.0))
        matrix[i, n_conds] = float(cases[i]["结果变量"])

    fig_h = max(4, n_cases * 0.42 + 1.5)
    fig_w = max(6, len(cols) * 1.1 + 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=BG)
    ax.set_facecolor(PANEL)

    # 自定义颜色：深蓝→浅蓝→绿
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "qca", ["#0d1a2a", "#1a3a5c", BLUE, GREEN], N=256
    )

    im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    # 格子内显示数值
    for i in range(n_cases):
        for j in range(len(cols)):
            val = matrix[i, j]
            text_color = "white" if val < 0.65 else "#0a1020"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7.5, color=text_color)

    # 轴标签
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(
        [c[:9] + "…" if len(c) > 9 else c for c in cols],
        color=TEXT, fontsize=8.5, rotation=30, ha="right"
    )
    ax.set_yticks(range(n_cases))
    ax.set_yticklabels([f"Case {i+1}" for i in range(n_cases)],
                       color=TEXT, fontsize=8.5)
    ax.tick_params(colors=SUBTEXT, length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    # 结果变量列分隔线
    ax.axvline(n_conds - 0.5, color=ORANGE, linewidth=1.5, linestyle="--", alpha=0.8)

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors=SUBTEXT, labelsize=8)
    cbar.set_label("隶属分数", color=TEXT, fontsize=9)
    cbar.outline.set_edgecolor(BORDER)

    ax.set_title("校准后模糊集隶属度热力图", color=TEXT, fontsize=12, pad=12)
    fig.tight_layout()
    return fig, _fig_to_bytes(fig)


# ════════════════════════════════════════════════════════════
# 图三：一致性-覆盖度散点图
# ════════════════════════════════════════════════════════════

def plot_consistency_coverage(path_metrics_list, sol_consist, sol_cov,
                               consist_threshold=0.80):
    """
    横轴 = 覆盖度，纵轴 = 一致性，每点 = 一条路径。
    标注路径编号，画出一致性阈值线和解的汇总点。
    """
    fig, ax = plt.subplots(figsize=(6.5, 5.5), facecolor=BG)
    ax.set_facecolor(PANEL)

    # 一致性阈值线
    ax.axhline(consist_threshold, color=RED, linewidth=1.0,
               linestyle="--", alpha=0.7,
               label=f"一致性阈值 = {consist_threshold}")

    # 各路径散点
    for k, m in enumerate(path_metrics_list):
        x = m["raw_coverage"]
        y = m["consistency"]
        ax.scatter(x, y, s=90, color=BLUE, zorder=5, edgecolors="white", linewidths=0.5)
        ax.annotate(
            f" 路径 {k+1}",
            (x, y), fontsize=8.5, color=TEXT,
            xytext=(5, 3), textcoords="offset points"
        )

    # 解的汇总点
    ax.scatter(sol_cov, sol_consist, s=130, color=ORANGE, zorder=6,
               marker="D", edgecolors="white", linewidths=0.6, label="解（汇总）")

    ax.set_xlabel("覆盖度（Coverage）", color=TEXT, fontsize=10)
    ax.set_ylabel("一致性（Consistency）", color=TEXT, fontsize=10)
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(max(0, consist_threshold - 0.15), 1.05)
    ax.tick_params(colors=SUBTEXT)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    ax.set_title("组态路径一致性-覆盖度散点图", color=TEXT, fontsize=12, pad=12)
    ax.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=TEXT, fontsize=8)

    fig.tight_layout()
    return fig, _fig_to_bytes(fig)
