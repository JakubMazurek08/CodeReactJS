import {Text} from "./Text.tsx";
import {Link} from "react-router-dom";

export const Navbar = () => {
    return(
        <nav className={'bg-white fixed border-b-2 w-screen h-16 border-green justify-between items-center px-[100px] flex'}>
            <Link to={'/'}><h1 className={'font-bold text-[32px]'}><span className='text-green'>Job</span><span className={'text-blue'}>Prep</span><span className={'text-black'}>AI</span></h1></Link>
            <div className={"h-full flex items-center gap-20"}>
                <Link to={'/'}><Text type={'h4'}>Find Job</Text></Link>
                <Link to={'/'}><Text type={'h4'}>About</Text></Link>
                <Link to={'/'}><Text type={'h4'}>Our Team</Text></Link>
            </div>
        </nav>
    )
}