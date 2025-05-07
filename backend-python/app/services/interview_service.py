import uuid
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os
import re
import random

# Add parent directory to path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.ai_service import get_ai_response, get_structured_output

# Configure logging
logger = logging.getLogger(__name__)

# Import storage functionality (placeholder - implement based on your storage solution)
# from services.data_service import save_interview, get_interview, update_interview

# Forbidden topics for filtering
FORBIDDEN_TOPICS = [
    "żart", "dowcip", "śmieszne", "zabawne", "memy", "śmiech", "hehehe", "haha",
    "nieprzyzwoite", "seks", "erotyka", "alkohol", "narkotyki", "wojna", "polityka",
    "religia", "kontrowersje", "obraza"
]

def filter_inappropriate_content(text: str) -> bool:
    """
    Filter inappropriate content from user input
    
    Args:
        text: Text to filter
        
    Returns:
        bool: True if text contains inappropriate content, False otherwise
    """
    text_lower = text.lower()
    for topic in FORBIDDEN_TOPICS:
        if topic in text_lower:
            return True
    return False

def create_interview_system_prompt(job_title: str, company_name: Optional[str] = "Not Specified", job_description: Optional[str] = "", required_skills: Optional[List[str]] = None) -> str:
    """
    Creates a generic system prompt for an AI acting as an interviewer for a specific role.
    This prompt is used when the AI needs to ask a question or react.
    """
    company_context = f" at {company_name}" if company_name else ""
    description_context = f"\nKey responsibilities and technologies might include: {job_description[:200]}..." if job_description else ""
    skills_context = f"\nKey required skills are: {', '.join(required_skills)}" if required_skills else ""

    return f"""You are a friendly, professional, and engaging AI hiring manager conducting a technical interview for the {job_title} role{company_context}.
Your goal is to assess the candidate's technical skills and problem-solving abilities relevant to this role.
{description_context}
{skills_context}
Maintain a conversational tone. Ask one question at a time. Wait for the candidate's response before proceeding.
Keep your responses concise and focused on the interview.
Respond in Polish, using natural Polish phrasing.
NEVER include <think> tags in your responses.
"""

def generate_interview_questions(job_data: Dict[str, Any], skills: List[str], experience_level: str, difficulty: str = "medium", num_questions: int = 5) -> List[str]:
    """
    Generate a list of interview questions using AI based on job data and candidate profile.
    Args:
        job_data: Job details (title, description, required_skills).
        skills: Candidate's skills (can be empty).
        experience_level: Candidate's experience level.
        difficulty: Desired difficulty (easy, medium, hard).
        num_questions: Number of questions to generate.
    Returns:
        A list of question strings.
    """
    job_title = job_data.get('title', 'the specified role')
    job_description = job_data.get('description', '')
    required_skills = job_data.get('required_skills', [])

    schema = {
        "type": "object",
        "properties": {
            "interview_questions": {
                "type": "array",
                "description": f"A list of exactly {num_questions} distinct technical interview questions for a {job_title} candidate with {experience_level} experience, considering these skills: {', '.join(skills if skills else ['general relevant skills'])}. Difficulty: {difficulty}. Questions should be in Polish.",
                "items": {"type": "string"}
            }
        },
        "required": ["interview_questions"]
    }

    prompt = f"""Please generate {num_questions} distinct technical interview questions for a candidate applying for the role of {job_title}.
Candidate's stated experience level: {experience_level}.
Candidate's known skills: {', '.join(skills) if skills else 'Not specified, focus on general skills for the role.'}
Job required skills: {', '.join(required_skills) if required_skills else 'General for the role.'}
Job description snippet: {job_description[:300]}...

Desired difficulty for questions: {difficulty}.
Focus on questions that assess problem-solving abilities and practical knowledge.
Ensure questions are in Polish.
"""
    
    system_prompt = "You are an AI assistant specialized in generating high-quality technical interview questions. Provide the output in the specified JSON format. Questions should be in Polish."
    
    try:
        logger.info(f"Generating {num_questions} interview questions for {job_title} ({difficulty}).")
        response = get_structured_output(prompt, system_prompt, schema)
        if response and "interview_questions" in response and isinstance(response["interview_questions"], list):
            questions = response["interview_questions"]
            logger.info(f"Successfully generated {len(questions)} questions.")
            return questions[:num_questions] # Ensure correct number of questions
        else:
            logger.error(f"Failed to generate interview questions in expected format. Response: {response}")
            return [f"Placeholder question: Describe a challenging project involving {random.choice(required_skills) if required_skills else 'your technical skills'}?"] * num_questions
    except Exception as e:
        logger.error(f"Error generating interview questions: {e}")
        return [f"Placeholder technical question about {job_title} (due to generation error)."] * num_questions

