import json
import logging
import re
from typing import Dict, List, Any
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.ai_service import get_structured_output

# Configure logging
logger = logging.getLogger(__name__)

# Common skills (case-insensitive)
SKILLS_LIST = [
    
    # Programming languages
    "python", "javascript", "typescript", "java", "c#", "c\\+\\+", "php", "go", "golang", "rust", "swift", 
    "kotlin", "ruby", "scala", "perl", "shell", "powershell", "bash", "r", "matlab", "objective-c", "lua",
    
    # Web development
    "html", "css", "html5", "css3", "sass", "scss", "less", "bootstrap", "tailwind", "tailwindcss", "emotion",
    "styled-components", "material-ui", "jquery", "wordpress", "webflow", "wix", "shopify",
    
    # Frontend frameworks & libraries
    "react", "vue", "angular", "svelte", "next.js", "nextjs", "gatsby", "nuxt", "ember", "redux", "mobx", 
    "webpack", "vite", "parcel", "rollup", "npm", "yarn", "pnpm", "babel", "jest", "cypress", "mocha",
    
    # Backend frameworks & libraries
    "node.js", "nodejs", "express", "nest.js", "nestjs", "django", "flask", "fastapi", "spring", "spring boot", 
    "laravel", "symfony", "aspnet", "asp.net", "rails", "sinatra", "phoenix", 
    
    # Database technologies
    "sql", "nosql", "mongodb", "mysql", "postgresql", "postgres", "sqlite", "oracle", "cassandra", "redis", 
    "elasticsearch", "neo4j", "dynamodb", "firestore", "firebase", "supabase", "cockroachdb", "mariadb",
    
    # DevOps & Cloud
    "aws", "azure", "gcp", "google cloud", "digitalocean", "heroku", "netlify", "vercel", "docker", "kubernetes", 
    "k8s", "jenkins", "github actions", "travis", "circleci", "terraform", "ansible", "chef", "puppet", "prometheus", 
    "grafana", "nginx", "apache", "serverless", "lambda", "ci/cd", "cicd",
    
    # Mobile development
    "android", "ios", "react native", "flutter", "xamarin", "cordova", "ionic", "swiftui", "kotlin multiplatform",
    
    # AI & Data Science
    "machine learning", "deep learning", "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", 
    "opencv", "nltk", "spacy", "huggingface", "transformers", "llm", "large language model", "gpt", "bert", 
    "data science", "data analysis", "data engineering", "tableau", "power bi", "looker", "snowflake", "hadoop", "spark",
    
    # Other technologies
    "graphql", "rest api", "restful", "webrtc", "websocket", "oauth", "jwt", "soap", "microservices", "soa", 
    "grpc", "etl", "selenium", "puppeteer", "playwright",
    
    # Version control
    "git", "github", "gitlab", "bitbucket", "svn", "mercurial",
    
    # Testing
    "unit testing", "integration testing", "e2e testing", "selenium", "qa", "quality assurance", "tdd", "bdd",
    
    # Project management & tools
    "agile", "scrum", "kanban", "jira", "confluence", "trello", "asana", "notion", "basecamp",
    
    # General tech terms
    "fullstack", "full-stack", "frontend", "front-end", "backend", "back-end", "devops", "sysadmin", "sre", 
    "security", "cybersecurity", "crypto", "blockchain", "web3", "data",

    # Soft skills often associated with tech
    "problem solving", "analytical", "communication", "teamwork", "collaboration", "adaptability", "creativity",

    # General Skills
    "cooking", "baking", "food preparation", "meal planning", "nutrition", "gardening", "landscaping", "farming", 
    "cleaning", "housekeeping", "organizing", "decluttering", "laundry", "ironing", "sewing", "knitting", 
    "crocheting", "tailoring", "mending", "childcare", "babysitting", "elder care", "pet care", "animal handling",
    "driving", "vehicle maintenance", "bicycle repair", "first aid", "cpr", "emergency preparedness", 
    "basic plumbing", "basic electrical work", "home repair", "painting", "decorating", "woodworking", "carpentry",
    "budgeting", "personal finance", "investing", "tax preparation", "negotiation", "sales", "customer service", 
    "public speaking", "presentation skills", "writing", "editing", "proofreading", "storytelling", "copywriting",
    "research", "data entry", "typing", "transcription", "translation", "interpreting", "foreign languages",
    "spanish", "french", "german", "mandarin", "japanese", "italian", "portuguese", "russian", "arabic", "hindi",
    "photography", "videography", "photo editing", "video editing", "graphic design", "illustration", "drawing", 
    "painting", "sculpting", "pottery", "calligraphy", "music performance", "singing", "instrument playing", 
    "guitar", "piano", "drums", "violin", "flute", "songwriting", "music composition", "djing", "audio editing",
    "dancing", "choreography", "acting", "theater performance", "event planning", "project management", 
    "time management", "leadership", "mentoring", "coaching", "teaching", "tutoring", "curriculum development",
    "physical fitness", "personal training", "yoga instruction", "swimming", "running", "cycling", "hiking", 
    "climbing", "team sports", "basketball", "soccer", "football", "baseball", "volleyball", "tennis", "golf",
    "martial arts", "self-defense", "meditation", "mindfulness", "critical thinking", "logic", "debate", 
    "game strategy", "chess", "poker", "bartending", "mixology", "wine tasting", "coffee brewing", "journalism",
    "archiving", "library science", "genealogy", "volunteering", "community organizing", "fundraising", "crafting",
    "scrapbooking", "jewelry making", "candle making", "soap making", "origami", "model building", "call center operations",
    "scheduling", "travel planning", "hospitality service", "cash handling", "inventory management", "logistics coordination",
    "warehousing", "catering", "event hosting", "tour guiding", "proofreading", "fact-checking", "speed reading",
    "memory techniques", "conflict resolution", "mediation", "counselling", "active listening", "networking",
    "report writing", "grant writing", "public relations", "social media management", "digital marketing", "content creation",
    "user experience design", "user interface design", "market research", "data analysis (general)", "statistics (general)",
    "survey design", "interviewing (research)", "meeting facilitation", "brainstorming", "decision making", "risk management (general)",
    "safety procedures", "quality control (general)"
]

