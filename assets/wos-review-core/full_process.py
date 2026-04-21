#!/usr/bin/env python3
"""
full_process.py
WOS 文献分析项目主入口
────────────────────────────────────────────────────────────────────────────
使用方式：
    python full_process.py

目录结构：
    ./citations/          ← 放置 WOS 导出的 .xls / .xlsx 文件
    ./outputs/            ← 所有生成的图表和中间 CSV（自动创建）
    ./settings.json       ← 全局配置（语言、色系、字号等）
    ./modules/            ← 各绘图子模块
    ./全球国家边界/        ← （可选）SHP 地图文件，缺失时自动降级为 cartopy

输出文件：
    outputs/01_yearly_stacked_bar.png   逐年发文量堆叠柱状图
    outputs/02_collab_bar.png           前十国家独立/合作研究对比图
    outputs/03_chord_diagram.png        国际合作弦图
    outputs/04_collaboration_map.png    国际合作地图
    outputs/05_keyword_bar.png          高频关键词柱状图
    outputs/06_keyword_pie.png          高频关键词饼图
    outputs/国家发文量.csv
    outputs/国际合作.csv
    outputs/逐年发文量.csv
────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
import json

# ── 路径设置（支持从任意目录调用）────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# ── 加载配置 ──────────────────────────────────────────────────────────────
def load_settings(settings_path: str = 'settings.json') -> dict:
    with open(settings_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    # 将字体和颜色注入为快捷键，方便子模块访问
    cfg['_fonts'] = cfg['fonts']
    cfg['_colors'] = cfg['colors']
    return cfg


def get_font_family(cfg: dict, lang: str) -> str:
    return cfg['fonts'].get(lang, 'DejaVu Sans')


def main():
    print("=" * 60)
    print("  WOS 文献分析项目  —  full_process.py")
    print("=" * 60)

    # ── 1. 加载配置 ──────────────────────────────────────────────────────
    cfg = load_settings('settings.json')
    lang = cfg.get('language', 'cn')
    citations_dir = cfg['paths']['citations_dir']
    outputs_dir = cfg['paths']['outputs_dir']
    font_family = get_font_family(cfg, lang)

    os.makedirs(outputs_dir, exist_ok=True)
    print(f"\n语言模式 : {lang.upper()}")
    print(f"引用目录 : {citations_dir}")
    print(f"输出目录 : {outputs_dir}")
    print(f"字体     : {font_family}")

    # ── 2. 数据处理 ──────────────────────────────────────────────────────
    print("\n[步骤 1/3] 合并 Excel 并提取统计数据……")
    from modules.data_processing import (
        load_and_merge_excel,
        build_country_stats,
        save_intermediate_csvs,
        extract_keywords,
    )

    merged_df = load_and_merge_excel(citations_dir)
    country_independent, country_collab_count, collab_pairs, yearly_country = \
        build_country_stats(merged_df)

    top_n_yearly = cfg['charts']['yearly_bar'].get('top_n_countries', 8)
    pub_csv, collab_csv, yearly_csv = save_intermediate_csvs(
        country_independent, country_collab_count,
        collab_pairs, yearly_country,
        output_dir=outputs_dir,
        top_n_yearly=top_n_yearly,
    )

    keywords = extract_keywords(citations_dir)
    print(f"  关键词总数: {len(keywords)}")

    # ── 3. 绘图 ──────────────────────────────────────────────────────────
    print("\n[步骤 2/3] 逐图绘制……")

    # 图 01：逐年发文量堆叠柱状图
    if cfg['charts']['yearly_bar'].get('enabled', True):
        from modules.plot_yearly_bar import plot_yearly_bar
        out = os.path.join(outputs_dir,
                           cfg['charts']['yearly_bar']['output_filename'])
        plot_yearly_bar(yearly_csv, out, cfg, lang, font_family)

    # 图 02：独立/合作研究柱状图
    if cfg['charts']['collab_bar'].get('enabled', True):
        from modules.plot_collab_bar import plot_collab_bar
        out = os.path.join(outputs_dir,
                           cfg['charts']['collab_bar']['output_filename'])
        plot_collab_bar(pub_csv, out, cfg, lang, font_family)

    # 图 03：国际合作弦图
    if cfg['charts']['chord'].get('enabled', True):
        from modules.plot_chord import plot_chord
        out = os.path.join(outputs_dir,
                           cfg['charts']['chord']['output_filename'])
        plot_chord(collab_csv, out, cfg, lang, font_family)

    # 图 04：国际合作地图
    if cfg['charts']['map'].get('enabled', True):
        from modules.plot_map import plot_map
        out = os.path.join(outputs_dir,
                           cfg['charts']['map']['output_filename'])
        plot_map(pub_csv, collab_csv, out, cfg, lang, font_family)

    # 图 05：关键词柱状图
    if cfg['charts']['keyword_bar'].get('enabled', True) and keywords:
        from modules.plot_keywords import plot_keyword_bar
        out = os.path.join(outputs_dir,
                           cfg['charts']['keyword_bar']['output_filename'])
        plot_keyword_bar(keywords, out, cfg, lang, font_family)

    # 图 06：关键词饼图
    if cfg['charts']['keyword_pie'].get('enabled', True) and keywords:
        from modules.plot_keywords import plot_keyword_pie
        out = os.path.join(outputs_dir,
                           cfg['charts']['keyword_pie']['output_filename'])
        plot_keyword_pie(keywords, out, cfg, lang, font_family)

    # 图 07：关键词词云图
    if cfg['charts'].get('wordcloud', {}).get('enabled', True) and keywords:
        from modules.plot_wordcloud import plot_wordcloud
        out = os.path.join(outputs_dir,
                           cfg['charts']['wordcloud']['output_filename'])
        plot_wordcloud(keywords, out, cfg, lang, font_family)

    # ── 4. 完成报告 ──────────────────────────────────────────────────────
    print("\n[步骤 3/3] 汇总输出文件……")
    output_files = sorted(os.listdir(outputs_dir))
    for fname in output_files:
        fpath = os.path.join(outputs_dir, fname)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"  {fname:<45} {size_kb:>8.1f} KB")

    print("\n" + "=" * 60)
    print("  全部完成！所有图表已保存至 outputs/ 目录。")
    print("=" * 60)


if __name__ == '__main__':
    main()
