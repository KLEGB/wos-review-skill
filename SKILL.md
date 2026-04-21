---
name: wos-review-workflow
description: Self-contained Web of Science review-analysis workflow with bundled source code, settings, plotting modules, and map shapefiles. Use when generating all charts or a single chart (Chinese/English), validating WOS Excel input columns, tuning chart colors, or troubleshooting map rendering path dependencies.
---

# WOS Review Workflow

## Source Layout (Bundled in Skill)

- Core source root: `assets/wos-review-core/`
- Included source:
  - `assets/wos-review-core/full_process.py`
  - `assets/wos-review-core/modules/`
  - `assets/wos-review-core/settings.json`
  - `assets/wos-review-core/全球国家边界/` (map shapefiles)
- Runtime folders:
  - `assets/wos-review-core/citations/`
  - `assets/wos-review-core/outputs/`

## Chart Types (7, CN/EN Compatible)

- `yearly_bar` / `annual` / `yearly` / `逐年发文` / `年度堆叠柱状图`
- `collab_bar` / `collaboration_bar` / `独立合作柱状图` / `合作柱状图`
- `chord` / `chord_diagram` / `弦图` / `合作弦图`
- `map` / `world_map` / `collaboration_map` / `地图` / `合作地图`
- `keyword_bar` / `keywords_bar` / `关键词柱状图`
- `keyword_pie` / `keywords_pie` / `关键词饼图`
- `wordcloud` / `word_cloud` / `词云`

## Input Requirements (`citations/*.xls(x)`)

- Put one or more `.xls` / `.xlsx` files in `assets/wos-review-core/citations/`, or pass `--citations-dir`.
- Recommended:
  - `UT` (used for deduplication)
- Required for country/collab/yearly/map charts:
  - `Addresses`
  - `Publication Year`
- Required for keyword charts:
  - `Author Keywords` and/or `Keywords Plus`
- `Addresses` should follow WOS style (semicolon-separated address blocks, country info at end of block).

## Run Commands

- Full pipeline (all charts):
```bash
python skills/wos-review/scripts/run_full_process.py
```

- Single chart + language:
```bash
python skills/wos-review/scripts/generate_single_chart.py --chart map --lang en
python skills/wos-review/scripts/generate_single_chart.py --chart 关键词饼图 --lang cn
```

- Single chart with external input/output folders:
```bash
python skills/wos-review/scripts/generate_single_chart.py --chart chord --lang en --citations-dir E:\data\wos --outputs-dir E:\data\wos_out
```

## Color Tuning

Edit `assets/wos-review-core/settings.json`:

- Global palette:
  - `colors.palette`
  - `colors.chord_palette`
- Collaboration bars:
  - `colors.bar_independent_color`
  - `colors.bar_collab_color`
- Map style:
  - `colors.map_cmap` or `charts.map.map_cmap`
  - `colors.collab_line_color` or `charts.map.collab_line_color`
  - `colors.grid_color`
  - `colors.equator_color`
  - `colors.land_edge_color`
  - `colors.ocean_bg_color`

## Critical Path Rule (Map Shapefiles)

Map plotting depends on:

- `assets/wos-review-core/全球国家边界/world_border2.shp`

And these sibling files must stay together in the same folder:

- `world_border2.shx`
- `world_border2.dbf`
- `world_border2.prj`
- `world_border2.sbn`
- `world_border2.sbx`

If these files are missing or moved, map drawing can fail or downgrade to cartopy fallback.

