// Update your Home component with this code

import { Navbar } from "../components/Navbar.tsx";
import { Text } from "../components/Text.tsx";
import { Input } from "../components/Input.tsx";
import { JobCard } from "../components/JobCard.tsx";
import {useRef, useState, useEffect} from "react";
import { Button } from "../components/Button.tsx";
import {Footer} from "../components/Footer.tsx";
export const SearchIcon: React.FC<React.SVGProps<SVGSVGElement>> = props => (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="256"
      height="256"
      viewBox="0 0 256 256"
      fill="none"
      {...props}
    >
      <g
        transform="translate(1.4065934065934016 1.4065934065934016) scale(2.81 2.81)"
        fill="none"
        fillRule="nonzero"
      >
        <path
          d="
            M87.803 77.194
            L68.212 57.602
            c9.5-14.422 7.912-34.054-4.766-46.732
           c0 0-.001 0-.001 0
            c-14.495-14.493-38.08-14.494-52.574 0
            c-14.494 14.495-14.494 38.079 0 52.575
            c7.248 7.247 16.767 10.87 26.287 10.87
            c7.134 0 14.267-2.035 20.445-6.104
            l19.591 19.591
            C78.659 89.267 80.579 90 82.498 90
            s3.84-.733 5.305-2.197
            C90.732 84.873 90.732 80.124 87.803 77.194
            z
  
            M21.48 52.837
            c-8.645-8.646-8.645-22.713 0-31.358
            c4.323-4.322 10-6.483 15.679-6.483
            c5.678 0 11.356 2.161 15.678 6.483
            c8.644 8.644 8.645 22.707.005 31.352
            c-.002.002-.004.003-.005.005
            c-.002.002-.003.003-.004.005
            C44.184 61.481 30.123 61.48 21.48 52.837
            z
          "
          fill="black"
          strokeLinecap="round"
        />
      </g>
    </svg>
  );
