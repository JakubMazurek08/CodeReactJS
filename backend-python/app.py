from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context
from flask_cors import CORS
import requests
import logging
import json
import os
import time
import re
import traceback
import uuid
from datetime import datetime
import threading
import random
import tempfile
import PyPDF2
from pdf2image import convert_from_path
from werkzeug.utils import secure_filename
import pytesseract
from app.services.flashcard_service import generate_flashcards_from_text

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
UPLOAD_FOLDER = tempfile.gettempdir()  # Use system temp directory
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
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
        ai_messages = []
        user_messages = []

        # Track vague answers from the user
        vague_answer_count = 0
        vague_answers = []

        # Define vague response patterns
        vague_patterns = [
            r"(?i)yes i know",
            r"(?i)^yes$",
            r"(?i)i know that",
            r"(?i)i am familiar with",
            r"(?i)i have experience",
            r"(?i)i understand",
            r"(?i)sounds good",
            r"(?i)of course",
            r"(?i)definitely",
            r"(?i)certainly",
            r"(?i)absolutely",
            r"(?i)^sure$",
            r"(?i)^okay$",
            r"(?i)^ok$",
            r"(?i)^i do$"
        ]

        # Get all AI messages and user messages for tracking
        for i, msg in enumerate(messages):
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
                user_message = msg.get('message', '')
                user_messages.append(user_message)

                # Check if this user message came right after an AI message with a question
                if i > 0 and not messages[i-1].get('isUser', True) and "?" in messages[i-1].get('message', ''):
                    # Check if the response is vague
                    is_vague = False
                    for pattern in vague_patterns:
                        if re.search(pattern, user_message):
                            is_vague = True
                            break

                    # Check if response is too short (less than 20 characters)
                    if len(user_message.strip()) < 20:
                        is_vague = True

                    # Check if response lacks technical details
                    contains_technical_detail = False
                    for skill in required_skills:
                        if skill.lower() in user_message.lower():
                            contains_technical_detail = True
                            break

                    for keyword in tech_keywords:
                        if keyword.lower() in user_message.lower():
                            contains_technical_detail = True
                            break

                    # If AI asked a technical question but response lacks technical details
                    if is_technical and not contains_technical_detail and len(user_message.strip()) < 50:
                        is_vague = True

                    if is_vague:
                        vague_answer_count += 1
                        vague_answers.append(user_message)

        # Force the end of the interview after enough exchanges
        # This is a fallback for cases where question counting doesn't work
        force_end = len(ai_messages) >= 10

        # Log for debugging
        logger.info(f"Technical questions asked: {technical_questions_asked}")
        logger.info(f"Total AI messages: {len(ai_messages)}")
        logger.info(f"Force end: {force_end}")
        logger.info(f"Vague answers: {vague_answer_count}")


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
        - Be friendly but professional - an effective technical interviewer
        - Always acknowledge the candidate's responses before asking your next question
        - If the candidate gives a vague or insufficient answer, politely ask for specific examples or more details
        - Don't be satisfied with answers like "Yes, I know that" or "I have experience with that" - push for concrete examples
        - Vary your phrasing and speaking style to sound natural
        - Use conversational language, contractions, and casual transitions when appropriate

        INTERVIEW GUIDELINES:
        1. Keep the conversation flowing naturally like a real interview
        2. Ask one question at a time about the candidate's experience with {skills_text}
        3. If the candidate gives a detailed answer, show interest before moving to your next question
        4. If the candidate says "I don't know" to a question, acknowledge it and move to a different question
        5. If the candidate gives a vague answer (like "Yes, I know that"), ask for specific examples or more details
        6. Ask a mix of technical questions, scenario-based questions, and experience questions
        7. Never repeat a question you've already asked
        8. Always respond in English
        9. Keep track of vague answers and penalize them in the final evaluation

        Previous questions asked (DO NOT repeat these):
        {previous_questions}

        Vague answers given by the candidate (push for better answers on new questions):
        {vague_answers}

        INTERVIEW STRUCTURE:
        - You will ask a total of 5 technical questions throughout the interview
        - You have asked {technical_questions_asked} technical questions so far
        - The candidate has given {vague_answer_count} vague answers so far
        - After the 5th question and the candidate's response, end the interview
        """

        end_summary = {}
        # End if 5+ technical questions or force end due to message count
        if (technical_questions_asked >= 5 or force_end) and len(messages) >= 2 and messages[-1].get('isUser', False):
            # Generate summary as JSON instead of string
            summary_prompt = f"""
            You are an AI evaluating a technical interview for a {job_title} position at {company}.

            The interview has concluded, and now you need to evaluate the candidate based on their answers.

            Required Skills for the position: {skills_text}

            CRITICAL EVALUATION INSTRUCTIONS:
            1. Carefully analyze the depth and specificity of answers
            2. Penalize vague answers significantly - if the candidate gave {vague_answer_count} vague answers, their rating should be reduced by at least {vague_answer_count * 10} points
            3. Look for specific examples and technical details in the answers
            4. Be strict in evaluating whether the candidate demonstrated actual knowledge
            5. Be especially critical of answers that just say "Yes, I know that" without elaboration
            6. If most answers are vague or lack depth, the candidate should not pass
            7. To pass, a candidate must demonstrate actual knowledge, not just claim to have it
            8. Rating should reflect demonstrated skill, not just claimed experience

            IMPORTANT: You must produce a JSON object with the following fields:
            1. "passed": a boolean indicating if the candidate passed the interview (true/false)
            2. "rating": a number from 1 to 100 representing the candidate's performance
            3. "improvements": an array of strings with at least 2 specific areas where the candidate could improve
            4. "summary": a detailed paragraph evaluating the candidate's performance
            5. "learning_roadmap": an object with the following structure:
               a. "key_areas": an array of 3-5 strings representing specific skills or topics the candidate should focus on
               b. "resources": an array of objects, each representing a learning resource with:
                  - "title": string - name of the resource
                  - "type": string - one of "article", "course", "book", "video", or "practice"
                  - "description": string - brief description of the resource
                  - "difficulty": string - one of "beginner", "intermediate", or "advanced"
                  - "url": string (optional) - a URL to a general learning platform like Coursera, Udemy, etc.
               c. "suggested_timeline": string - a brief timeline for learning these skills

            Based on the candidate's performance in the interview, create a personalized learning roadmap to help them improve in areas where they struggled.

            Here is the conversation between the interviewer and the candidate to evaluate:
            {json.dumps(messages, indent=2)}

            Important evaluation factors:
            - The candidate gave {vague_answer_count} vague answers during the interview
            - Vague answers should significantly reduce their score
            - If more than 2 answers were vague, the candidate should likely not pass

            Analyze their answers carefully. Evaluate technical knowledge, communication skills, and relevant experience.
            If they frequently said "I don't know" or gave vague or incorrect answers, they should receive a lower score and not pass.
            If they demonstrated good understanding of the required skills with specific examples, they should receive a higher score and likely pass.

            Return ONLY the JSON object with these fields and nothing else.
            """

            # Try to get a structured output for the summary
            try:
                # Define the schema for structured output
                json_schema = {
                    "type": "object",
                    "properties": {
                        "passed": {"type": "boolean"},
                        "rating": {"type": "integer", "minimum": 1, "maximum": 100},
                        "improvements": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"},
                        "learning_roadmap": {
                            "type": "object",
                            "properties": {
                                "key_areas": {"type": "array", "items": {"type": "string"}},
                                "resources": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "title": {"type": "string"},
                                            "type": {"type": "string", "enum": ["article", "course", "book", "video", "practice"]},
                                            "description": {"type": "string"},
                                            "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
                                            "url": {"type": "string"}
                                        },
                                        "required": ["title", "type", "description", "difficulty"]
                                    }
                                },
                                "suggested_timeline": {"type": "string"}
                            },
                            "required": ["key_areas", "resources", "suggested_timeline"]
                        }
                    },
                    "required": ["passed", "rating", "improvements", "summary", "learning_roadmap"]
                }

                # Get structured JSON output
                summary_response = get_structured_output(
                    prompt=f"Evaluate this technical interview with {vague_answer_count} vague responses out of {len(user_messages)} total responses",
                    system_prompt=summary_prompt,
                    schema=json_schema
                )


                # Check if we got a valid response
                if isinstance(summary_response, dict) and "passed" in summary_response:
                   end_summary = summary_response

                   # Ensure the rating reflects vague answers
                   if vague_answer_count > 0:
                       # Decrease rating based on vague answers
                       end_summary["rating"] = max(0, min(end_summary["rating"], 100 - (vague_answer_count * 10)))

                       # If 3 or more vague answers, candidate should not pass
                       if vague_answer_count >= 3:
                           end_summary["passed"] = False

                   # Ensure improvements mention vague answers if they were an issue
                   if vague_answer_count > 0 and not any("specific" in imp.lower() or "detail" in imp.lower() or "vague" in imp.lower() or "elaborate" in imp.lower() for imp in end_summary.get("improvements", [])):
                       if "improvements" not in end_summary:
                           end_summary["improvements"] = []
                       end_summary["improvements"].append("Provide specific examples and details rather than vague answers")

                   # Debug the learning_roadmap structure
                   logger.info(f"Raw summary response: {json.dumps(summary_response, indent=2)}")

                   if "learning_roadmap" not in end_summary:
                       logger.error("learning_roadmap field is missing entirely")
                   elif not end_summary["learning_roadmap"]:
                       logger.error("learning_roadmap field is empty or null")
                   elif "resources" not in end_summary["learning_roadmap"]:
                       logger.error("resources field is missing from learning_roadmap")
                   elif not end_summary["learning_roadmap"]["resources"]:
                       logger.error("resources array is empty")
                       # Force the resources array to contain expected data
                       end_summary["learning_roadmap"]["resources"] = [
                           {
                               "title": f"{job_title} Technical Interview Guide",
                               "type": "course",
                               "description": f"A comprehensive course on {job_title} interview preparation",
                               "difficulty": "intermediate",
                               "url": "https://www.udemy.com"
                           }
                       ]
                   else:
                       logger.info(f"resources array contains {len(end_summary['learning_roadmap']['resources'])} items")
                else:
                    # Fallback if structured output fails
                    logger.warning(f"Failed to get structured interview summary: {summary_response}")
                    # Create a basic fallback summary with learning roadmap
                    end_summary = {
                        "passed": vague_answer_count < 3 and "don't know" not in " ".join(user_messages).lower().count(),
                        "rating": max(0, 65 - (vague_answer_count * 10)),
                        "improvements": [
                            "Provide specific technical details rather than vague answers",
                            "Share real-world examples from past experience",
                            "Demonstrate deeper knowledge of the technologies mentioned"
                        ],
                        "summary": f"The candidate interviewed for the {job_title} position but gave {vague_answer_count} vague answers without sufficient technical detail. This suggests they may not have the depth of knowledge required for this role.",
                        "learning_roadmap": {
                            "key_areas": ["Technical fundamentals", "Interview preparation", "Practical experience"],
                            "resources": [
                                {
                                    "title": f"{job_title} fundamentals",
                                    "type": "course",
                                    "description": "A course covering the core concepts needed for this role",
                                    "difficulty": "beginner",
                                    "url": "https://www.coursera.org"
                                },
                                {
                                    "title": "Technical interview preparation",
                                    "type": "book",
                                    "description": "Guide to answering common technical questions",
                                    "difficulty": "intermediate",
                                    "url": "https://www.amazon.com"
                                }
                            ],
                            "suggested_timeline": "2-4 weeks of focused study and practice"
                        }
                    }
            except Exception as summary_error:
                logger.error(f"Error generating structured summary: {summary_error}")
                # Fallback in case of errors
                end_summary = {
                    "passed": vague_answer_count < 3,
                    "rating": max(10, 70 - (vague_answer_count * 15)),
                    "improvements": ["Provide specific examples rather than vague answers", "Demonstrate deeper knowledge of required technologies"],
                    "summary": f"The candidate interviewed for the {job_title} position and gave {vague_answer_count} vague answers, suggesting they may not have the depth of knowledge required for this role.",
                    "learning_roadmap": {
                        "key_areas": ["Core technologies", "Communication skills", "Technical depth"],
                        "resources": [
                            {
                                "title": "Technical documentation",
                                "type": "article",
                                "description": "Read official documentation for required technologies",
                                "difficulty": "intermediate"
                            }
                        ],
                        "suggested_timeline": "1-2 weeks of study"
                    }
                }

            # Add to system prompt
            system_prompt += "\n\nIMPORTANT: This is the FINAL message of the interview. You MUST end the interview now with a closing statement. DO NOT ask any more questions."

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

            # Check if the user gave a vague answer
            is_vague_response = False
            for pattern in vague_patterns:
                if re.search(pattern, user_input):
                    is_vague_response = True
                    break

            # Also check if response is too short
            if len(user_input.strip()) < 20:
                is_vague_response = True

            # Check if the user said they don't know
            if "dont know" in user_input.lower() or "don't know" in user_input.lower():
                # Add special instruction to move on
                system_prompt += "\n\nIMPORTANT: The candidate just indicated they don't know the answer. Acknowledge this briefly and move on to a completely different question. DO NOT repeat the same question or stay on the same topic."
            elif is_vague_response:
                # Add special instruction to ask for more details
                system_prompt += f"\n\nIMPORTANT: The candidate just gave a vague answer: '{user_input}'. Politely but firmly ask for specific examples or more technical details. Tell them you need concrete examples to evaluate their knowledge. DO NOT accept this vague answer and move on. Press for specifics."

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

        # Log for debugging what we're returning
        logger.info(f"Returning endSummary: {bool(end_summary)}")
        if end_summary:
            logger.info(f"EndSummary contains learning_roadmap: {'learning_roadmap' in end_summary}")

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

        

@app.route("/api/extract-pdf", methods=["POST"])
def extract_pdf():
    """Endpoint to extract text from uploaded PDF file and analyze it with AI"""
    # Check if the post request has the file part
    if 'pdf_file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400
    
    file = request.files['pdf_file']
    
    # If user does not select file, browser might send an empty file
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Check if it's a PDF file
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Invalid file format. Only PDF files are allowed."}), 400
    
    try:
        # Save the file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text with pdfminer.six (you'll need to install this)
        # pip install pdfminer.six
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.pdfdocument import PDFDocument
            from pdfminer.pdfparser import PDFParser
            
            # Extract text with more aggressive settings
            text = ""
            with open(filepath, 'rb') as file:
                # Try with default settings first
                text = extract_text(file)
                
                if not text.strip():
                    # If that fails, try with more aggressive settings
                    file.seek(0)  # Reset file pointer
                    parser = PDFParser(file)
                    doc = PDFDocument(parser)
                    
                    # Check if PDF has extraction restrictions
                    if not doc.is_extractable:
                        logger.warning(f"PDF {filename} has extraction restrictions")
                    
                    # Try again with more aggressive settings
                    file.seek(0)  # Reset file pointer
                    text = extract_text(file, laparams=None)  # Try without layout analysis
                
                if not text.strip():
                    # Try with PyPDF2 as a fallback
                    file.seek(0)  # Reset file pointer
                    pdf_reader = PyPDF2.PdfReader(file)
                    fallback_text = ""
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        page_text = page.extract_text()
                        if page_text:
                            fallback_text += page_text + "\n\n"
                    
                    if fallback_text.strip():
                        text = fallback_text
            
            # If still no text, return an error
            if not text.strip():
                logger.warning(f"Failed to extract text from {filename} with all methods")
                return jsonify({
                    "error": "Could not extract text from PDF. The file may be secured or contain only images.",
                    "error_type": "extraction_failed",
                    "suggestions": [
                        "Try uploading a PDF with extractable text content",
                        "Use a PDF that was created directly from a word processor rather than a design program",
                        "Check if the PDF contains actual text rather than images of text"
                    ]
                }), 200
            
            # Process text with AI
            logger.info(f"Successfully extracted {len(text)} characters from {filename}")
            
            # Prepare system prompt for CV analysis
            system_prompt = """
            You are a professional CV and resume analyzer. Your task is to extract key information 
            from the given text which comes from a PDF resume or CV. Analyze the text carefully 
            and extract the following information:
            
            1. Create a concise summary of the candidate's professional profile and experience
            2. Identify the main professional role of the candidate based on their experience
            3. Determine what type of job they might be seeking based on their background
            4. Extract the most important technical and soft skills
            5. Extract the most important technologies they've worked with
            6. Extract programming languages they know
            7. Extract frameworks they've used
            8. Extract tools they're familiar with
            9. Extract certifications they have
            10. Extract major projects they've worked on
            
            Provide this information in a structured JSON format with the following keys:
            - user_summary: A concise paragraph about the candidate's background and strengths
            - user_role: An array of their primary and secondary professional roles
            - job: The type of position they appear to be qualified for
            - skills: A comma-separated string of their key skills (both technical and soft)
            
            Only include information that is actually present or can be confidently inferred from the text.
            If the document is too long, summarize it and extract the most important information.
            If the document is too short, provide a detailed analysis of the text.
            If the document is in a different language, translate it to English and then analyze it.
            If the document contains any personal information, remove it before analyzing.
            If the document contains any sensitive information, remove it before analyzing.
            If the document contains any confidential information, remove it before analyzing.
            If the document contains any illegal information, remove it before analyzing.
            If the document contains any offensive information, remove it before analyzing.
            If the document contains any spam information, remove it before analyzing.
            If the document contains any irrelevant information, remove it before analyzing.
            If the document contains any duplicate information, remove it before analyzing.
            If the document contains any misleading information, remove it before analyzing.
            If the document contains any false information, remove it before analyzing.
            If the document contains any outdated information, remove it before analyzing.
            Provide this information in a structured format.
            """
            
            # Define schema for structured output
            json_schema = {
                "type": "object", 
                "properties": {
                    "user_summary": {"type": "string"},
                    "user_role": {"type": "array", "items": {"type": "string"}},
                    "job": {"type": "string"},
                    "skills": {"type": "string"}
                },
                "required": ["user_summary", "user_role", "job", "skills"]
            }
            
            # Call AI service for CV analysis
            structured_analysis = get_structured_output(
                prompt=f"Analyze this resume/CV text and extract key information: {text[:3000]}...",
                system_prompt=system_prompt,
                schema=json_schema
            )
            
            # Process and return the AI analysis
            if isinstance(structured_analysis, dict) and "user_summary" in structured_analysis:
                logger.info(f"Successfully analyzed CV for {filename}")
                return jsonify({
                    "success": True,
                    "text": text[:5000] + ("..." if len(text) > 5000 else ""),
                    "analysis": structured_analysis
                })
            else:
                # Fallback if structured output fails
                logger.warning(f"Problem with AI structured output: {structured_analysis}")
                
                # Try getting a regular AI response as fallback
                ai_response = get_ai_response(
                    prompt=f"Analyze this resume/CV text and extract key information: {text[:3000]}...",
                    system_prompt=system_prompt
                )
                
                return jsonify({
                    "success": True,
                    "text": text[:5000] + ("..." if len(text) > 5000 else ""),
                    "raw_analysis": ai_response
                })
                
        except Exception as e:
            logger.error(f"Error in PDF processing: {str(e)}", exc_info=True)
            return jsonify({"error": f"Error processing PDF: {str(e)}"}), 500
        
        finally:
            # Remove temporary file
            try:
                if os.path.exists(filepath):
                    os.unlink(filepath)
            except Exception as cleanup_error:
                logger.warning(f"Error removing temporary file: {str(cleanup_error)}")
    
    except Exception as e:
        logger.error(f"Error handling uploaded file: {str(e)}", exc_info=True)
        return jsonify({"error": f"Error processing file: {str(e)}"}), 500
@app.route('/api/flashcards', methods=['POST'])
def generate_flashcards_endpoint():
    """
    Endpoint to generate flashcards from a given text.
    
    Request parameters:
    - text: The text content to generate flashcards from (required)
    - category: Optional category to focus the flashcards on (e.g., "technical", "behavioral")
    - max_cards: Optional maximum number of flashcards to generate (default 10)
    - min_length: Optional minimum character length for answers (default 50)
    - max_length: Optional maximum character length for answers (default 250)
    
    Returns:
    - JSON object containing generated flashcards and metadata
    """
    data = request.json or {}
    text = data.get('text', '')
    category = data.get('category')
    max_cards = min(int(data.get('max_cards', 10)), 20)  # Cap at 20 cards maximum
    
    # Validate input
    if not text:
        return jsonify({"error": "Missing text for flashcard generation"}), 400
    
    if len(text) < 50:
        return jsonify({
            "error": "Text is too short for meaningful flashcard generation",
            "suggestions": [
                "Provide a longer text with more substantial content",
                "Try uploading a complete document or transcript"
            ]
        }), 400
    
    try:
        # Import here to avoid circular imports
        from app.services.flashcard_service import generate_flashcards_from_text
        
        # Generate flashcards
        logger.info(f"Generating flashcards from text ({len(text)} chars), category: {category}")
        flashcards = generate_flashcards_from_text(text, category)
        
        # Filter and format the flashcards
        if flashcards:
            # Filter based on length constraints if specified
            min_length = int(data.get('min_length', 50))
            max_length = int(data.get('max_length', 250))
            
            filtered_cards = []
            for card in flashcards:
                # Filter based on answer length
                answer_length = len(card.get('answer', ''))
                if answer_length >= min_length and answer_length <= max_length:
                    filtered_cards.append(card)
                    
                # Stop once we have enough cards
                if len(filtered_cards) >= max_cards:
                    break
            
            # Use the filtered cards, or all cards if none passed the filter
            final_cards = filtered_cards if filtered_cards else flashcards[:max_cards]
            
            # Add timestamps
            current_time = time.time()
            for card in final_cards:
                card['created_at'] = current_time
                
            # Save to storage if enabled
            if FIREBASE_ENABLED.lower() == 'true' and data.get('save', False):
                try:
                    # Optional: Save flashcards to storage
                    current_user = auth.current_user
                    if current_user:
                        # Create a flashcards collection entry
                        flashcard_set = {
                            'userId': current_user.uid,
                            'title': data.get('title', 'Generated Flashcards'),
                            'description': data.get('description', f"Generated from text ({len(text)} characters)"),
                            'category': category or 'general',
                            'cards': final_cards,
                            'created_at': serverTimestamp()
                        }
                        
                        # Add to 'flashcards' collection
                        doc_ref = addDoc(collection(db, 'flashcards'), flashcard_set)
                        logger.info(f"Saved flashcard set with ID: {doc_ref.id}")
                except Exception as save_error:
                    logger.error(f"Error saving flashcards: {save_error}", exc_info=True)
                    # Continue even if saving fails
            
            return jsonify({
                "success": True,
                "flashcards": final_cards,
                "total": len(final_cards),
                "source_length": len(text),
                "category": category or "general",
                "message": f"Generated {len(final_cards)} flashcards"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to generate meaningful flashcards",
                "flashcards": [],
                "suggestions": [
                    "Try with different text content",
                    "Ensure the text contains factual or educational content"
                ]
            }), 200
    
    except Exception as e:
        logger.error(f"Error generating flashcards: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": f"Error generating flashcards: {str(e)}",
            "flashcards": []
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