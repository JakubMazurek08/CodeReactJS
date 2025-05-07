import { useRef, useEffect, useState } from "react";
import { Text } from "../components/Text.tsx";
import { Navbar } from "../components/Navbar.tsx";

export const InterviewChatbot = () => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [value, setValue] = useState("");

    const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const textarea = textareaRef.current;
        setValue(e.target.value);

        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 240)}px`;
        }
    };

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
            <main className="px-[400px] pt-30 pb-[140px] min-h-screen bg-background">
                <Text type="h1">Test Interview - Google</Text>

                <div className="w-full flex flex-col gap-10 mt-10">
                    <div className="w-10/12">
                        <Text>
                            Hi Jakub, thanks for coming in today. Let’s start with a simple question — can you
                            tell me a bit about yourself and what drew you to frontend development?
                        </Text>
                    </div>
                    <div className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                        <Text>
                            Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got
                            into coding when I was 12, starting with game development in Unity, but over time I
                            became more passionate about building interactive and efficient web applications.
                            Now I specialize in React and TypeScript, and I enjoy turning complex ideas into
                            clean, user-friendly interfaces. I'm currently looking for a position where I can
                            grow my skills in a real-world environment, contribute to a team, and keep learning.
                        </Text>
                    </div>
                    <div className="w-10/12">
                        <Text>
                            Hi Jakub, thanks for coming in today. Let’s start with a simple question — can you
                            tell me a bit about yourself and what drew you to frontend development?
                        </Text>
                    </div>
                    <div className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                        <Text>
                            Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got
                            into coding when I was 12, starting with game development in Unity, but over time I
                            became more passionate about building interactive and efficient web applications.
                            Now I specialize in React and TypeScript, and I enjoy turning complex ideas into
                            clean, user-friendly interfaces. I'm currently looking for a position where I can
                            grow my skills in a real-world environment, contribute to a team, and keep learning.
                        </Text>
                    </div>
                    <div className="w-10/12">
                        <Text>
                            Hi Jakub, thanks for coming in today. Let’s start with a simple question — can you
                            tell me a bit about yourself and what drew you to frontend development?
                        </Text>
                    </div>
                    <div className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                        <Text>
                            Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got
                            into coding when I was 12, starting with game development in Unity, but over time I
                            became more passionate about building interactive and efficient web applications.
                            Now I specialize in React and TypeScript, and I enjoy turning complex ideas into
                            clean, user-friendly interfaces. I'm currently looking for a position where I can
                            grow my skills in a real-world environment, contribute to a team, and keep learning.
                        </Text>
                    </div>
                    <div className="w-10/12">
                        <Text>
                            Hi Jakub, thanks for coming in today. Let’s start with a simple question — can you
                            tell me a bit about yourself and what drew you to frontend development?
                        </Text>
                    </div>
                    <div className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                        <Text>
                            Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got
                            into coding when I was 12, starting with game development in Unity, but over time I
                            became more passionate about building interactive and efficient web applications.
                            Now I specialize in React and TypeScript, and I enjoy turning complex ideas into
                            clean, user-friendly interfaces. I'm currently looking for a position where I can
                            grow my skills in a real-world environment, contribute to a team, and keep learning.
                        </Text>
                    </div>
                    <div className="w-10/12">
                        <Text>
                            Hi Jakub, thanks for coming in today. Let’s start with a simple question — can you
                            tell me a bit about yourself and what drew you to frontend development?
                        </Text>
                    </div>
                    <div className="w-8/12 self-end bg-white shadow-xl p-4 rounded-[10px]">
                        <Text>
                            Hi, thanks for having me! I'm Jakub Mazurek, a frontend developer from Lublin. I got
                            into coding when I was 12, starting with game development in Unity, but over time I
                            became more passionate about building interactive and efficient web applications.
                            Now I specialize in React and TypeScript, and I enjoy turning complex ideas into
                            clean, user-friendly interfaces. I'm currently looking for a position where I can
                            grow my skills in a real-world environment, contribute to a team, and keep learning.
                        </Text>
                    </div>
                </div>
            </main>

            {/* Fixed bottom input with horizontal padding */}
            <div className="fixed bottom-0 left-0 w-full bg-background px-[400px] pb-4 pt-2">
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={handleInput}
                    className="bg-white w-full p-4 shadow-lg resize-none rounded-md overflow-y-auto leading-relaxed focus:outline-none transition-all duration-100 ease-in-out max-h-60 min-h-[3rem]"
                    placeholder="Respond..."
                    rows={1}
                />
            </div>
        </>
    );
};
