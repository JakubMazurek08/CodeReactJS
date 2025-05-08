import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";
import { setDoc, doc, collection } from "firebase/firestore";
import { auth, db } from "../lib/firebase.ts";
import { useNavigate } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Text } from "../components/Text";
import { Button } from "../components/Button";

type FormFields = {
    email: string;
    password: string;
    username?: string;
};

export const LoginPage = () => {
    const [isRegistering, setIsRegistering] = useState(false);
    const [loading, setLoading] = useState(false);
    const [errorLoggingIn, setErrorLoggingIn] = useState(false);
    const navigate = useNavigate();
    const [show, setShow] = useState(false);

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<FormFields>();

    useEffect(() => { setShow(true); }, []);

    const addUser = async (id: string, username: string) => {
        const userCollectionRef = collection(db, "users");
        await setDoc(doc(userCollectionRef, id), {
            username,
            creationDate: new Date().toLocaleDateString("pl-PL"),
        });
    };

    const onSubmit = async ({ email, password, username }: FormFields) => {
        setLoading(true);
        setErrorLoggingIn(false);
        try {
            if (isRegistering) {
                if (!username) return;
                const userCredential = await createUserWithEmailAndPassword(auth, email, password);
                await addUser(userCredential.user.uid, username);
                console.log("Registration success!", userCredential.user);
                navigate("/");
            } else {
                const userCredential = await signInWithEmailAndPassword(auth, email, password);
                console.log("Login success!", userCredential.user);
                navigate("/");
            }
            reset();
        } catch (error: any) {
            console.error("Auth error:", error.code, error.message);
            setErrorLoggingIn(true);
        } finally {
            setLoading(false);
        }
    };


    const toggleMode = () => {
        setIsRegistering(prev => !prev);
        setErrorLoggingIn(false);
    };

    return (
        <>
            <Navbar />
            <div className="w-screen h-screen flex flex-col items-center justify-center p-4 bg-background">
                <div className={`bg-white shadow-lg rounded-lg p-8 w-full max-w-md transition-all duration-700 ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
                    <div className="text-center mb-8">
                        <Text type="h2">
                            {isRegistering ? "Create Account" : "Log In"}
                        </Text>
                        <button
                            onClick={toggleMode}
                            className="text-sm text-blue hover:underline transition-colors"
                        >
                            {isRegistering ? "Already have an account? Log in" : "Don't have an account? Register"}
                        </button>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5">
                        {errorLoggingIn && (
                            <div className="bg-red-50 text-red-500 p-3 rounded-md text-center font-medium">
                                Invalid email or password.
                            </div>
                        )}

                        <div className="flex flex-col">
                            <label className="mb-1 font-medium">Email</label>
                            <input
                                autoFocus
                                {...register("email", {
                                    required: "Email is required",
                                    validate: (email) =>
                                        /\S+@\S+\.\S+/.test(email) || "Please enter a valid email",
                                })}
                                placeholder="you@example.com"
                                className={`p-3 border rounded-lg focus:outline-none transition-all ${
                                    errors.email
                                        ? "border-red-500 focus:ring-2 focus:ring-red-200"
                                        : "border-gray-200 focus:ring-2 focus:ring-blue-200"
                                }`}
                            />
                            {errors.email && (
                                <span className="text-red-500 text-sm mt-1">{errors.email.message}</span>
                            )}
                        </div>

                        <div className="flex flex-col">
                            <label className="mb-1 font-medium">Password</label>
                            <input
                                type="password"
                                {...register("password", {
                                    required: "Password is required",
                                    minLength: {
                                        value: 6,
                                        message: "Password must be at least 6 characters"
                                    }
                                })}
                                placeholder="Your password"
                                className={`p-3 border rounded-lg focus:outline-none transition-all ${
                                    errors.password
                                        ? "border-red-500 focus:ring-2 focus:ring-red-200"
                                        : "border-gray-200 focus:ring-2 focus:ring-blue-200"
                                }`}
                            />
                            {errors.password && (
                                <span className="text-red-500 text-sm mt-1">{errors.password.message}</span>
                            )}
                        </div>

                        {isRegistering && (
                            <div className="flex flex-col">
                                <label className="mb-1 font-medium">Username</label>
                                <input
                                    {...register("username", {
                                        required: "Username is required",
                                        minLength: {
                                            value: 3,
                                            message: "Username must be at least 3 characters"
                                        }
                                    })}
                                    placeholder="Your username"
                                    className={`p-3 border rounded-lg focus:outline-none transition-all ${
                                        errors.username
                                            ? "border-red-500 focus:ring-2 focus:ring-red-200"
                                            : "border-gray-200 focus:ring-2 focus:ring-blue-200"
                                    }`}
                                />
                                {errors.username && (
                                    <span className="text-red-500 text-sm mt-1">{errors.username.message}</span>
                                )}
                            </div>
                        )}

                        <Button
                            type="submit"
                            disabled={loading}
                            color={isRegistering ? "green" : "blue"}
                            className={`mt-4 w-full transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 ${loading ? "opacity-70 cursor-not-allowed" : ""}`}
                        >
                            {loading ? "Please wait..." : isRegistering ? "Create Account" : "Log In"}
                        </Button>
                    </form>
                </div>
            </div>
        </>
    );
};