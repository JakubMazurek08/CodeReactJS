import os
import logging
from logging.handlers import RotatingFileHandler

# Configure application-wide logging
def configure_logging():
    """Configure logging for the application"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handler
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    
    # Configure logging format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    
    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Configure console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

# Configure logging
configure_logging()

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Check if Firebase is enabled
FIREBASE_ENABLED = os.environ.get("FIREBASE_ENABLED", "false").lower() == "true"

# Import storage interfaces after logging is configured
if FIREBASE_ENABLED:
    try:
        logger.info("Using Firebase storage")
        from app.services.firebase_storage import (
            FirebaseJobStorage as JobStorage,
            FirebaseInterviewStorage as InterviewStorage,
            FirebaseCVStorage as CVStorage
        )
    except ImportError as e:
        logger.error(f"Error importing Firebase storage: {e}")
        logger.warning("Falling back to local storage")
        from app.services.local_storage import (
            LocalJobStorage as JobStorage,
            LocalInterviewStorage as InterviewStorage,
            LocalCVStorage as CVStorage
        )
else:
    logger.info("Using local storage")
    from app.services.local_storage import (
        LocalJobStorage as JobStorage,
        LocalInterviewStorage as InterviewStorage,
        LocalCVStorage as CVStorage
    )

# Storage instances
_job_storage = None
_interview_storage = None
_cv_storage = None

def get_job_storage():
    """Get job storage interface"""
    global _job_storage
    if _job_storage is None:
        _job_storage = JobStorage()
    return _job_storage

def get_interview_storage():
    """Get interview storage interface"""
    global _interview_storage
    if _interview_storage is None:
        _interview_storage = InterviewStorage()
    return _interview_storage

def get_cv_storage():
    """Get CV storage interface"""
    global _cv_storage
    if _cv_storage is None:
        _cv_storage = CVStorage()
    return _cv_storage

# Create data directories
def create_data_directories():
    """Create required data directories"""
    dirs = ["data", "data/jobs", "data/interviews", "data/cv"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Initialize data directories
create_data_directories()

logger.info("JobPrepAI application initialized") 