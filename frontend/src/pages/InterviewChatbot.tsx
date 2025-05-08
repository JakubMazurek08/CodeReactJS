import { useRef, useEffect, useState } from "react";
import { Text } from "../components/Text.tsx";
import { Navbar } from "../components/Navbar.tsx";
import { useContext } from "react";
import { jobContext } from "../context/jobContext.ts";
import { useNavigate, useParams } from "react-router-dom";
import {  doc, getDoc } from "firebase/firestore";
import { db } from "../lib/firebase.ts";
import {Roadmap} from "../components/RoadMap.tsx";
import {saveSummary} from "../lib/summaryService.ts";
import {auth} from "../lib/firebase.ts";
import {InterviewSummary} from "../components/InterviewSummary.tsx";

// Define types for our messages
interface Message {
    id: string;
    message: string;
    isUser: boolean;
    endSummary?: InterviewSummary;
}

// Define the structure for our interview summary
interface InterviewSummary {
    learning_roadmap: any;
    passed: boolean;
    rating: number;
    improvements: string[];
    summary: string;
}

// Job interface
interface Job {
    id: string;
    title: string;
    company: string;
    description: string;
    required_skills: string[];
    experience_level: string;
    employment_type: string;
    location: string;
    [key: string]: any; // For additional properties
}

