interface InputsProps extends React.InputHTMLAttributes<HTMLInputElement>{
    placeholder?: string;
    color?: 'green' | 'blue';
};

export const Input = ({color = 'blue', placeholder, ...rest}:InputsProps) => {
    return (
        <input {...rest}  placeholder={placeholder}
               className={`w-full border-1 bg-white ${color == 'blue' ? "border-blue" : "border-green"} text-[16px] text-black font-roboto py-[6px] px-4 rounded-full focus:outline-none`}/>
    )
}