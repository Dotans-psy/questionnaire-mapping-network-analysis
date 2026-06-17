# Questionnaire Mapping Network Analysis

This project builds publication-ready static questionnaire validity/correlation network figures for the self-reification questionnaire mapping project.

The notebook reads `data/tier1_validity_extraction.xlsx`, cleans the extracted validity rows, and constructs a graph where nodes are questionnaires/scales and edges are significant empirical relationships.

## Core Rule

The default node universe is all questionnaires that appear in the `focal_questionnaire` column.

The current manuscript figure also includes three explicit related-only questionnaire exceptions from `related_questionnaire`:

- `(PSCQ): Past Self-Continuity Questionnaire`
- `(ES): Essentialist Beliefs about Human Kinds Scale`
- `(IPTheory - S): Implicit person theory measure - specific abilities`

Rows where `related_questionnaire` names any other outside questionnaire are excluded from the graph unless that questionnaire also appears somewhere in `focal_questionnaire`. These excluded rows are saved separately for QA.

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
- `focal_questionnaire` is in the focal questionnaire set.
- `related_questionnaire` is either in the focal questionnaire set or one of the three explicitly included related-only questionnaires.

All focal questionnaires are included as nodes, including isolated questionnaires with no eligible edges. The three explicitly included related-only questionnaires are also included as graph nodes.

## Outputs

Running the notebook writes:

- `outputs/figures/self questionnaires mapping network.png`
- `outputs/figures/self questionnaires mapping network.pdf`
- `outputs/figures/self questionnaires mapping network.svg`
- `outputs/figures/self_concept_cluster_network.png`
- `outputs/figures/self_concept_cluster_network.pdf`
- `outputs/figures/self_concept_cluster_network.svg`
- `outputs/figures/essentialism_cluster_network.png`
- `outputs/figures/essentialism_cluster_network.pdf`
- `outputs/figures/essentialism_cluster_network.svg`
- `outputs/tables/cleaned_network_edges.csv`
- `outputs/tables/network_nodes.csv`
- `outputs/tables/network_node_label_key.csv`
- `outputs/tables/excluded_rows_QA.csv`
- `outputs/tables/excluded_non_focal_related_questionnaires.csv`

The combined figure shows the self-concept cluster, the essentialism cluster, and isolated nodes. The two cluster-specific figure files are generated in addition to the combined network figure.

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
