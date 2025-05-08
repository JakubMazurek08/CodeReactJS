// src/components/FlashcardsSection.tsx
import React, { useState, useEffect } from "react";
import { Flashcard } from "./FlashCard";
import { Text } from "./Text";

interface Card {
    id: number | string;
    front: string;
    back: string;
}

interface FlashcardSet {
    id: string;
    title: string;
    description: string;
    cards: Card[];
}

interface FlashcardsSectionProps {
    flashcardSet?: FlashcardSet;
    className?: string;
}

export const FlashcardsSection: React.FC<FlashcardsSectionProps> = ({
                                                                        flashcardSet,
                                                                        className = ""
                                                                    }) => {
    const [currentCardIndex, setCurrentCardIndex] = useState(0);
    const [isFlipped, setIsFlipped] = useState(false);
    const [completedCards, setCompletedCards] = useState<string[]>([]);
    const [showSummary, setShowSummary] = useState(false);
    const [confidence, setConfidence] = useState<Record<string, string>>({});

    // Return early if no flashcard set is provided
    if (!flashcardSet || !flashcardSet.cards || flashcardSet.cards.length === 0) {
        return (
            <div className={`bg-white rounded-lg shadow-xl p-6 ${className}`}>
                <Text type="h3" className="font-semibold mb-4">Interview Flashcards</Text>
                <p className="text-gray-500 text-center py-8">No flashcards available for this interview.</p>
            </div>
        );
    }

    // Add CSS for 3D transforms
    useEffect(() => {
        const style = document.createElement("style");
        style.innerHTML = `
      .perspective-1000 {
        perspective: 1000px;
      }
      .transform-style-preserve-3d {
        transform-style: preserve-3d;
      }
      .backface-hidden {
        backface-visibility: hidden;
      }
      .rotate-y-180 {
        transform: rotateY(180deg);
      }
    `;
        document.head.appendChild(style);
        return () => {
            // Cleanup the style element
            document.head.removeChild(style);
        };
    }, []);

    const handleToggleFlip = () => {
        setIsFlipped(!isFlipped);
    };

    const handleMarkConfidence = (level: string) => {
        const currentCard = flashcardSet.cards[currentCardIndex];
        const cardId = typeof currentCard.id === 'number'
            ? `card-${currentCard.id}`
            : currentCard.id.toString();

        const updatedConfidence = {
            ...confidence,
            [cardId]: level,
        };
        setConfidence(updatedConfidence);

        // Add to completed cards
        if (!completedCards.includes(cardId)) {
            setCompletedCards([
                ...completedCards,
                cardId,
            ]);
        }

        // Move to next card
        handleNextCard();
    };

    const handleNextCard = () => {
        if (currentCardIndex < flashcardSet.cards.length - 1) {
            setCurrentCardIndex(currentCardIndex + 1);
            setIsFlipped(false);
        } else {
            // End of deck, show summary
            setShowSummary(true);
        }
    };

    const handlePrevCard = () => {
        if (currentCardIndex > 0) {
            setCurrentCardIndex(currentCardIndex - 1);
            setIsFlipped(false);
        }
    };

    const handleRestartSet = () => {
        setCurrentCardIndex(0);
        setIsFlipped(false);
        setCompletedCards([]);
        setConfidence({});
        setShowSummary(false);
    };

    // Calculate confidence levels for summary
    const getConfidenceSummary = () => {
        const total = flashcardSet.cards.length;
        const confidenceCounts = {
            high: 0,
            medium: 0,
            low: 0,
        };

        Object.values(confidence).forEach((level) => {
            confidenceCounts[level as keyof typeof confidenceCounts]++;
        });

        return {
            high: confidenceCounts.high,
            medium: confidenceCounts.medium,
            low: confidenceCounts.low,
            total: total,
        };
    };

    return (
        <div className={`bg-white rounded-lg shadow-xl p-6 ${className}`}>
            <Text type="h3" className="font-semibold mb-4">Interview Flashcards</Text>

            {showSummary ? (
                // Summary view after completing the set
                <div>
                    <div className="bg-gray-50 rounded-xl p-6 mb-4">
                        <Text type="h4" className="font-bold mb-3 text-gray-800">
                            Study Summary
                        </Text>
                        <p className="mb-4 text-gray-600">
                            You've completed studying "{flashcardSet.title}"
                        </p>

                        {/* Summary statistics */}
                        <div className="mb-6">
                            <h5 className="font-medium text-md mb-2 text-gray-700">
                                Your confidence levels:
                            </h5>
                            <div className="flex justify-between mb-4">
                                <div className="text-center">
                                    <div className="text-xl font-bold text-green-600">
                                        {getConfidenceSummary().high}
                                    </div>
                                    <div className="text-xs text-gray-500">High</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-xl font-bold text-yellow-500">
                                        {getConfidenceSummary().medium}
                                    </div>
                                    <div className="text-xs text-gray-500">Medium</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-xl font-bold text-red-500">
                                        {getConfidenceSummary().low}
                                    </div>
                                    <div className="text-xs text-gray-500">Low</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-xl font-bold">
                                        {getConfidenceSummary().total - completedCards.length}
                                    </div>
                                    <div className="text-xs text-gray-500">Skipped</div>
                                </div>
                            </div>

                            {/* Progress bar */}
                            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div className="flex h-full">
                                    <div
                                        className="bg-green-500 h-full"
                                        style={{
                                            width: `${
                                                (getConfidenceSummary().high /
                                                    getConfidenceSummary().total) *
                                                100
                                            }%`,
                                        }}
                                    ></div>
                                    <div
                                        className="bg-yellow-500 h-full"
                                        style={{
                                            width: `${
                                                (getConfidenceSummary().medium /
                                                    getConfidenceSummary().total) *
                                                100
                                            }%`,
                                        }}
                                    ></div>
                                    <div
                                        className="bg-red-500 h-full"
                                        style={{
                                            width: `${
                                                (getConfidenceSummary().low /
                                                    getConfidenceSummary().total) *
                                                100
                                            }%`,
                                        }}
                                    ></div>
                                </div>
                            </div>
                        </div>

                        {/* Action buttons */}
                        <div className="flex justify-center">
                            <button
                                onClick={handleRestartSet}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                            >
                                Study Again
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                // Study mode view
                <div className="flex flex-col items-center">
                    <div className="w-full">
                        {/* Title and description */}
                        <div className="mb-4 text-center">
                            <Text type="h4" className="font-medium text-gray-800">
                                {flashcardSet.title}
                            </Text>
                            <p className="text-sm text-gray-600">{flashcardSet.description}</p>
                        </div>

                        {/* Study progress */}
                        <div className="mb-4">
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-500 h-2 rounded-full"
                                    style={{
                                        width: `${
                                            ((currentCardIndex + 1) / flashcardSet.cards.length) * 100
                                        }%`,
                                    }}
                                ></div>
                            </div>
                            <div className="text-xs text-gray-500 text-right mt-1">
                                {currentCardIndex + 1} of {flashcardSet.cards.length}
                            </div>
                        </div>

                        {/* Flashcard with flip animation */}
                        <div className="mb-6">
                            <Flashcard
                                front={flashcardSet.cards[currentCardIndex].front}
                                back={flashcardSet.cards[currentCardIndex].back}
                                isFlipped={isFlipped}
                                onClick={handleToggleFlip}
                            />
                        </div>

                        {/* When card is flipped (showing answer), show confidence buttons */}
                        {isFlipped && (
                            <div className="mb-6">
                                <p className="text-center mb-2 text-sm text-gray-700 font-medium">
                                    How well did you know this?
                                </p>
                                <div className="flex justify-center space-x-3">
                                    <button
                                        onClick={() => handleMarkConfidence("low")}
                                        className="px-3 py-1 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition"
                                    >
                                        Not Well
                                    </button>
                                    <button
                                        onClick={() => handleMarkConfidence("medium")}
                                        className="px-3 py-1 text-sm bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition"
                                    >
                                        Somewhat
                                    </button>
                                    <button
                                        onClick={() => handleMarkConfidence("high")}
                                        className="px-3 py-1 text-sm bg-green-500 text-white rounded-md hover:bg-green-600 transition"
                                    >
                                        Very Well
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Navigation buttons */}
                        <div className="flex justify-between">
                            <button
                                onClick={handlePrevCard}
                                disabled={currentCardIndex === 0}
                                className={`px-3 py-1 text-sm rounded-md ${
                                    currentCardIndex === 0
                                        ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                                        : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                                } transition`}
                            >
                                Previous
                            </button>
                            {isFlipped ? (
                                <button
                                    onClick={handleNextCard}
                                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                                >
                                    {currentCardIndex === flashcardSet.cards.length - 1 ? "Finish" : "Next"}
                                </button>
                            ) : (
                                <button
                                    onClick={handleToggleFlip}
                                    className="px-3 py-1 text-sm bg-gray-800 text-white rounded-md hover:bg-gray-900 transition"
                                >
                                    Show Answer
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};