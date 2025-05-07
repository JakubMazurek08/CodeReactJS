import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import time

# Configure logging
logger = logging.getLogger(__name__)

# Sample jobs (imported from parent module if available)
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    from sample_jobs import SAMPLE_JOBS
except ImportError:
    logger.warning("Could not import sample jobs, using empty list")
    SAMPLE_JOBS = []

class BaseLocalStorage:
    """Base class for local storage implementations"""
    
    def __init__(self, directory: str):
        """
        Initialize local storage
        
        Args:
            directory: Directory to store data
        """
        self.directory = directory
        os.makedirs(directory, exist_ok=True)
    
    def _generate_id(self, prefix: str = "") -> str:
        """Generate a unique ID"""
        return f"{prefix}{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    def _get_file_path(self, item_id: str) -> str:
        """Get file path for an item"""
        return os.path.join(self.directory, f"{item_id}.json")
    
    def _save_item(self, item_id: str, data: Dict[str, Any]) -> bool:
        """Save item to a file"""
        try:
            with open(self._get_file_path(item_id), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving item {item_id}: {e}")
            return False
    
    def _get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get item from a file"""
        try:
            file_path = self._get_file_path(item_id)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error getting item {item_id}: {e}")
            return None
    
    def _list_items(self) -> List[Dict[str, Any]]:
        """List all items in the directory"""
        items = []
        try:
            for filename in os.listdir(self.directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.directory, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        items.append(json.load(f))
        except Exception as e:
            logger.error(f"Error listing items: {e}")
        return items

class LocalJobStorage(BaseLocalStorage):
    """Local storage implementation for jobs"""
    
    def __init__(self, data_file: str = "data/jobs.json"):
        """Initialize local storage with data file path"""
        super().__init__('data/jobs')
        self.data_file = data_file
        self._ensure_data_dir()
        
        # Initialize with sample data if file doesn't exist
        if not os.path.exists(self.data_file):
            self._initialize_sample_data()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
    
    def _initialize_sample_data(self):
        """Initialize with sample job data if file doesn't exist"""
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
            },
            {
                "id": "job3",
                "title": "DevOps Engineer",
                "company": "CloudTech",
                "location": "Remote",
                "description": "Seeking a DevOps engineer to manage our cloud infrastructure.",
                "required_skills": ["Docker", "Kubernetes", "AWS", "Linux", "CI/CD"],
                "experience_level": "senior",
                "employment_type": "Full-time",
                "created_at": time.time()
            }
        ]
        
        self._save_data(sample_jobs)
        logger.info(f"Initialized sample data with {len(sample_jobs)} jobs")
    
    def _load_data(self) -> List[Dict[str, Any]]:
        """Load job data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading job data: {e}")
            return []
    
    def _save_data(self, data: List[Dict[str, Any]]) -> bool:
        """Save job data to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving job data: {e}")
            return False
    
    def list_jobs(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by keyword
        
        Args:
            keyword: Optional keyword to filter jobs
            
        Returns:
            List of job data
        """
        jobs = self._load_data()
        
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
        
        return filtered_jobs
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            Job data or None if not found
        """
        jobs = self._load_data()
        
        for job in jobs:
            if str(job.get('id')) == str(job_id):
                return job
        
        return None
    
    def save_job(self, job_data: Dict[str, Any]) -> str:
        """
        Save a new job or update existing one
        
        Args:
            job_data: Job data to save
            
        Returns:
            Job ID
        """
        jobs = self._load_data()
        
        # Check if job already exists
        job_id = job_data.get('id')
        if not job_id:
            job_id = f"job_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            job_data['id'] = job_id
            job_data['created_at'] = time.time()
            jobs.append(job_data)
        else:
            # Update existing job
            for i, job in enumerate(jobs):
                if str(job.get('id')) == str(job_id):
                    job_data['updated_at'] = time.time()
                    jobs[i] = job_data
                    break
            else:
                # Job with this ID doesn't exist, add as new
                job_data['created_at'] = time.time()
                jobs.append(job_data)
        
        self._save_data(jobs)
        return job_id

class LocalInterviewStorage(BaseLocalStorage):
    """Local storage implementation for interviews"""
    
    def __init__(self, data_file: str = "data/interviews.json"):
        """Initialize local storage with data file path"""
        super().__init__('data/interviews')
        self.data_file = data_file
    
    def _load_data(self) -> Dict[str, Any]:
        """Load interview data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading interview data: {e}")
            return {}
    
    def _save_data(self, data: Dict[str, Any]) -> bool:
        """Save interview data to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving interview data: {e}")
            return False
    
    def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific interview by ID
        
        Args:
            interview_id: Interview ID
            
        Returns:
            Interview data or None if not found
        """
        interviews = self._load_data()
        return interviews.get(interview_id)
    
    def save_interview(self, interview_data: Dict[str, Any]) -> str:
        """
        Save a new interview
        
        Args:
            interview_data: Interview data to save
            
        Returns:
            Interview ID
        """
        interviews = self._load_data()
        
        interview_id = interview_data.get('id')
        if not interview_id:
            interview_id = f"interview_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            interview_data['id'] = interview_id
        
        interview_data['updated_at'] = time.time()
        interviews[interview_id] = interview_data
        
        self._save_data(interviews)
        return interview_id
    
    def update_interview(self, interview_id: str, interview_data: Dict[str, Any]) -> bool:
        """
        Update an existing interview
        
        Args:
            interview_id: Interview ID
            interview_data: Updated interview data
            
        Returns:
            True if successful
        """
        interviews = self._load_data()
        
        if interview_id not in interviews:
            return False
        
        interview_data['updated_at'] = time.time()
        interviews[interview_id] = interview_data
        
        return self._save_data(interviews)
    
    def list_interviews(self, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all interviews, optionally filtered by job ID
        
        Args:
            job_id: Optional job ID to filter interviews
            
        Returns:
            List of interview data
        """
        interviews = self._load_data()
        
        # Convert to list
        interview_list = list(interviews.values())
        
        # Filter by job ID if provided
        if job_id:
            interview_list = [i for i in interview_list if i.get('job_id') == job_id]
        
        # Sort by creation time (descending)
        interview_list.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return interview_list

class LocalCVStorage(BaseLocalStorage):
    """Local storage implementation for CV analyses"""
    
    def __init__(self, data_dir: str = "data/cv"):
        """Initialize local storage with data directory path"""
        super().__init__(data_dir)
        self.data_dir = data_dir
        self.analysis_file = os.path.join(data_dir, "analysis.json")
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_analysis_data(self) -> Dict[str, Any]:
        """Load CV analysis data from file"""
        try:
            if os.path.exists(self.analysis_file):
                with open(self.analysis_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading CV analysis data: {e}")
            return {}
    
    def _save_analysis_data(self, data: Dict[str, Any]) -> bool:
        """Save CV analysis data to file"""
        try:
            with open(self.analysis_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving CV analysis data: {e}")
            return False
    
    def save_cv_file(self, content: str, job_id: str) -> str:
        """
        Save a CV file
        
        Args:
            content: CV content
            job_id: Job ID
            
        Returns:
            CV file URL
        """
        cv_id = f"cv_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        file_path = os.path.join(self.data_dir, f"{cv_id}.txt")
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Return a relative URL
            return f"data/cv/{cv_id}.txt"
        except Exception as e:
            logger.error(f"Error saving CV file: {e}")
            return ""
    
    def save_cv_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """
        Save CV analysis data
        
        Args:
            analysis_data: Analysis data to save
            
        Returns:
            Analysis ID
        """
        analyses = self._load_analysis_data()
        
        analysis_id = analysis_data.get('id')
        if not analysis_id:
            analysis_id = f"analysis_{int(time.time())}_{str(uuid.uuid4())[:8]}"
            analysis_data['id'] = analysis_id
        
        analysis_data['created_at'] = time.time()
        analyses[analysis_id] = analysis_data
        
        self._save_analysis_data(analyses)
        return analysis_id
    
    def get_cv_analysis(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific CV analysis by ID
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis data or None if not found
        """
        analyses = self._load_analysis_data()
        return analyses.get(analysis_id)
    
    def list_cv_analyses(self, job_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all CV analyses, optionally filtered by job ID
        
        Args:
            job_id: Optional job ID to filter analyses
            
        Returns:
            List of analysis data
        """
        analyses = self._load_analysis_data()
        
        # Convert to list
        analysis_list = list(analyses.values())
        
        # Filter by job ID if provided
        if job_id:
            analysis_list = [a for a in analysis_list if a.get('job_id') == job_id]
        
        # Sort by creation time (descending)
        analysis_list.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        
        return analysis_list 