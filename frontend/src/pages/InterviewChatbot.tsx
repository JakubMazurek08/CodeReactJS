import { useRef, useEffect, useState } from "react";
import { Text } from "../components/Text.tsx";
import { Navbar } from "../components/Navbar.tsx";
import {Footer} from "../components/Footer.tsx";

// Define a type for our messages
interface Message {
    text: string;
    isUser: boolean;
}

export const InterviewChatbot = () => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const [value, setValue] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            text: "Hi Jakub, thanks for coming in today. Let's start with a simple question — can you tell me a bit about yourself and what drew you to frontend development?",
            isUser: false
        },
        {
            text: "Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got into coding when I was 12, starting with game development in Unity, but over time I became more passionate about building interactive and efficient web applications. Now I specialize in React and TypeScript, and I enjoy turning complex ideas into clean, user-friendly interfaces. I'm currently looking for a position where I can grow my skills in a real-world environment, contribute to a team, and keep learning.",
            isUser: true
        }
    ]);

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
        if (value.trim() === '' || isLoading) return;

        // Add user message
        const userMessage = {
            text: value.trim(),
            isUser: true
        };
        setMessages(prev => [...prev, userMessage]);
        setValue('');
        setIsLoading(true);

        try {
            // Send message to backend API
            const response = await fetch('http://localhost:5000/api/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: userMessage.text,
                    history: messages
                })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();

            // Add AI response
            const aiMessage = {
                text: data.response || "I'm sorry, I couldn't process your request. Please try again.",
                isUser: false
            };

            setMessages(prev => [...prev, aiMessage]);
        } catch (error) {
            console.error('Error sending message:', error);

            // For testing, add a placeholder AI response
            const placeholderResponse = {
                text: "This is a test AI response. In a real environment, I would respond to your specific message. How about we discuss your technical skills next?",
                isUser: false
            };

            setMessages(prev => [...prev, placeholderResponse]);
        } finally {
            setIsLoading(false);
        }
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
                <Text type="h1">Test Interview - Google</Text>

                <div className="w-full flex flex-col gap-10 mt-10">
                    {messages.map((message, index) => (
                        message.isUser ? (
                            // User message
                            <div key={index} className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                                <Text>{message.text}</Text>
                            </div>
                        ) : (
                            // AI message
                            <div key={index} className="w-10/12">
                                <Text>{message.text}</Text>
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
                        className="bg-white w-full p-4 shadow-lg resize-none rounded-md overflow-y-auto leading-relaxed focus:outline-none transition-all duration-100 ease-in-out max-h-60 min-h-[3rem]"
                        placeholder="Respond..."
                        rows={1}
                        disabled={isLoading}
                    />
                    <button
                        onClick={handleSubmit}
                        disabled={isLoading || value.trim() === ''}
                        className={`absolute right-3 bottom-3 rounded-full p-2 bg-blue-500 text-white 
                        ${(isLoading || value.trim() === '') ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-600'}`}
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