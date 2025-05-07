import { type ReactNode, useEffect, useState } from "react";
import { onAuthStateChanged } from "firebase/auth";
import { Navigate } from "react-router-dom";
import {auth} from "./lib/firebase.ts";

export const ProtectedRoute = ({ children }: { children: ReactNode }) => {
    const [userChecked, setUserChecked] = useState(false);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            setIsAuthenticated(!!user);
            setUserChecked(true);
        });

        return () => unsubscribe();
    }, []);

    if (!userChecked) return <div>Loading...</div>;

    return isAuthenticated ? <>{children}</> : <Navigate to="/login" />;
};
