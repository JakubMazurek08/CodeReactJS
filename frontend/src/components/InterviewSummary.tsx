// src/components/InterviewSummary.tsx
import { useEffect, useRef, useState } from 'react';
import { Text } from './Text.tsx';
import { Roadmap } from './RoadMap.tsx';
import { auth } from '../lib/firebase.ts';
import { saveSummary } from '../lib/summaryService.ts';

interface Message {
    id: string;
    message: string;
    isUser: boolean;
}

interface Resource {
    title: string;
    type: string;
    description: string;
    difficulty: string;
    url?: string;
}

interface LearningRoadmapData {
    key_areas: string[];
    resources: Resource[];
    suggested_timeline: string;
}

interface InterviewSummaryData {
    passed: boolean;
    rating: number;
    improvements: string[];
    summary: string;
    learning_roadmap?: LearningRoadmapData;
}

interface InterviewSummaryProps {
    summaryData: InterviewSummaryData;
    job: any;
    messages: Message[];
    showTranscript?: boolean;
    savedId?: string;
}

export const InterviewSummary = ({ summaryData, job, messages, showTranscript = true, savedId }: InterviewSummaryProps) => {
    const [isSaving, setIsSaving] = useState(false);
    const [isSaved, setIsSaved] = useState(Boolean(savedId));
    const [saveError, setSaveError] = useState<string | null>(null);
    const [saveId, setSaveId] = useState<string | null>(savedId || null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    const getRatingColor = (rating: number) => {
        if (rating >= 80) return 'bg-green-500';
        if (rating >= 60) return 'bg-green-400';
        if (rating >= 40) return 'bg-yellow-500';
        if (rating >= 20) return 'bg-orange-500';
        return 'bg-red-500';
    };


    const handleSaveInterview = async () => {
        if (!job || !summaryData || isSaving || isSaved || saveId) return;

        // Cancel auto-save timer if it's still pending
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }

        if (!auth.currentUser) {
            setSaveError("Please log in to save your interview summary");
            return;
        }

        setIsSaving(true);
        setSaveError(null);

        try {
            const savedId = await saveSummary(job, messages, summaryData);
            if (savedId) {
                setIsSaved(true);
                setSaveId(savedId);
                console.log("Interview saved successfully with ID:", savedId);
            } else {
                setSaveError("Failed to save interview summary");
            }
        } catch (error) {
            console.error("Error saving interview:", error);
            setSaveError(`Error saving: ${error instanceof Error ? error.message : String(error)}`);
        } finally {
            setIsSaving(false);
        }
    };

    useEffect(() => {
        const autoSave = async () => {
            if (auth.currentUser && !isSaved && !saveId && !isSaving && job && summaryData) {
                setIsSaving(true);
                try {
                    const savedId = await saveSummary(job, messages, summaryData);
                    if (savedId) {
                        setIsSaved(true);
                        setSaveId(savedId);
                        console.log("Interview auto-saved with ID:", savedId);
                    }
                } catch (error) {
                    console.error("Auto-save error:", error);
                } finally {
                    setIsSaving(false);
                }
            }
        };

        timerRef.current = setTimeout(autoSave, 1000);
        return () => {
            if (timerRef.current) {
                clearTimeout(timerRef.current);
                timerRef.current = null;
            }
        };
    }, []);

    return (
        <div className="w-full space-y-8">
            <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <Text type="h2" className="text-2xl font-bold mb-2">Interview Result</Text>
                        <Text type="p" className="text-gray-600">{job?.title} at {job?.company}</Text>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className={`rounded-full ${summaryData.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'} px-4 py-2 font-medium text-sm`}>
                            {summaryData.passed ? 'Passed' : 'Needs Improvement'}
                        </div>

                        {!savedId && (
                            <>
                                {isSaving ? (
                                    <div className="text-sm text-gray-500 flex items-center">
                                        <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin mr-2"></div>
                                        Saving...
                                    </div>
                                ) : isSaved ? (
                                    <div className="text-sm text-green-600 flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                        Saved
                                    </div>
                                ) : saveError ? (
                                    <div className="text-sm text-red-600 flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                        </svg>
                                        Save failed
                                    </div>
                                ) : auth.currentUser ? (
                                    <button
                                        onClick={handleSaveInterview}
                                        className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
                                    >
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                                            <path d="M7.707 10.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V6h5a2 2 0 012 2v7a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2h5v5.586l-1.293-1.293zM9 4a1 1 0 012 0v2H9V4z" />
                                        </svg>
                                        Save
                                    </button>
                                ) : (
                                    <div className="text-sm text-gray-500">
                                        Login to save
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                <div className="mb-8">
                    <Text type="h3" className="font-semibold mb-2">Overall Assessment</Text>
                    <Text type="p" className="text-gray-700">{summaryData.summary}</Text>
                </div>

                <div className="mb-8">
                    <div className="flex justify-between items-center mb-2">
                        <Text type="h3" className="font-semibold">Performance Rating</Text>
                        <Text type="p" className="font-bold">{summaryData.rating}/100</Text>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4">
                        <div
                            className={`h-4 rounded-full ${getRatingColor(summaryData.rating)}`}
                            style={{ width: `${summaryData.rating}%` }}
                        ></div>
                    </div>
                </div>

                <div>
                    <Text type="h3" className="font-semibold mb-4">Areas for Improvement</Text>
                    <ul className="space-y-2">
                        {summaryData.improvements.map((improvement, index) => (
                            <li key={index} className="flex items-start">
                                <span className="mr-2 mt-1 text-red-500">•</span>
                                <Text type="p" className="text-gray-700">{improvement}</Text>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>

            {summaryData.learning_roadmap && (
                <Roadmap roadmap={summaryData.learning_roadmap} />
            )}

            {showTranscript && messages.length > 0 && (
                <div className="bg-white rounded-lg shadow-xl p-8">
                    <Text type="h3" className="font-semibold mb-4">Interview Transcript</Text>
                    <div className="space-y-4 max-h-96 overflow-y-auto">
                        {messages.map((message) => (
                            <div key={message.id} className={`p-3 rounded-lg ${message.isUser ? 'bg-blue-50 ml-8' : 'bg-gray-50 mr-8'}`}>
                                <div className="text-xs font-medium mb-1 text-gray-500">
                                    {message.isUser ? 'You' : 'PrepJobAI'}
                                </div>
                                <Text type="p">{message.message}</Text>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