def analyze_interview_responses(
    user_responses: List[str], 
    job_title: str, 
    job_description: Optional[str] = "", 
    required_skills: Optional[List[str]] = None,
    questions_asked: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze user responses from an interview and provide feedback.
    Args:
        user_responses: List of user's answers.
        job_title: Title of the job for context.
        job_description: Brief description of the job.
        required_skills: List of skills for the job.
        questions_asked: The actual questions that were asked.
    Returns:
        Dictionary with performance analysis (strengths, areas_for_improvement, overall_feedback).
    """
    if not user_responses:
        return {"error": "No responses to analyze."}

    responses_text = ""
    if questions_asked and len(questions_asked) == len(user_responses):
        for i, question in enumerate(questions_asked):
            responses_text += f"Pytanie {i+1}: {question}\nOdpowiedź kandydata {i+1}: {user_responses[i]}\n\n"
    else:
        for i, response in enumerate(user_responses):
            responses_text += f"Odpowiedź kandydata {i+1}: {response}\n\n"

    job_context = f" stanowisko {job_title}."
    if job_description:
        job_context += f" Opis stanowiska: {job_description[:300]}..."
    if required_skills:
        job_context += f" Wymagane umiejętności: {', '.join(required_skills)}."

    schema = {
        "type": "object",
        "properties": {
            "strengths": {
                "type": "array",
                "description": "Observed strengths in the candidate's answers. (In Polish)",
                "items": {"type": "string"}
            },
            "areas_for_improvement": {
                "type": "array",
                "description": "Areas where the candidate's answers could be improved or were lacking. (In Polish)",
                "items": {"type": "string"}
            },
            "overall_feedback": {
                "type": "string",
                "description": "A concise overall summary and feedback for the candidate. (In Polish)"
            },
            "suggested_next_steps": {
                "type": "array",
                "description": "Suggestions for the candidate to improve or learn more. (In Polish)",
                "items": {"type": "string"}
            }
        },
        "required": ["strengths", "areas_for_improvement", "overall_feedback"]
    }

    prompt = f"""Przeanalizuj poniższy transkrypt odpowiedzi kandydata z rozmowy kwalifikacyjnej na{job_context}

Transkrypt odpowiedzi:
{responses_text}

Twoim zadaniem jest ocena tych odpowiedzi. Zidentyfikuj:
1.  Mocne strony wypowiedzi kandydata (strengths).
2.  Obszary, w których odpowiedzi mogłyby być lepsze lub czegoś brakowało (areas_for_improvement).
3.  Sformułuj ogólną opinię i podsumowanie (overall_feedback).
4.  Zaproponuj konkretne następne kroki lub tematy do nauki dla kandydata (suggested_next_steps).

Informacje zwrotne powinny być konstruktywne, profesjonalne i pomocne dla kandydata.
Odpowiedz w języku polskim.
"""
    
    system_prompt = "Jesteś doświadczonym menedżerem HR specjalizującym się w analizie rozmów kwalifikacyjnych i udzielaniu feedbacku. Odpowiedź musi być w formacie JSON zgodnym z podanym schematem, w języku polskim."

    try:
        logger.info(f"Analyzing {len(user_responses)} interview responses for {job_title}.")
        analysis = get_structured_output(prompt, system_prompt, schema)
        if analysis and "strengths" in analysis and "areas_for_improvement" in analysis and "overall_feedback" in analysis:
            logger.info("Successfully analyzed interview responses.")
            return analysis
        else:
            logger.error(f"Failed to analyze responses in expected format. Response: {analysis}")
            return {"error": "Analysis failed to produce expected fields.", "details": analysis}

    except Exception as e:
        logger.error(f"Error analyzing interview responses: {e}")
        return {"error": str(e)}

# Old functions (to be reviewed or removed if not used by new flow)
# def create_safe_prompt_for_interview(job_title: str, skills: List[str], experience_level: str) -> str:
#     # This prompt might be too generic for the new one-by-one question flow. 
#     # We'll use more specific system prompts directly in app.py for controlling the AI's role turn-by-turn.
#     return f"""Jesteś rekruterem AI prowadzącym rozmowę kwalifikacyjną na stanowisko {job_title}.
#     Twoim zadaniem jest ocena umiejętności technicznych kandydata w odniesieniu do tego stanowiska.
#     Doświadczenie kandydata: {experience_level}. Umiejętności kandydata: {', '.join(skills) if skills else 'nie określono'}.
#     Pytaj o konkretne aspekty techniczne, problemy do rozwiązania, lub poproś o wyjaśnienie konceptów.
#     Zadawaj pytania jedno po drugim. Odpowiadaj wyłącznie w języku polskim.
#     Twoje odpowiedzi powinny być zwięzłe i profesjonalne.
#     NEVER include <think> tags in your responses.
#     """

def filter_inappropriate_content(text: str) -> bool:
    """Basic filter for inappropriate content."""
    inappropriate_keywords = ["example_bad_word1", "example_bad_word2"] # Add more comprehensive list
    if any(keyword in text.lower() for keyword in inappropriate_keywords):
        logger.warning(f"Inappropriate content detected: {text[:100]}...")
        return True
    return False 