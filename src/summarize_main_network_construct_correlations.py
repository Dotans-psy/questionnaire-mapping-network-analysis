"""Summarize main-network focal questionnaires linked to target constructs.

The script defines the main network as the largest connected component in the
Tier 1+2 cleaned edge list, then scans the full database workbook for rows
whose focal questionnaire is in that main component and whose related
questionnaire contains Self-Esteem or Authenticity. Significance is not used as
a filter, so non-significant and unclear rows are retained. The workbook also
includes Tier 1-only sheets using the focal questionnaire Tier column.
"""

from __future__ import annotations

import re
from pathlib import Path

import networkx as nx
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "database_validity_extraction.xlsx"
CLEANED_EDGES_PATH = PROJECT_ROOT / "outputs" / "tables" / "tier_1_2_cleaned_network_edges.csv"
OUTPUT_PATH = PROJECT_ROOT / "outputs" / "tables" / "main_network_self_esteem_authenticity_correlations.xlsx"

CONSTRUCTS = {
    "Self-Esteem": re.compile(r"self[-\s]?esteem", flags=re.IGNORECASE),
    "Authenticity": re.compile(r"authenticity", flags=re.IGNORECASE),
}

REQUIRED_DATABASE_COLUMNS = [
    "focal_questionnaire",
    "related_questionnaire",
    "relation_value",
    "significance",
    "Tier",
]


def clean_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def canonical_column(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def questionnaire_key(value: object) -> str:
    return clean_text(value).casefold()


def focal_count_key(questionnaire: object) -> str:
    """Collapse questionnaire subscales to a questionnaire-level acronym key."""
    text = clean_text(questionnaire)
    match = re.match(r"^\(([^)]+)\)", text)
    if not match:
        prefix_match = re.match(r"^([A-Za-z][A-Za-z0-9]*)\s*\([^)]+\)\s*:", text)
        if prefix_match:
            return prefix_match.group(1).strip()
        return text.casefold()

    acronym = re.sub(r"\s+", " ", match.group(1).strip())
    if " - " in acronym:
        return acronym.split(" - ", 1)[0].strip()

    if "-" in acronym:
        base, suffix = acronym.rsplit("-", 1)
        suffix = suffix.strip().upper()
        roman_versions = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"}
        if suffix not in roman_versions:
            return base.strip()

    return acronym


def parse_tier(value: object) -> int | None:
    text = clean_text(value)
    match = re.search(r"\d+", text)
    if not match:
        return None
    return int(match.group(0))


def load_database() -> pd.DataFrame:
    raw = pd.read_excel(DATABASE_PATH)
    canonical_to_actual = {canonical_column(column): column for column in raw.columns}

    missing = [
        column
        for column in REQUIRED_DATABASE_COLUMNS
        if canonical_column(column) not in canonical_to_actual
    ]
    if missing:
        raise ValueError(
            "Missing required database columns after normalization: "
            + ", ".join(missing)
            + ". Actual columns: "
            + ", ".join(map(str, raw.columns))
        )

    rename_map = {
        canonical_to_actual[canonical_column(column)]: column
        for column in REQUIRED_DATABASE_COLUMNS
    }
    optional_columns = ["relation_source_type", "article_reference", "notes"]
    for column in optional_columns:
        actual = canonical_to_actual.get(canonical_column(column))
        if actual:
            rename_map[actual] = column

    df = raw.rename(columns=rename_map).copy()
    df["original_row"] = df.index + 2
    df["focal_questionnaire"] = df["focal_questionnaire"].map(clean_text)
    df["related_questionnaire"] = df["related_questionnaire"].map(clean_text)
    df["significance"] = df["significance"].map(clean_text)
    df["tier_numeric"] = df["Tier"].map(parse_tier)
    df["focal_key"] = df["focal_questionnaire"].map(questionnaire_key)
    df["focal_count_key"] = df["focal_questionnaire"].map(focal_count_key)
    return df


def main_component_node_keys() -> set[str]:
    edges = pd.read_csv(CLEANED_EDGES_PATH)
    graph = nx.Graph()
    graph.add_edges_from(edges[["node_u_key", "node_v_key"]].itertuples(index=False, name=None))
    if graph.number_of_nodes() == 0:
        return set()
    return set(max(nx.connected_components(graph), key=len))


def construct_table(
    df: pd.DataFrame,
    main_nodes: set[str],
    construct: str,
    pattern: re.Pattern[str],
    tier_filter: int | None = None,
) -> pd.DataFrame:
    related_matches = df["related_questionnaire"].str.contains(pattern, na=False)
    focal_in_main = df["focal_key"].isin(main_nodes)
    mask = related_matches & focal_in_main
    if tier_filter is not None:
        mask &= df["tier_numeric"].eq(tier_filter)
    table = df.loc[mask].copy()

    columns = [
        "focal_questionnaire",
        "focal_count_key",
        "Tier",
        "related_questionnaire",
        "relation_value",
        "significance",
        "relation_source_type",
        "original_row",
    ]
    columns = [column for column in columns if column in table.columns]
    table = table[columns].rename(columns={
        "focal_questionnaire": "focal_questionnaire_correlated_with_construct",
        "focal_count_key": "focal_questionnaire_count_key",
        "Tier": "focal_tier",
        "related_questionnaire": "related_scale",
        "relation_value": "correlation_value",
    })
    table.insert(0, "construct", construct)
    return table.sort_values([
        "focal_questionnaire_count_key",
        "focal_questionnaire_correlated_with_construct",
        "related_scale",
    ]).reset_index(drop=True)


def write_construct_sheet(writer: pd.ExcelWriter, sheet_name: str, table: pd.DataFrame) -> None:
    unique_count = table["focal_questionnaire_count_key"].nunique()
    summary = pd.DataFrame([
        {"metric": "unique_focal_questionnaire_count", "value": unique_count},
        {"metric": "row_count", "value": len(table)},
        {"metric": "unique_related_scale_count", "value": table["related_scale"].nunique()},
    ])
    summary.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)
    table.to_excel(writer, sheet_name=sheet_name, index=False, startrow=len(summary) + 3)


