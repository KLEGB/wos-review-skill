"""
modules/plot_collab_bar.py
绘制前十国家独立研究与国际合作研究对比柱状图（竖构图 4:6）
"""

import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def plot_collab_bar(pub_csv_path: str, output_path: str,
                    cfg: dict, lang: str, font_family: str):
    """
    参数：
        pub_csv_path : 国家发文量.csv 的路径
        output_path  : 输出图片路径
        cfg          : 完整 settings dict
        lang         : "cn" 或 "en"
        font_family  : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8-whitegrid')
    matplotlib.rcParams['font.family'] = font_family

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['collab_bar']
    country_cn_map = cfg.get('country_cn_map', {})

    color_independent = colors_cfg['bar_independent_color']
    color_collab = colors_cfg['bar_collab_color']

    df = pd.read_csv(pub_csv_path)
    df['总计'] = df['独立研究'] + df['国际合作研究']
    top_n = chart_cfg.get('top_n_countries', 10)
    df = df.sort_values('总计', ascending=False).head(top_n)

    if lang == 'cn':
        df['label'] = df['国家'].map(country_cn_map).fillna(df['国家'])
    else:
        df['label'] = df['国家']

    countries = df['label'].values
    independent = df['独立研究'].values
    collaboration = df['国际合作研究'].values
    total = df['总计'].values

    figsize = chart_cfg.get('figsize', [8, 12])
    fig, ax = plt.subplots(figsize=figsize)

    x_pos = np.arange(len(countries))
    bar_width = chart_cfg.get('bar_width', 0.38)

    ax.bar(x_pos - bar_width / 2, independent, width=bar_width,
           label=chart_cfg[f'legend_independent_{lang}'],
           color=color_independent, edgecolor='white', linewidth=0.5)

    ax.bar(x_pos + bar_width / 2, collaboration, width=bar_width,
           label=chart_cfg[f'legend_collab_{lang}'],
           color=color_collab, edgecolor='white', linewidth=0.5)

    # 数值标注
    for i in range(len(countries)):
        if independent[i] > 0:
            ax.text(x_pos[i] - bar_width / 2,
                    independent[i] + max(total) * 0.008,
                    str(independent[i]),
                    ha='center', va='bottom',
                    fontsize=fonts['annotation_size'] - 1,
                    fontweight='bold', color=color_independent)
        if collaboration[i] > 0:
            ax.text(x_pos[i] + bar_width / 2,
                    collaboration[i] + max(total) * 0.008,
                    str(collaboration[i]),
                    ha='center', va='bottom',
                    fontsize=fonts['annotation_size'] - 1,
                    fontweight='bold', color=color_collab)

    title = chart_cfg[f'title_{lang}']
    ylabel = chart_cfg.get(f'ylabel_{lang}', '')
    xlabel_label = '发文量' if lang == 'cn' else 'Number of Publications'

    ax.set_title(title, fontsize=fonts['title_size'], fontweight='bold', pad=18)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(countries, rotation=40, ha='right',
                       fontsize=fonts['tick_size'])
    ax.set_ylabel(xlabel_label, fontsize=fonts['label_size'],
                  fontweight='bold', labelpad=10)
    ax.set_ylim(0, max(total) * 1.18)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.tick_params(axis='y', labelsize=fonts['tick_size'])

    ax.legend(loc='upper right', fontsize=fonts['legend_size'],
              framealpha=0.9, edgecolor='gray', fancybox=True)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 独立/合作研究柱状图 → {output_path}")
