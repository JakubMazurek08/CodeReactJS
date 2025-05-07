class FirebaseJobStorage:
    """Firebase storage implementation for jobs"""
    
    def __init__(self):
        """Initialize Firebase storage for jobs"""
        self.collection = db.collection('jobs')
        # Remove the sample data initialization
        # self._initialize_sample_data()
    
    # You can either remove this method entirely or modify it to not do anything
    def _initialize_sample_data(self):
        """This method is now disabled - will not initialize sample data"""
        logger.info("Sample data initialization is disabled")
        return
    
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