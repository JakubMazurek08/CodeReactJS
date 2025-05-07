import {Text} from "./Text.tsx";

export const JobCard = () => {
    return(
        <div className={'bg-white shadow-2xl rounded-[10px] w-full p-8'}>
            <div className={'h-full flex-1 flex flex-col justify-between'}>
                <Text type={'h1'}>Technical Solutions Engineer - Security, Google Cloud</Text>
                <div>
                    <Text type={'h4'}>Google</Text>
                    <Text type={'p'}>Warszawa, Śródmieście</Text>
                </div>
            </div>
            <div className={'flex flex-col'}></div>
        </div>
    )
}