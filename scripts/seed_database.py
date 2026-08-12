"""
Load data/approved_words.csv into the `words` table.

Usage:
    python scripts/seed_database.py
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Word  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "approved_words.csv"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    added, skipped = 0, 0
    try:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                exists = db.query(Word).filter_by(normalized_word=row["normalized_word"]).first()
                if exists:
                    skipped += 1
                    continue
                db.add(Word(
                    word=row["word"],
                    normalized_word=row["normalized_word"],
                    category=row["category"],
                    is_active=True,
                ))
                added += 1
        db.commit()
    finally:
        db.close()
    print(f"Seeded {added} new words, skipped {skipped} already present.")


if __name__ == "__main__":
    main()
