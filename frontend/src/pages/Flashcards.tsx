import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Footer } from "../components/Footer";

// Mock data - this would come from your backend after test/interview completion
const mockFlashcardSet = {
  id: 1,
  title: "Key Interview Concepts",
  description: "Important concepts from your interview test",
  cards: [
    {
      id: 1,
      front: "What is a closure?",
      back: "A function that has access to variables from its outer (enclosing) scope, even after the outer function has returned.",
    },
    {
      id: 2,
      front: "What is hoisting?",
      back: "JavaScript's default behavior of moving declarations to the top of the current scope.",
    },
    {
      id: 3,
      front: "What is the difference between == and ===?",
      back: "== compares values with type coercion, while === compares both values and types without coercion.",
    },
    {
      id: 4,
      front: "What is a Promise?",
      back: "An object representing the eventual completion or failure of an asynchronous operation and its resulting value.",
    },
    {
      id: 5,
      front: "What is event bubbling?",
      back: "The propagation of an event from the target element up through the DOM tree to the document root.",
    },
  ],
};

// Additional mock sets that might be recommended
const mockRecommendedSets = [
  {
    id: 2,
    title: "React Fundamentals",
    description: "Core React concepts and hooks",
    cards: [
      {
        id: 1,
        front: "What is JSX?",
        back: "A syntax extension for JavaScript that looks similar to HTML and allows you to create React elements.",
      },
      {
        id: 2,
        front: "What is the purpose of useState?",
        back: "A React Hook that lets you add state to functional components.",
      },
      {
        id: 3,
        front: "What is the virtual DOM?",
        back: "A programming concept where a virtual representation of the UI is kept in memory and synced with the real DOM.",
      },
      {
        id: 4,
        front: "What are props?",
        back: "Arguments passed into React components, similar to HTML attributes.",
      },
      {
        id: 5,
        front: "What is the purpose of useEffect?",
        back: "A React Hook that lets you perform side effects in function components, similar to lifecycle methods in class components.",
      },
    ],
  },
  {
    id: 3,
    title: "System Design Basics",
    description: "Fundamental system design concepts",
    cards: [
      {
        id: 1,
        front: "What is scalability?",
        back: "The capability of a system to handle a growing amount of work by adding resources.",
      },
      {
        id: 2,
        front: "What is a load balancer?",
        back: "A device that distributes network traffic across multiple servers to ensure no single server is overwhelmed.",
      },
      {
        id: 3,
        front: "What is caching?",
        back: "The process of storing copies of data in a cache to improve performance and reduce database load.",
      },
      {
        id: 4,
        front: "What is sharding?",
        back: "A database architecture pattern related to horizontal partitioning of data.",
      },
      {
        id: 5,
        front: "What is CAP theorem?",
        back: "States that it is impossible for a distributed data store to simultaneously provide more than two out of Consistency, Availability, and Partition tolerance.",
      },
    ],
  },
];

