#!/usr/bin/env python
"""
Upload jobs.json → Firestore  (one document per job, ID = job['id'])
-------------------------------------------------------------------
Pliki obok skryptu:
- firebase-credentials.json  – klucz serwisowy z Google Cloud
- jobs.json                  – lista ogłoszeń (jak w przykładzie)

Ustaw CRED_PATH / JOBS_PATH jeśli pliki są gdzie indziej.
"""

import json
import pathlib
import firebase_admin
from firebase_admin import credentials, firestore

# ---------- ŚCIEŻKI DO PLIKÓW ----------
CRED_PATH = pathlib.Path("firebase-credentials.json")
JOBS_PATH = pathlib.Path("jobs.json")
# --------------------------------------

def init_firestore():
    """Inicjalizuje Firebase Admin SDK i zwraca klienta Firestore."""
    if not CRED_PATH.is_file():
        raise FileNotFoundError(f"Brak pliku z poświadczeniami: {CRED_PATH.resolve()}")
    cred = credentials.Certificate(CRED_PATH)
    app = firebase_admin.initialize_app(cred)
    return firestore.client(app)

def load_jobs():
    """Wczytuje jobs.json i zwraca listę słowników."""
    if not JOBS_PATH.is_file():
        raise FileNotFoundError(f"Brak jobs.json: {JOBS_PATH.resolve()}")
    with JOBS_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("jobs.json musi zawierać listę obiektów.")
    return data

def upload_jobs(db, jobs):
    """Zapisuje ogłoszenia w kolekcji 'jobs' (docID = job['id'])."""
    batch = db.batch()
    for job in jobs:
        job_id = job.get("id")
        if not job_id:
            print("⚠️  Pominięto rekord bez pola 'id':", job)
            continue
        doc_ref = db.collection("jobs").document(job_id)
        batch.set(doc_ref, job)        # nadpisuje, jeśli istnieje
    batch.commit()
    print(f"🚀  Wysłano {len(jobs)} dokumentów do kolekcji 'jobs'.")

def main():
    db = init_firestore()
    jobs = load_jobs()
    upload_jobs(db, jobs)

if __name__ == "__main__":
    main()
