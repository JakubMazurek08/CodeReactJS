from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import requests
import logging
import json
import os
import time
import re
import uuid
from datetime import datetime
import threading
import random

# Import services and utils
from app.services.ai_service import check_ai_server_health, get_ai_response, get_structured_output, AI_MODEL
from app.utils.skill_extractor import extract_skills_from_text
from app.services.interview_service import (
    create_interview_system_prompt,
    analyze_interview_responses,
    generate_interview_questions
)
from app.services.job_matching_service import match_job_to_skills, match_jobs_with_ai

# Import storage interfaces
from app import get_job_storage, get_interview_storage, get_cv_storage, FIREBASE_ENABLED

# Check if Firebase is enabled from environment
os.environ['FIREBASE_ENABLED'] = os.environ.get('FIREBASE_ENABLED', 'false')

# Configure logging
logger = logging.getLogger(__name__)

# Initialize storage interfaces
job_storage = get_job_storage()
interview_storage = get_interview_storage()
cv_storage = get_cv_storage()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Middleware to check AI server status before each request
@app.before_request
def check_server_before_request():
    # Only check for API requests
    if request.path.startswith('/api/') and not request.path.startswith('/api/model/health'):
        check_ai_server_health()

# API routes

@app.route('/api/search', methods=['POST'])
def search_jobs():
    data = request.json
    
    if not data:
        return jsonify({"error": "No input data"}), 400
    
    job_keyword = data.get('job_keyword', '')
    profile_text = data.get('profile_text', '')
    
    logger.info(f"Received search query: keyword={job_keyword}")
    logger.info(f"Profile text length: {len(profile_text)}")
    
    if not job_keyword or not profile_text:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Extract skills and experience level from text
        extracted_data = extract_skills_from_text(profile_text)
        skills = extracted_data.get('skills', [])
        experience = extracted_data.get('experience_level', 'junior')
        
        # Log extracted data
        logger.info(f"Extracted skills: {skills}")
        logger.info(f"Experience level: {experience}")
        
        # If no skills found, return error
        if not skills:
            return jsonify({
                "error": "Failed to extract skills from text",
                "suggestion": "Please provide more details about your technical skills"
            }), 400
        
        # Get jobs from storage
        all_jobs = job_storage.list_jobs(keyword=job_keyword)
        logger.info(f"Found {len(all_jobs)} jobs for keyword: {job_keyword}")
        
        # Match jobs to skills
        results = []
        for job in all_jobs:
            try:
                # Calculate match percentage
                match_percentage = match_job_to_skills(job, skills, experience)
                
                # Accept jobs with match above 30%
                if match_percentage >= 30:
                    job_data = job.copy()
                    job_data['match_percentage'] = match_percentage
                    results.append(job_data)
            except Exception as job_error:
                logger.error(f"Error processing job: {job_error}")
                continue
        
        # Sort results by match percentage (descending)
        results.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        logger.info(f"Found {len(results)} matching jobs with score above 30%")
        
        return jsonify({
            "results": results,
            "extracted_skills": skills,
            "experience_level": experience
        })
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Error searching jobs: {str(e)}"}), 500


@app.route('/api/model/health', methods=['GET'])
def check_models_health():
    """Endpoint to check AI server status"""
    # Force check server status
    server_status = check_ai_server_health(force_check=True)
    
    # Check all servers
    all_servers_status = []
    
    # Assuming OLLAMA_SERVERS is accessible here or redefine
    # from app.services.ai_service import OLLAMA_SERVERS 
    global OLLAMA_SERVERS # Or pass it somehow
    
    for server_url in OLLAMA_SERVERS:
        try:
            start_time = time.time()
            response = requests.get(f"{server_url}/api/tags", timeout=3)
            ping_time = time.time() - start_time
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                available_models = [model.get("name") for model in models]
                
                all_servers_status.append({
                    "server": server_url,
                    "status": "online",
                    "response_time": round(ping_time, 3),
                    "available_models": available_models,
                    "last_checked": time.time()
                })
            else:
                all_servers_status.append({
                    "server": server_url,
                    "status": "error",
                    "error": f"HTTP Error: {response.status_code}",
                    "response_time": round(ping_time, 3),
                    "available_models": [],
                    "last_checked": time.time()
                })
        except Exception as e:
            all_servers_status.append({
                "server": server_url,
                "status": "offline",
                "error": str(e),
                "response_time": 0,
                "available_models": [],
                "last_checked": time.time()
            })
    
    # Calculate statistics
    online_servers = sum(1 for s in all_servers_status if s["status"] == "online")
    
    return jsonify({
        "current_server": server_status['current_server'],
        "current_server_status": server_status,
        "servers": all_servers_status,
        "online_servers": online_servers,
        "total_servers": len(all_servers_status),
        "availability_percentage": round((online_servers / len(all_servers_status)) * 100, 1),
        "timestamp": time.time()
    })


