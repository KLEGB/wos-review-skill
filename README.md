# WOS Review Workflow Skill

A self-contained skill for review analysis based on Web of Science exports (`.xls/.xlsx`), including statistics and chart generation.

## Install As A Codex Skill

Codex discovers local skills from:

- Windows: `C:\Users\<YourUser>\.codex\skills\`
- Linux/macOS: `${HOME}/.codex/skills/`

Deploy this repo folder as:

- `${CODEX_HOME:-$HOME/.codex}/skills/wos-review/`

After copying, ensure `SKILL.md` exists at:

- `.../skills/wos-review/SKILL.md`

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

## Release Artifacts

This project publishes two release formats:

- `*.zip`: Standard source archive. Unzip and place the `wos-review` folder into `${CODEX_HOME:-$HOME/.codex}/skills/`.
- `*.skill`: Skill package format. Import/install directly if your Codex environment supports `.skill` package import; otherwise treat it as a distributable artifact and use the `.zip` path.

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

## How To Talk To Agent

After the skill is installed, talk to Codex/Agent in natural language and explicitly mention the skill plus your target output.

Examples:

- `Use $wos-review-workflow to run the full pipeline with Chinese labels.`
- `Use $wos-review-workflow and generate only map in English.`
- `Use $wos-review-workflow, update color palette to blue-green, then regenerate chord and map.`
- `Use $wos-review-workflow to validate whether my citations xlsx has required columns before plotting.`

## Notes

- For map rendering, keep all shapefile siblings together under `assets/wos-review-core/全球国家边界/`:
  - `.shp`, `.shx`, `.dbf`, `.prj`, `.sbn`, `.sbx`
- Color tuning is controlled by `assets/wos-review-core/settings.json`.
