import {Text} from "./Text.tsx";
import {Link} from "react-router-dom";

export const Navbar = () => {
    return(
        <nav className={'bg-white fixed border-b-2 w-screen h-16 border-green justify-between items-center px-[100px] flex'}>
            <Link to={'/'}><h1 className={'font-bold text-[32px]'}><span className='text-green'>Job</span><span className={'text-blue'}>Prep</span><span className={'text-black'}>AI</span></h1></Link>
            <div className={"h-full items-center gap-20 hidden md:flex"}>
                <Link to={'/'}><Text type={'h4'}>Find Job</Text></Link>
                <Link to={'/'}><Text type={'h4'}>About</Text></Link>
                <Link to={'/'}><Text type={'h4'}>Our Team</Text></Link>
                <Link to={'/user'} className="ml-4">
                    <div className="w-10 h-10 bg-blue text-white rounded-full flex items-center justify-center hover:bg-blue-600 transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>
                </Link>
            </div>
        </nav>
    )
}