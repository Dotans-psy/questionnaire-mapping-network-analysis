# Questionnaire Mapping Network Analysis

This project builds a questionnaire validity/correlation network for the self-reification questionnaire mapping project.

The notebook reads `data/tier1_validity_extraction.xlsx`, cleans the extracted validity rows, and constructs a graph where nodes are questionnaires/scales and edges are significant empirical relationships.

## Core Rule

Only questionnaires that appear in the `focal_questionnaire` column are allowed to become graph nodes.

Rows where `related_questionnaire` names an outside questionnaire are excluded from the graph unless that questionnaire also appears somewhere in `focal_questionnaire`. These excluded rows are saved separately for QA.

## Expected Input

Place the source workbook here:

```text
data/tier1_validity_extraction.xlsx
```

The main worksheet is expected to contain these columns:

- `focal_questionnaire`
- `related_questionnaire`
- `relation_value`
- `significance`
- `relation_source_type`

The notebook normalizes minor naming differences such as capitalization. In the inspected workbook, `Significance` is mapped to `significance`.

## Filtering Rules

An edge is included only when all of the following are true:

- `significance` equals `yes`, case-insensitive.
- `relation_source_type` is one of:
  - `correlation_only`
  - `convergent_validity`
  - `regression_semipartial correlation`
- `relation_value` can be parsed as a numeric correlation-like value.
- Both `focal_questionnaire` and `related_questionnaire` are in the focal questionnaire set.

All focal questionnaires are included as nodes, including isolated questionnaires with no eligible edges.

## Outputs

Running the notebook writes:

- `outputs/figures/self_concept_network.html`
- `outputs/figures/self_concept_network.png`
- `outputs/tables/cleaned_network_edges.csv`
- `outputs/tables/network_nodes.csv`
- `outputs/tables/excluded_rows_QA.csv`
- `outputs/tables/excluded_non_focal_related_questionnaires.csv`

## How To Run

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

Open and run:

```text
notebooks/01_questionnaire_validity_network.ipynb
```

The notebook is designed to run top to bottom from either the project root or the `notebooks/` directory.

## Connect To GitHub Manually

If a private GitHub repository was not created automatically, create an empty private repository named `questionnaire_mapping_network_analysis` on GitHub, then run:

```bash
git remote add origin git@github.com:YOUR_USERNAME/questionnaire_mapping_network_analysis.git
git branch -M main
git push -u origin main
```

