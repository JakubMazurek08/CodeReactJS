import { Navbar } from "../components/Navbar.tsx";
import { Text } from "../components/Text.tsx";
import { Input } from "../components/Input.tsx";
import { JobCard } from "../components/JobCard.tsx";
import { useRef, useState, useEffect } from "react";
import { Button } from "../components/Button.tsx";
import { Footer } from "../components/Footer.tsx";
import { useSearchHistory } from "../hooks/useSearchHistory"; // This would be a custom hook you'd create

export const Home = () => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [experience, setExperience] = useState("");
    const [position, setPosition] = useState("");
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState({ position: "", experience: "" });
    const [errorMessage, setErrorMessage] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [sortOption, setSortOption] = useState("match_percentage"); // Default sort by match percentage
    const itemsPerPage = 5;

    // This would be your custom hook for managing search history
    const { searchHistory, addSearch, clearHistory } = useSearchHistory();

    // Restore the last search from localStorage on component mount
    useEffect(() => {
        const savedSearch = localStorage.getItem('lastSearch');
        if (savedSearch) {
            const { position, experience, jobs } = JSON.parse(savedSearch);
            setPosition(position);
            setExperience(experience);
            setJobs(jobs);
        }
    }, []);

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

    // Auto-resize textarea on content change
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
        } else if (experience.trim().length < 50) {
            newErrors.experience = "Please provide more details about your experience (at least 50 characters)";
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
            setErrorMessage("");
            setCurrentPage(1); // Reset to first page on new search

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

            if (!response.ok) {
                throw new Error(`Error: ${response.status} ${response.statusText}`);
            }

            const responseData = await response.json();

            // Set jobs and sort initially by match percentage
            const sortedJobs = [...responseData.matches].sort((a, b) =>
                b.match_percentage - a.match_percentage
            );

            setJobs(sortedJobs);

            // Add to search history
            addSearch({
                id: Date.now(),
                position,
                experience,
                timestamp: new Date().toISOString(),
                resultCount: sortedJobs.length
            });

            // Save to localStorage
            localStorage.setItem('lastSearch', JSON.stringify({
                position,
                experience,
                jobs: sortedJobs
            }));

        } catch (error) {
            console.error("Error fetching jobs:", error);
            setErrorMessage(error.message || "An error occurred while searching for jobs. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    // Handle sorting of jobs
    const handleSortChange = (e) => {
        const option = e.target.value;
        setSortOption(option);

        const sortedJobs = [...jobs].sort((a, b) => {
            if (option === "match_percentage") {
                return b.match_percentage - a.match_percentage;
            } else if (option === "title") {
                return a.title.localeCompare(b.title);
            } else if (option === "company") {
                return a.company.localeCompare(b.company);
            } else if (option === "date") {
                return b.created_at - a.created_at;
            }
            return 0;
        });

        setJobs(sortedJobs);
    };

    // Load a saved search
    const loadSearch = (savedSearch) => {
        setPosition(savedSearch.position);
        setExperience(savedSearch.experience);
        submit();
    };

    // Calculate pagination
    const indexOfLastJob = currentPage * itemsPerPage;
    const indexOfFirstJob = indexOfLastJob - itemsPerPage;
    const currentJobs = jobs.slice(indexOfFirstJob, indexOfLastJob);
    const totalPages = Math.ceil(jobs.length / itemsPerPage);

    // Change page
    const paginate = (pageNumber) => setCurrentPage(pageNumber);

    return (
        <>
            <Navbar />
            <main className="px-6 md:px-10 py-20 md:py-30 min-h-screen bg-background flex flex-col items-center">
                <div className="w-full max-w-4xl">
                    <Text type="h1">Find a Job</Text>

                    {/* Search Form */}
                    <div className="mt-6 flex flex-col gap-4 bg-white p-6 rounded-lg shadow-md">
                        <div>
                            <label htmlFor="position" className="block text-sm font-medium text-gray-700 mb-1">
                                Position / Role
                            </label>
                            <Input
                                id="position"
                                placeholder="e.g. Frontend Developer, Data Scientist"
                                value={position}
                                onChange={handlePositionChange}
                                className={errors.position ? "border-red-500" : ""}
                            />
                            {errors.position && (
                                <p className="text-red-500 text-sm mt-1">{errors.position}</p>
                            )}
                        </div>

                        <div>
                            <label htmlFor="experience" className="block text-sm font-medium text-gray-700 mb-1">
                                Your Experience & Skills
                            </label>
                            <textarea
                                id="experience"
                                ref={textareaRef}
                                value={experience}
                                onChange={handleTextareaInput}
                                placeholder="Describe your work experience, technical skills, education, and projects..."
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

                    {/* Recent Searches */}
                    {searchHistory.length > 0 && (
                        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
                            <div className="flex justify-between items-center mb-4">
                                <Text type="h3">Recent Searches</Text>
                                <button
                                    onClick={clearHistory}
                                    className="text-sm text-gray-500 hover:text-gray-700"
                                >
                                    Clear History
                                </button>
                            </div>
                            <div className="space-y-2">
                                {searchHistory.slice(0, 3).map((search) => (
                                    <div key={search.id} className="flex justify-between p-3 bg-gray-50 rounded-md hover:bg-gray-100">
                                        <div>
                                            <p className="font-medium">{search.position}</p>
                                            <p className="text-sm text-gray-500">
                                                {new Date(search.timestamp).toLocaleDateString()} •
                                                {search.resultCount} results
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => loadSearch(search)}
                                            className="text-blue-500 hover:text-blue-700"
                                        >
                                            Load
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Error Message */}
                    {errorMessage && (
                        <div className="mt-6 p-4 bg-red-50 text-red-700 rounded-md">
                            {errorMessage}
                        </div>
                    )}

                    {/* Loading Indicator */}
                    {isLoading && (
                        <div className="flex justify-center mt-8">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500"></div>
                        </div>
                    )}

                    {/* Results Section */}
                    {jobs.length > 0 && !isLoading && (
                        <div className="mt-10">
                            <div className="flex justify-between items-center mb-6">
                                <Text type="h2">Matching Jobs ({jobs.length})</Text>
                                <div className="flex items-center">
                                    <label htmlFor="sort" className="mr-2 text-sm text-gray-600">Sort by:</label>
                                    <select
                                        id="sort"
                                        value={sortOption}
                                        onChange={handleSortChange}
                                        className="bg-white p-2 border border-gray-300 rounded-md text-sm"
                                    >
                                        <option value="match_percentage">Match %</option>
                                        <option value="title">Job Title</option>
                                        <option value="company">Company</option>
                                        <option value="date">Date Posted</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex flex-col items-center gap-6">
                                {currentJobs.map((job, index) => (
                                    <JobCard key={index} data={job} />
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex justify-center mt-8">
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => paginate(Math.max(1, currentPage - 1))}
                                            disabled={currentPage === 1}
                                            className={`px-4 py-2 rounded-md ${
                                                currentPage === 1
                                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                            }`}
                                        >
                                            Previous
                                        </button>

                                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((number) => (
                                            <button
                                                key={number}
                                                onClick={() => paginate(number)}
                                                className={`px-4 py-2 rounded-md ${
                                                    currentPage === number
                                                        ? 'bg-blue-500 text-white'
                                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                                }`}
                                            >
                                                {number}
                                            </button>
                                        ))}

                                        <button
                                            onClick={() => paginate(Math.min(totalPages, currentPage + 1))}
                                            disabled={currentPage === totalPages}
                                            className={`px-4 py-2 rounded-md ${
                                                currentPage === totalPages
                                                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                            }`}
                                        >
                                            Next
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* No Results Message */}
                    {!isLoading && jobs.length === 0 && position.trim() !== "" && experience.trim() !== "" && (
                        <div className="text-center py-8 mt-6 bg-white rounded-lg shadow-md">
                            <Text type="h3" className="text-gray-700">No matching jobs found</Text>
                            <p className="text-gray-500 mt-2">Try adjusting your search terms or adding more details to your experience.</p>
                        </div>
                    )}
                </div>
            </main>
            <Footer/>
        </>
    );
};