@app.route('/api/match-jobs', methods=['GET', 'POST'])
def match_jobs_with_ai_endpoint():
    """Endpoint to match jobs to profile text using AI"""
    # Handle data from GET or POST
    if request.method == 'POST':
        data = request.json or {}
    else:  # GET
        data = request.args.to_dict()
    
    profile_text = data.get('profile_text', '')
    job_keyword = data.get('job_keyword', '')
    limit = int(data.get('limit', 10))
    
    if not profile_text:
        return jsonify({"error": "Missing user profile description (profile_text)"}), 400
    
    if len(profile_text) < 10:
        return jsonify({"error": "Profile text is too short. Please provide more information."}), 400
        
    try:
        all_jobs = job_storage.list_jobs()
        if not all_jobs:
            return jsonify({
                "message": "No jobs found in database",
                "matches": [],
                "total_matches": 0 # Use snake_case
            })
        
        # match_jobs_with_ai now returns snake_case keys
        matches_snake_case = match_jobs_with_ai(profile_text, job_keyword, all_jobs)
        
        limited_matches = matches_snake_case[:limit]
        
        return jsonify({
            "matches": limited_matches, # Already snake_case
            "total_matches": len(limited_matches), # Use snake_case
            "message": f"Found {len(limited_matches)} matching jobs"
        })
    
    except Exception as e:
        logger.error(f"Error matching jobs: {e}", exc_info=True)
        return jsonify({"error": f"Error matching jobs: {str(e)}"}), 500


@app.route('/api/conversation', methods=['POST'])
def handle_conversation():
    """Endpoint to handle interview conversation with AI"""
    data = request.json

    if not data:
        return jsonify({"error": "No input data"}), 400

    # Extract job information and conversation history
    job = data.get('job')
    messages = data.get('messages', [])

    if not job:
        return jsonify({
            "id": str(uuid.uuid4()),
            "isUser": False,
            "message": "Error: Missing job information"
        }), 400

    try:
        # Create system prompt for interview context
        job_title = job.get('title', 'the position')
        company = job.get('company', 'our company')
        job_description = job.get('description', '')
        required_skills = job.get('required_skills', [])
        experience_level = job.get('experience_level', 'mid')

        # Count technical questions asked (not just messages)
        technical_questions_asked = 0
        previous_questions = []
<<<<<<< HEAD
        ai_messages = []
        user_messages = []

        # Get all AI messages for better tracking
        for msg in messages:
            if not msg.get('isUser', True):
                message_text = msg.get('message', '')
                ai_messages.append(message_text)
                # Count question marks in non-user messages
                if "?" in message_text:
                    # Add to technical questions if not just a greeting
                    # More robust question detection
                    is_technical = False
                    for skill in required_skills:
                        if skill.lower() in message_text.lower():
                            is_technical = True
                            break

                    # Also count questions about programming concepts
                    tech_keywords = ['code', 'programming', 'software', 'database', 'api',
                                    'algorithm', 'function', 'class', 'object', 'method',
                                    'framework', 'library', 'deploy', 'architecture']

                    for keyword in tech_keywords:
                        if keyword.lower() in message_text.lower():
                            is_technical = True
                            break

                    if is_technical:
                        technical_questions_asked += 1
                        previous_questions.append(message_text)
            else:
                # Store user messages for evaluation later
                user_messages.append(msg.get('message', ''))

        # Force the end of the interview after enough exchanges
        # This is a fallback for cases where question counting doesn't work
        force_end = len(ai_messages) >= 10

        # Log for debugging
        logger.info(f"Technical questions asked: {technical_questions_asked}")
        logger.info(f"Total AI messages: {len(ai_messages)}")
        logger.info(f"Force end: {force_end}")
