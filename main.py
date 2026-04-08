from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from dotenv import load_dotenv

from pubmed_client import PubMedClient
from zhipu_client import ZhipuClient


DEFAULT_GENE = "EGFR"
DEFAULT_DRUG = "gefitinib"
MAX_ABSTRACT_CHARS = 600


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Infer a cancer drug-gene relationship using PubMed and Zhipu AI."
    )
    parser.add_argument("--gene", help="Gene symbol, for example EGFR")
    parser.add_argument("--drug", help="Drug name, for example gefitinib")
    parser.add_argument(
        "--cancer",
        default="cancer",
        help="Cancer context for PubMed search, default: cancer",
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=2,
        help="Number of PubMed articles to retrieve, default: 2",
    )
    parser.add_argument(
        "--model",
        default="glm-4.7-flash",
        help="Zhipu model name, default: glm-4.7-flash",
    )
    return parser.parse_args()


def choose_value(value: str | None, default: str) -> str:
    return value.strip() if value and value.strip() else default


def build_query(gene: str, drug: str, cancer: str) -> str:
    return f"({gene}) AND ({drug}) AND ({cancer})"


def shorten_text(text: str, max_chars: int = MAX_ABSTRACT_CHARS) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def build_prompt(gene: str, drug: str, cancer: str, articles: List[dict]) -> str:
    article_blocks = []
    for index, article in enumerate(articles, start=1):
        abstract_text = shorten_text(article["abstract"] or "No abstract available.")
        article_blocks.append(
            "\n".join(
                [
                    f"Article {index}",
                    f"PMID: {article['pmid']}",
                    f"Title: {article['title']}",
                    f"Abstract: {abstract_text}",
                ]
            )
        )

    joined_articles = "\n\n".join(article_blocks)
    return f"""
You are given PubMed evidence about the relationship between a gene and a drug in {cancer}.

Gene: {gene}
Drug: {drug}
Cancer context: {cancer}

Please read the PubMed evidence and return a JSON object with these fields:
- summary: a concise literature summary in 2-4 sentences
- inference: one of [supports_targeting, suggests_association, no_clear_evidence, conflicting_evidence]
- explanation: explain why you chose that inference
- evidence_pmids: a JSON array of PMID strings that support your answer

Important rules:
- Use only the evidence provided below.
- If the evidence is weak or indirect, say so clearly.
- Do not invent PMIDs.
- Return valid JSON only.

PubMed evidence:
{joined_articles}
""".strip()


def validate_env() -> tuple[str, str | None, str | None]:
    zhipu_api_key = os.getenv("ZHIPU_API_KEY")
    ncbi_api_key = os.getenv("NCBI_API_KEY")
    ncbi_email = os.getenv("NCBI_EMAIL")
    ncbi_tool = os.getenv("NCBI_TOOL")

    if not zhipu_api_key:
        raise ValueError("Missing ZHIPU_API_KEY in environment variables or .env.")

    return zhipu_api_key, ncbi_api_key, ncbi_email or ncbi_tool


def main() -> int:
    load_dotenv()
    args = parse_args()
    gene = choose_value(args.gene, DEFAULT_GENE)
    drug = choose_value(args.drug, DEFAULT_DRUG)

    zhipu_api_key = os.getenv("ZHIPU_API_KEY")
    ncbi_api_key = os.getenv("NCBI_API_KEY")
    ncbi_email = os.getenv("NCBI_EMAIL")
    ncbi_tool = os.getenv("NCBI_TOOL", "drug_gene_relationship_demo")

    if not zhipu_api_key:
        print("Error: missing ZHIPU_API_KEY in .env or environment variables.", file=sys.stderr)
        return 1

    query = build_query(gene, drug, args.cancer)
    pubmed_client = PubMedClient(
        api_key=ncbi_api_key,
        email=ncbi_email,
        tool=ncbi_tool,
    )
    zhipu_client = ZhipuClient(api_key=zhipu_api_key, model=args.model, timeout=180)

    try:
        print(
            json.dumps(
                {
                    "status": "running",
                    "gene": gene,
                    "drug": drug,
                    "cancer": args.cancer,
                    "max_articles": args.max_articles,
                },
                ensure_ascii=False,
            )
        )
        pmids = pubmed_client.search_pubmed(query, retmax=args.max_articles)
        if not pmids:
            print(
                json.dumps(
                    {
                        "query": query,
                        "summary": "No PubMed articles were found for this query.",
                        "inference": "no_clear_evidence",
                        "explanation": "The PubMed search returned no articles, so no relationship can be inferred.",
                        "evidence_pmids": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        articles = pubmed_client.fetch_abstracts(pmids)
        prompt = build_prompt(gene, drug, args.cancer, articles)
        result = zhipu_client.infer_relationship(prompt)
        result["query"] = query
        result["retrieved_pmids"] = pmids

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
