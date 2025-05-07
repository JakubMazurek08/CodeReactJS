import {createBrowserRouter, RouterProvider} from "react-router-dom";
import {LoginPage} from "./pages/LoginPage";
import {ProtectedRoute} from "./ProtectedRoute.tsx";
import {Home} from "./pages/Home.tsx";

const router = createBrowserRouter([
    {
        path: "/",
        element: <ProtectedRoute><Home/></ProtectedRoute>
    },
    {
        path: "/login",
        element: <LoginPage />
    }
]);

export const Router = () => {
    return (
        <RouterProvider router={router}/>
    )
}