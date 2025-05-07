import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    children: React.ReactNode;
    color?: "green" | "blue";
    className?: string;
}

export const Button = ({
                           children,
                           color = "blue",
                           className = "",
                           ...props
                       }: ButtonProps) => {
    const colorClassMap = {
        green: {
            background: "bg-green",
        },
        blue: {
            background: "bg-blue",
        },
    };

    const selectedColor = colorClassMap[color];

    const baseClasses =
        "w-fit px-4 py-1 rounded-lg cursor-pointer active:scale-95 transition-all duration-200 text-[20px] text-white font-roboto";

    return (
        <button
            className={`${baseClasses} ${selectedColor.background} ${className}`}
            {...props}
        >
            {children}
        </button>
    );
};