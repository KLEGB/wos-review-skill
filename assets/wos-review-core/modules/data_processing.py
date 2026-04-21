"""
modules/data_processing.py
合并 citations 目录下所有 WOS 导出 Excel，提取国家信息，生成三个中间 CSV：
  - 国家发文量.csv
  - 国际合作.csv
  - 逐年发文量.csv
"""

import os
import re
import pandas as pd
from collections import defaultdict
from itertools import combinations


# ── 国家名标准化映射（与 map_cite.py 保持一致）────────────────────────────
STANDARD_MAP = {
    "PEOPLES R CHINA": "China",
    "PR CHINA": "China",
    "CHINA": "China",
    "USA": "USA",
    "U.S.A.": "USA",
    "UNITED STATES": "USA",
    "ENGLAND": "UK",
    "SCOTLAND": "UK",
    "WALES": "UK",
    "NORTH IRELAND": "UK",
    "UNITED KINGDOM": "UK",
    "REPU OF KOREA": "South Korea",
    "SOUTH KOREA": "South Korea",
    "KOREA": "South Korea",
    "RUSSIAN FEDERATION": "Russia",
    "RUSSIA": "Russia",
    "VIETNAM": "Vietnam",
    "VIET NAM": "Vietnam",
    "TURKIYE": "Turkiye",
    "TURKEY": "Turkiye",
    "TAIWAN": "China",
    "TAIF": "Saudi Arabia",
    "SAUDI ARABIA": "Saudi Arabia",
    "BOSNIA & HERCEG": "Bosnia & Herceg",
    "UNITED ARAB EMIRATES": "UAE",
    "UAE": "UAE",
    "IRAN": "Iran",
    "ISLAMIC REPUBLIC OF IRAN": "Iran",
}


def _normalize_country_name(raw_name: str) -> str:
    """将地址末段的国家名标准化。"""
    upper = raw_name.upper().strip()
    # 直接匹配
    if upper in STANDARD_MAP:
        return STANDARD_MAP[upper]
    # 去除非字母字符后再匹配
    cleaned = re.sub(r'[^A-Z\s&]', '', upper).strip()
    if cleaned in STANDARD_MAP:
        return STANDARD_MAP[cleaned]
    # 返回 Title Case 原始值
    return raw_name.strip().title()


def extract_countries_from_address(address_str: str) -> list:
    """
    从 WOS Addresses 字段中提取国家列表（每个分号分隔的地址块取最后一段）。
    返回去重后的国家列表（最多保留前两个不同国家，与原工作流一致）。
    """
    if pd.isna(address_str):
        return []
    # 去除 [Author Name] 标注
    clean_addr = re.sub(r'\[.*?\]', '', str(address_str))
    clean_addr = clean_addr.replace('\xa0', ' ')
    blocks = [b.strip() for b in clean_addr.split(';') if b.strip()]

    found = []
    seen = set()
    for block in blocks:
        parts = [p.strip() for p in block.split(',') if p.strip()]
        if not parts:
            continue
        country = _normalize_country_name(parts[-1])
        if country and country not in seen:
            seen.add(country)
            found.append(country)

    # 保留前两个不同国家（与原工作流逻辑一致）
    return found[:2]


def load_and_merge_excel(citations_dir: str) -> pd.DataFrame:
    """加载 citations 目录下所有 xls/xlsx 文件并合并，自动去重。"""
    dfs = []
    for filename in sorted(os.listdir(citations_dir)):
        if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
            continue
        filepath = os.path.join(citations_dir, filename)
        try:
            if filename.endswith('.xls'):
                df = pd.read_excel(filepath, engine='xlrd', dtype=str)
            else:
                df = pd.read_excel(filepath, engine='openpyxl', dtype=str)
            dfs.append(df)
            print(f"  已读取: {filename}  ({len(df)} 行)")
        except Exception as exc:
            print(f"  [警告] 无法读取 {filename}: {exc}")

    if not dfs:
        raise FileNotFoundError(f"在 {citations_dir} 中未找到任何 Excel 文件。")

    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"合并后总行数: {len(merged_df)}")

    # 按 UT 字段去重
    if 'UT' in merged_df.columns:
        before = len(merged_df)
        merged_df = merged_df.drop_duplicates(subset=['UT'])
        print(f"去重后行数: {len(merged_df)}（去除 {before - len(merged_df)} 条重复）")

    return merged_df


