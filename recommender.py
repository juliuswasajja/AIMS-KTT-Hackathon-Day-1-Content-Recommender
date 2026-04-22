"""Tier 1 content-based recommender scaffold (TF-IDF + cosine similarity)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CATALOG_DF: pd.DataFrame | None = None
VECTORIZER: TfidfVectorizer | None = None
CATALOG_TFIDF = None
POPULARITY_BY_SKU = pd.Series(dtype=float)


def load_data(data_dir: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load required CSV files from `data_dir` and return catalog, queries, click_log."""
    base = Path(data_dir)
    paths = {
        "catalog": base / "catalog.csv",
        "queries": base / "queries.csv",
        "click_log": base / "click_log.csv",
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing required file(s): "
            + ", ".join(missing)
            + ". Expected: data/catalog.csv, data/queries.csv, data/click_log.csv"
        )

    try:
        catalog_df = pd.read_csv(paths["catalog"])
        queries_df = pd.read_csv(paths["queries"])
        click_log_df = pd.read_csv(paths["click_log"])
    except Exception as exc:
        raise ValueError(f"Failed to read CSV files from '{data_dir}': {exc}") from exc

    return catalog_df, queries_df, click_log_df


def build_text_fields(catalog_df: pd.DataFrame) -> pd.DataFrame:
    """Build a single text field from available columns used for TF-IDF search."""
    candidate_cols = ["title", "description", "category", "material", "origin_district"]
    usable_cols = [col for col in candidate_cols if col in catalog_df.columns]
    if not usable_cols:
        raise ValueError(
            "catalog.csv is missing text columns. Need at least one of: "
            "title, description, category, material, origin_district."
        )

    out = catalog_df.copy()
    out["text_combined"] = (
        out[usable_cols].fillna("").astype(str).agg(" ".join, axis=1).str.replace(r"\s+", " ", regex=True).str.strip()
    )
    return out


def fit_vectorizer(catalog_df: pd.DataFrame) -> None:
    """Fit the TF-IDF vectorizer on catalog text and cache matrix/state in memory."""
    global CATALOG_DF, VECTORIZER, CATALOG_TFIDF

    if catalog_df.empty:
        raise ValueError("catalog.csv is empty; cannot build recommender index.")
    if "text_combined" not in catalog_df.columns:
        raise ValueError("Missing 'text_combined'. Run build_text_fields(catalog_df) first.")

    CATALOG_DF = catalog_df.copy()
    VECTORIZER = TfidfVectorizer(lowercase=True, strip_accents="unicode", ngram_range=(1, 2))
    CATALOG_TFIDF = VECTORIZER.fit_transform(CATALOG_DF["text_combined"])


def _tokenize(text: str) -> set[str]:
    """Normalize text into simple lowercase tokens."""
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    return set(tokens)


def _build_popularity(click_log_df: pd.DataFrame) -> pd.Series:
    """Create a simple per-SKU popularity signal from click logs."""
    if "sku" not in click_log_df.columns:
        return pd.Series(dtype=float)

    if "clicked" in click_log_df.columns:
        clicked = pd.to_numeric(click_log_df["clicked"], errors="coerce").fillna(0.0)
    else:
        clicked = pd.Series(1.0, index=click_log_df.index)

    popularity = clicked.groupby(click_log_df["sku"].astype(str)).sum()
    if popularity.empty:
        return popularity

    max_value = float(popularity.max())
    if max_value <= 0:
        return popularity.astype(float)
    return (popularity / max_value).astype(float)


def recommend(q: str, top_k: int = 5, similarity_threshold: float = 0.2) -> pd.DataFrame:
    """Return top-k catalog items ranked by cosine similarity to query `q`."""
    if CATALOG_DF is None or VECTORIZER is None or CATALOG_TFIDF is None:
        raise RuntimeError("Recommender is not initialized. Call fit_vectorizer(catalog_df) first.")
    if not q or not q.strip():
        raise ValueError("Query is empty. Pass a query using --q.")
    if top_k < 1:
        raise ValueError("top_k must be >= 1.")

    query_vector = VECTORIZER.transform([q])
    scores = cosine_similarity(query_vector, CATALOG_TFIDF).ravel()

    ranked = CATALOG_DF.copy()
    ranked["score"] = scores
    ranked["popularity"] = ranked["sku"].astype(str).map(POPULARITY_BY_SKU).fillna(0.0)

    # Main ranking path: TF-IDF + cosine similarity on local catalog, with popularity as tie-breaker.
    ranked = ranked.sort_values(["score", "popularity"], ascending=[False, False])
    top_score = float(ranked["score"].iloc[0]) if not ranked.empty else 0.0

    if top_score >= float(similarity_threshold):
        selected = ranked.head(top_k)
    else:
        # Curated fallback path for weak semantic match:
        # 1) prefer obvious category/material keyword matches from the query
        # 2) break ties with click-log popularity
        # 3) keep cosine score as final tie-break for explainability
        query_tokens = _tokenize(q)

        def keyword_match(row: pd.Series) -> int:
            field_tokens = _tokenize(row.get("category", "")) | _tokenize(row.get("material", ""))
            return int(bool(query_tokens & field_tokens))

        ranked["keyword_match"] = ranked.apply(keyword_match, axis=1)
        selected = ranked.sort_values(
            ["keyword_match", "popularity", "score"],
            ascending=[False, False, False],
        ).head(top_k)

    return selected.reindex(columns=["sku", "title", "category", "material", "origin_district", "price_rwf", "score"])


def format_results(results_df: pd.DataFrame) -> str:
    """Format recommendation rows into a clean terminal table."""
    if results_df.empty:
        return "No items found above similarity threshold."

    display = results_df.copy()

    if "price_rwf" in display.columns:
        price = pd.to_numeric(display["price_rwf"], errors="coerce")
        display["price_rwf"] = np.where(
            price.notna(),
            price.map(lambda x: f"{int(round(x)):,}"),
            display["price_rwf"],
        )

    if "score" in display.columns:
        display["score"] = pd.to_numeric(display["score"], errors="coerce").fillna(0.0).map(lambda x: f"{x:.3f}")

    return display.fillna("").to_string(index=False)


def main() -> int:
    """CLI entry point for running Tier 1 recommendations."""
    parser = argparse.ArgumentParser(description="Tier 1 content-based recommender (TF-IDF + cosine).")
    parser.add_argument("--q", required=True, help='Example: --q "cadeau en cuir pour femme"')
    parser.add_argument("--top_k", type=int, default=5, help="Number of results to return.")
    parser.add_argument("--similarity_threshold", type=float, default=0.2, help="Minimum cosine similarity.")
    parser.add_argument("--data_dir", default="data", help="Folder containing catalog.csv, queries.csv, click_log.csv.")
    args = parser.parse_args()

    global POPULARITY_BY_SKU
    try:
        catalog_df, _, click_log_df = load_data(args.data_dir)
        catalog_df = build_text_fields(catalog_df)
        fit_vectorizer(catalog_df)
        POPULARITY_BY_SKU = _build_popularity(click_log_df)
        results = recommend(args.q, top_k=args.top_k, similarity_threshold=args.similarity_threshold)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("=" * 80)
    print("Tier 1 Content-Based Recommender")
    print(f"Query: {args.q}")
    print(f"Top K: {args.top_k} | Similarity threshold: {args.similarity_threshold}")
    print("-" * 80)
    print(format_results(results))
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
