# Process Log (AIMS KTT S2.T1.3)

## 1) Hour-by-Hour Timeline (Apr 22, approx.)
- **11:30-12:00**: Read challenge scope and set Tier 1 approach (single local catalog, TF-IDF retrieval, no embeddings/API).
- **12:00-13:00**: Built initial `recommender.py` scaffold with required functions, CLI query path, and graceful file/column checks.
- **13:00-13:30**: Noticed missing dataset step; created `generate_data.py` with fixed seed and three files:
  - `data/catalog.csv` (~400 rows)
  - `data/queries.csv` (~120 rows)
  - `data/click_log.csv` (~5000 rows)
- **13:30-13:45**: Added `inspect_data.py` for schema/quality checks and ran validation passes.
- **13:45-14:05**: Implemented local-boost/fallback in `recommend(q)`:
  - normal path = cosine ranking
  - weak-match path = category/material keyword preference + click popularity tie-break
- **14:05-14:25**: Built and rebuilt `eval.ipynb`; fixed notebook formatting issue where code cells contained literal `\\n`.
- **14:25-14:40**: Finalized documentation artifacts:
  - `README.md` updated with actual evaluation numbers and defense notes
  - `dispatcher.md` added for offline artisan operating model
  - `SIGNED.md` + `LICENSE` completed

## 2) Tools Used and Why
- **Codex (GPT-5 coding assistant)**: primary implementation and refactoring support across Python files and notebook JSON.
- **Python 3**: script execution, notebook validation, and quick metric checks.
- **pandas / numpy / scikit-learn**: core data processing and TF-IDF + cosine retrieval.
- **Terminal utilities (`rg`, `sed`, `pdftotext`)**:
  - `rg`/`sed` for fast file inspection and targeted edits
  - `pdftotext` to extract the exact honor-code text from the provided brief PDF

## 3) Three Sample Prompts Actually Used
1. "Open `recommender.py` and replace the placeholder lines with a clean, minimal Python scaffold for a Tier 1 content-based recommender."
2. "Create a file named `generate_data.py` for a Tier 1 hackathon project called 'Made in Rwanda Content Recommender'."
3. "Open `eval.ipynb` and build a simple, readable evaluation notebook."

## 4) One Discarded Prompt and Why
- **Discarded prompt attempt**: "Generate the notebook as one raw JSON blob with escaped newlines in code cells."
- **Why discarded**: this produced literal `\\n` artifacts in notebook code cells in VS Code/Jupyter, causing syntax errors.  
  I replaced that approach by rewriting `eval.ipynb` with clean multiline cell source and re-validating execution.

## 5) Hardest Decision (Short Reflection)
The hardest decision was how to keep fallback behavior both useful and defensible at Tier 1. A more complex intent classifier or multi-stage ranking could improve edge cases, but would be harder to explain and risk overfitting synthetic data. I chose a simple rule: keep TF-IDF + cosine as the main ranker, and only when the top score is weak, switch to a local substitute fallback that prioritizes obvious category/material keyword matches, then breaks ties with click popularity. This kept the logic transparent for live defense while still avoiding empty or low-quality outputs on weak queries.
