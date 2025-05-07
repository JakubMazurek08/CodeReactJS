import { useRef, useEffect, useState } from "react";
import { Text } from "../components/Text.tsx";
import { Navbar } from "../components/Navbar.tsx";
import { useContext } from "react";
import { jobContext } from "../context/jobContext.ts";

// Define types for our messages
interface Message {
    id: string;
    message: string;
    isUser: boolean;
    endSummary?: string; // Add endSummary field
}

export const InterviewChatbot = () => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { job } = useContext(jobContext);
    const [value, setValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isInterviewEnded, setIsInterviewEnded] = useState(false);
    const [showSummaryPopup, setShowSummaryPopup] = useState(false);
    const [interviewSummary, setInterviewSummary] = useState("");

    // Fetch initial message when component loads
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
            if (data.endSummary) {
                setIsInterviewEnded(true);
                setInterviewSummary(data.endSummary);
                setShowSummaryPopup(true);
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
            if (aiMessage.endSummary) {
                setIsInterviewEnded(true);
                setInterviewSummary(aiMessage.endSummary);
                setShowSummaryPopup(true);
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

    // Handle closing the summary popup
    const closeSummaryPopup = () => {
        setShowSummaryPopup(false);
    };

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 240)}px`;
        }
    }, [value]);

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

                    {/* Interview ended banner (alternative to popup) */}
                    {isInterviewEnded && !showSummaryPopup && (
                        <div className="w-full bg-green-50 border border-green-200 p-4 rounded-lg mt-4">
                            <Text type="p" className="font-medium">Interview Complete</Text>
                            <button
                                onClick={() => setShowSummaryPopup(true)}
                                className="mt-2 text-blue-500 hover:text-blue-700 underline"
                            >
                                View Summary
                            </button>
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
                        className="bg-white w-full p-4 shadow-lg resize-none rounded-md overflow-y-auto leading-relaxed focus:outline-none transition-all duration-100 ease-in-out max-h-60 min-h-[3rem]"
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

            {/* Summary Popup */}
            {showSummaryPopup && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <Text type="h2">Interview Summary</Text>
                                <button
                                    onClick={closeSummaryPopup}
                                    className="text-gray-500 hover:text-gray-700"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="18" y1="6" x2="6" y2="18"></line>
                                        <line x1="6" y1="6" x2="18" y2="18"></line>
                                    </svg>
                                </button>
                            </div>
                            <div className="border-t border-gray-200 pt-4">
                                <Text>{interviewSummary}</Text>
                            </div>
                            <div className="mt-6 flex justify-end">
                                <button
                                    onClick={closeSummaryPopup}
                                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};