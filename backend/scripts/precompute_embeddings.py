#!/usr/bin/env python3
"""
Pre-compute semantic embeddings for all words in the database.

This script:
1. Connects to the database
2. Loads the embedding model
3. Computes embeddings for all active words
4. Stores embeddings in the word_embeddings table
5. Enables the sentence_transformers scoring backend

Usage:
    python scripts/precompute_embeddings.py
"""

import json
import os
import sys
from pathlib import Path

# Keep the precompute job within small Render instance limits.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# Add backend to path so we can import app modules
backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from sentence_transformers import SentenceTransformer
import numpy as np

from app.database import SessionLocal
from app.config import get_settings
from app import models

settings = get_settings()


def precompute_embeddings():
    """Load all words and pre-compute their embeddings."""
    db = SessionLocal()
    try:
        # Fetch all active words
        words = db.execute(
            select(models.Word).where(models.Word.is_active.is_(True))
        ).scalars().all()
        
        if not words:
            print("No active words found in database. Run seed_database.py first.")
            return

        existing_count = db.execute(
            select(models.WordEmbedding).where(
                models.WordEmbedding.model_name == settings.embedding_model
            )
        ).scalars().all()
        if len(existing_count) == len(words):
            print(f"Embeddings already exist for all {len(words)} active words. Skipping.")
            return

        print(f"Loading embedding model: {settings.embedding_model}")
        model = SentenceTransformer(settings.embedding_model)
        
        print(f"Found {len(words)} active words. Computing embeddings...")
        
        # Get all normalized words for batch encoding
        normalized_words = [word.normalized_word for word in words]
        
        # Encode all words at once (more efficient than one-by-one)
        embeddings = model.encode(
            normalized_words,
            batch_size=32,
            normalize_embeddings=True,  # Normalize to unit length for cosine similarity
            show_progress_bar=True,
        )
        
        print(f"Computed {len(embeddings)} embeddings. Storing in database...")
        
        if existing_count:
            print(f"Warning: {len(existing_count)} embeddings already exist for this model.")
            print("Deleting old embeddings...")
            for embedding in existing_count:
                db.delete(embedding)
            db.commit()
        
        # Store embeddings
        for word, embedding in zip(words, embeddings):
            # Convert embedding to JSON string
            embedding_json = json.dumps(embedding.tolist())
            
            word_embedding = models.WordEmbedding(
                word_id=word.id,
                embedding=embedding_json,
                model_name=settings.embedding_model,
            )
            db.add(word_embedding)
        
        db.commit()
        print(f"✓ Successfully stored {len(embeddings)} embeddings in database")
        print(f"✓ Model: {settings.embedding_model}")
        print("\nNext steps:")
        print("1. Update .env: set SCORING_BACKEND=sentence_transformers")
        print("2. Restart your application")
        
    except Exception as e:
        db.rollback()
        print(f"✗ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    precompute_embeddings()