def format_workbook(path: Path) -> None:
    workbook = load_workbook(path)
    header_fill = PatternFill("solid", fgColor="D9EAF7")
    summary_fill = PatternFill("solid", fgColor="E2F0D9")

    for sheet in workbook.worksheets:
        for cell in sheet[1]:
            cell.font = Font(bold=True)
            cell.fill = summary_fill
        table_header_row = 7
        for cell in sheet[table_header_row]:
            cell.font = Font(bold=True)
            cell.fill = header_fill
            cell.alignment = Alignment(wrap_text=True)
        for row in sheet.iter_rows():
            for cell in row:
                cell.alignment = Alignment(vertical="top", wrap_text=True)
        for column_cells in sheet.columns:
            max_length = max(len(str(cell.value or "")) for cell in column_cells)
            width = min(max(max_length + 2, 12), 60)
            sheet.column_dimensions[get_column_letter(column_cells[0].column)].width = width
        sheet.freeze_panes = "A8"

    workbook.save(path)


def main() -> None:
    df = load_database()
    main_nodes = main_component_node_keys()
    tables = {
        construct: construct_table(df, main_nodes, construct, pattern)
        for construct, pattern in CONSTRUCTS.items()
    }
    tier_1_tables = {
        construct: construct_table(df, main_nodes, construct, pattern, tier_filter=1)
        for construct, pattern in CONSTRUCTS.items()
    }
    workbook_tables = {
        "Self-Esteem": tables["Self-Esteem"],
        "Authenticity": tables["Authenticity"],
        "Tier 1 Self-Esteem": tier_1_tables["Self-Esteem"],
        "Tier 1 Authenticity": tier_1_tables["Authenticity"],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        for sheet_name, table in workbook_tables.items():
            write_construct_sheet(writer, sheet_name, table)
    format_workbook(OUTPUT_PATH)

    summary_rows = []
    for scope, scoped_tables in [
        ("Main network", tables),
        ("Main network Tier 1", tier_1_tables),
    ]:
        summary_rows.extend(
            {
                "scope": scope,
                "construct": construct,
                "unique_focal_questionnaire_count": table["focal_questionnaire_count_key"].nunique(),
                "row_count": len(table),
                "unique_related_scale_count": table["related_scale"].nunique(),
            }
            for construct, table in scoped_tables.items()
        )
    summary = pd.DataFrame(summary_rows)

    print("\nMain-network construct correlation summary")
    print(summary.to_string(index=False))
    print(f"\nSaved Excel file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
