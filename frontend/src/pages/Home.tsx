import {Navbar} from "../components/Navbar.tsx";
import {Text} from "../components/Text.tsx";
import {Input} from "../components/Input.tsx";
import {JobCard} from "../components/JobCard.tsx";

export const Home = () => {
    return <>
        <Navbar/>
        <main className="px-6 pt-30 min-h-screen bg-background flex flex-col items-center">
            <div className="w-full max-w-5xl">
                <Text type="h1">Find a Job</Text>
                <Input placeholder="Position, company, key words..."/>
                <div className="flex flex-col items-center gap-10 mt-10">
                    <JobCard/>
                    <JobCard/>
                </div>
            </div>
        </main>

    </>
}