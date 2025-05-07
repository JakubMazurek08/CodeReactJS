import os
import json
import logging
import time
from typing import Dict, List, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore

# Configure logging
logger = logging.getLogger(__name__)

# Path to Firebase credentials file
FIREBASE_CREDENTIALS_PATH = "firebase-credentials.json"

# Initialize Firebase
try:
    # Check if app is already initialized
    if not firebase_admin._apps:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    raise

class FirebaseJobStorage:
    """Firebase storage implementation for jobs"""
    
    def __init__(self):
        """Initialize Firebase storage for jobs"""
        self.collection = db.collection('jobs')
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample job data if collection is empty"""
        try:
            # Check if collection is empty
            docs = self.collection.limit(1).stream()
            if len(list(docs)) > 0:
                logger.info("Job collection already has data, skipping initialization")
                return
            
            # Load sample data from jobs.json if available
            logger.info("Job collection is empty, initializing with sample data")
            try:
                with open('jobs.json', 'r', encoding='utf-8') as f:
                    sample_jobs = json.load(f)
                    logger.info(f"Loaded {len(sample_jobs)} jobs from jobs.json")
            except Exception as e:
                logger.warning(f"Could not load jobs.json: {e}")
                # Fallback to minimal sample data
                sample_jobs = [
                    {
                        "id": "job1",
                        "title": "Python Developer",
                        "company": "TechCorp",
                        "location": "Warsaw",
                        "description": "Looking for an experienced Python developer to join our team.",
                        "required_skills": ["Python", "Django", "Flask", "SQL", "Git"],
                        "experience_level": "mid",
                        "employment_type": "Full-time",
                        "created_at": time.time()
                    },
                    {
                        "id": "job2",
                        "title": "Frontend Developer",
                        "company": "WebSolutions",
                        "location": "Krakow",
                        "description": "Join our team to create modern web applications.",
                        "required_skills": ["JavaScript", "React", "HTML", "CSS", "TypeScript"],
                        "experience_level": "junior",
                        "employment_type": "Full-time",
                        "created_at": time.time()
                    }
                ]
            
            # Add jobs to Firestore
            batch = db.batch()
            for job in sample_jobs:
                # Ensure job has an ID
                if 'id' not in job:
                    job['id'] = f"job_{int(time.time())}_{len(batch._writes)}"
                
                # Add job to batch
                job_ref = self.collection.document(job['id'])
                batch.set(job_ref, job)
                
                # Firestore has a limit of 500 operations per batch
                if len(batch._writes) >= 450:
                    batch.commit()
                    logger.info(f"Committed batch of {len(batch._writes)} jobs")
                    batch = db.batch()
            
            # Commit any remaining writes
            if batch._writes:
                batch.commit()
                logger.info(f"Committed remaining {len(batch._writes)} jobs")
            
            logger.info(f"Initialized sample data with {len(sample_jobs)} jobs")
            
        except Exception as e:
            logger.error(f"Error initializing sample data: {e}")
    
    def list_jobs(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by keyword
        
        Args:
            keyword: Optional keyword to filter jobs
            
        Returns:
            List of job data
        """
        try:
            # Get all jobs
            jobs = []
            docs = self.collection.stream()
            
            for doc in docs:
                jobs.append(doc.to_dict())
            
            logger.info(f"Retrieved {len(jobs)} jobs from Firebase")
            
            if not keyword:
                return jobs
            
            # Filter by keyword in title, description, or skills
            keyword_lower = keyword.lower()
            filtered_jobs = []
            
            for job in jobs:
                title = job.get('title', '').lower()
                description = job.get('description', '').lower()
                required_skills = [s.lower() for s in job.get('required_skills', [])]
                
                if (keyword_lower in title or 
                    keyword_lower in description or 
                    any(keyword_lower in skill for skill in required_skills)):
                    filtered_jobs.append(job)
            
            logger.info(f"Filtered to {len(filtered_jobs)} jobs with keyword '{keyword}'")
            return filtered_jobs
            
        except Exception as e:
            logger.error(f"Error listing jobs: {e}")
            return []
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job data or None if not found
        """
        try:
            doc_ref = self.collection.document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning(f"Job {job_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None
    
    def save_job(self, job_data: Dict[str, Any]) -> str:
        """
        Save a job
        
        Args:
            job_data: Job data
            
        Returns:
            Job ID
        """
        try:
            # Ensure job has an ID
            if 'id' not in job_data:
                job_data['id'] = f"job_{int(time.time())}_{str(time.time()).split('.')[-1]}"
            
            # Set created_at if not present
            if 'created_at' not in job_data:
                job_data['created_at'] = time.time()
            
            # Save to Firestore
            doc_ref = self.collection.document(job_data['id'])
            doc_ref.set(job_data)
            
            logger.info(f"Saved job {job_data['id']}")
            return job_data['id']
            
        except Exception as e:
            logger.error(f"Error saving job: {e}")
            return ""

class FirebaseInterviewStorage:
    """Firebase storage implementation for interviews"""
    
    def __init__(self):
        """Initialize Firebase storage for interviews"""
        self.collection = db.collection('interviews')
    
    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific interview by ID
        
        Args:
            interview_id: Interview ID
            
        Returns:
            Interview data or None if not found
        """
        try:
            doc_ref = self.collection.document(interview_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning(f"Interview {interview_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting interview {interview_id}: {e}")
            return None
    
    def save_interview(self, interview_data: Dict[str, Any]) -> str:
        """
        Save an interview
        
        Args:
            interview_data: Interview data
            
        Returns:
            Interview ID
        """
        try:
            # Ensure interview has an ID
            if 'id' not in interview_data:
                interview_data['id'] = f"interview_{int(time.time())}_{str(time.time()).split('.')[-1]}"
            
            # Save to Firestore
            doc_ref = self.collection.document(interview_data['id'])
            doc_ref.set(interview_data)
            
            logger.info(f"Saved interview {interview_data['id']}")
            return interview_data['id']
            
        except Exception as e:
            logger.error(f"Error saving interview: {e}")
            return ""
    
    def update_interview(self, interview_id: str, interview_data: Dict[str, Any]) -> bool:
        """
        Update an interview
        
        Args:
            interview_id: Interview ID
            interview_data: Interview data
            
        Returns:
            Success flag
        """
        try:
            # Save to Firestore
            doc_ref = self.collection.document(interview_id)
            doc_ref.update(interview_data)
            
            logger.info(f"Updated interview {interview_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating interview {interview_id}: {e}")
            return False
    
    def list_interviews(self, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all interviews, optionally filtered by job ID
        
        Args:
            job_id: Optional job ID to filter interviews
            
        Returns:
            List of interview data
        """
        try:
            # Get all interviews
            interviews = []
            
            if job_id:
                # Filter by job ID
                docs = self.collection.where('job_id', '==', job_id).stream()
            else:
                # Get all interviews
                docs = self.collection.stream()
            
            for doc in docs:
                interviews.append(doc.to_dict())
            
            return interviews
            
        except Exception as e:
            logger.error(f"Error listing interviews: {e}")
            return []

class FirebaseCVStorage:
    """Firebase storage implementation for CV analyses"""
    
    def __init__(self):
        """Initialize Firebase storage for CV analyses"""
        self.collection = db.collection('cv_analyses')
    
    def save_cv_file(self, content: str, job_id: str) -> str:
        """
        Save a CV file
        
        Args:
            content: CV content
            job_id: Associated job ID
            
        Returns:
            CV ID
        """
        try:
            # Generate unique ID
            cv_id = f"cv_{int(time.time())}_{str(time.time()).split('.')[-1]}"
            
            # Save to Firestore
            doc_ref = self.collection.document(cv_id)
            doc_ref.set({
                'id': cv_id,
                'content': content,
                'job_id': job_id,
                'created_at': time.time()
            })
            
            logger.info(f"Saved CV {cv_id}")
            return cv_id
            
        except Exception as e:
            logger.error(f"Error saving CV: {e}")
            return ""
    
    def save_cv_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """
        Save a CV analysis
        
        Args:
            analysis_data: CV analysis data
            
        Returns:
            Analysis ID
        """
        try:
            # Ensure analysis has an ID
            if 'id' not in analysis_data:
                analysis_data['id'] = f"cv_analysis_{int(time.time())}_{str(time.time()).split('.')[-1]}"
            
            # Save to Firestore
            doc_ref = self.collection.document(analysis_data['id'])
            doc_ref.set(analysis_data)
            
            logger.info(f"Saved CV analysis {analysis_data['id']}")
            return analysis_data['id']
            
        except Exception as e:
            logger.error(f"Error saving CV analysis: {e}")
            return ""
    
    def get_cv_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific CV analysis by ID
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis data or None if not found
        """
        try:
            doc_ref = self.collection.document(analysis_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning(f"CV analysis {analysis_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error getting CV analysis {analysis_id}: {e}")
            return None
    
    def list_cv_analyses(self, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all CV analyses, optionally filtered by job ID
        
        Args:
            job_id: Optional job ID to filter analyses
            
        Returns:
            List of analysis data
        """
        try:
            # Get all analyses
            analyses = []
            
            if job_id:
                # Filter by job ID
                docs = self.collection.where('job_id', '==', job_id).stream()
            else:
                # Get all analyses
                docs = self.collection.stream()
            
            for doc in docs:
                analyses.append(doc.to_dict())
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error listing CV analyses: {e}")
            return [] 