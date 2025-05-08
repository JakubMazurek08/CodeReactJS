// src/components/FlashCard.tsx
import React from "react";

interface FlashcardProps {
    front: string;
    back: string;
    isFlipped: boolean;
    onClick: () => void;
}

export const Flashcard: React.FC<FlashcardProps> = ({
                                                        front,
                                                        back,
                                                        isFlipped,
                                                        onClick,
                                                    }) => {
    return (
        <div
            className="cursor-pointer w-full h-60 perspective-1000"
            onClick={onClick}
        >
            <div
                className={`relative w-full h-full transform-style-preserve-3d transition-transform duration-500 ease-in-out ${
                    isFlipped ? "rotate-y-180" : ""
                }`}
            >
                {/* Front card */}
                <div
                    className={`absolute w-full h-full bg-white border border-gray-200 rounded-xl p-6 shadow-md backface-hidden transform ${
                        isFlipped ? "rotate-y-180" : ""
                    }`}
                >
                    <div className="flex flex-col justify-center items-center h-full">
                        <div className="text-center">
                            <p className="font-medium text-gray-800">{front}</p>
                        </div>
                        <div className="absolute bottom-3 right-3">
                            <p className="text-xs text-gray-400">Click to flip</p>
                        </div>
                    </div>
                </div>

                {/* Back card */}
                <div
                    className={`absolute w-full h-full bg-gray-50 border border-gray-200 rounded-xl p-6 shadow-md backface-hidden transform rotate-y-180 ${
                        isFlipped ? "" : "rotate-y-180"
                    }`}
                >
                    <div className="flex flex-col justify-center items-center h-full">
                        <div className="text-center">
                            <p className="font-medium text-gray-800">{back}</p>
                        </div>
                        <div className="absolute bottom-3 right-3">
                            <p className="text-xs text-gray-400">Click to flip</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};