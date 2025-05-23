interface TextProps {
    children: React.ReactNode;
    type?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'small' | 'nav';
    className?: string;
}

export const Text = ({children, type, className = ""}:TextProps) => {
    if (type === 'h1') {
        return <h1 className={`text-[36px] text-black font-bold font-roboto ${className}`}>{children}</h1>;
    }else if (type === 'h2'){
        return <h2 className={`text-[28px] text-black font-semibold font-roboto ${className}`}>{children}</h2>;
    }else if (type === 'h3'){
        return <h3 className={`text-[24px] text-black font-semibold font-roboto ${className}`}>{children}</h3>;
    }else if (type === 'h4'){
        return <h4 className={`text-[20px] text-black font-roboto ${className}`}>{children}</h4>;
    }
    return <p className={`text-[16px] text-black font-roboto ${className}`}>{children}</p>;
}