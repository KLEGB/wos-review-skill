"""
modules/plot_chord.py
绘制国家间国际合作弦图（Chord Diagram）
"""

import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
from matplotlib.patches import Wedge


def plot_chord(collab_csv_path: str, output_path: str,
               cfg: dict, lang: str, font_family: str):
    """
    参数：
        collab_csv_path : 国际合作.csv 的路径
        output_path     : 输出图片路径
        cfg             : 完整 settings dict
        lang            : "cn" 或 "en"
        font_family     : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['chord']
    country_cn_map = cfg.get('country_cn_map', {})
    palette = colors_cfg['chord_palette']

    # ── 数据准备 ──────────────────────────────────────────────────────────
    df_raw = pd.read_csv(collab_csv_path)
    min_collab = chart_cfg.get('min_collab_count', 5)
    df = df_raw[df_raw['合作文章数量'] >= min_collab].copy()

    top_n = chart_cfg.get('top_n_countries', 14)
    all_countries = pd.concat([df['国家一'], df['国家二']])
    top_countries = all_countries.value_counts().head(top_n).index.tolist()

    df = df[df['国家一'].isin(top_countries) & df['国家二'].isin(top_countries)].copy()
    df['pair'] = df.apply(
        lambda r: tuple(sorted([r['国家一'], r['国家二']])), axis=1)
    df = df.groupby('pair')['合作文章数量'].sum().reset_index()
    df[['国家一', '国家二']] = pd.DataFrame(df['pair'].tolist(), index=df.index)

    country_total = {}
    for _, row in df.iterrows():
        for c in [row['国家一'], row['国家二']]:
            country_total[c] = country_total.get(c, 0) + row['合作文章数量']
    ordered_countries = sorted(
        top_countries, key=lambda x: country_total.get(x, 0), reverse=True)

    n = len(ordered_countries)
    idx = {c: i for i, c in enumerate(ordered_countries)}
    matrix = np.zeros((n, n))
    for _, row in df.iterrows():
        i, j = idx[row['国家一']], idx[row['国家二']]
        matrix[i][j] = row['合作文章数量']
        matrix[j][i] = row['合作文章数量']

    total_flow = matrix.sum(axis=1)
    grand_total = total_flow.sum()

    # ── 弧段角度计算 ──────────────────────────────────────────────────────
    gap_deg = chart_cfg.get('gap_deg', 2.5)
    available_deg = 360.0 - gap_deg * n
    arc_sizes = (total_flow / grand_total) * available_deg

    start_angles = np.zeros(n)
    end_angles = np.zeros(n)
    current = 90.0
    for i in range(n):
        start_angles[i] = current
        end_angles[i] = current - arc_sizes[i]
        current = end_angles[i] - gap_deg

    def d2r(d): return np.deg2rad(d)

    # ── 画布 ──────────────────────────────────────────────────────────────
    figsize = chart_cfg.get('figsize', [14, 14])
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_aspect('equal')
    ax.axis('off')

    outer_r = 1.0
    arc_w = chart_cfg.get('arc_width', 0.075)
    inner_r = outer_r - arc_w

    # ── 弧段 ──────────────────────────────────────────────────────────────
    for i in range(n):
        wedge = Wedge((0, 0), outer_r,
                      end_angles[i], start_angles[i],
                      width=arc_w,
                      color=palette[i % len(palette)], zorder=3)
        ax.add_patch(wedge)

    # ── 弦 ────────────────────────────────────────────────────────────────
    max_flow = matrix.max()
    arc_offset = np.zeros(n)
    pairs = [(i, j, matrix[i][j])
             for i in range(n) for j in range(i + 1, n) if matrix[i][j] > 0]
    pairs.sort(key=lambda x: x[2])

    for i, j, flow in pairs:
        frac_i = flow / total_flow[i] * arc_sizes[i]
        frac_j = flow / total_flow[j] * arc_sizes[j]
        a1 = start_angles[i] - arc_offset[i] - frac_i / 2
        a2 = start_angles[j] - arc_offset[j] - frac_j / 2
        arc_offset[i] += frac_i
        arc_offset[j] += frac_j

        p1 = np.array([inner_r * np.cos(d2r(a1)), inner_r * np.sin(d2r(a1))])
        p2 = np.array([inner_r * np.cos(d2r(a2)), inner_r * np.sin(d2r(a2))])
        ctrl = np.array([0.0, 0.0])

        verts = [p1, ctrl, ctrl, p2]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(verts, codes)

        alpha = 0.2 + 0.6 * (flow / max_flow)
        lw = 0.6 + 6.0 * (flow / max_flow)
        color_i = palette[i % len(palette)]
        patch = mpatches.PathPatch(path, facecolor='none',
                                   edgecolor=color_i, linewidth=lw,
                                   alpha=alpha, zorder=2)
        ax.add_patch(patch)

    # ── 标签 ──────────────────────────────────────────────────────────────
    label_r = outer_r + 0.05
    text_r = outer_r + 0.22

    for i in range(n):
        mid_angle = (start_angles[i] + end_angles[i]) / 2.0
        mid_rad = d2r(mid_angle)
        lx0 = label_r * np.cos(mid_rad)
        ly0 = label_r * np.sin(mid_rad)
        tx = text_r * np.cos(mid_rad)
        ty = text_r * np.sin(mid_rad)
        color = palette[i % len(palette)]

        ax.plot([lx0, tx * 0.97], [ly0, ty * 0.97],
                color=color, lw=1.0, alpha=0.7, zorder=4)

        ha = 'left' if np.cos(mid_rad) >= 0 else 'right'
        raw_name = ordered_countries[i]
        label = country_cn_map.get(raw_name, raw_name) if lang == 'cn' else raw_name
        total_label = f"{label}\n({int(total_flow[i])})"

        ax.text(tx, ty, total_label,
                ha=ha, va='center',
                fontsize=fonts['label_size'] - 1,
                fontweight='bold',
                color=color, zorder=5, linespacing=1.3)

    # ── 标题 ──────────────────────────────────────────────────────────────
    title = chart_cfg[f'title_{lang}']
    ax.set_title(title, fontsize=fonts['title_size'],
                 fontweight='bold', pad=20, color='#1B2631')

    ax.set_xlim(-1.65, 1.65)
    ax.set_ylim(-1.65, 1.65)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 国际合作弦图 → {output_path}")