export const InterviewChatbot = () => {
    const navigate = useNavigate();
    const { id } = useParams<{ id: string }>();
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { job, setJob } = useContext(jobContext);
    const [value, setValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isJobLoading, setIsJobLoading] = useState(false);
    const [jobLoadError, setJobLoadError] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isInterviewEnded, setIsInterviewEnded] = useState(false);
    const [interviewSummary, setInterviewSummary] = useState<InterviewSummary | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [isSaved, setIsSaved] = useState(false);
    const [saveError, setSaveError] = useState<string | null>(null);

    // Fetch job from Firebase if not in context
    useEffect(() => {
        const fetchJobFromFirebase = async () => {
            if (!job && id) {
                setIsJobLoading(true);
                setJobLoadError(null);

                try {
                    // Get job document from Firestore
                    const jobRef = doc(db, "jobs", id);
                    const jobDoc = await getDoc(jobRef);

                    if (jobDoc.exists()) {
                        // Create job object with both document data and id
                        const jobData = {
                            id: jobDoc.id,
                            ...jobDoc.data()
                        } as Job;

                        // Update context with job data
                        setJob(jobData);
                        console.log("Job loaded from Firebase:", jobData);
                    } else {
                        setJobLoadError("Job not found");
                        console.error("No job found with ID:", id);
                    }
                } catch (error) {
                    setJobLoadError(`Error loading job: ${error instanceof Error ? error.message : String(error)}`);
                    console.error("Error fetching job:", error);
                } finally {
                    setIsJobLoading(false);
                }
            }
        };

        fetchJobFromFirebase();
    }, [id, job, setJob]);

    // Fetch initial message when component loads or job is loaded
    useEffect(() => {
        if (job && messages.length === 0) {
            startInterview();
        }
    }, [job]);

    const startInterview = async () => {
        if (!job) return;

        setIsLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    job: job,
                    messages: []
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Check if interview ends at the beginning (shouldn't happen, but just in case)
            if (data.endSummary && Object.keys(data.endSummary).length > 0) {
                setIsInterviewEnded(true);
                setInterviewSummary(data.endSummary);
            }

            setMessages([data]);
        } catch (error) {
            console.error('Error starting interview:', error);
            // Fallback initial message if API fails
            setMessages([{
                id: 'initial',
                message: "Hello! I'm PrepJobAI from " + job.company + ". Thanks for joining this interview for the " + job.title + " position. Could you tell me a bit about yourself and why you're interested in this role?",
                isUser: false
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const textarea = textareaRef.current;
        setValue(e.target.value);

        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 240)}px`;
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const handleSubmit = async () => {
        if (value.trim() === '' || isLoading || !job || isInterviewEnded) return;

        // Create user message
        const userMessage = {
            id: Date.now().toString(),
            message: value.trim(),
            isUser: true
        };

        // Add user message to chat
        setMessages(prev => [...prev, userMessage]);
        setValue('');
        setIsLoading(true);

        try {
            // Send conversation to backend API
            const response = await fetch('http://localhost:5000/api/conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    job: job,
                    messages: [...messages, userMessage]
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const aiMessage = await response.json();

            // Check if the interview has ended
            if (aiMessage.endSummary && Object.keys(aiMessage.endSummary).length > 0) {
                setIsInterviewEnded(true);
                setInterviewSummary(aiMessage.endSummary);
            }

            // Add AI response to chat
            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error sending message:', error);

            // Fallback response if API fails
            const fallbackResponse = {
                id: Date.now().toString(),
                message: "I apologize, but I'm having trouble connecting to our systems. Could you please try again in a moment?",
                isUser: false
            };

            setMessages(prev => [...prev, fallbackResponse]);
        } finally {
            setIsLoading(false);
        }
    };

    // Create a color based on the rating (red to green gradient)


    const handleSaveInterview = async () => {
        if (!job || !interviewSummary || isSaving || isSaved) return;

        // Check if user is logged in
        if (!auth.currentUser) {
            setSaveError("Please log in to save your interview summary");
            return;
        }

        setIsSaving(true);
        setSaveError(null);

        try {
            const savedId = await saveSummary(job, messages, interviewSummary);
            if (savedId) {
                setIsSaved(true);
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
    if (isInterviewEnded && interviewSummary && !isSaved && !isSaving && auth.currentUser) {
        handleSaveInterview();
    }
}, [isInterviewEnded, interviewSummary, isSaved, isSaving, auth.currentUser]);

    // If job is loading, show loading state
    if (isJobLoading) {
        return (
            <>
                <Navbar />
                <main className="px-[50px] sm:px-[100px] md:px-[200px] lg:px-[300px] pt-30 pb-[140px] min-h-screen bg-background flex justify-center items-center">
                    <div className="text-center">
                        <div className="flex justify-center mb-4">
                            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                        </div>
                        <Text type="h2">Loading job details...</Text>
                    </div>
                </main>
            </>
        );
    }

    // If job loading failed, show error
    if (jobLoadError) {
        return (
            <>
                <Navbar />
                <main className="px-[50px] sm:px-[100px] md:px-[200px] lg:px-[300px] pt-30 pb-[140px] min-h-screen bg-background flex justify-center items-center">
                    <div className="text-center">
                        <div className="text-red-500 text-5xl mb-4">⚠️</div>
                        <Text type="h2" className="mb-4">Unable to load job</Text>
                        <Text type="p" className="mb-6">{jobLoadError}</Text>
                        <button
                            onClick={() => navigate('/jobs')}
                            className="px-6 py-3 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition"
                        >
                            Back to Job Listings
                        </button>
                    </div>
                </main>
            </>
        );
    }

    // If interview has ended, show the summary page
    if (isInterviewEnded && interviewSummary) {
        return (
            <>
                <Navbar />
                <main className="px-[50px] sm:px-[100px] md:px-[200px] lg:px-[300px] pt-30 pb-[140px] min-h-screen bg-background">
                    <Text type="h1" className="mb-6">Interview Complete</Text>
                    <InterviewSummary
                        summaryData={interviewSummary}
                        job={job}
                        messages={messages}
                        showTranscript={true}
                    />
                </main>
            </>
        );
    }

    // Regular interview chat UI
    return (
        <>
            <Navbar />

            {/* Page content */}
            <main className="px-[50px] sm:px-[100px] md:px-[200px] lg:px-[300px] xl:px-[400px] pt-30 pb-[140px] min-h-screen bg-background">
                <Text type="h1">Interview - {job?.title || 'Loading...'}</Text>
                <Text type="p" className="mt-2">{job?.company || ''}</Text>

                <div className="w-full flex flex-col gap-10 mt-10">
                    {messages.map((message) => (
                        message.isUser ? (
                            // User message
                            <div key={message.id} className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                                <Text>{message.message}</Text>
                            </div>
                        ) : (
                            // AI message
                            <div key={message.id} className="w-10/12">
                                <Text>{message.message}</Text>
                            </div>
                        )
                    ))}

                    {/* Loading indicator */}
                    {isLoading && (
                        <div className="w-10/12">
                            <div className="flex space-x-2">
                                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce"></div>
                                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                <div className="w-3 h-3 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                            </div>
                        </div>
                    )}

                    {/* Invisible div for scrolling to bottom */}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* Fixed bottom input with horizontal padding */}
            <div className="fixed bottom-0 left-0 w-full bg-background px-[50px] sm:px-[100px] md:px-[200px] lg:px-[300px] xl:px-[400px] pb-4 pt-2">
                <div className="relative">
                    <textarea
                        ref={textareaRef}
                        value={value}
                        onChange={handleInput}
                        onKeyDown={handleKeyDown}
                        className="bg-white w-full p-4 pr-10 shadow-lg resize-none rounded-md overflow-y-auto leading-relaxed focus:outline-none transition-all duration-100 ease-in-out max-h-60 min-h-[3rem]"
                        placeholder={isInterviewEnded ? "Interview Complete" : "Respond..."}
                        rows={1}
                        disabled={isLoading || isInterviewEnded}
                    />
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading || value.trim() === '' || isInterviewEnded}
                        className={`absolute right-3 bottom-3 rounded-full p-2 bg-blue-500 text-white 
                      ${(isLoading || value.trim() === '' || isInterviewEnded) ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'}`}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 2L11 13"></path>
                            <path d="M22 2L15 22L11 13L2 9L22 2Z"></path>
                        </svg>
                    </button>
                </div>
            </div>
        </>
    );
};