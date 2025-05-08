import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Text } from "../components/Text";

// 3D Tilt Feature Card
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  children: React.ReactNode;
  bgColor: string;
  borderColor: string;
  delay?: number;
}
const FeatureCard: React.FC<FeatureCardProps> = ({
  icon,
  title,
  children,
  bgColor,
  borderColor,
  delay = 0,
}) => {
  const [show, setShow] = useState(false);
  const [tilt, setTilt] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
    const card = e.currentTarget;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * 10; // max 10deg
    const rotateY = ((x - centerX) / centerX) * -10;
    setTilt({ x: rotateX, y: rotateY });
  };
  const handleMouseLeave = () => setTilt({ x: 0, y: 0 });

  return (
    <div
      className={`tilt-card group relative border rounded-xl overflow-hidden transition-transform duration-400 ease-[cubic-bezier(0.175,0.885,0.32,1.275)] ${
        show ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
      } hover:-translate-y-4 hover:scale-[1.02]`}
      style={{ borderColor: "Background", perspective: 1000 }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Gradient border effect */}
      <div
        className="pointer-events-none absolute inset-0 rounded-xl z-10"
        style={{
          padding: 2,
          background: "lightgray",
          transition: "opacity 0.4s ease",
          opacity: 0.7,
        }}
      />
      <div
        className="tilt-card-inner relative z-20 p-6 h-full"
        style={{
          background: bgColor,
          borderRadius: 12,
          transform: `rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`,
          transition: "transform 0.5s cubic-bezier(0.23, 1, 0.32, 1)",
        }}
      >
        <div className="text-center mb-4">
          <div
            className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center"
            style={{ background: borderColor }}
          >
            <span className="text-2xl text-white">{icon}</span>
          </div>
          <Text type="h3">{title}</Text>
        </div>
        <Text type="p">{children}</Text>
      </div>
      {/* Show border on hover */}
      <style>{`
        .group:hover > div:first-child { opacity: 1 !important; }
      `}</style>
    </div>
  );
};

// Scroll Down Arrow Component
const ScrollArrow: React.FC = () => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const handleScroll = () => {
      // Hide arrow when user has scrolled down
      if (window.scrollY > 100) {
        setIsVisible(false);
      } else {
        setIsVisible(true);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToFeatures = () => {
    // Smooth scroll to the features section
    const featuresSection = document.getElementById('features-section');
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div 
      className={`absolute bottom-6 left-1/2 transform -translate-x-1/2 cursor-pointer transition-opacity duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      } hover:scale-110`}
      onClick={scrollToFeatures}
    >
      <div className="flex flex-col items-center">
        <div className="text-white font-medium px-4 py-2 rounded-full bg-gradient-to-r from-blue-500 to-green-500 shadow-lg mb-3">
          <span>Discover More</span>
        </div>
        
        <div className="w-12 h-12 rounded-full bg-white shadow-lg flex items-center justify-center animate-bounce">
          <svg 
            width="24" 
            height="24" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              d="M12 5L12 19M12 19L19 12M12 19L5 12" 
              stroke="url(#gradient)" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round"
              transform="rotate(180 12 12)"
            />
            <defs>
              <linearGradient id="gradient" x1="5" y1="12" x2="19" y2="12" gradientUnits="userSpaceOnUse">
                <stop stopColor="var(--color-blue)" />
                <stop offset="1" stopColor="var(--color-green)" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>
    </div>
  );
};

export const LandingPage: React.FC = () => {
  // For staggered animation of feature cards
  // (now handled by FeatureCard delay prop)

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "var(--color-background)" }}
    >
      {/* Hero Section */}
      <div className="flex overflow-hidden h-[100vh] items-center relative bg-gradient-to-br from-blue-50 to-green-50">
        {/* Background elements for visual interest */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-20 w-64 h-64 rounded-full bg-blue-200 opacity-20 blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-80 h-80 rounded-full bg-green-200 opacity-20 blur-3xl"></div>
          <div className="absolute top-40 right-40 w-40 h-40 rounded-full bg-blue-300 opacity-10 blur-2xl"></div>
        </div>
        
        <div className="container mx-auto px-4 py-20 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            <div className="mb-2">
              <span className="inline-block px-4 py-1 rounded-full text-sm font-medium mb-4" style={{ backgroundColor: "rgba(var(--color-blue-rgb), 0.1)", color: "var(--color-blue)" }}>
                AI-Powered Interview Training
              </span>
            </div>
            <div className="mb-8">
              <Text type="h1">Master Your Interview Skills</Text>
            </div>
            <div className="mb-12">
              <Text type="p">
                Experience realistic interview simulations powered by AI. Get
                instant feedback and improve your performance with every
                practice session.
              </Text>
            </div>
            <div className="space-x-6">
              <Link to={"/home"}>
                <button
                  className="px-10 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 hover:cursor-pointer shadow-lg"
                  style={{
                    backgroundColor: "var(--color-blue)",
                    color: "white",
                  }}
                >
                  Start Practicing Now
                </button>
              </Link>
              <button
                className="px-10 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg hover:cursor-pointer active:scale-95 border-2"
                style={{
                  borderColor: "var(--color-green)",
                  color: "var(--color-green)",
                }}
              >
                Learn More
              </button>
            </div>
          </div>
        </div>
        
        {/* Scroll Down Arrow */}
        <ScrollArrow />
      </div>

      {/* Features Section */}
      <div id="features-section" className="py-20" style={{ backgroundColor: "white" }}>
        <div className="container mx-auto px-4">
          <div className="text-center mb-16">
            <Text type="h2">Why Choose Our Platform?</Text>
          </div>
          <div className="grid md:grid-cols-3 gap-12">
            <FeatureCard
              icon="🎯"
              title="Realistic Simulations"
              bgColor="var(--color-background)"
              borderColor="var(--color-blue)"
              delay={200}
            >
              Practice with AI-powered interviews that mimic real-world
              scenarios and questions.
            </FeatureCard>
            <FeatureCard
              icon="💡"
              title="Instant Feedback"
              bgColor="var(--color-background)"
              borderColor="var(--color-green)"
              delay={400}
            >
              Receive detailed feedback on your responses, body language, and
              communication skills.
            </FeatureCard>
            <FeatureCard
              icon="📈"
              title="Track Progress"
              bgColor="var(--color-background)"
              borderColor="var(--color-blue)"
              delay={600}
            >
              Monitor your improvement over time with detailed analytics and
              performance metrics.
            </FeatureCard>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div
        className="py-20"
        style={{ backgroundColor: "var(--color-background)" }}
      >
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-2xl mx-auto">
            <div className="mb-6">
              <Text type="h2">Ready to Ace Your Next Interview?</Text>
            </div>
            <div className="mb-8">
              <Text type="p">
                Join thousands of professionals who have improved their
                interview skills with our platform.
              </Text>
            </div>
            <Link to={"/home"}>
              <button
                className="px-12 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg hover:cursor-pointer active:scale-95 shadow-lg"
                style={{
                  backgroundColor: "var(--color-green)",
                  color: "white",
                }}
              >
                Get Started for Free
              </button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};