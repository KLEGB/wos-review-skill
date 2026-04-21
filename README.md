# WOS Review Workflow Skill

A self-contained skill for review analysis based on Web of Science exports (`.xls/.xlsx`), including statistics and chart generation.

## Features

- Full workflow execution from one entry script.
- Single-chart generation by chart type and language (`cn` / `en`).
- 7 chart types:
  - `yearly_bar` (annual stacked bar)
  - `collab_bar` (independent vs collaboration bar)
  - `chord` (international collaboration chord diagram)
  - `map` (international collaboration map)
  - `keyword_bar` (keyword frequency bar)
  - `keyword_pie` (keyword distribution pie)
  - `wordcloud` (keyword word cloud)
- Built-in map shapefile bundle for stable map rendering.

## Directory

```text
wos-review/
├─ SKILL.md
├─ LICENSE
├─ README.md
├─ agents/
├─ scripts/
│  ├─ run_full_process.py
│  └─ generate_single_chart.py
└─ assets/
   └─ wos-review-core/
      ├─ full_process.py
      ├─ settings.json
      ├─ modules/
      ├─ citations/
      ├─ outputs/
      └─ 全球国家边界/
```

## Input Requirements

Put WOS Excel files in:

- `assets/wos-review-core/citations/`

Recommended/required columns:

- Recommended: `UT` (deduplication)
- Required for country/collab/year/map: `Addresses`, `Publication Year`
- Required for keyword charts: `Author Keywords` and/or `Keywords Plus`

## Usage

Run from repository root:

```bash
python skills/wos-review/scripts/run_full_process.py
```

Generate one chart:

```bash
python skills/wos-review/scripts/generate_single_chart.py --chart map --lang en
python skills/wos-review/scripts/generate_single_chart.py --chart 关键词饼图 --lang cn
```

Use external input/output folders:

```bash
python skills/wos-review/scripts/generate_single_chart.py --chart chord --lang en --citations-dir E:\data\wos --outputs-dir E:\data\wos_out
```

## Notes

- For map rendering, keep all shapefile siblings together under `assets/wos-review-core/全球国家边界/`:
  - `.shp`, `.shx`, `.dbf`, `.prj`, `.sbn`, `.sbx`
- Color tuning is controlled by `assets/wos-review-core/settings.json`.