def build_country_stats(merged_df: pd.DataFrame) -> tuple:
    """
    从合并后的 DataFrame 中提取：
    - country_pub_count: dict {country: count}（总发文量）
    - country_independent: dict {country: count}（独立研究）
    - country_collab: dict {country: count}（国际合作）
    - collab_pairs: dict {(c1, c2): count}（两两合作）
    - yearly_country: dict {year: {country: count}}（逐年发文量）
    """
    country_independent = defaultdict(int)
    country_collab_count = defaultdict(int)
    collab_pairs = defaultdict(int)
    yearly_country = defaultdict(lambda: defaultdict(int))

    for _, row in merged_df.iterrows():
        countries = extract_countries_from_address(row.get('Addresses', ''))
        year_raw = row.get('Publication Year', '')
        try:
            year = int(str(year_raw).strip())
        except (ValueError, TypeError):
            year = None

        if not countries:
            continue

        unique_countries = list(dict.fromkeys(countries))  # 保序去重

        if len(unique_countries) == 1:
            country_independent[unique_countries[0]] += 1
        else:
            for country in unique_countries:
                country_collab_count[country] += 1
            for pair in combinations(sorted(unique_countries), 2):
                collab_pairs[pair] += 1

        for country in unique_countries:
            if year:
                yearly_country[year][country] += 1

    return country_independent, country_collab_count, collab_pairs, yearly_country


def save_intermediate_csvs(country_independent, country_collab_count,
                            collab_pairs, yearly_country,
                            output_dir: str, top_n_yearly: int = 8):
    """将中间统计结果保存为 CSV 文件。"""
    os.makedirs(output_dir, exist_ok=True)

    # ── 国家发文量.csv ────────────────────────────────────────────────────
    all_countries = set(country_independent.keys()) | set(country_collab_count.keys())
    rows = []
    for country in all_countries:
        ind = country_independent.get(country, 0)
        col = country_collab_count.get(country, 0)
        rows.append({'国家': country, '独立研究': ind, '国际合作研究': col})
    df_pub = pd.DataFrame(rows)
    df_pub['总计'] = df_pub['独立研究'] + df_pub['国际合作研究']
    df_pub = df_pub.sort_values('总计', ascending=False).reset_index(drop=True)
    pub_path = os.path.join(output_dir, '国家发文量.csv')
    df_pub.to_csv(pub_path, index=False, encoding='utf-8-sig')
    print(f"  已保存: {pub_path}")

    # ── 国际合作.csv ──────────────────────────────────────────────────────
    collab_rows = [{'国家一': c1, '国家二': c2, '合作文章数量': cnt}
                   for (c1, c2), cnt in collab_pairs.items()]
    df_collab = pd.DataFrame(collab_rows).sort_values('合作文章数量', ascending=False)
    collab_path = os.path.join(output_dir, '国际合作.csv')
    df_collab.to_csv(collab_path, index=False, encoding='utf-8-sig')
    print(f"  已保存: {collab_path}")

    # ── 逐年发文量.csv ────────────────────────────────────────────────────
    # 找出发文总量最高的 top_n 国家
    top_countries = df_pub.head(top_n_yearly)['国家'].tolist()

    all_years = sorted(yearly_country.keys())
    yearly_rows = []
    for year in all_years:
        row_data = {'年份': year}
        year_total_by_country = yearly_country[year]
        others = 0
        for country, cnt in year_total_by_country.items():
            if country in top_countries:
                row_data[country] = cnt
            else:
                others += cnt
        # 补全缺失国家为 0
        for country in top_countries:
            row_data.setdefault(country, 0)
        row_data['其他'] = others
        yearly_rows.append(row_data)

    col_order = ['年份'] + top_countries + ['其他']
    df_yearly = pd.DataFrame(yearly_rows)[col_order]
    yearly_path = os.path.join(output_dir, '逐年发文量.csv')
    df_yearly.to_csv(yearly_path, index=False, encoding='utf-8-sig')
    print(f"  已保存: {yearly_path}")

    return pub_path, collab_path, yearly_path


def extract_keywords(citations_dir: str) -> list:
    """从 citations 目录中提取所有关键词（Author Keywords + Keywords Plus）。"""
    all_keywords = []
    for filename in sorted(os.listdir(citations_dir)):
        if not (filename.endswith('.xls') or filename.endswith('.xlsx')):
            continue
        filepath = os.path.join(citations_dir, filename)
        try:
            if filename.endswith('.xls'):
                df = pd.read_excel(filepath, engine='xlrd', dtype=str)
            else:
                df = pd.read_excel(filepath, engine='openpyxl', dtype=str)
        except Exception as exc:
            print(f"  [警告] 关键词提取跳过 {filename}: {exc}")
            continue
        for col in ['Author Keywords', 'Keywords Plus']:
            if col in df.columns:
                for kws in df[col].dropna().astype(str):
                    all_keywords.extend(
                        [kw.strip().upper() for kw in kws.split(';') if kw.strip()]
                    )
    return all_keywords
