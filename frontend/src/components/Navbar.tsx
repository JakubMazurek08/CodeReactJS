import { Text } from "./Text.tsx";
import { Link } from "react-router-dom";
import { useState } from "react";

export const Navbar = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    return(
        <nav className={'bg-white fixed border-b-2 w-screen h-16 border-green justify-between items-center px-4 md:px-[100px] flex z-50'}>
            <Link to={'/'}>
                <h1 className={'font-bold text-[32px]'}>
                    <span className={'text-blue-800'}>Interv</span>
                    
                    <span className={'text-black'}>You</span>
                </h1>
            </Link>

            {/* Desktop Menu */}
            <div className={"h-full items-center gap-10 hidden md:flex"}>
                <Link to={'/home'}>
                    <Text type={'h4'}>Find Jobs</Text>
                </Link>
                <Link to={'/interviews'}>
                    <Text type={'h4'}>My Interviews</Text>
                </Link>
                <Link to={'/user'} className="ml-4">
                    <div className="w-10 h-10 bg-blue text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>
                </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
                className="md:hidden flex items-center"
                onClick={toggleMenu}
                aria-label="Toggle menu"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    {isMenuOpen ? (
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M6 18L18 6M6 6l12 12"
                        />
                    ) : (
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 6h16M4 12h16M4 18h16"
                        />
                    )}
                </svg>
            </button>

            {/* Mobile Menu Dropdown */}
            {isMenuOpen && (
                <div className="absolute top-16 left-0 right-0 bg-white shadow-md py-4 px-6 md:hidden flex flex-col gap-4 border-b border-gray-200">
                    <Link to={'/home'} onClick={() => setIsMenuOpen(false)}>
                        <Text type={'h4'}>Find Jobs</Text>
                    </Link>
                    <Link to={'/interviews'} onClick={() => setIsMenuOpen(false)}>
                        <Text type={'h4'}>My Interviews</Text>
                    </Link>
                    <Link to={'/user'} onClick={() => setIsMenuOpen(false)}>
                        <Text type={'h4'}>Profile</Text>
                    </Link>
                </div>
            )}
        </nav>
    );
};