=======
        for i, msg in enumerate(messages):
            if not msg.get('isUser', True) and "?" in msg.get('message', ''):
                # Check if this is likely a technical question (not just a greeting/follow-up)
                message_text = msg.get('message', '').lower()
                if any(tech_term in message_text for tech_term in required_skills):
                    technical_questions_asked += 1
                    previous_questions.append(msg.get('message', ''))
>>>>>>> 80ed8e9634b0d88d7d9c15caa40feaaae6daac16

        # Map experience level to more descriptive text
        experience_map = {
            'junior': 'entry-level (0-2 years)',
            'mid': 'mid-level (3-5 years)',
            'senior': 'senior-level (5+ years)',
            'lead': 'lead/manager level (7+ years)'
        }

        experience_text = experience_map.get(experience_level, 'experienced')

        # Format the required skills as a comma-separated list
        skills_text = ', '.join(required_skills)

        # Build the system prompt
        system_prompt = f"""
        You are an interviewer named PrepJobAI working at {company}, interviewing a candidate for a {experience_text} {job_title} position.

        Job Description: {job_description}

        Required Skills: {skills_text}

        CONVERSATIONAL STYLE:
        - Be friendly, conversational, and personable - not robotic or overly formal
        - Acknowledge the candidate's responses before asking your next question
        - If the candidate says they don't know something, don't repeat the question - move on to a different topic
        - Vary your phrasing and speaking style to sound natural and human-like
        - Use conversational language, contractions (like "you're" instead of "you are"), and casual transitions
        - Start your responses with a brief acknowledgment or comment on what the candidate just said
        - DO NOT start every response with the same phrase like "PrepJobAI from TechCorp"

        INTERVIEW GUIDELINES:
        1. Keep the conversation flowing naturally like a real interview
        2. Ask one question at a time about the candidate's experience with {skills_text}
        3. If the candidate gives a detailed answer, show interest before moving to your next question
        4. If the candidate says "I don't know" to a question, acknowledge it and move to a different question
        5. Ask a mix of technical questions, scenario-based questions, and experience questions
        6. Never repeat a question you've already asked
        7. Always respond in English

        Previous questions asked (DO NOT repeat these):
        {previous_questions}

        INTERVIEW STRUCTURE:
        - You will ask a total of 5 technical questions throughout the interview
        - You have asked {technical_questions_asked} technical questions so far
        - After the 5th question and the candidate's response, end the interview
        """

        # Check if this is the end of the interview
<<<<<<< HEAD
        end_summary = {}
        # End if 5+ technical questions or force end due to message count
        if (technical_questions_asked >= 5 or force_end) and len(messages) >= 2 and messages[-1].get('isUser', False):
            # Generate summary as JSON instead of string
            summary_prompt = f"""
            You are an AI evaluating a technical interview for a {job_title} position at {company}.
=======
        end_summary = ""
        if technical_questions_asked >= 5 and len(messages) >= 2 and messages[-1].get('isUser', False):
            end_summary = f"""
            Thank you for taking the time to interview with us for the {job_title} position at {company}.
            I've enjoyed our conversation about your experience with {', '.join(required_skills[:3])}.
