import { useState } from "react";
import { useForm } from "react-hook-form";
import { createUserWithEmailAndPassword, signInWithEmailAndPassword } from "firebase/auth";
import { setDoc, doc, collection } from "firebase/firestore";
import { auth, db } from "../lib/firebase.ts";
import {useNavigate} from "react-router-dom";

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

    const {
        register,
        handleSubmit,
        reset,
        formState: { errors },
    } = useForm<FormFields>();

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
        <div className="w-screen h-screen flex flex-col items-center justify-center p-4">
            <h1 className="text-5xl font-bold mb-2">{isRegistering ? "Create Account" : "Log in"}</h1>
            <button onClick={toggleMode} className="text-sm mb-4 text-primary-light hover:underline">
                {isRegistering ? "Already have an account? Log in" : "Don't have an account? Register"}
            </button>

            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 w-full max-w-sm">
                {errorLoggingIn && (
                    <div className="text-red-500 font-medium">Invalid email or password.</div>
                )}

                <div className="flex flex-col">
                    <label>Email</label>
                    <input
                        autoFocus
                        {...register("email", {
                            required: "Email is required",
                            validate: (email) =>
                                /\S+@\S+\.\S+/.test(email) || "Please enter a valid email",
                        })}
                        placeholder="you@example.com"
                        className={`mt-1 p-2 border-2 rounded-md ${
                            errors.email ? "border-red-500" : "border-primary-light"
                        }`}
                    />
                    {errors.email && (
                        <span className="text-red-500 text-sm">{errors.email.message}</span>
                    )}
                </div>

                <div className="flex flex-col">
                    <label>Password</label>
                    <input
                        type="password"
                        {...register("password", { required: "Password is required" })}
                        placeholder="Your password"
                        className={`mt-1 p-2 border-2 rounded-md ${
                            errors.password ? "border-red-500" : "border-primary-light"
                        }`}
                    />
                    {errors.password && (
                        <span className="text-red-500 text-sm">{errors.password.message}</span>
                    )}
                </div>

                {isRegistering && (
                    <div className="flex flex-col">
                        <label>Username</label>
                        <input
                            {...register("username", { required: "Username is required" })}
                            placeholder="Your username"
                            className={`mt-1 p-2 border-2 rounded-md ${
                                errors.username ? "border-red-500" : "border-primary-light"
                            }`}
                        />
                        {errors.username && (
                            <span className="text-red-500 text-sm">{errors.username.message}</span>
                        )}
                    </div>
                )}

                <button
                    type="submit"
                    disabled={loading}
                    className="mt-4 py-2 rounded bg-gray-200"
                >
                    {loading ? "Please wait..." : isRegistering ? "Register" : "Log in"}
                </button>
            </form>
        </div>
    );
};
