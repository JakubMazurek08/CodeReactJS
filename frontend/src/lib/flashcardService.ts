// src/lib/flashcardService.ts
import { auth } from './firebase';

export interface FlashcardData {
    id: number | string;
    front: string;
    back: string;
}

export interface FlashcardSetData {
    id: string;
    title: string;
    description: string;
    cards: FlashcardData[];
}

interface FlashcardRequestPayload {
    summary: string;
    improvements: string[];
    passed: boolean;
    rating: number;
    userId: string;
}

// API endpoint for flashcards
const FLASHCARDS_API_URL = 'localhost:5000/api/generate-flashcards'; // Replace with your actual endpoint

/**
 * Fetches flashcards based on interview summary data
 * @param payload Interview summary data for generating flashcards
 * @returns Promise with the flashcards data
 */
export const fetchFlashcardsFromSummary = async (payload: FlashcardRequestPayload): Promise<FlashcardSetData> => {
    try {
        // Make sure to get the current user ID if not provided
        if (!payload.userId && auth.currentUser) {
            payload.userId = auth.currentUser.uid;
        }

        const response = await fetch(FLASHCARDS_API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to fetch flashcards: ${response.status} ${response.statusText} - ${errorText}`);
        }

        return await response.json() as FlashcardSetData;
    } catch (error) {
        console.error('Error fetching flashcards:', error);
        throw error;
    }
};

/**
 * Handles a fallback when API fails or is unavailable
 * @param interview Data to generate fallback flashcards from
 * @returns A basic set of flashcards
 */
export const generateFallbackFlashcards = (
    jobTitle: string,
    improvements: string[],
    passed: boolean
): FlashcardSetData => {
    // Create basic flashcards from improvements
    const improvementCards = improvements.map((improvement, index) => {
        const improvementText = improvement.toString();
        let question = 'How can you improve in this area?';

        if (improvementText.toLowerCase().includes('knowledge')) {
            question = 'What knowledge gaps should you address?';
        } else if (improvementText.toLowerCase().includes('example')) {
            question = 'What kind of examples should you prepare?';
        } else if (improvementText.toLowerCase().includes('articulate') ||
            improvementText.toLowerCase().includes('communicate')) {
            question = 'How can you better communicate your experience?';
        } else if (improvementText.toLowerCase().includes('technical')) {
            question = 'What technical skills need improvement?';
        }

        return {
            id: `improvement-${index}`,
            front: question,
            back: improvementText
        };
    });

    // Add general cards
    const generalCards: FlashcardData[] = [
        {
            id: 'general-1',
            front: `What key skills are needed for a ${jobTitle} position?`,
            back: 'Technical expertise, communication skills, problem-solving ability, and domain knowledge.'
        },
        {
            id: 'general-2',
            front: 'How should you prepare for your next interview?',
            back: 'Review feedback from this interview, practice answers aloud, research the company, and prepare relevant experience examples.'
        }
    ];

    // Combine all cards
    const allCards = [...improvementCards, ...generalCards];

    return {
        id: `fallback-flashcards-${Date.now()}`,
        title: `${jobTitle} Interview Review`,
        description: 'Key concepts to review from your interview feedback',
        cards: allCards
    };
};