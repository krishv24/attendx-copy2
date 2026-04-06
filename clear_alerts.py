#!/usr/bin/env python3
"""clear_alerts.py - Delete all alert documents from Firestore."""
from app import create_app
from app.extensions import db


def delete_collection(collection_name, batch_size=400):
    deleted = 0
    while True:
        docs = db.collection(collection_name).limit(batch_size).get()
        if not docs:
            break
        batch = db.batch()
        for doc in docs:
            batch.delete(doc.reference)
            deleted += 1
        batch.commit()
    return deleted


def main():
    app = create_app()
    with app.app_context():
        count = delete_collection("alerts")
        print(f"Deleted {count} alert documents.")


if __name__ == "__main__":
    main()
