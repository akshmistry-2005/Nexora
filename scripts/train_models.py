"""CLI Script to train and persist all machine learning models for Nexora."""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal
from app.services.ml_training import train_all_models


def main():
    print("Beginning Nexora Machine Learning training pipeline...")
    with SessionLocal() as db:
        metadata = train_all_models(db, random_state=42)

    for model_id, meta in metadata.items():
        print(f"\n[OK] Model '{model_id}' trained successfully:")
        print(f"     Target: {meta['target_variable']}")
        print(f"     Candidate: {meta['candidate_algorithm']}")
        print(f"     Candidate Metrics: {meta['candidate_metrics']}")
        print(f"     Baseline Metrics: {meta['baseline_metrics']}")
        print(f"     Artifact: {meta['artifact_path']}")

    print("\nAll model artifacts and governance metadata updated successfully.")


if __name__ == "__main__":
    main()