>>>>>>> 80ed8e9634b0d88d7d9c15caa40feaaae6daac16

            The interview has concluded, and now you need to evaluate the candidate based on their answers.

            Required Skills for the position: {skills_text}

            IMPORTANT: You must produce a JSON object with the following fields:
            1. "passed": a boolean indicating if the candidate passed the interview (true/false)
            2. "rating": a number from 1 to 100 representing the candidate's performance
            3. "improvements": an array of strings with at least 2 specific areas where the candidate could improve
            4. "summary": a detailed paragraph evaluating the candidate's performance

            Here is the conversation between the interviewer and the candidate to evaluate:
            {json.dumps(messages, indent=2)}

            Analyze their answers carefully. Evaluate technical knowledge, communication skills, and relevant experience.
            If they frequently said "I don't know" or gave incorrect answers, they should receive a lower score and likely not pass.
            If they demonstrated good understanding of the required skills, they should receive a higher score and likely pass.

            Return ONLY the JSON object with these fields and nothing else.
            """

<<<<<<< HEAD
            # Try to get a structured output for the summary
            try:
                # Define the schema for structured output
                json_schema = {
                    "type": "object",
                    "properties": {
                        "passed": {"type": "boolean"},
                        "rating": {"type": "integer", "minimum": 1, "maximum": 100},
                        "improvements": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    },
                    "required": ["passed", "rating", "improvements", "summary"]
                }

                # Get structured JSON output
                summary_response = get_structured_output(
                    prompt=f"Evaluate this technical interview: {len(user_messages)} responses",
                    system_prompt=summary_prompt,
                    schema=json_schema
                )

                # Check if we got a valid response
                if isinstance(summary_response, dict) and "passed" in summary_response:
                    end_summary = summary_response
                else:
                    # Fallback if structured output fails
                    logger.warning(f"Failed to get structured interview summary: {summary_response}")
                    end_summary = {
                        "passed": False if "don't know" in " ".join(user_messages).lower() else True,
                        "rating": 65,
                        "improvements": ["Be more specific with technical answers", "Provide real-world examples"],
                        "summary": f"The candidate interviewed for the {job_title} position and demonstrated some knowledge of {skills_text}. Further evaluation is recommended."
                    }
            except Exception as summary_error:
                logger.error(f"Error generating structured summary: {summary_error}")
                # Fallback in case of errors
                end_summary = {
                    "passed": True,
                    "rating": 70,
                    "improvements": ["Be more specific with technical answers", "Demonstrate deeper knowledge of required technologies"],
                    "summary": f"The candidate interviewed for the {job_title} position and showed potential. They should be considered for the next round."
                }

            # Add to system prompt
            system_prompt += "\n\nIMPORTANT: This is the FINAL message of the interview. You MUST end the interview now with a closing statement. DO NOT ask any more questions."

=======
>>>>>>> 80ed8e9634b0d88d7d9c15caa40feaaae6daac16
        # Generate AI response based on conversation state
        if not messages:
            # This is the start of the conversation - use a warm, friendly introduction
            prompt = f"I'm here for the {job_title} interview."

            # Call get_ai_response with the right format
            ai_response = get_ai_response(
                prompt=prompt,
                system_prompt=system_prompt
            )
        else:
            # Get the last message from the user
            last_message = messages[-1]

            if not last_message.get('isUser', False):
                # If the last message was not from the user (rare case), use a generic prompt
                user_input = "Please continue the interview."
            else:
                user_input = last_message.get('message', '')

            # Check if the user said they don't know
            if "dont know" in user_input.lower() or "don't know" in user_input.lower():
                # Add special instruction to move on
                system_prompt += "\n\nIMPORTANT: The candidate just indicated they don't know the answer. Acknowledge this briefly and move on to a completely different question. DO NOT repeat the same question or stay on the same topic."

            # Create context from previous messages
            context = []
            for msg in messages[:-1]:  # exclude the last message which we're handling separately
                role = "user" if msg.get('isUser', True) else "assistant"
                context.append({
                    "role": role,
                    "content": msg.get('message', '')
                })

            # Call get_ai_response with the context
            ai_response = get_ai_response(
                prompt=user_input,
                system_prompt=system_prompt,
                context=context
            )

        # Ensure we have an English response
        if ai_response.startswith("Przepraszamy") or "asystent AI" in ai_response:
            # This is an error message in Polish, return an English error
            return jsonify({
                "id": str(uuid.uuid4()),
                "isUser": False,
                "message": "Sorry, there was an error communicating with the AI assistant. Please try again later.",
                "endSummary": {}
            })

        # Return the response with endSummary if needed
        return jsonify({
            "id": str(uuid.uuid4()),
            "isUser": False,
            "message": ai_response,
            "endSummary": end_summary
        })

    except Exception as e:
        logger.error(f"Error in conversation handling: {e}", exc_info=True)
        return jsonify({
            "id": str(uuid.uuid4()),
            "isUser": False,
            "message": f"An unexpected error occurred: {str(e)}",
            "endSummary": {}
        }), 500


# Serve static files
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Background task to check server status
def background_server_check():
    while True:
        try:
            check_ai_server_health()
            time.sleep(300)  # Check every 5 minutes
        except Exception as e:
            logger.error(f"Error in background server check: {e}")
            time.sleep(60)  # On error, wait 1 minute

# Run the application
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    # Start background server check
    background_thread = threading.Thread(target=background_server_check, daemon=True)
    background_thread.start()
    
    # Check AI server status on startup
    status = check_ai_server_health(force_check=True)
    if status['is_online']:
        logger.info(f"AI server available: {status['current_server']}")
        logger.info(f"Available models: {status['available_models']}")
    else:
        logger.warning("AI servers unavailable. Application will retry in background.")
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True) 