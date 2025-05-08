# Import the required services/utilities at the top of your app.py
# from app.services.flashcard_service import generate_flashcards_from_text

# Add this to your app/services directory
# app/services/flashcard_service.py

import logging
from typing import List, Dict, Any, Optional

from app.services.ai_service import get_structured_output, get_ai_response

logger = logging.getLogger(__name__)

def generate_flashcards_from_text(text: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate flashcards from a given text using AI.
    
    Args:
        text: The text to generate flashcards from
        category: Optional category to focus the flashcards on (e.g., "technical", "behavioral")
        
    Returns:
        A list of flashcard objects with 'question' and 'answer' fields
    """
    try:
        # Prepare system prompt for flashcard generation
        category_instruction = ""
        if category:
            if category.lower() == "technical":
                category_instruction = "Focus on technical concepts, coding problems, and technical knowledge."
            elif category.lower() == "behavioral":
                category_instruction = "Focus on behavioral interview questions and soft skills."
            else:
                category_instruction = f"Focus on {category} related concepts and questions."
        
        system_prompt = f"""
        You are an AI assistant that generates educational flashcards based on the provided text.
        Create a set of flashcards with questions and answers based on the content.
        {category_instruction}
        
        Follow these guidelines:
        1. Create concise, focused questions that test understanding of key concepts
        2. Ensure answers are comprehensive but not too lengthy (50-150 words ideal)
        3. Cover various difficulty levels from basic to advanced concepts
        4. Include a mix of factual recall and applied understanding questions
        5. Ensure questions are clear and unambiguous
        6. Organize flashcards in a logical progression if possible
        7. Create between 5-10 flashcards depending on the richness of the content
        
        Format the output as a JSON array of objects, each with:
        - "question": The flashcard question (required)
        - "answer": The answer to the question (required)
        - "difficulty": The difficulty level ("easy", "medium", or "hard") (required)
        - "category": A category for the flashcard based on the content (required)
        - "tags": An array of relevant tags for the flashcard (required)
        
        Only include information that is actually present in the text.
        """
        
        # Define schema for structured output
        json_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "answer": {"type": "string"},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "category": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["question", "answer", "difficulty", "category", "tags"]
            }
        }
        
        # Truncate text if too long
        max_text_length = 3000
        truncated_text = text[:max_text_length] + ("..." if len(text) > max_text_length else "")
        
        # Call AI service for flashcard generation
        flashcards = get_structured_output(
            prompt=f"Generate educational flashcards from this text: {truncated_text}",
            system_prompt=system_prompt,
            schema=json_schema
        )
        
        # Check if we got a valid response
        if not isinstance(flashcards, list):
            logger.warning(f"Invalid flashcards format received: {type(flashcards)}")
            # Fallback to basic structure
            return fallback_flashcard_generation(text, category)
        
        # Additional validations
        valid_flashcards = []
        for card in flashcards:
            if isinstance(card, dict) and "question" in card and "answer" in card:
                # Ensure all required fields are present
                card["difficulty"] = card.get("difficulty", "medium")
                card["category"] = card.get("category", "general")
                card["tags"] = card.get("tags", [])
                # Add a unique ID for each flashcard
                card["id"] = f"card_{hash(card['question']) % 10000}"
                valid_flashcards.append(card)
                
        return valid_flashcards
                
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}", exc_info=True)
        return fallback_flashcard_generation(text, category)

def fallback_flashcard_generation(text: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fallback method to generate basic flashcards when structured output fails.
    
    Args:
        text: The text to generate flashcards from
        category: Optional category to focus on
        
    Returns:
        A list of basic flashcard objects
    """
    try:
        system_prompt = """
        Create 5 simple flashcards from the given text. Format each flashcard as:
        
        Q: [Question]
        A: [Answer]
        
        Make each flashcard focus on a different concept from the text.
        """
        
        truncated_text = text[:2000] + ("..." if len(text) > 2000 else "")
        ai_response = get_ai_response(
            prompt=f"Create 5 simple flashcards from this text: {truncated_text}",
            system_prompt=system_prompt
        )
        
        # Parse the response into flashcards
        flashcards = []
        lines = ai_response.split('\n')
        current_question = None
        current_answer = []
        
        for line in lines:
            line = line.strip()
            if line.startswith("Q:"):
                # Save previous Q&A if exists
                if current_question and current_answer:
                    flashcards.append({
                        "question": current_question,
                        "answer": '\n'.join(current_answer),
                        "difficulty": "medium",
                        "category": category or "general",
                        "tags": [],
                        "id": f"card_{len(flashcards)}"
                    })
                # Start new question
                current_question = line[2:].strip()
                current_answer = []
            elif line.startswith("A:"):
                current_answer.append(line[2:].strip())
            elif current_answer:  # Continue previous answer
                current_answer.append(line)
        
        # Add the last flashcard
        if current_question and current_answer:
            flashcards.append({
                "question": current_question,
                "answer": '\n'.join(current_answer),
                "difficulty": "medium",
                "category": category or "general",
                "tags": [],
                "id": f"card_{len(flashcards)}"
            })
        
        # If parsing failed, create a default set
        if not flashcards:
            flashcards = [
                {
                    "question": "What is the main topic of this text?",
                    "answer": "This text discusses various concepts related to the provided content.",
                    "difficulty": "easy",
                    "category": "general",
                    "tags": ["overview"],
                    "id": "card_default_1"
                },
                {
                    "question": "What are some key points from this text?",
                    "answer": "The text covers several important aspects related to the subject matter.",
                    "difficulty": "medium",
                    "category": "general",
                    "tags": ["key points"],
                    "id": "card_default_2"
                }
            ]
            
        return flashcards
            
    except Exception as e:
        logger.error(f"Error in fallback flashcard generation: {e}", exc_info=True)
        # Return minimal default set
        return [
            {
                "question": "What is this text about?",
                "answer": "This text contains information related to the subject.",
                "difficulty": "easy",
                "category": "general",
                "tags": [],
                "id": "card_default_0"
            }
        ]