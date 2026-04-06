#!/usr/bin/env python3
"""Restore Firestore collections from a timestamped JSON backup.

Usage:
  python3 restore_firestore.py backups/firestore_backup_YYYYmmdd_HHMMSS
"""

import sys
import json
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 restore_firestore.py <backup_folder_path>")
        sys.exit(1)

    backup_dir = Path(sys.argv[1]).resolve()
    if not backup_dir.is_dir():
        print(f"Error: directory not found -> {backup_dir}")
        sys.exit(1)

    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"Error: manifest.json not found in {backup_dir}")
        sys.exit(1)

    root = Path(__file__).resolve().parent
    cred_path = root / "firebase-credentials.json"
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(str(cred_path)))

    db = firestore.client()

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    for coll_info in manifest.get("collections", []):
        coll_name = coll_info["name"]
        file_name = coll_info["file"]
        json_path = backup_dir / file_name

        if not json_path.exists():
            print(f"Warning: {json_path} missing, skipping {coll_name}.")
            continue

        with json_path.open("r", encoding="utf-8") as f:
            docs = json.load(f)

        print(f"Restoring {len(docs)} documents to collection '{coll_name}'...")
        batch = db.batch()
        batch_count = 0

        for doc_obj in docs:
            doc_id = doc_obj["id"]
            doc_data = doc_obj["data"]

            doc_ref = db.collection(coll_name).document(doc_id)
            batch.set(doc_ref, doc_data)
            batch_count += 1

            if batch_count == 500:
                batch.commit()
                batch = db.batch()
                batch_count = 0

        if batch_count > 0:
            batch.commit()

    print("Restore completed successfully!")


if __name__ == "__main__":
    main()
