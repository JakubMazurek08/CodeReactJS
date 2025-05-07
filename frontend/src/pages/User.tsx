import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getAuth, signOut } from "firebase/auth";
import { Navbar } from "../components/Navbar";
import { Text } from "../components/Text";
import { Button } from "../components/Button";

export const User = () => {
    const [user, setUser] = useState<{
        displayName: string | null;
        email: string | null;
        photoURL: string | null;
    } | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();
    const auth = getAuth();

    useEffect(() => {
        // Check authentication state when component mounts
        const unsubscribe = auth.onAuthStateChanged((currentUser) => {
            if (currentUser) {
                // User is signed in
                setUser({
                    displayName: currentUser.displayName,
                    email: currentUser.email,
                    photoURL: currentUser.photoURL
                });
            } else {
                // User is not signed in, redirect to login
                navigate("/login");
            }
            setIsLoading(false);
        });

        // Cleanup subscription on unmount
        return () => unsubscribe();
    }, [auth, navigate]);

    const handleLogout = async () => {
        try {
            await signOut(auth);
            navigate("/");
        } catch (error) {
            console.error("Error signing out: ", error);
        }
    };

    if (isLoading) {
        return (
            <>
                <Navbar />
                <div className="flex justify-center items-center min-h-screen bg-background">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue"></div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <main className="px-6 sm:px-12 md:px-24 lg:px-32 pt-30 min-h-screen bg-background">
                <div className="max-w-4xl mx-auto">
                    <div className="bg-white rounded-lg shadow-lg p-8 mt-8">
                        <div className="flex flex-col md:flex-row items-center gap-8">
                            <div className="flex-1 text-center md:text-left">
                                <Text type="h2">
                                    {user?.displayName || "User"}
                                </Text>
                                <Text className="text-gray-600 mt-2">
                                    {user?.email || "No email provided"}
                                </Text>
                            </div>

                            <Button
                                onClick={handleLogout}
                                color="blue"
                                className="mt-4 md:mt-0"
                            >
                                Logout
                            </Button>
                        </div>

                        <div className="mt-12 border-t pt-8">
                            <Text type="h3">Your Activity</Text>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                                <div className="bg-gray-50 p-6 rounded-lg">
                                    <Text type="h4">Recent Job Applications</Text>
                                    <div className="mt-4">
                                        <p className="text-gray-500">You haven't applied to any jobs yet.</p>
                                    </div>
                                </div>

                                <div className="bg-gray-50 p-6 rounded-lg">
                                    <Text type="h4">Saved Jobs</Text>
                                    <div className="mt-4">
                                        <p className="text-gray-500">No saved jobs found.</p>
                                    </div>
                                </div>

                                <div className="bg-gray-50 p-6 rounded-lg">
                                    <Text type="h4">Interview Practice</Text>
                                    <div className="mt-4">
                                        <p className="text-gray-500">You haven't completed any practice interviews.</p>
                                    </div>
                                </div>

                                <div className="bg-gray-50 p-6 rounded-lg">
                                    <Text type="h4">Account Settings</Text>
                                    <div className="mt-4">
                                        <Button color="green" className="mb-2">
                                            Edit Profile
                                        </Button>
                                        <p className="text-sm text-gray-500 mt-2">
                                            Update your personal information and preferences
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </>
    );
};