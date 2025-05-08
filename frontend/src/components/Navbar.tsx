import { Text } from "./Text.tsx";
import { Link } from "react-router-dom";
import { useState } from "react";

export const Navbar = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    return(
<<<<<<< HEAD
        <nav className={'bg-white fixed border-b-2 w-screen h-16 border-green justify-between items-center px-4 md:px-[100px] flex z-50'}>
            <Link to={'/'}>
                <h1 className={'font-bold text-[32px]'}>
                    <span className={'text-blue-800'}>Interv</span>
                    
                    <span className={'text-black'}>You</span>
=======
        <nav className={'bg-white fixed border-b w-full h-16 border-gray-200 shadow-sm justify-between items-center px-4 md:px-[100px] flex z-50'}>
            <Link to={'/'} className="flex items-center">
                <h1 className={'font-bold text-[28px] md:text-[32px]'}>
                    <span className='text-green'>Job</span>
                    <span className={'text-blue'}>Prep</span>
                    <span className={'text-black'}>AI</span>
>>>>>>> 1f3fe06b526fa12a6ccec2374c6c2ffdaeed6bcd
                </h1>
            </Link>

            {/* Desktop Menu */}
            <div className={"h-full items-center gap-8 hidden md:flex"}>
                <Link to={'/home'} className="relative group">
                    <Text type={'h4'} className="text-gray-700 hover:text-blue transition-colors">Find Jobs</Text>
                    <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-blue group-hover:w-full transition-all duration-300"></span>
                </Link>
                <Link to={'/interviews'} className="relative group">
                    <Text type={'h4'} className="text-gray-700 hover:text-blue transition-colors">My Interviews</Text>
                    <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-blue group-hover:w-full transition-all duration-300"></span>
                </Link>
                <Link to={'/user'} className="ml-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-blue to-green text-white rounded-full flex items-center justify-center hover:shadow-md transition-all duration-300 hover:scale-105">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                        </svg>
                    </div>
                </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
                className="md:hidden flex items-center p-2 rounded-md hover:bg-gray-100 transition-colors"
                onClick={toggleMenu}
                aria-label="Toggle menu"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-6 w-6 text-gray-700"
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
                <div className="absolute top-16 left-0 right-0 bg-white shadow-lg py-4 px-6 md:hidden flex flex-col gap-4 border-b border-gray-200 animate-fadeIn">
                    <Link to={'/home'} onClick={() => setIsMenuOpen(false)} className="p-2 hover:bg-gray-50 rounded-md transition-colors">
                        <Text type={'h4'} className="text-gray-700">Find Jobs</Text>
                    </Link>
                    <Link to={'/interviews'} onClick={() => setIsMenuOpen(false)} className="p-2 hover:bg-gray-50 rounded-md transition-colors">
                        <Text type={'h4'} className="text-gray-700">My Interviews</Text>
                    </Link>
                    <Link to={'/user'} onClick={() => setIsMenuOpen(false)} className="p-2 hover:bg-gray-50 rounded-md transition-colors flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-blue to-green text-white rounded-full flex items-center justify-center">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                            </svg>
                        </div>
                        <Text type={'h4'} className="text-gray-700">Profile</Text>
                    </Link>
                </div>
            )}
        </nav>
    );
};