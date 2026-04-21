"""
modules/plot_map.py
绘制国际合作地图
风格参考 map_cite.py：Blues 色阶填色 + 红色弧线合作连线 + 经纬网格
支持两种模式：
  - 有 SHP 文件（shp_file 路径有效）：使用 geopandas 精确绘制
  - 无 SHP 文件：使用 cartopy 内置 Natural Earth 数据绘制（自动降级）
"""

import os
import re
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.ticker as ticker


def _load_world_gdf(shp_file: str, country_col: str):
    """尝试加载 SHP 文件，失败则返回 None。"""
    if shp_file and os.path.exists(shp_file):
        try:
            import geopandas as gpd
            world = gpd.read_file(shp_file)
            return world, country_col
        except Exception as exc:
            print(f"  [警告] 无法加载 SHP 文件: {exc}")
    return None, None


def _build_pub_counts(pub_csv_path: str) -> dict:
    """从国家发文量.csv 构建 {country: count} 字典。"""
    df = pd.read_csv(pub_csv_path)
    df['总计'] = df['独立研究'] + df['国际合作研究']
    return dict(zip(df['国家'], df['总计']))


def _build_collab_dict(collab_csv_path: str) -> dict:
    """从国际合作.csv 构建 {(c1, c2): count} 字典。"""
    df = pd.read_csv(collab_csv_path)
    result = {}
    for _, row in df.iterrows():
        pair = tuple(sorted([row['国家一'], row['国家二']]))
        result[pair] = result.get(pair, 0) + int(row['合作文章数量'])
    return result


# ── 国家名 → 地图标准名映射（用于 cartopy/geopandas 匹配）────────────────
_COUNTRY_TO_MAP = {
    'China': 'China',
    'USA': 'United States of America',
    'UK': 'United Kingdom',
    'South Korea': 'South Korea',
    'Canada': 'Canada',
    'Australia': 'Australia',
    'Germany': 'Germany',
    'Singapore': 'Singapore',
    'Japan': 'Japan',
    'India': 'India',
    'Italy': 'Italy',
    'Spain': 'Spain',
    'France': 'France',
    'Netherlands': 'Netherlands',
    'Saudi Arabia': 'Saudi Arabia',
    'Iran': 'Iran',
    'Malaysia': 'Malaysia',
    'Belgium': 'Belgium',
    'Sweden': 'Sweden',
    'Switzerland': 'Switzerland',
    'Norway': 'Norway',
    'Denmark': 'Denmark',
    'Pakistan': 'Pakistan',
    'Egypt': 'Egypt',
    'UAE': 'United Arab Emirates',
    'Russia': 'Russia',
    'Brazil': 'Brazil',
    'Mexico': 'Mexico',
    'Turkey': 'Turkey',
    'Turkiye': 'Turkey',
    'Indonesia': 'Indonesia',
    'Taiwan': 'China',
    'New Zealand': 'New Zealand',
}


