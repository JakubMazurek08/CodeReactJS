import logging
import uuid
from typing import Dict, List, Any, Optional
import sys
import os
import re
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.ai_service import get_structured_output

# Configure logging
logger = logging.getLogger(__name__)

# Job categories and keywords
JOB_CATEGORIES = {
    "tech": ["developer", "software", "programmer", "engineer", "devops", "data", "it", "web", "frontend", "backend", "fullstack", 
             "architect", "admin", "analyst", "tech", "computer", "system", "network", "security", "cloud", "database", "qa", "tester"],
    "healthcare": ["doctor", "nurse", "therapist", "physician", "medical", "health", "clinical", "caregiver", "healthcare", 
                   "patient", "physio", "rehab", "pharmacy", "dental", "surgeon"],
    "finance": ["accountant", "financial", "finance", "banking", "investment", "trading", "broker", "auditor", "tax", "accounting"],
    "education": ["teacher", "professor", "educator", "tutor", "lecturer", "instructor", "coach", "teaching", "education", "training"],
    "hospitality": ["chef", "cook", "hotel", "restaurant", "catering", "hospitality", "tourism", "travel", "kitchen"],
    "retail": ["sales", "retail", "cashier", "store", "shop", "customer", "seller", "vendor", "merchandiser"],
    "logistics": ["driver", "transport", "delivery", "logistics", "warehouse", "shipping", "supply", "inventory", "fleet"]
}

# Job synonyms for matching
JOB_SYNONYMS = {
    "szef kuchni": ["chef", "cook", "head chef", "kucharz"],
    "kucharz": ["chef", "cook", "culinary"],
    "kierowca": ["driver", "chauffeur"],
    "programista": ["developer", "software engineer", "coder", "programmer"],
    "nauczyciel": ["teacher", "educator", "instructor"],
    "opiekunka": ["caregiver", "nanny", "babysitter"],
    "sprzedawca": ["sales", "salesman", "retail associate"],
    "mechanik": ["mechanic", "technician"]
}

def match_job_to_skills(job: Dict[str, Any], user_skills: List[str], experience_level: str) -> int:
    """
    Calculate match percentage between job and user skills
    
    Args:
        job: Job data
        user_skills: List of user skills
        experience_level: User's experience level
        
    Returns:
        Match percentage (0-100)
    """
    try:
        # Extract job data
        job_skills = job.get('required_skills', [])
        job_experience = job.get('experience_level', 'junior')
        
        if not job_skills or not user_skills:
            return 30  # Default minimum match
        
        # Calculate skills match percentage
        matching_skills = set(s.lower() for s in user_skills) & set(s.lower() for s in job_skills)
        skills_match = 0
        
        if job_skills:
            skills_match = int((len(matching_skills) / len(job_skills)) * 100)
        
        # Experience level conversion
        experience_levels = {'junior': 1, 'mid': 2, 'senior': 3, 'expert': 4}
        user_exp_level = experience_levels.get(experience_level.lower(), 1)
        job_exp_level = experience_levels.get(job_experience.lower(), 1)
        
        # Experience match score
        # If user has higher level, it's good (100%)
        # If user has 1 level below, it's ok (70%)
        # If user has 2+ levels below, it's not a good match (50%)
        exp_match = 100
        if user_exp_level < job_exp_level:
            if job_exp_level - user_exp_level == 1:
                exp_match = 70
            else:
                exp_match = 50
        
        # Calculate final match score - weighted average of skills and experience
        # Skills have higher weight (70%) than experience (30%)
        final_match = int((skills_match * 0.7) + (exp_match * 0.3))
        
        # Cap minimum and maximum match percentage
        return max(30, min(100, final_match))
    
    except Exception as e:
        logger.error(f"Error matching job to skills: {e}")
        return 30  # Default minimum match

