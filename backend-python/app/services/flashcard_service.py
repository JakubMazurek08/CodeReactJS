import logging
import uuid
from typing import Dict, Any, List

from app.services.ai_service import get_structured_output, get_ai_response

logger = logging.getLogger(__name__)

def generate_flashcards_from_interview_result(interview_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate flashcards from interview results using AI.
    
    Args:
        interview_result: Dictionary containing interview results with summary, improvements, etc.
        
    Returns:
        A CardSet object with id, title, description and cards
    """
    try:
        # Extract relevant information from the interview result
        summary = interview_result.get('summary', '')
        improvements = interview_result.get('improvements', [])
        passed = interview_result.get('passed', False)
        rating = interview_result.get('rating', 0)
        
        # Prepare system prompt for flashcard generation
        system_prompt = """
        You are an AI assistant that generates educational flashcards based on interview results.
        Create a set of flashcards with front (question) and back (answer) based on the interview summary and areas for improvement.
        
        Follow these guidelines:
        1. Create concise, focused questions on the front of each card
        2. Provide comprehensive but concise answers on the back of each card
        3. Cover both strengths mentioned in the summary and areas for improvement
        4. Focus on actionable learning points that will help in future interviews
        5. Create between 5-10 flashcards depending on the richness of the content
        
        Format the output as a JSON object with:
        - "id": A unique identifier (use "temp-id", it will be replaced)
        - "title": A descriptive title for the flashcard set
        - "description": A brief description of what the flashcards cover
        - "cards": An array of card objects, each with:
          - "id": A numerical ID for the card (1, 2, 3, etc.)
          - "front": The question or prompt (front of the flashcard)
          - "back": The answer or explanation (back of the flashcard)
        
        Only include information that is present in the provided interview data.
        """
        
        # Define schema for structured output
        json_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "number"},
                            "front": {"type": "string"},
                            "back": {"type": "string"}
                        },
                        "required": ["id", "front", "back"]
                    }
                }
            },
            "required": ["id", "title", "description", "cards"]
        }
        
        # Create the prompt with interview data
        interview_data = f"""
        Interview Summary: {summary}
        
        Areas for Improvement:
        {' '.join([f'- {item}' for item in improvements])}
        
        Interview Result: {'Passed' if passed else 'Failed'}
        Rating: {rating}/100
        """
        
        # Call AI service for flashcard generation
        flashcard_set = get_structured_output(
            prompt=f"Generate educational flashcards from this interview result: {interview_data}",
            system_prompt=system_prompt,
            schema=json_schema
        )
        
        # Replace the temporary ID with a real UUID
        if isinstance(flashcard_set, dict):
            flashcard_set["id"] = str(uuid.uuid4())
        
        return flashcard_set
                
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}", exc_info=True)
        raise e  # Re-raise the exception instead of falling back to default data