def plot_map(pub_csv_path: str, collab_csv_path: str, output_path: str,
             cfg: dict, lang: str, font_family: str):
    """
    参数：
        pub_csv_path    : 国家发文量.csv
        collab_csv_path : 国际合作.csv
        output_path     : 输出图片路径
        cfg             : 完整 settings dict
        lang            : "cn" 或 "en"
        font_family     : 字体名称
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['map']

    shp_file = chart_cfg.get('shp_file', '')
    country_col = chart_cfg.get('country_col', 'NAME_0')
    map_cmap = chart_cfg.get('map_cmap', colors_cfg.get('map_cmap', 'Blues'))
    collab_line_color = chart_cfg.get('collab_line_color',
                                      colors_cfg.get('collab_line_color', '#e63946'))
    grid_color = colors_cfg.get('grid_color', '#858585')
    equator_color = colors_cfg.get('equator_color', '#7e7e7e')
    land_edge_color = colors_cfg.get('land_edge_color', '#abb2b9')
    ocean_bg_color = colors_cfg.get('ocean_bg_color', '#ebebeb')

    pub_counts = _build_pub_counts(pub_csv_path)
    collab_dict = _build_collab_dict(collab_csv_path)

    figsize = chart_cfg.get('figsize', [16, 9])
    dpi = chart_cfg.get('dpi', 150)

    # ── 尝试 geopandas 模式 ──────────────────────────────────────────────
    world_gdf, col_name = _load_world_gdf(shp_file, country_col)

    if world_gdf is not None:
        _draw_with_geopandas(world_gdf, col_name, pub_counts, collab_dict,
                             figsize, dpi, map_cmap, collab_line_color,
                             grid_color, equator_color, land_edge_color,
                             ocean_bg_color, fonts, chart_cfg, lang,
                             output_path)
    else:
        _draw_with_cartopy(pub_counts, collab_dict,
                           figsize, dpi, map_cmap, collab_line_color,
                           grid_color, equator_color, land_edge_color,
                           ocean_bg_color, fonts, chart_cfg, lang,
                           output_path)

    print(f"  [✓] 国际合作地图 → {output_path}")


# ── geopandas 绘制 ────────────────────────────────────────────────────────
def _draw_with_geopandas(world_gdf, col_name, pub_counts, collab_dict,
                          figsize, dpi, map_cmap, collab_line_color,
                          grid_color, equator_color, land_edge_color,
                          ocean_bg_color, fonts, chart_cfg, lang, output_path):
    import geopandas as gpd

    # 映射发文量
    mapped_counts = {}
    for country, cnt in pub_counts.items():
        map_name = _COUNTRY_TO_MAP.get(country, country)
        mapped_counts[map_name] = mapped_counts.get(map_name, 0) + cnt

    world_gdf['pub_count'] = world_gdf[col_name].map(mapped_counts).fillna(0)
    max_pub = world_gdf['pub_count'].max()

    raw_ticks = [0, 1, 10, 50, 100, 200, 500, 1000, 2000, 5000]
    raw_ticks = [t for t in raw_ticks if t <= max_pub]
    if max_pub not in raw_ticks:
        raw_ticks.append(int(max_pub))
    log_ticks = [np.log1p(t) for t in raw_ticks]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # 海洋背景
    ocean_rect = patches.Rectangle((-180, -85), 360, 170,
                                    linewidth=0, facecolor=ocean_bg_color, zorder=0)
    ax.add_patch(ocean_rect)

    # 经纬网格
    for lon in range(-180, 181, 30):
        ax.axvline(lon, color=grid_color, linewidth=0.6, zorder=1)
    for lat in range(-90, 91, 30):
        ax.axhline(lat, color=grid_color, linewidth=0.6, zorder=1)
    ax.axhline(0, color=equator_color, linewidth=1.5, linestyle='--', zorder=2)

    # 国家填色
    world_gdf.plot(column=np.log1p(world_gdf['pub_count']),
                   ax=ax, cmap=map_cmap,
                   edgecolor=land_edge_color, linewidth=0.3, zorder=3)

    # 色条
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    cax = inset_axes(ax, width="80%", height="5%", loc='lower center',
                     bbox_to_anchor=(0, 0.05, 1, 1),
                     bbox_transform=ax.transAxes, borderpad=0)
    sm = plt.cm.ScalarMappable(
        cmap=map_cmap,
        norm=plt.Normalize(vmin=0, vmax=np.log1p(max_pub)))
    cb = fig.colorbar(sm, cax=cax, orientation='horizontal', ticks=log_ticks)
    cb.ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f'{int(np.expm1(x))}'))
    cb.ax.tick_params(labelsize=fonts['tick_size'] - 2, color='grey')
    label_text = '发文量' if lang == 'cn' else 'Publication Count'
    cb.set_label(label_text, fontsize=fonts['tick_size'],
                 labelpad=-80, y=1.2)

    # 合作弧线
    centroids = {row[col_name]: row['geometry'].centroid
                 for _, row in world_gdf.iterrows()
                 if row['geometry'] is not None}
    mapped_centroids = {}
    for country_raw, centroid in centroids.items():
        mapped_centroids[country_raw] = centroid

    if collab_dict:
        max_collab = max(collab_dict.values())
        for (c1, c2), weight in collab_dict.items():
            m1 = _COUNTRY_TO_MAP.get(c1, c1)
            m2 = _COUNTRY_TO_MAP.get(c2, c2)
            if m1 in mapped_centroids and m2 in mapped_centroids:
                p1 = mapped_centroids[m1]
                p2 = mapped_centroids[m2]
                lw = np.log1p(weight) * 0.6
                alpha = min(0.2 + (weight / max_collab) * 0.5, 0.7)
                arc = patches.FancyArrowPatch(
                    (p1.x, p1.y), (p2.x, p2.y),
                    connectionstyle="arc3,rad=0.2",
                    arrowstyle="-",
                    color=collab_line_color,
                    linewidth=lw, alpha=alpha, zorder=4, antialiased=True)
                ax.add_patch(arc)

    ax.set_xlim([-180, 180])
    ax.set_ylim([-85, 85])
    ax.axis('off')
    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()


# ── cartopy 降级绘制 ──────────────────────────────────────────────────────
def _draw_with_cartopy(pub_counts, collab_dict,
                        figsize, dpi, map_cmap, collab_line_color,
                        grid_color, equator_color, land_edge_color,
                        ocean_bg_color, fonts, chart_cfg, lang, output_path):
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    import cartopy.io.shapereader as shpreader
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors

    fig = plt.figure(figsize=figsize, dpi=dpi)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
    ax.set_extent([-180, 180, -85, 85], crs=ccrs.PlateCarree())

    ax.set_facecolor(ocean_bg_color)

    # 国家填色
    shpfilename = shpreader.natural_earth(
        resolution='110m', category='cultural', name='admin_0_countries')
    reader = shpreader.Reader(shpfilename)
    countries_shp = list(reader.records())

    max_pub = max(pub_counts.values()) if pub_counts else 1
    norm = mcolors.Normalize(vmin=0, vmax=np.log1p(max_pub))
    cmap_obj = cm.get_cmap(map_cmap)

    country_name_map = {}
    for rec in countries_shp:
        name = rec.attributes.get('NAME_LONG', rec.attributes.get('NAME', ''))
        country_name_map[name] = rec

    # 映射
    mapped_counts = {}
    for country, cnt in pub_counts.items():
        map_name = _COUNTRY_TO_MAP.get(country, country)
        mapped_counts[map_name] = mapped_counts.get(map_name, 0) + cnt

    for rec in countries_shp:
        name = rec.attributes.get('NAME_LONG', rec.attributes.get('NAME', ''))
        cnt = mapped_counts.get(name, 0)
        color = cmap_obj(norm(np.log1p(cnt)))
        ax.add_geometries([rec.geometry], ccrs.PlateCarree(),
                          facecolor=color, edgecolor=land_edge_color,
                          linewidth=0.3, zorder=3)

    # 经纬网格
    gl = ax.gridlines(color=grid_color, linewidth=0.6,
                      xlocs=range(-180, 181, 30),
                      ylocs=range(-90, 91, 30), zorder=1)

    # 赤道
    ax.plot([-180, 180], [0, 0], color=equator_color, linewidth=1.5,
            linestyle='--', transform=ccrs.PlateCarree(), zorder=2)

    # 合作弧线（使用国家质心）
    centroids_cartopy = {}
    for rec in countries_shp:
        name = rec.attributes.get('NAME_LONG', rec.attributes.get('NAME', ''))
        try:
            centroid = rec.geometry.centroid
            centroids_cartopy[name] = (centroid.x, centroid.y)
        except Exception:
            pass

    if collab_dict:
        max_collab = max(collab_dict.values())
        for (c1, c2), weight in collab_dict.items():
            m1 = _COUNTRY_TO_MAP.get(c1, c1)
            m2 = _COUNTRY_TO_MAP.get(c2, c2)
            if m1 in centroids_cartopy and m2 in centroids_cartopy:
                x1, y1 = centroids_cartopy[m1]
                x2, y2 = centroids_cartopy[m2]
                lw = np.log1p(weight) * 0.6
                alpha = min(0.2 + (weight / max_collab) * 0.5, 0.7)
                arc = patches.FancyArrowPatch(
                    (x1, y1), (x2, y2),
                    connectionstyle="arc3,rad=0.2",
                    arrowstyle="-",
                    color=collab_line_color,
                    linewidth=lw, alpha=alpha, zorder=4,
                    antialiased=True,
                    transform=ccrs.PlateCarree())
                ax.add_patch(arc)

    # 色条
    sm = plt.cm.ScalarMappable(cmap=map_cmap, norm=norm)
    sm.set_array([])
    raw_ticks = [0, 1, 10, 50, 100, 200, 500, 1000, 2000, 5000]
    raw_ticks = [t for t in raw_ticks if t <= max_pub]
    if max_pub not in raw_ticks:
        raw_ticks.append(int(max_pub))
    log_ticks = [np.log1p(t) for t in raw_ticks]
    cb = fig.colorbar(sm, ax=ax, orientation='horizontal',
                      fraction=0.03, pad=0.04, ticks=log_ticks)
    cb.ax.xaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, pos: f'{int(np.expm1(x))}'))
    label_text = '发文量' if lang == 'cn' else 'Publication Count'
    cb.set_label(label_text, fontsize=fonts['tick_size'])

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
