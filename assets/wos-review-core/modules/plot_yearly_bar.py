"""
modules/plot_yearly_bar.py
绘制各国逐年发文量堆叠柱状图（竖构图 4:6）
色系统一使用 settings.json 中的 palette
"""

import os
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


def plot_yearly_bar(yearly_csv_path: str, output_path: str,
                    cfg: dict, lang: str, font_family: str):
    """
    参数：
        yearly_csv_path : 逐年发文量.csv 的路径
        output_path     : 输出图片路径
        cfg             : settings["charts"]["yearly_bar"]
        lang            : "cn" 或 "en"
        font_family     : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False
    plt.style.use('seaborn-v0_8-whitegrid')
    matplotlib.rcParams['font.family'] = font_family  # 样式后重设字体

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['yearly_bar']
    country_cn_map = cfg.get('country_cn_map', {})

    palette = colors_cfg['palette']

    df = pd.read_csv(yearly_csv_path)

    # 将列名翻译为中文（仅 cn 模式）
    if lang == 'cn':
        df.columns = [country_cn_map.get(col, col) for col in df.columns]

    year_col = '年份' if lang == 'cn' else 'Year'
    if year_col not in df.columns:
        year_col = df.columns[0]

    years = df[year_col].values
    countries = [col for col in df.columns if col != year_col]

    figsize = chart_cfg.get('figsize', [8, 12])
    fig, ax = plt.subplots(figsize=figsize)

    bottom = np.zeros(len(years))
    for i, country in enumerate(countries):
        values = df[country].values
        ax.bar(years, values, bottom=bottom, label=country,
               color=palette[i % len(palette)],
               width=chart_cfg.get('bar_width', 0.65),
               edgecolor='white', linewidth=0.3)
        bottom += values

    title = chart_cfg[f'title_{lang}']
    xlabel = chart_cfg[f'xlabel_{lang}']
    ylabel = chart_cfg[f'ylabel_{lang}']

    ax.set_title(title, fontsize=fonts['title_size'], fontweight='bold', pad=18)
    ax.set_xlabel(xlabel, fontsize=fonts['label_size'], fontweight='bold', labelpad=10)
    ax.set_ylabel(ylabel, fontsize=fonts['label_size'], fontweight='bold', labelpad=10)
    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, ha='right', fontsize=fonts['tick_size'])
    ax.set_ylim(0, max(bottom) * 1.18)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.tick_params(axis='y', labelsize=fonts['tick_size'])

    ax.legend(loc='upper left', fontsize=fonts['legend_size'],
              ncol=3, framealpha=0.9, edgecolor='gray', fancybox=True)

    for i, year in enumerate(years):
        total = int(bottom[i])
        if total > 0:
            ax.text(year, total + max(bottom) * 0.005, str(total),
                    ha='center', va='bottom',
                    fontsize=fonts['annotation_size'], fontweight='bold',
                    color='#333333')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 逐年发文量堆叠柱状图 → {output_path}")