export const Home = () => {
    const positionRef = useRef<HTMLTextAreaElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [experience, setExperience] = useState("");
    const [position, setPosition] = useState("");
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState({ position: "", experience: "" });
    const [show, setShow] = useState(false);
    const [showJobs, setShowJobs] = useState<number[]>([]);
    const [cvFile, setCvFile] = useState<File | null>(null);
    
    useEffect(() => { setShow(true); }, []);

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
    useEffect(() => {
        const textarea = positionRef.current;
        if (textarea) {
          textarea.style.height = "auto";
          textarea.style.height = `${Math.min(textarea.scrollHeight, 300)}px`;
        }
      }, [position]);
    const handlePositionChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setPosition(e.target.value);
        if (errors.position) {
            setErrors(prev => ({ ...prev, position: "" }));
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.type === 'application/pdf') {
                setCvFile(file);
                // Clear validation errors when CV is uploaded
                setErrors(prev => ({ ...prev, experience: "", position: "" }));
                console.log("PDF uploaded successfully:", file.name);
            } else {
                alert('Please upload a PDF file only');
                e.target.value = '';
            }
        }
    };

    const triggerFileInput = () => {
        fileInputRef.current?.click();
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

        if (!position.trim() && !cvFile) {
            newErrors.position = "Position field cannot be empty";
            valid = false;
        }

        if (!experience.trim() && !cvFile) {
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

            let formData;
            let URL;
            
            if (cvFile) {
                // Use FormData for file upload
                formData = new FormData();
                formData.append('pdf_file', cvFile); // Changed from 'cv_file' to 'pdf_file'
                formData.append('job_keyword', position);
                
                // First extract the text from the PDF
                URL = "http://localhost:5000/api/extract-pdf";
                
                const extractResponse = await fetch(URL, {
                    method: "POST",
                    body: formData
                });
                
                if (!extractResponse.ok) {
                    throw new Error(`PDF extraction failed: ${extractResponse.status}: ${extractResponse.statusText}`);
                }
                
                const extractData = await extractResponse.json();
                
                if (extractData.error) {
                    throw new Error(`PDF extraction error: ${extractData.error}`);
                }
                
                // Now use the extracted text to match jobs
                const analysis = extractData.analysis || {};
                const profileText = analysis.user_summary || extractData.text || "";
                
                // Use the regular match-jobs API with the extracted text
                URL = "http://localhost:5000/api/match-jobs";
                const matchResponse = await fetch(URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        profile_text: profileText,
                        job_keyword: position
                    })
                });
                
                if (!matchResponse.ok) {
                    throw new Error(`Job matching failed: ${matchResponse.status}: ${matchResponse.statusText}`);
                }
                
                const responseData = await matchResponse.json();
                
                if (responseData.error) {
                    throw new Error(responseData.error);
                }
                
                setJobs(responseData.matches || []);
                
                // Log success message
                console.log(`Found ${responseData.matches?.length || 0} jobs matching your CV for position: ${position}`);
            } else {
                // Use regular JSON for text-based submission
                const data = {
                    profile_text: experience,
                    job_keyword: position,
                };
                
                URL = "http://localhost:5000/api/match-jobs";
                const response = await fetch(URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(data)
                });
                
                if (!response.ok) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                
                const responseData = await response.json();
                
                if (responseData.error) {
                    throw new Error(responseData.error);
                }
                
                setJobs(responseData.matches || []);
            }

        } catch (error: any) {
            console.error("Error fetching jobs:", error);
            alert(`Error fetching jobs: ${error.message || "Please try again later."}`);
        } finally {
            setIsLoading(false);
        }
    };

    // This function is now removed since we're handling CV submission in the main submit function

    useEffect(() => {
        if (jobs.length > 0) {
            setShowJobs([]);
            jobs.forEach((_, i) => {
                setTimeout(() => setShowJobs(prev => [...prev, i]), 150 * i);
            });
        }
    }, [jobs]);

    return (
        <>
            <Navbar />
            <main className="px-6 py-30 min-h-screen bg-background flex flex-col items-center">
                <div className="w-full max-w-5xl">
                    <Text type="h1">Find a Job</Text>

                    <div className="mt-6 flex flex-col gap-4">
                        <div>
                            <textarea
                                placeholder="Position / Role"
                                value={position}
                                ref={positionRef}
                                onChange={handlePositionChange}
                                className={`bg-white w-full p-4 shadow-md resize-none rounded-lg overflow-y-auto leading-relaxed focus:outline-none transition-all duration-150 ease-in-out max-h-[300px] min-h-[4rem] border ${
                                    errors.position ? "border-red-500" : "border-gray-200"
                                } focus:ring-2 focus:ring-blue-400`}
                            />
                            {errors.position && (
                                <p className="text-red-500 text-sm mt-1">{errors.position}</p>
                            )}
                        </div>

                        <div className="relative flex items-center">
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
                            <Button
                            color={'blue'}
                            onClick={submit}
                            disabled={isLoading} 
                            className={`absolute top-1/2 right-1 transform -translate-y-1/2 bg-white text-white px-4 py-1 rounded-r-lg  h-5/10 ${ isLoading ? "search-wiggle" : ""} `}
                            >
                            <SearchIcon className="w-6 h-6 " />
                            </Button>
                        
                        </div>
                        {errors.experience && (
                                <p className="text-red-500 text-sm mt-1">{errors.experience}</p>
                            )}
                            
                        
                        <div className="flex items-center justify-center gap-2 text-gray-500">
                        <span className="text-gray-500">━━━━━━━━━━━━━━━━━━━━{'\u00A0'}{'\u00A0'}{'\u00A0'}{'\u00A0'}OR{'\u00A0'}{'\u00A0'}{'\u00A0'}{'\u00A0'}━━━━━━━━━━━━━━━━━━━━</span>
                        </div>

                        {/* CV Upload button */}
                        <div className="flex flex-col items-center gap-4">
                            <div className="flex items-center gap-3">
                                <div 
                                    onClick={triggerFileInput}
                                    className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-blue-500 text-white px-6 py-3 rounded-lg cursor-pointer shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 active:scale-95"
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                    <span className="font-medium">Upload CV (PDF)</span>
                                </div>
                            
                                {cvFile && (
                                    <span className="text-green-600 flex items-center">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                        </svg>
                                        {cvFile.name}
                                    </span>
                                )}
                            </div>
                            
                            {/* No need for a separate search button as the main search will handle CV uploads */}
                        </div>
                        
                        {/* Hidden file input */}
                        <input 
                            type="file"
                            ref={fileInputRef}
                            onChange={handleFileChange}
                            accept=".pdf"
                            className="hidden"
                        />
                    </div>

                    {isLoading && (
                        <div className="flex justify-center mt-8">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
                        </div>
                    )}

                    <div className="flex flex-col items-center gap-10 mt-10">
                        {jobs.length > 0 ? (
                            jobs.map((job, index) => (
                                <div key={index} className={`w-full transition-all duration-700 ${showJobs.includes(index) ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                                    <JobCard data={job} />
                                </div>
                            ))
                        ) : !isLoading && jobs.length === 0 && ((position.trim() !== "" && experience.trim() !== "") || cvFile) ? (
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