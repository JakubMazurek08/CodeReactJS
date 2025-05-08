import {createBrowserRouter, RouterProvider} from "react-router-dom";
import {LoginPage} from "./pages/LoginPage";
import {Home} from "./pages/Home.tsx";
import {InterviewChatbot} from "./pages/InterviewChatbot.tsx";
import {User} from "./pages/User.tsx";
import {ProtectedRoute} from "./ProtectedRoute.tsx";
import {LandingPage} from "./pages/LandingPage";
import {InterviewPage} from "./pages/InterviewPage.tsx";

const router = createBrowserRouter([
    {
        path: "/",
        element: <LandingPage/>
    },
    {
        path: "/home",
        element: <Home/>
    },
    {
        path: "/login",
        element: <LoginPage />
    },
    {
        path: "/interview/:id",
        element: <InterviewChatbot/>
    },
    {
        path: "/user",
        element: <ProtectedRoute><User/></ProtectedRoute>
    },
    {
        path: "/interviews",
        element: <ProtectedRoute><InterviewPage/></ProtectedRoute>
    }
]);

export const Router = () => {
    return (
        <RouterProvider router={router}/>
    )
}