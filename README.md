# Drug-Gene Relationship Minimal Demo

This project is a minimal reproduction of the paper workflow:

1. Search PubMed with a gene name and a drug name.
2. Fetch the top article abstracts.
3. Send the evidence to a Zhipu model.
4. Return a structured relationship judgment.

## Files

- `main.py`: program entry point
- `pubmed_client.py`: PubMed E-utilities search and fetch
- `zhipu_client.py`: Zhipu chat completions API client
- `.env.example`: environment variable template

## Setup

1. Create a virtual environment if you want:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example` and fill in your real keys:

```env
ZHIPU_API_KEY=your_full_zhipu_api_key
NCBI_API_KEY=your_ncbi_api_key
NCBI_EMAIL=your_email@example.com
NCBI_TOOL=drug_gene_relationship_demo
```

`NCBI_API_KEY` is optional for low-rate testing, but recommended.

## Run

```powershell
py main.py --gene EGFR --drug gefitinib
```

Optional arguments:

- `--cancer "lung cancer"`
- `--max-articles 5`
- `--model glm-4.7-flash`

## Output

The program prints JSON with fields like:

- `summary`
- `inference`
- `explanation`
- `evidence_pmids`
- `retrieved_pmids`