// Flashcard component with flip animation
const Flashcard = ({ front, back, isFlipped, onClick }) => {
  return (
    <div
      className="relative w-full h-64 cursor-pointer perspective-1000"
      onClick={onClick}
    >
      <div
        className={`absolute w-full h-full transition-transform duration-500 transform-style-preserve-3d ${
          isFlipped ? "rotate-y-180" : ""
        }`}
      >
        {/* Front face */}
        <div className="absolute w-full h-full rounded-xl shadow-lg bg-white p-8 flex items-center justify-center backface-hidden">
          <div className="text-center">
            <p className="text-xl font-medium text-gray-800">{front}</p>
          </div>
        </div>

        {/* Back face */}
        <div className="absolute w-full h-full rounded-xl shadow-lg bg-gradient-to-br from-blue-50 to-green-50 p-8 flex items-center justify-center backface-hidden rotate-y-180">
          <div className="text-center">
            <p className="text-xl font-medium text-gray-800">{back}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default function FlashcardsApp() {
  const [activeSet, setActiveSet] = useState(mockFlashcardSet);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [completedCards, setCompletedCards] = useState([]);
  const [showSummary, setShowSummary] = useState(false);
  const [confidence, setConfidence] = useState({});
  const [recommendedSets, setRecommendedSets] = useState(mockRecommendedSets);

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

  const handleMarkConfidence = (level) => {
    const updatedConfidence = {
      ...confidence,
      [activeSet.cards[currentCardIndex].id]: level,
    };
    setConfidence(updatedConfidence);

    // Add to completed cards
    if (!completedCards.includes(activeSet.cards[currentCardIndex].id)) {
      setCompletedCards([
        ...completedCards,
        activeSet.cards[currentCardIndex].id,
      ]);
    }

    // Move to next card
    handleNextCard();
  };

  const handleNextCard = () => {
    if (currentCardIndex < activeSet.cards.length - 1) {
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

  const handleSelectSet = (set) => {
    setActiveSet(set);
    handleRestartSet();
  };

  // Calculate confidence levels for summary
  const getConfidenceSummary = () => {
    const total = activeSet.cards.length;
    const confidenceCounts = {
      high: 0,
      medium: 0,
      low: 0,
    };

    Object.values(confidence).forEach((level) => {
      confidenceCounts[level]++;
    });

    return {
      high: confidenceCounts.high,
      medium: confidenceCounts.medium,
      low: confidenceCounts.low,
      total: total,
    };
  };

  // We assume this would be the page loaded after test/interview completion
  return (
    <div>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <main className="flex-grow container mx-auto p-4">
          {showSummary ? (
            // Summary view after completing the set
            <div className="max-w-2xl mx-auto">
              <div className="bg-white rounded-xl shadow-lg p-8 mb-6">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">
                  Study Summary
                </h2>
                <p className="mb-6 text-gray-600">
                  You've completed studying "{activeSet.title}"
                </p>

                {/* Summary statistics */}
                <div className="mb-8">
                  <h3 className="font-semibold text-lg mb-2 text-gray-700">
                    Your confidence levels:
                  </h3>
                  <div className="flex justify-between mb-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {getConfidenceSummary().high}
                      </div>
                      <div className="text-sm text-gray-500">High</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-500">
                        {getConfidenceSummary().medium}
                      </div>
                      <div className="text-sm text-gray-500">Medium</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-500">
                        {getConfidenceSummary().low}
                      </div>
                      <div className="text-sm text-gray-500">Low</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {getConfidenceSummary().total - completedCards.length}
                      </div>
                      <div className="text-sm text-gray-500">Skipped</div>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
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
                <div className="flex justify-between">
                  <button
                    onClick={handleRestartSet}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
                  >
                    Study Again
                  </button>
                  <Link to={"/home"}>
                    <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-100 transition">
                      Return to Dashboard
                    </button>
                  </Link>
                </div>
              </div>

              {/* Recommended sets */}
              <div>
                <h2 className="text-xl font-bold mb-4 text-gray-800">
                  Recommended Flashcard Sets
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {recommendedSets.map((set) => (
                    <div
                      key={set.id}
                      className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-md transition border-l-4 border-blue-500"
                      onClick={() => handleSelectSet(set)}
                    >
                      <h3 className="font-bold text-blue-600">{set.title}</h3>
                      <p className="text-sm text-gray-600">{set.description}</p>
                      <p className="text-xs text-gray-500 mt-2">
                        {set.cards.length} cards
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            // Study mode view
            <div className="flex flex-col items-center">
              <div className="w-full max-w-2xl">
                {/* Title and description */}
                <div className="mb-6 text-center">
                  <h2 className="text-2xl font-bold text-gray-800">
                    {activeSet.title}
                  </h2>
                  <p className="text-gray-600">{activeSet.description}</p>
                </div>

                {/* Study progress */}
                <div className="mb-4">
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className="bg-gradient-to-r from-green to-blue h-2.5 rounded-full"
                      style={{
                        width: `${
                          (currentCardIndex / activeSet.cards.length) * 100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>

                {/* Flashcard with flip animation */}
                <div className="mb-6">
                  <Flashcard
                    front={activeSet.cards[currentCardIndex].front}
                    back={activeSet.cards[currentCardIndex].back}
                    isFlipped={isFlipped}
                    onClick={handleToggleFlip}
                  />
                </div>

                {/* When card is flipped (showing answer), show confidence buttons */}
                {isFlipped && (
                  <div className="mb-6">
                    <p className="text-center mb-2 text-gray-700 font-medium">
                      How well did you know this?
                    </p>
                    <div className="flex justify-center space-x-4">
                      <button
                        onClick={() => handleMarkConfidence("low")}
                        className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition"
                      >
                        Not Well
                      </button>
                      <button
                        onClick={() => handleMarkConfidence("medium")}
                        className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition"
                      >
                        Somewhat
                      </button>
                      <button
                        onClick={() => handleMarkConfidence("high")}
                        className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition"
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
                    className={`px-4 py-2 rounded-md ${
                      currentCardIndex === 0
                        ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                        : "bg-lightblue text-black hover:opacity-90"
                    } transition`}
                  >
                    Previous
                  </button>
                  {currentCardIndex === activeSet.cards.length - 1 ? (
                    <button
                      onClick={() => setShowSummary(true)}
                      className="px-4 py-2 bg-blue text-white rounded-md hover:opacity-90 transition"
                    >
                      Finish
                    </button>
                  ) : (
                    <button
                      onClick={handleNextCard}
                      className="px-4 py-2 bg-blue text-white rounded-md hover:opacity-90 transition"
                    >
                      Next
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
      <Footer />
    </div>
  );
}
