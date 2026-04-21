"""
modules/plot_wordcloud.py
绘制高频关键词词云图（WordCloud）
色系：使用 settings.json 中的 palette 生成自定义颜色函数，
      与其他图表保持统一风格。
参考：freq_analysis.py
"""

import os
import random
from collections import Counter
import matplotlib
import matplotlib.pyplot as plt
from wordcloud import WordCloud


def _make_color_func(palette: list):
    """
    根据 palette 列表生成 WordCloud 的 color_func，
    使词云颜色与其他图表色系一致。
    """
    def color_func(word, font_size, position, orientation,
                   random_state=None, **kwargs):
        hex_color = random.choice(palette)
        # 将 hex 转为 r,g,b
        hex_color = hex_color.lstrip('#')
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgb({r},{g},{b})"
    return color_func


def plot_wordcloud(keywords: list, output_path: str,
                   cfg: dict, lang: str, font_family: str):
    """
    绘制词云图。
    参数：
        keywords    : 关键词列表（已大写）
        output_path : 输出图片路径
        cfg         : 完整 settings dict
        lang        : "cn" 或 "en"
        font_family : 字体名称（词云图使用系统字体路径）
    """
    matplotlib.rcParams['font.family'] = font_family
    matplotlib.rcParams['axes.unicode_minus'] = False

    fonts = cfg['_fonts']
    colors_cfg = cfg['_colors']
    chart_cfg = cfg['charts']['wordcloud']
    palette = colors_cfg['palette']

    max_words = chart_cfg.get('max_words', 100)
    figsize = chart_cfg.get('figsize', [14, 7])

    if not keywords:
        print("  [跳过] 词云图：无可用关键词数据")
        return

    # 统计词频，生成 {word: freq} 字典供 WordCloud 使用
    counter = Counter(keywords)
    freq_dict = dict(counter.most_common(max_words))

    color_func = _make_color_func(palette)

    # 尝试找到系统中文字体路径（用于词云内部文字，关键词均为英文无需中文字体）
    wc_font_path = None  # 关键词均为英文，不需指定中文字体

    wc = WordCloud(
        width=int(figsize[0] * 100),
        height=int(figsize[1] * 100),
        background_color='white',
        max_words=max_words,
        color_func=color_func,
        prefer_horizontal=0.85,
        margin=4,
        collocations=False,
        font_path=wc_font_path,
    ).generate_from_frequencies(freq_dict)

    title = chart_cfg[f'title_{lang}']

    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')

    # 标题单独设置中文字体，避免乱码
    import matplotlib.font_manager as fm
    cn_font_candidates = [
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf',
        '/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc',
    ]
    title_font_path = None
    for fp in cn_font_candidates:
        if os.path.exists(fp):
            title_font_path = fp
            break
    if title_font_path:
        title_font_prop = fm.FontProperties(fname=title_font_path,
                                            size=fonts['title_size'])
        ax.set_title(title, fontproperties=title_font_prop,
                     fontweight='bold', pad=16, color='#1B2631')
    else:
        ax.set_title(title, fontsize=fonts['title_size'],
                     fontweight='bold', pad=16, color='#1B2631')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close()
    print(f"  [✓] 词云图 → {output_path}")
