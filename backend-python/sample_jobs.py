"""
Module that loads sample jobs data from jobs.json
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

# Ścieżka do pliku jobs.json
JOBS_PATH = "jobs.json"

try:
    # Wczytaj dane z jobs.json
    with open(JOBS_PATH, 'r', encoding='utf-8') as f:
        SAMPLE_JOBS = json.load(f)
    logger.info(f"Wczytano {len(SAMPLE_JOBS)} ofert pracy z jobs.json")
except Exception as e:
    logger.error(f"Błąd podczas wczytywania jobs.json: {e}")
    # Domyślne oferty pracy w przypadku błędu wczytywania pliku
    SAMPLE_JOBS = [
        {
            "id": "sample1",
            "title": "Python Developer",
            "company": "Example Corp",
            "location": "Remote",
            "description": "Developing Python applications",
            "required_skills": ["Python", "Django", "Flask"],
            "experience_level": "mid",
            "salary_range": "$50,000 - $70,000",
            "employment_type": "Full-time",
            "remote": True
        },
        {
            "id": "sample2",
            "title": "Frontend Developer",
            "company": "Sample Inc",
            "location": "Warsaw",
            "description": "Building modern web interfaces",
            "required_skills": ["JavaScript", "React", "HTML", "CSS"],
            "experience_level": "junior",
            "salary_range": "$30,000 - $50,000",
            "employment_type": "Full-time",
            "remote": False
        }
    ] 