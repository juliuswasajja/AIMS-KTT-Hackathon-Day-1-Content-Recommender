"""Generate synthetic Tier 1 data for the Made in Rwanda Content Recommender.

Outputs:
- data/catalog.csv (about 400 rows)
- data/queries.csv (about 120 rows)
- data/click_log.csv (about 5000 rows)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd


SEED = 42
BASELINE_COL = "synthetic_best_local_substitute_sku"


@dataclass(frozen=True)
class CategorySpec:
    items: List[str]
    adjectives: List[str]
    materials: List[str]
    desc_phrases: List[str]
    price_min: int
    price_max: int


def _normalize(text: str) -> str:
    """Lowercase and keep only alphanumeric tokens for simple deterministic matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _build_catalog(n_rows: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create synthetic artisan catalog rows with plausible Rwanda product metadata."""
    categories = ["apparel", "leather", "basketry", "jewellery", "home-decor"]
    category_probs = np.array([0.23, 0.30, 0.17, 0.13, 0.17])

    districts = [
        "Gasabo",
        "Kicukiro",
        "Nyarugenge",
        "Musanze",
        "Rubavu",
        "Huye",
        "Nyagatare",
        "Rwamagana",
        "Muhanga",
        "Nyanza",
        "Rusizi",
        "Karongi",
        "Gicumbi",
        "Bugesera",
        "Kayonza",
    ]

    specs: Dict[str, CategorySpec] = {
        "apparel": CategorySpec(
            items=["kitenge dress", "tailored shirt", "light jacket", "wrap skirt", "festival top"],
            adjectives=["classic", "modern", "everyday", "elegant", "artisan"],
            materials=["kitenge cotton", "organic cotton", "linen blend"],
            desc_phrases=[
                "hand-finished seams",
                "comfortable daily wear",
                "locally tailored fit",
                "bold print accents",
            ],
            price_min=9000,
            price_max=65000,
        ),
        "leather": CategorySpec(
            items=[
                "tote bag",
                "crossbody bag",
                "wallet",
                "belt",
                "sandals",
                "card holder",
                "passport case",
            ],
            adjectives=["premium", "durable", "soft", "classic", "hand-stitched"],
            materials=[
                "cow leather",
                "goat leather",
                "vegetable tanned leather",
                "full grain leather",
                "cuir artisanal",
            ],
            desc_phrases=[
                "clean handmade stitching",
                "ideal gift for women",
                "everyday city use",
                "finished by local artisans",
                "cadeau en cuir pour femme",
            ],
            price_min=12000,
            price_max=150000,
        ),
        "basketry": CategorySpec(
            items=["agaseke basket", "storage basket", "fruit basket", "wall basket", "woven tray"],
            adjectives=["woven", "lightweight", "traditional", "decorative", "functional"],
            materials=["sisal", "raffia", "banana fiber"],
            desc_phrases=[
                "handwoven by cooperatives",
                "natural texture finish",
                "good for home storage",
                "crafted in small batches",
            ],
            price_min=5000,
            price_max=45000,
        ),
        "jewellery": CategorySpec(
            items=["beaded necklace", "earrings", "bracelet", "pendant set", "anklet"],
            adjectives=["delicate", "bright", "statement", "minimal", "gift-ready"],
            materials=["brass", "silver tone metal", "glass beads", "horn"],
            desc_phrases=[
                "hand-assembled details",
                "lightweight for daily use",
                "inspired by local motifs",
                "small artisan workshop",
            ],
            price_min=6000,
            price_max=80000,
        ),
        "home-decor": CategorySpec(
            items=["table runner", "cushion cover", "wall hanging", "ceramic vase", "wood candle holder"],
            adjectives=["warm", "textured", "modern", "handmade", "minimal"],
            materials=["kitenge cotton", "wood", "ceramic", "sisal", "banana fiber"],
            desc_phrases=[
                "adds warmth to living room",
                "crafted for everyday decor",
                "designed for small spaces",
                "simple artisan finish",
            ],
            price_min=7000,
            price_max=90000,
        ),
    }

    artisan_ids = [f"ART{idx:03d}" for idx in range(1, 91)]
    skus = [f"MIR{idx:04d}" for idx in range(1, n_rows + 1)]
    sampled_categories = rng.choice(categories, size=n_rows, p=category_probs)

    rows = []
    for sku, category in zip(skus, sampled_categories):
        spec = specs[category]
        item = rng.choice(spec.items)
        adjective = rng.choice(spec.adjectives)
        material = rng.choice(spec.materials)
        district = rng.choice(districts)
        artisan = rng.choice(artisan_ids)

        title = f"{adjective.title()} {item.title()}"
        desc_piece = rng.choice(spec.desc_phrases)
        description = f"{desc_piece}. {material} piece from {district}."

        raw_price = int(rng.integers(spec.price_min, spec.price_max + 1))
        price_rwf = int(round(raw_price / 500.0) * 500)

        rows.append(
            {
                "sku": sku,
                "title": title,
                "description": description,
                "category": category,
                "material": material,
                "origin_district": district,
                "price_rwf": price_rwf,
                "artisan_id": artisan,
            }
        )

    return pd.DataFrame(rows)


def _best_match_sku(query_text: str, catalog_df: pd.DataFrame) -> str:
    """Deterministic synthetic best-local reference using simple keyword overlap."""
    query_tokens = set(_normalize(query_text).split())
    if not query_tokens:
        return str(catalog_df.sort_values(["price_rwf", "sku"]).iloc[0]["sku"])

    score_rows = []
    for row in catalog_df.itertuples(index=False):
        title_tokens = set(_normalize(str(row.title)).split())
        desc_tokens = set(_normalize(str(row.description)).split())
        category_tokens = set(_normalize(str(row.category)).split())
        material_tokens = set(_normalize(str(row.material)).split())
        district_tokens = set(_normalize(str(row.origin_district)).split())

        score = 0.0
        for token in query_tokens:
            if token in title_tokens:
                score += 3.0
            if token in desc_tokens:
                score += 2.0
            if token in category_tokens or token in material_tokens:
                score += 2.0
            if token in district_tokens:
                score += 1.0

        score_rows.append((row.sku, score, row.price_rwf))

    score_df = pd.DataFrame(score_rows, columns=["sku", "score", "price_rwf"])
    best = score_df.sort_values(["score", "price_rwf", "sku"], ascending=[False, True, True]).iloc[0]
    return str(best["sku"])


def _build_queries(catalog_df: pd.DataFrame, n_rows: int, rng: np.random.Generator) -> pd.DataFrame:
    """Create multilingual buyer-intent queries with a deterministic synthetic reference SKU."""
    seed_queries = [
        "leather bag for women",
        "cadeau en cuir pour femme",
        "sac cuir femme kigali",
        "wallet gift men",
        "belt leather rwanda",
        "sandals cuir femme",
        "home decor basket",
        "panier decoration salon",
        "agaseke gift",
        "beaded necklace women",
        "earrings cadeau",
        "kitenge dress",
        "table runner home",
        "decor mural rwanda",
        "crossbody leather",
        "cuir portefeuille",
        "gift for mom rwanda",
        "house warming gift",
        "basket set",
        "bracelet femme",
        "lether bag",
        "cadeu cuir",
        "jewelery gift",
        "baskt home",
        "feme cadeau",
        "small wallet",
        "big tote",
        "decor",
        "cuir",
        "gift women",
    ]

    en_heads = ["gift", "leather", "wallet", "bag", "belt", "home decor", "basket", "earrings", "dress"]
    en_tails = [
        "for women",
        "for men",
        "for office",
        "in kigali",
        "made in rwanda",
        "for home",
        "for mom",
    ]
    fr_heads = ["cadeau", "sac cuir", "portefeuille", "decoration maison", "bijoux", "panier"]
    fr_tails = ["pour femme", "pour homme", "kigali", "rwanda", "maison", "salon"]
    mixed_heads = ["cadeau leather", "sac gift", "panier home decor", "cuir bag", "femme wallet", "deco basket"]
    short_terms = [
        "cuire bag",
        "lether",
        "cadeu",
        "jewelery",
        "baskt",
        "sac",
        "wallet",
        "decor home",
    ]

    queries = list(seed_queries)
    while len(queries) < n_rows:
        bucket = rng.choice(["en", "fr", "mix", "short"], p=[0.35, 0.25, 0.25, 0.15])
        if bucket == "en":
            q = f"{rng.choice(en_heads)} {rng.choice(en_tails)}"
        elif bucket == "fr":
            q = f"{rng.choice(fr_heads)} {rng.choice(fr_tails)}"
        elif bucket == "mix":
            q = f"{rng.choice(mixed_heads)} {rng.choice(['for women', 'pour femme', 'kigali', 'rwanda'])}"
        else:
            q = rng.choice(short_terms)
        queries.append(q)

    queries = queries[:n_rows]
    records = []
    for idx, query_text in enumerate(queries, start=1):
        best_sku = _best_match_sku(query_text, catalog_df)
        # Story for defense:
        # - `catalog_df` is the local Made-in-Rwanda catalog only.
        # - each row in `queries.csv` is buyer search intent, including some broader/global behavior.
        # - `BASELINE_COL` is a deterministic synthetic anchor for the best local substitute SKU.
        records.append(
            {
                "query_id": f"Q{idx:04d}",
                "query_text": query_text,
                BASELINE_COL: best_sku,
            }
        )
    return pd.DataFrame(records)


def _build_click_log(
    queries_df: pd.DataFrame, catalog_df: pd.DataFrame, n_rows: int, rng: np.random.Generator
) -> pd.DataFrame:
    """Create synthetic click signals with simple position bias and baseline affinity."""
    sku_list = catalog_df["sku"].to_numpy()

    # Global popularity prior per SKU (synthetic): some products are naturally more popular.
    popularity = rng.lognormal(mean=0.0, sigma=0.6, size=len(sku_list))
    popularity = popularity / popularity.sum()
    sku_to_pop = dict(zip(sku_list, popularity))

    # Position bias: top results are more likely to receive clicks.
    ctr_by_rank = np.array([0.34, 0.26, 0.20, 0.16, 0.13, 0.10, 0.08, 0.06, 0.05, 0.04])
    rank_values = np.arange(1, 11)

    query_weights = []
    for q in queries_df["query_text"].astype(str):
        qn = _normalize(q)
        w = 1.0
        if "cuir" in qn or "leather" in qn:
            w += 0.5
        if "gift" in qn or "cadeau" in qn:
            w += 0.3
        if "femme" in qn or "women" in qn:
            w += 0.2
        query_weights.append(w)
    query_weights = np.array(query_weights, dtype=float)
    query_weights = query_weights / query_weights.sum()

    events = []
    for idx in range(1, n_rows + 1):
        q_idx = int(rng.choice(len(queries_df), p=query_weights))
        q_row = queries_df.iloc[q_idx]

        rank = int(rng.choice(rank_values))
        baseline_sku = str(q_row[BASELINE_COL])

        if rank <= 2 and rng.random() < 0.75:
            shown_sku = baseline_sku
        elif rank <= 5 and rng.random() < 0.40:
            shown_sku = baseline_sku
        else:
            shown_sku = str(rng.choice(sku_list, p=popularity))

        base_ctr = ctr_by_rank[rank - 1]
        pop_boost = 0.7 + 0.6 * sku_to_pop[shown_sku] * len(sku_list)
        click_prob = min(0.95, base_ctr * pop_boost)
        if shown_sku == baseline_sku:
            click_prob = min(0.95, click_prob * 1.35)

        clicked = int(rng.random() < click_prob)
        events.append(
            {
                "event_id": f"E{idx:05d}",
                "query_id": q_row["query_id"],
                "query_text": q_row["query_text"],
                "sku": shown_sku,
                "rank_position": rank,
                "clicked": clicked,
            }
        )

    return pd.DataFrame(events)


def main() -> None:
    """Generate all synthetic datasets and save them under ./data."""
    rng = np.random.default_rng(SEED)
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)

    catalog_df = _build_catalog(n_rows=400, rng=rng)
    queries_df = _build_queries(catalog_df=catalog_df, n_rows=120, rng=rng)
    click_log_df = _build_click_log(queries_df=queries_df, catalog_df=catalog_df, n_rows=5000, rng=rng)

    catalog_path = os.path.join(data_dir, "catalog.csv")
    queries_path = os.path.join(data_dir, "queries.csv")
    click_log_path = os.path.join(data_dir, "click_log.csv")

    catalog_df.to_csv(catalog_path, index=False)
    queries_df.to_csv(queries_path, index=False)
    click_log_df.to_csv(click_log_path, index=False)

    print("Synthetic data generated successfully")
    print(f"- {catalog_path}: {len(catalog_df)} rows")
    print(f"- {queries_path}: {len(queries_df)} rows")
    print(f"- {click_log_path}: {len(click_log_df)} rows")
    print(f"- Click-through rate: {click_log_df['clicked'].mean():.3f}")
    print("- Categories:")
    print(catalog_df["category"].value_counts().to_string())


if __name__ == "__main__":
    main()
