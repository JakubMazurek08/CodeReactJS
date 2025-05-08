// src/pages/Interviews.tsx
import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Text } from '../components/Text';
import { Footer } from '../components/Footer';
import { getUserInterviews, type SavedInterview } from '../lib/summaryService.ts';
import { Link } from 'react-router-dom';
import { auth } from '../lib/firebase.ts';
import { InterviewSummary } from "../components/InterviewSummary.tsx";
import { onAuthStateChanged } from 'firebase/auth';
import { FlashcardsSection } from '../components/FlashcardsSection';

// Define interfaces for flashcard data
interface FlashcardData {
    id: number | string;
    front: string;
    back: string;
}

interface FlashcardSetData {
    id: string;
    title: string;
    description: string;
    cards: FlashcardData[];
}

// Add to SavedInterview interface
declare module '../lib/summaryService.ts' {
    interface SavedInterview {
        flashcardSet?: FlashcardSetData;
    }
}

// API endpoint
const FLASHCARDS_API_URL = 'http://localhost:5000/api/generate-flashcards'; // REPLACE WITH YOUR ACTUAL ENDPOINT

export const InterviewPage = () => {
    const [interviews, setInterviews] = useState<SavedInterview[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedInterview, setSelectedInterview] = useState<SavedInterview | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [showFlashcards, setShowFlashcards] = useState<boolean>(false);
    const [isLoadingFlashcards, setIsLoadingFlashcards] = useState<boolean>(false);
    const [flashcardError, setFlashcardError] = useState<string | null>(null);

    // Listen for auth state changes
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            setIsAuthenticated(!!user);
            if (user) {
                fetchInterviews();
            } else {
                setIsLoading(false);
                setInterviews([]);
            }
        });

        return () => unsubscribe();
    }, []);

    // Fetch user's interviews
    const fetchInterviews = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const userInterviews = await getUserInterviews();
            // Sort by date (newest first)
            userInterviews.sort((a, b) => {
                // Handle Firestore timestamps
                const dateA = a.date?.toDate ? a.date.toDate() : new Date(a.date);
                const dateB = b.date?.toDate ? b.date.toDate() : new Date(b.date);
                return dateB.getTime() - dateA.getTime();
            });

            setInterviews(userInterviews);
        } catch (err) {
            console.error("Error fetching interviews:", err);
            setError("Failed to load your interviews. Please try again later.");
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch flashcards for a specific interview - DIRECT API CALL
    const fetchFlashcards = async () => {
        if (!selectedInterview) return;

        // If we already have flashcards for this interview, no need to fetch again
        if (selectedInterview.flashcardSet) {
            setShowFlashcards(true);
            return;
        }

        setIsLoadingFlashcards(true);
        setFlashcardError(null);

        try {
            // Prepare the API request payload
            const payload = {
                summary: selectedInterview.summary.summary,
                improvements: selectedInterview.summary.improvements,
                passed: selectedInterview.summary.passed,
                rating: selectedInterview.summary.rating,
                userId: auth.currentUser?.uid || 'anonymous'
            };

            console.log('Sending flashcard request with payload:', payload);

            // Make the API call
            const response = await fetch(FLASHCARDS_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
            });

            console.log('API Response status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                throw new Error(`API call failed: ${response.status}`);
            }

            // Parse the JSON response
            const flashcardData = await response.json();
            console.log('Received flashcard data:', flashcardData);

            // Update the selected interview with the flashcard data
            const updatedInterview = {
                ...selectedInterview,
                flashcardSet: flashcardData
            };

            // Update state
            setSelectedInterview(updatedInterview);

            // Update the interview in the list
            setInterviews(prevInterviews =>
                prevInterviews.map(interview =>
                    interview.id === selectedInterview.id ? updatedInterview : interview
                )
            );

            // Show flashcards
            setShowFlashcards(true);
        } catch (err) {
            console.error("Error fetching flashcards:", err);
            setFlashcardError(`Failed to load flashcards: ${err instanceof Error ? err.message : String(err)}`);
        } finally {
            setIsLoadingFlashcards(false);
        }
    };

    // Format date for display
    const formatDate = (timestamp: any) => {
        if (!timestamp) return 'Unknown date';

        const date = timestamp?.toDate ? timestamp.toDate() : new Date(timestamp);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    // Toggle between summary and flashcards view
    const toggleFlashcardsView = () => {
        if (!showFlashcards) {
            // Fetch flashcards when switching to flashcards view
            fetchFlashcards();
        } else {
            // Just toggle back to summary
            setShowFlashcards(false);
        }
    };

    return (
        <>
            <Navbar />
            <main className="px-6 py-30 min-h-screen bg-background flex flex-col items-center">
                <div className="w-full max-w-5xl">
                    <Text type="h1" className="mb-6">Your Interview History</Text>

                    {!isAuthenticated ? (
                        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
                            <Text type="h3" className="mb-4">Please Log In</Text>
                            <Text type="p">You need to be logged in to view your interview history.</Text>
                        </div>
                    ) : isLoading ? (
                        <div className="flex justify-center py-12">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                        </div>
                    ) : error ? (
                        <div className="bg-red-50 p-6 rounded-lg border border-red-200 text-red-700">
                            <Text type="p">{error}</Text>
                        </div>
                    ) : interviews.length === 0 ? (
                        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
                            <Text type="h3" className="mb-4">No Interviews Found</Text>
                            <Text type="p" className="mb-6">You haven't completed any interviews yet.</Text>
                            <Link to="/" className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition">
                                Find Jobs to Interview
                            </Link>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* List View */}
                            {!selectedInterview && (
                                <div className="bg-white p-6 rounded-lg shadow-lg">
                                    <Text type="h2" className="mb-4">Recent Interviews</Text>
                                    <div className="overflow-hidden">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                            <tr>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Position
                                                </th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Company
                                                </th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Date
                                                </th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Result
                                                </th>
                                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                            {interviews.map((interview) => (
                                                <tr key={interview.id} className="hover:bg-gray-50">
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm font-medium text-gray-900">{interview.jobTitle}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm text-gray-500">{interview.company}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <div className="text-sm text-gray-500">{formatDate(interview.date)}</div>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap">
                                                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                                            interview.summary.passed
                                                                ? 'bg-green-100 text-green-800'
                                                                : 'bg-red-100 text-red-800'
                                                        }`}>
                                                          {interview.summary.passed ? 'Passed' : 'Needs Improvement'}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                        <button
                                                            onClick={() => {
                                                                setSelectedInterview(interview);
                                                                setShowFlashcards(false);
                                                            }}
                                                            className="text-blue-600 cursor-pointer hover:text-blue-900"
                                                        >
                                                            View Details
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {/* Detail View */}
                            {selectedInterview && (
                                <div>
                                    <div className="flex justify-between items-center mb-6">
                                        <button
                                            onClick={() => setSelectedInterview(null)}
                                            className="flex items-center cursor-pointer text-blue-600 hover:text-blue-800"
                                        >
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clipRule="evenodd" />
                                            </svg>
                                            Back to List
                                        </button>

                                        <div className="flex items-center space-x-4">
                                            {/* Toggle between summary and flashcards */}
                                            <button
                                                onClick={toggleFlashcardsView}
                                                className={`px-3 py-1 text-sm rounded-md border cursor-pointer ${
                                                    showFlashcards
                                                        ? 'bg-blue-600 text-white border-blue-600'
                                                        : 'bg-white text-blue-600 border-blue-600'
                                                }`}
                                                disabled={isLoadingFlashcards}
                                            >
                                                {isLoadingFlashcards ? (
                                                    <span className="flex items-center">
                                                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                        </svg>
                                                        Loading...
                                                    </span>
                                                ) : (
                                                    showFlashcards ? 'View Summary' : 'Practice Flashcards'
                                                )}
                                            </button>

                                            <div className="text-sm text-gray-500">
                                                {formatDate(selectedInterview.date)}
                                            </div>
                                        </div>
                                    </div>


                                    {/* Flashcard error message */}
                                    {flashcardError && showFlashcards && (
                                        <div className="bg-red-50 p-6 rounded-lg border border-red-200 text-red-700 mb-8">
                                            <Text type="p">{flashcardError}</Text>
                                        </div>
                                    )}

                                    {/* Display either the flashcards or the interview summary */}
                                    {showFlashcards && selectedInterview.flashcardSet ? (
                                        <FlashcardsSection
                                            flashcardSet={selectedInterview.flashcardSet}
                                            className="mb-8"
                                        />
                                    ) : (
                                        <div className="mb-8">
                                            <InterviewSummary
                                                summaryData={selectedInterview.summary}
                                                job={{
                                                    id: selectedInterview.jobId,
                                                    title: selectedInterview.jobTitle,
                                                    company: selectedInterview.company
                                                }}
                                                messages={selectedInterview.messages}
                                                showTranscript={true}
                                                savedId={selectedInterview.id}
                                                hideFlashcardsButton={true} // Hide flashcards button in the summary
                                            />
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </main>
            <Footer />
        </>
    );
};