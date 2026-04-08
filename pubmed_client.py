from __future__ import annotations

from typing import List
from xml.etree import ElementTree

import requests


EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedClient:
    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        tool: str = "drug_gene_relationship_demo",
        timeout: int = 30,
    ) -> None:
        self.api_key = api_key
        self.email = email
        self.tool = tool
        self.timeout = timeout

    def search_pubmed(self, query: str, retmax: int = 5) -> List[str]:
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "sort": "relevance",
            "retmax": retmax,
            "tool": self.tool,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email

        response = requests.get(
            f"{EUTILS_BASE_URL}/esearch.fcgi",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("esearchresult", {}).get("idlist", [])

    def fetch_abstracts(self, pmids: List[str]) -> List[dict]:
        if not pmids:
            return []

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "tool": self.tool,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.email:
            params["email"] = self.email

        response = requests.get(
            f"{EUTILS_BASE_URL}/efetch.fcgi",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()

        root = ElementTree.fromstring(response.text)
        records = []
        for article in root.findall(".//PubmedArticle"):
            pmid = _text_or_empty(article.find(".//PMID"))
            title = " ".join(article.findtext(".//ArticleTitle", default="").split())

            abstract_parts = []
            for abstract_node in article.findall(".//Abstract/AbstractText"):
                label = abstract_node.attrib.get("Label")
                text = " ".join("".join(abstract_node.itertext()).split())
                if not text:
                    continue
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)

            records.append(
                {
                    "pmid": pmid,
                    "title": title,
                    "abstract": "\n".join(abstract_parts),
                }
            )
        return records


def _text_or_empty(node: ElementTree.Element | None) -> str:
    if node is None or node.text is None:
        return ""
    return node.text.strip()

