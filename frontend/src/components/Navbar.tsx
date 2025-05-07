import {Text} from "./Text.tsx";
import {Link} from "react-router-dom";

export const Navbar = () => {
    return(
        <nav className={'bg-white fixed border-b-2 w-screen h-20 border-green justify-between px-[100px] flex'}>
            <h1 className={'font-bold text-[48px]'}><span className='text-green'>Job</span><span className={'text-blue'}>Prep</span><span className={'text-black'}>AI</span></h1>
            <div className={"h-full flex items-center gap-16"}>
                <Link to={'/'}><Text type={'h3'}>Find Job</Text></Link>
                <Link to={'/'}><Text type={'h3'}>About</Text></Link>
                <Link to={'/'}><Text type={'h3'}>Our Team</Text></Link>
            </div>
        </nav>
    )
}