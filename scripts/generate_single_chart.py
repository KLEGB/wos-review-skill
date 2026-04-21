#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


CHART_ALIASES = {
    "yearly_bar": {"yearly_bar", "yearly", "annual", "逐年发文", "年度堆叠柱状图"},
    "collab_bar": {"collab_bar", "collaboration_bar", "独立合作柱状图", "合作柱状图"},
    "chord": {"chord", "chord_diagram", "弦图", "合作弦图"},
    "map": {"map", "world_map", "collaboration_map", "地图", "合作地图"},
    "keyword_bar": {"keyword_bar", "keywords_bar", "关键词柱状图"},
    "keyword_pie": {"keyword_pie", "keywords_pie", "关键词饼图"},
    "wordcloud": {"wordcloud", "word_cloud", "词云"},
}


def normalize_chart_key(raw_key: str) -> str:
    query = raw_key.strip().lower()
    for chart_key, aliases in CHART_ALIASES.items():
        alias_lower = {a.lower() for a in aliases}
        if query in alias_lower:
            return chart_key
    raise ValueError(
        f"Unsupported chart type: {raw_key}. Supported: {', '.join(CHART_ALIASES.keys())}"
    )


def load_settings(settings_path: Path) -> dict:
    with settings_path.open("r", encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["_fonts"] = cfg["fonts"]
    cfg["_colors"] = cfg["colors"]
    return cfg


def get_font_family(cfg: dict, lang: str) -> str:
    return cfg["fonts"].get(lang, "DejaVu Sans")


def main():
    parser = argparse.ArgumentParser(description="Generate one WOS chart by type and language.")
    parser.add_argument("--chart", required=True, help="Chart key, Chinese/English aliases supported.")
    parser.add_argument("--lang", default="cn", choices=["cn", "en"], help="Output language.")
    parser.add_argument(
        "--citations-dir",
        default=None,
        help="Optional citations directory. Default: skill bundled core citations directory.",
    )
    parser.add_argument(
        "--outputs-dir",
        default=None,
        help="Optional outputs directory. Default: skill bundled core outputs directory.",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    skill_root = script_path.parents[1]
    core_root = skill_root / "assets" / "wos-review-core"
    settings_path = core_root / "settings.json"

    if not settings_path.exists():
        raise FileNotFoundError(f"Missing bundled settings: {settings_path}")

    os.chdir(core_root)
    sys.path.insert(0, str(core_root))

    chart_key = normalize_chart_key(args.chart)
    cfg = load_settings(settings_path)
    cfg["language"] = args.lang

    citations_dir = Path(args.citations_dir) if args.citations_dir else (core_root / "citations")
    outputs_dir = Path(args.outputs_dir) if args.outputs_dir else (core_root / "outputs")
    cfg["paths"]["citations_dir"] = str(citations_dir)
    cfg["paths"]["outputs_dir"] = str(outputs_dir)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    font_family = get_font_family(cfg, args.lang)

    from modules.data_processing import (
        build_country_stats,
        extract_keywords,
        load_and_merge_excel,
        save_intermediate_csvs,
    )

    merged_df = load_and_merge_excel(str(citations_dir))
    country_independent, country_collab_count, collab_pairs, yearly_country = build_country_stats(merged_df)
    pub_csv, collab_csv, yearly_csv = save_intermediate_csvs(
        country_independent,
        country_collab_count,
        collab_pairs,
        yearly_country,
        output_dir=str(outputs_dir),
        top_n_yearly=cfg["charts"]["yearly_bar"].get("top_n_countries", 8),
    )
    keywords = extract_keywords(str(citations_dir))

    if chart_key == "yearly_bar":
        from modules.plot_yearly_bar import plot_yearly_bar

        out = outputs_dir / cfg["charts"]["yearly_bar"]["output_filename"]
        plot_yearly_bar(yearly_csv, str(out), cfg, args.lang, font_family)
    elif chart_key == "collab_bar":
        from modules.plot_collab_bar import plot_collab_bar

        out = outputs_dir / cfg["charts"]["collab_bar"]["output_filename"]
        plot_collab_bar(pub_csv, str(out), cfg, args.lang, font_family)
    elif chart_key == "chord":
        from modules.plot_chord import plot_chord

        out = outputs_dir / cfg["charts"]["chord"]["output_filename"]
        plot_chord(collab_csv, str(out), cfg, args.lang, font_family)
    elif chart_key == "map":
        from modules.plot_map import plot_map

        out = outputs_dir / cfg["charts"]["map"]["output_filename"]
        plot_map(pub_csv, collab_csv, str(out), cfg, args.lang, font_family)
    elif chart_key == "keyword_bar":
        if not keywords:
            raise RuntimeError("No keywords found. Check Author Keywords / Keywords Plus.")
        from modules.plot_keywords import plot_keyword_bar

        out = outputs_dir / cfg["charts"]["keyword_bar"]["output_filename"]
        plot_keyword_bar(keywords, str(out), cfg, args.lang, font_family)
    elif chart_key == "keyword_pie":
        if not keywords:
            raise RuntimeError("No keywords found. Check Author Keywords / Keywords Plus.")
        from modules.plot_keywords import plot_keyword_pie

        out = outputs_dir / cfg["charts"]["keyword_pie"]["output_filename"]
        plot_keyword_pie(keywords, str(out), cfg, args.lang, font_family)
    elif chart_key == "wordcloud":
        if not keywords:
            raise RuntimeError("No keywords found. Check Author Keywords / Keywords Plus.")
        from modules.plot_wordcloud import plot_wordcloud

        out = outputs_dir / cfg["charts"]["wordcloud"]["output_filename"]
        plot_wordcloud(keywords, str(out), cfg, args.lang, font_family)

    print(f"[OK] Generated chart: {chart_key} (lang={args.lang})")
    print(f"[OK] outputs_dir: {outputs_dir}")


if __name__ == "__main__":
    main()
