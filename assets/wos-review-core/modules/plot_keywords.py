"""
modules/plot_keywords.py
绘制高频关键词柱状图与饼图
色系统一使用 settings.json 中的 palette（与 freq_2.py 保持一致）
"""

import os
from collections import Counter
import matplotlib
import matplotlib.pyplot as plt


def plot_keyword_bar(keywords: list, output_path: str,
                     cfg: dict, lang: str, font_family: str):
    """
    绘制高频关键词柱状图。
    参数：
        keywords    : 关键词列表（已大写）
        output_path : 输出图片路径
        cfg         : 完整 settings dict
        lang        : "cn" 或 "en"
        font_family : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8-whitegrid')
    matplotlib.rcParams['font.family'] = font_family

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['keyword_bar']
    palette = colors_cfg['palette']

    top_n = chart_cfg.get('top_n', 20)
    counter = Counter(keywords)
    most_common = counter.most_common(top_n)
    if not most_common:
        print("  [跳过] 关键词柱状图：无可用数据")
        return

    words, counts = zip(*most_common)

    figsize = chart_cfg.get('figsize', [12, 7])
    fig, ax = plt.subplots(figsize=figsize)

    bar_colors = [palette[i % len(palette)] for i in range(len(words))]
    bars = ax.bar(words, counts, color=bar_colors,
                  edgecolor='white', linewidth=0.5)

    # 数值标注
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(counts) * 0.008,
                str(count),
                ha='center', va='bottom',
                fontsize=fonts['annotation_size'],
                fontweight='bold', color='#333333')

    title = chart_cfg[f'title_{lang}']
    xlabel = chart_cfg[f'xlabel_{lang}']
    ylabel = chart_cfg[f'ylabel_{lang}']

    ax.set_title(title, fontsize=fonts['title_size'], fontweight='bold', pad=16)
    ax.set_xlabel(xlabel, fontsize=fonts['label_size'], fontweight='bold', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=fonts['label_size'], fontweight='bold', labelpad=10)
    ax.set_xticks(range(len(words)))
    ax.set_xticklabels(words, rotation=45, ha='right',
                       fontsize=fonts['tick_size'] - 1)
    ax.tick_params(axis='y', labelsize=fonts['tick_size'])
    ax.set_ylim(0, max(counts) * 1.18)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 关键词柱状图 → {output_path}")


def plot_keyword_pie(keywords: list, output_path: str,
                     cfg: dict, lang: str, font_family: str):
    """
    绘制高频关键词饼图（与 freq_2.py 风格一致）。
    参数：
        keywords    : 关键词列表（已大写）
        output_path : 输出图片路径
        cfg         : 完整 settings dict
        lang        : "cn" 或 "en"
        font_family : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['keyword_pie']
    palette = colors_cfg['palette']
    pie_edge_color = colors_cfg.get('pie_edge_color', 'white')

    top_n = chart_cfg.get('top_n', 10)
    counter = Counter(keywords)
    most_common = counter.most_common(top_n)
    if not most_common:
        print("  [跳过] 关键词饼图：无可用数据")
        return

    words, counts = zip(*most_common)
    colors = [palette[i % len(palette)] for i in range(len(words))]

    figsize = chart_cfg.get('figsize', [10, 10])
    fig, ax = plt.subplots(figsize=figsize)

    wedges, texts, autotexts = ax.pie(
        counts,
        labels=words,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        wedgeprops={'edgecolor': pie_edge_color, 'linewidth': 1.5},
        textprops={'fontsize': fonts['label_size']}
    )

    for autotext in autotexts:
        autotext.set_fontsize(fonts['label_size'] - 1)
        autotext.set_color('white')
        autotext.set_weight('bold')

    for text in texts:
        text.set_fontsize(fonts['label_size'])

    title = chart_cfg[f'title_{lang}']
    ax.set_title(title, fontsize=fonts['title_size'], fontweight='bold', pad=16)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 关键词饼图 → {output_path}")