def extract_skills_from_text(text: str) -> Dict[str, Any]:
    """
    Extract skills and experience level from text
    
    Args:
        text: Text to extract skills from
        
    Returns:
        Dictionary with extracted skills and experience level
    """
    # Clean text
    text = text.lower()
    
    # Extract skills
    skills = set()
    
    # Check for skills using regex patterns
    for skill in SKILLS_LIST:
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, text, re.IGNORECASE):
            # Add clean skill name (without regex escapes)
            clean_skill = skill.replace("\\+\\+", "++").replace("\\", "")
            skills.add(clean_skill)
    
    # Special case for C++ since regex is tricky with +
    if "c++" in text.lower():
        skills.add("c++")
    
    # Extract experience level
    experience_level = "junior"  # Default
    
    # Experience indicators
    senior_indicators = [
        "senior", "lead", "staff", "principal", "architect", "10+ years", "decade", 
        "extensive experience", "expert", "manager", "head of", "director"
    ]
    
    mid_indicators = [
        "mid", "intermediate", "5+ years", "5 years", "experienced", 
        "solid experience", "proficient", "3+ years", "3 years"
    ]
    
    junior_indicators = [
        "junior", "entry", "graduate", "begin", "start", "trainee", "intern", 
        "apprentice", "1 year", "1+ years", "2 years", "student"
    ]
    
    # Check for experience level indicators
    for indicator in senior_indicators:
        if indicator in text.lower():
            experience_level = "senior"
            break
    
    if experience_level == "junior":  # Only check if not already senior
        for indicator in mid_indicators:
            if indicator in text.lower():
                experience_level = "mid"
                break
    
    # Extract years of experience using regex
    years_patterns = [
        r'(\d+)[\+]?\s*years?\s*(?:of)?\s*(?:experience|work)',
        r'(?:experience|work)(?:d)?(?:\s*for)?\s*(\d+)[\+]?\s*years?',
        r'(\d+)[\+]?\s*years?'
    ]
    
    max_years = 0
    for pattern in years_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                years = int(match)
                max_years = max(max_years, years)
            except ValueError:
                pass
    
    # Adjust experience level based on years
    if max_years > 0:
        if max_years >= 5:
            experience_level = "senior"
        elif max_years >= 2:
            experience_level = "mid"
        else:
            experience_level = "junior"
    
    logger.info(f"Extracted {len(skills)} skills from text")
    logger.info(f"Determined experience level: {experience_level}")
    
    return {
        "skills": list(skills),
        "experience_level": experience_level
    } 