import {Text} from "./Text.tsx";
import {Button} from "./Button.tsx"
import {useNavigate} from "react-router-dom";
import {useContext} from "react";
import {jobContext} from "../context/jobContext.ts";

export const JobCard = ({data}:any) => {
    const navigate = useNavigate();
    const {setJob} = useContext(jobContext);

    return (
        <div className="bg-white shadow-lg rounded-[10px] w-full max-w-4xl p-6 flex flex-col md:flex-row justify-between gap-6">
            <div className="flex-1 flex flex-col justify-between gap-4">
                <Text type="h2">{data.title} - {data.company}</Text>
                <div>
                    <Text type="p">{data.location}</Text>
                </div>
            </div>
            <div className="flex flex-col w-1/3 justify-between gap-4 items-start">
                <div className="flex gap-2 items-center">
                    <img className="h-5" src="iconMoney.png" alt="Salary"/>
                    <Text>{data.salary_range}</Text>
                </div>
                <div className="flex gap-2 items-center">
                    <img className="h-5" src="iconTime.png" alt="Time"/>
                    <Text>{data.employment_type}</Text>
                </div>
                <Button onClick={()=>{setJob(data);navigate(`/interview/${data.id}`)}} color={'green'}>Practice Interview</Button>
            </div>
        </div>
    );
};
