import {createBrowserRouter, RouterProvider} from "react-router-dom";
import {LoginPage} from "./pages/LoginPage";
import {Home} from "./pages/Home.tsx";
import {InterviewChatbot} from "./pages/InterviewChatbot.tsx";
import {LandingPage} from "./pages/LandingPage";

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
    }
]);

export const Router = () => {
    return (
        <RouterProvider router={router}/>
    )
}