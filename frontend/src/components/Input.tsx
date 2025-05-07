interface InputsProps extends React.InputHTMLAttributes<HTMLInputElement>{
    placeholder?: string;
};

export const Input = ({placeholder, ...rest}:InputsProps) => {
    return (
        <input {...rest} placeholder={placeholder}
               className={`w-full p-4 shadow-md  bg-white  text-[16px] text-black font-roboto rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400`}/>
    )
}