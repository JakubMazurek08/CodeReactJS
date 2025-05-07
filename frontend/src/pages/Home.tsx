import {Navbar} from "../components/Navbar.tsx";
import {Text} from "../components/Text.tsx";
import {Input} from "../components/Input.tsx";

export const Home = () => {
    return <>
        <Navbar/>
        <main className={'px-[400px] pt-30 min-h-screen bg-background'}>
            <Text type={'h1'}>Find a Job</Text>
            <Input placeholder={'Position, company, key words...'}></Input>
            <div className={'w-1/2 flex flex-col gap-16'}>
                {/*Tu bedziemy mapowac karty*/}
            </div>
        </main>
    </>
}