def match_jobs_with_ai(profile_text: str, job_keyword: str = "", jobs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Match jobs using AI. Returns list with snake_case keys.
    """
    # Return empty list if no jobs provided
    if not jobs:
        logger.warning("No jobs provided to match_jobs_with_ai")
        return []
    
    logger.info(f"Starting AI job matching (snake_case) with {len(jobs)} jobs, keyword: '{job_keyword}'")
    
    # Clean text - remove excess whitespace and limit length
    clean_profile_text = re.sub(r'\s+', ' ', profile_text).strip()
    clean_job_keyword = re.sub(r'\s+', ' ', job_keyword).strip()
    
    # Truncate if too long
    if len(clean_profile_text) > 6000: # Slightly reduced to make space for keyword and prompt
        clean_profile_text = clean_profile_text[:6000] + "..."
    
    # Extract skills from profile for fallback
    from app.utils.skill_extractor import extract_skills_from_text # Moved here to be used in fallback too
    extracted_profile_skills_data = {}
    try:
        extracted_profile_skills_data = extract_skills_from_text(clean_profile_text)
        skills_for_fallback_matching = extracted_profile_skills_data.get("skills", [])
        experience_for_fallback = extracted_profile_skills_data.get("experience_level", "junior")
        logger.info(f"Extracted skills for fallback: {skills_for_fallback_matching}, Experience: {experience_for_fallback}")
    except Exception as e:
        logger.error(f"Error extracting skills for fallback: {e}")
        skills_for_fallback_matching = []
        experience_for_fallback = "junior"

    # Prepare list of job details for AI
    job_data_for_ai = []
    for job in jobs:
        job_data_for_ai.append({
            "id": job.get('id', ''),
            "title": job.get('title', ''),
            "description": job.get('description', '')[:300] + "...",
            "required_skills": job.get('required_skills', []),
            "experience_level": job.get('experience_level', 'junior')
        })
    
    # Define schema for structured output
    schema = {
        "type": "object",
        "properties": {
            "job_matches": {
                "type": "array",
                "description": "List of jobs with match scores.",
                "items": {
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string"
                        },
                        "match_percentage": {
                            "type": "integer"
                        },
                        "reasoning": {
                            "type": "string",
                            "maxLength": 150
                        },
                        "matching_skills": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "missing_skills": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    },
                    "required": ["job_id", "match_percentage", "reasoning", "matching_skills", "missing_skills"]
                }
            },
            "extracted_user_skills": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            }
        },
        "required": ["job_matches", "extracted_user_skills"]
    }
    
    # Prepare prompt for AI
    prompt = f"""Analyze profile and keyword to find matches.
Profile: {clean_profile_text}
Keyword: {clean_job_keyword if clean_job_keyword else "Not specified"}
Job List ({len(job_data_for_ai)}):
{json.dumps(job_data_for_ai, indent=2)}
Instructions: Assess suitability. Determine match_percentage, reasoning, matching_skills, missing_skills. Extract extracted_user_skills. Return up to 10 matches, ordered. Use snake_case keys in JSON output.
    """
    
    # System prompt for AI
    system_prompt = """AI job matching assistant. Match candidates to jobs. Prioritize keyword. Provide reasoning. Output MUST be JSON per schema using snake_case keys. Respond in Polish if input is Polish, else English.
    """
    
    matched_jobs_final_snake = []
    try:
        logger.info("Sending request to AI for job matching (snake_case).")
        ai_results = get_structured_output(prompt, system_prompt, schema)
        
        if "error" in ai_results:
            raise Exception(f"AI service failed: {ai_results.get('details')}")
        
        job_matches_from_ai = ai_results.get("job_matches", [])
        extracted_skills_by_ai = ai_results.get("extracted_user_skills", [])
        logger.info(f"AI extracted {len(extracted_skills_by_ai)} skills: {extracted_skills_by_ai}")
        logger.info(f"AI returned {len(job_matches_from_ai)} job matches.")
        
        if job_matches_from_ai:
            for ai_match in job_matches_from_ai:
                job_id = ai_match.get("job_id")
                original_job_data = next((job for job in jobs if str(job.get("id")) == str(job_id)), None)
                
                if original_job_data:
                    job_result = original_job_data.copy()
                    # Update with AI results (ensure keys match AI output/schema)
                    job_result["match_percentage"] = ai_match.get("match_percentage", 30)
                    job_result["matching_skills"] = ai_match.get("matching_skills", [])
                    job_result["missing_skills"] = ai_match.get("missing_skills", [])
                    job_result["reasoning"] = ai_match.get("reasoning", "No reasoning.")
                    job_result["ai_extracted_user_skills"] = extracted_skills_by_ai
                    matched_jobs_final_snake.append(job_result) # Append directly (already snake_case)
            
            matched_jobs_final_snake.sort(key=lambda x: x.get("match_percentage", 0), reverse=True)
            logger.info(f"Returning {len(matched_jobs_final_snake)} AI-matched jobs (snake_case).")
            return matched_jobs_final_snake

        logger.warning("AI matching returned no results. Falling back.")

    except Exception as e:
        logger.error(f"Error during AI job matching: {e}. Falling back.", exc_info=True)

    # Fallback to simpler matching method using extracted skills if AI fails or returns no results
    logger.info(f"Using fallback (snake_case): {len(skills_for_fallback_matching)} skills, {experience_for_fallback} experience, keyword '{job_keyword}'")
    
    fallback_results_snake = []
    
    # In fallback, if a job_keyword is present, we can still try to filter by it simply
    # This part mimics some of the old keyword filtering for the fallback
    jobs_for_fallback = jobs
    if job_keyword:
        keyword_lower = job_keyword.lower()
        # Expand with synonyms for keyword in fallback
        keyword_synonyms = [keyword_lower]
        for pl_word, en_words in JOB_SYNONYMS.items():
            if keyword_lower == pl_word.lower() or keyword_lower in [w.lower() for w in en_words]:
                keyword_synonyms.extend(en_words)
                keyword_synonyms.append(pl_word)
        keyword_synonyms = list(set([w.lower() for w in keyword_synonyms]))

        temp_filtered_jobs = []
        for job in jobs:
            title = job.get('title', '').lower()
            desc = job.get('description', '').lower()
            job_skills_text = ' '.join(job.get('required_skills', [])).lower()
            
            matched_by_keyword = False
            for syn in keyword_synonyms:
                if syn in title or syn in desc or syn in job_skills_text:
                    matched_by_keyword = True
                    break
            if matched_by_keyword:
                temp_filtered_jobs.append(job)
        jobs_for_fallback = temp_filtered_jobs
        logger.info(f"Fallback keyword filter resulted in {len(jobs_for_fallback)} jobs.")


    if not skills_for_fallback_matching and not job_keyword: # if no skills and no keyword, cannot do much in fallback
         logger.warning("Fallback matching has no skills from profile and no keyword. Returning empty list.")
         return []

    for job in jobs_for_fallback: # Use keyword-filtered jobs if keyword was present
        match_percentage = match_job_to_skills(job, skills_for_fallback_matching, experience_for_fallback)
        
        # Boost score slightly if the job title itself contains the keyword in fallback
        if job_keyword and job_keyword.lower() in job.get('title', '').lower():
            match_percentage = min(100, match_percentage + 10) # Small boost

        if match_percentage >= 30: # Threshold for fallback
            job_result = job.copy()
            job_result["match_percentage"] = match_percentage
            job_result["matching_skills"] = list(set(s.lower() for s in skills_for_fallback_matching) & 
                                             set(s.lower() for s in job.get('required_skills', [])))
            job_result["missing_skills"] = list(set(s.lower() for s in job.get('required_skills', [])) - 
                                            set(s.lower() for s in skills_for_fallback_matching))
            job_result["reasoning"] = "Matched based on basic skill and experience comparison (fallback)."
            fallback_results_snake.append(job_result)
    
    fallback_results_snake.sort(key=lambda x: x["match_percentage"], reverse=True)
    
    logger.info(f"Returning {len(fallback_results_snake)} basic-matched jobs (fallback, snake_case).")
    return fallback_results_snake 