import {Text} from "./Text.tsx";
import {Button} from "./Button.tsx"

export const JobCard = () => {
    return (
        <div className="bg-white shadow-lg rounded-[10px] w-full max-w-4xl p-6 flex justify-between gap-6">
            <div className="flex-1 flex flex-col justify-between gap-4">
                <Text type="h2">Technical Solutions Engineer - Security, Google Cloud</Text>
                <div>
                    <Text type="p">Google</Text>
                    <Text type="p">Warszawa, Śródmieście</Text>
                </div>
            </div>
            <div className="flex flex-col justify-between gap-4 items-start">
                <div className="flex gap-2 items-center">
                    <img className="h-5" src="iconLanguage.png" alt="Language"/>
                    <Text>English, Polish</Text>
                </div>
                <div className="flex gap-2 items-center">
                    <img className="h-5" src="iconMoney.png" alt="Salary"/>
                    <Text>30k - 80k</Text>
                </div>
                <div className="flex gap-2 items-center">
                    <img className="h-5" src="iconTime.png" alt="Time"/>
                    <Text>Fulltime</Text>
                </div>
                <Button color={'green'}>Practice Interview</Button>
            </div>
        </div>
    );
};
