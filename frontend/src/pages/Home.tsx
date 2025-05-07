import { Navbar } from "../components/Navbar.tsx";
import { Text } from "../components/Text.tsx";
import { Input } from "../components/Input.tsx";
import { JobCard } from "../components/JobCard.tsx";
import {useRef, useState, useEffect, useContext} from "react";
import { Button } from "../components/Button.tsx";
import {Footer} from "../components/Footer.tsx";

export const Home = () => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [experience, setExperience] = useState("");
    const [position, setPosition] = useState("");
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState({ position: "", experience: "" });

    const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setExperience(e.target.value);
        if (errors.experience) {
            setErrors(prev => ({ ...prev, experience: "" }));
        }

        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
        }
    };

    const handlePositionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setPosition(e.target.value);
        if (errors.position) {
            setErrors(prev => ({ ...prev, position: "" }));
        }
    };

    useEffect(() => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = "auto";
            textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
        }
    }, [experience]);

    const validateForm = () => {
        let valid = true;
        const newErrors = { position: "", experience: "" };

        if (!position.trim()) {
            newErrors.position = "Position field cannot be empty";
            valid = false;
        }

        if (!experience.trim()) {
            newErrors.experience = "Experience field cannot be empty";
            valid = false;
        }

        setErrors(newErrors);
        return valid;
    };

    const submit = async () => {
        // Validate the form
        if (!validateForm()) {
            return;
        }

        // Prevent multiple submissions
        if (isLoading) {
            return;
        }

        try {
            setIsLoading(true);

            const data = {
                profile_text: experience,
                job_keyword: position,
            };

            const URL = "http://localhost:5000/api/match-jobs";
            const response = await fetch(URL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            const responseData = await response.json();
            setJobs(responseData.matches);
            console.log(responseData);

        } catch (error) {
            console.error("Error fetching jobs:", error);
            // You could also add error state handling here
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <Navbar />
            <main className="px-6 pt-30 min-h-screen bg-background flex flex-col items-center">
                <div className="w-full max-w-5xl">
                    <Text type="h1">Find a Job</Text>

                    <div className="mt-6 flex flex-col gap-4">
                        <div>
                            <Input
                                placeholder="Position / Role"
                                value={position}
                                onChange={handlePositionChange}
                                className={errors.position ? "border-red-500" : ""}
                            />
                            {errors.position && (
                                <p className="text-red-500 text-sm mt-1">{errors.position}</p>
                            )}
                        </div>

                        <div>
                            <textarea
                                ref={textareaRef}
                                value={experience}
                                onChange={handleTextareaInput}
                                placeholder="Describe your work experience and skills..."
                                className={`bg-white w-full p-4 shadow-md resize-none rounded-lg overflow-y-auto leading-relaxed focus:outline-none transition-all duration-150 ease-in-out max-h-[300px] min-h-[4rem] border ${
                                    errors.experience ? "border-red-500" : "border-gray-200"
                                } focus:ring-2 focus:ring-blue-400`}
                                rows={1}
                            />
                            {errors.experience && (
                                <p className="text-red-500 text-sm mt-1">{errors.experience}</p>
                            )}
                        </div>

                        <Button
                            color={'blue'}
                            onClick={submit}
                            disabled={isLoading}
                            className={isLoading ? "opacity-70 cursor-not-allowed" : ""}
                        >
                            {isLoading ? "Searching..." : "Search"}
                        </Button>
                    </div>

                    {isLoading && (
                        <div className="flex justify-center mt-8">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
                        </div>
                    )}

                    <div className="flex flex-col items-center gap-10 mt-10">
                        {jobs.length > 0 ? (
                            jobs.map((job, index) => (
                                <JobCard key={index} data={job} />
                            ))
                        ) : !isLoading && jobs.length === 0 && position.trim() !== "" && experience.trim() !== "" ? (
                            <div className="text-center py-8">
                                <p className="text-gray-500">No matching jobs found. Try adjusting your search criteria.</p>
                            </div>
                        ) : null}
                    </div>
                </div>

            </main>
            <Footer/>
        </>
    );
};