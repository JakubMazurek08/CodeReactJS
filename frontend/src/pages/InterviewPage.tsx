// src/pages/Interviews.tsx
import { useEffect, useState } from 'react';
import { Navbar } from '../components/Navbar';
import { Text } from '../components/Text';
import { Footer } from '../components/Footer';
import { getUserInterviews, type SavedInterview } from '../lib/summaryService.ts';
import { Link } from 'react-router-dom';
import { auth } from '../lib/firebase.ts';
import {InterviewSummary} from "../components/InterviewSummary.tsx";

export const InterviewPage = () => {
    const [interviews, setInterviews] = useState<SavedInterview[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedInterview, setSelectedInterview] = useState<SavedInterview | null>(null);

    // Fetch user's interviews
    useEffect(() => {
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

        if (auth.currentUser) {
            fetchInterviews();
        } else {
            setIsLoading(false);
        }
    }, []);

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

    return (
        <>
            <Navbar />
            <main className="px-6 py-30 min-h-screen bg-background flex flex-col items-center">
                <div className="w-full max-w-5xl">
                    <Text type="h1" className="mb-6">Your Interview History</Text>

                    {!auth.currentUser ? (
                        <div className="bg-white p-8 rounded-lg shadow-lg text-center">
                            <Text type="h3" className="mb-4">Please Log In</Text>
                            <Text type="p">You need to be logged in to view your interview history.</Text>
                            {/* Add login button or redirect here */}
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
                                                            onClick={() => setSelectedInterview(interview)}
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
                                        <div className="text-sm text-gray-500">
                                            {formatDate(selectedInterview.date)}
                                        </div>
                                    </div>

                                    {/* Use the interview summary component */}
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
                                        />
                                    </div>
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