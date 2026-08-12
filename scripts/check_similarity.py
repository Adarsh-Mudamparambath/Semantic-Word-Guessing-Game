"""
Semantic diversity validation for the candidate word list.

Full O(n^2) pairwise comparison across ~1000 words is wasteful and, since
this project scores similarity via an LLM judge (see app/scoring.py) rather
than local embedding vectors, pairwise LLM calls for 1000 words would be
~500k calls. Instead this script:

  1. Groups candidates by category (near-duplicates are far more likely
     within the same category than across categories).
  2. Sends each category's word list to Claude in ONE batched call, asking
     it to flag any pairs/groups that are near-synonyms or overly close in
     meaning (e.g. ocean/sea), given a configurable strictness threshold.
  3. Writes a report to data/diversity_report.json for developer review.

This keeps the check to ~N_CATEGORIES API calls instead of N^2.

Usage:
    python scripts/check_similarity.py --threshold strict
"""

import argparse
import csv
import json
import os
from collections import defaultdict
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

PROMPT_TEMPLATE = """You are validating word diversity for a semantic word-guessing game.
Below is a list of words from the "{category}" category. Flag any groups of
words that are near-synonyms or so semantically close that having both as
SEPARATE secret answers in the game would be unfair/confusing (e.g. "ocean"
and "sea"). Strictness level: {threshold}.

Words:
{words}

Respond ONLY with JSON, no prose, in this exact shape:
{{"near_duplicate_groups": [["word_a", "word_b"], ["word_c", "word_d", "word_e"]]}}
If none, return {{"near_duplicate_groups": []}}.
"""


def load_candidates():
    by_category = defaultdict(list)
    with open(DATA_DIR / "candidate_words.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_category[row["category"]].append(row["word"])
    return by_category


def check_category(client, category, words, threshold):
    prompt = PROMPT_TEMPLATE.format(
        category=category, threshold=threshold, words=", ".join(words)
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)["near_duplicate_groups"]
    except (json.JSONDecodeError, KeyError, IndexError):
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", default="moderate",
                         choices=["strict", "moderate", "loose"],
                         help="How aggressively to flag near-duplicates")
    args = parser.parse_args()

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    by_category = load_candidates()

    report = {}
    for category, words in by_category.items():
        groups = check_category(client, category, words, args.threshold)
        if groups:
            report[category] = groups

    out_path = DATA_DIR / "diversity_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    total_flags = sum(len(g) for g in report.values())
    print(f"Checked {len(by_category)} categories. Flagged {total_flags} near-duplicate group(s).")
    print(f"Report written to {out_path}")
    if report:
        print("Review the report and remove/replace one word per flagged group in")
        print("data/approved_words.csv, then re-run scripts/seed_database.py.")


if __name__ == "__main__":
    main()
