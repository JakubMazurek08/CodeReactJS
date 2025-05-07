import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Text } from '../components/Text';

export const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    // For staggered animation of feature cards
    const [showFeatures, setShowFeatures] = useState([false, false, false]);
    useEffect(() => {
        const timers = [
            setTimeout(() => setShowFeatures(f => [true, f[1], f[2]]), 200),
            setTimeout(() => setShowFeatures(f => [f[0], true, f[2]]), 400),
            setTimeout(() => setShowFeatures(f => [f[0], f[1], true]), 600),
        ];
        return () => timers.forEach(clearTimeout);
    }, []);

    return (
        <div className="min-h-screen" style={{ backgroundColor: 'var(--color-background)' }}>
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div className="container mx-auto px-4 py-20">
                    <div className="text-center max-w-4xl mx-auto">
                        <div className="mb-8">
                            <Text type="h1">
                                Master Your Interview Skills
                            </Text>
                        </div>
                        <div className="mb-12">
                            <Text type="p">
                                Experience realistic interview simulations powered by AI. 
                                Get instant feedback and improve your performance with every practice session.
                            </Text>
                        </div>
                        <div className="space-x-6">
                            <button
                                onClick={() => navigate('/login')}
                                className="px-10 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 shadow-lg"
                                style={{ backgroundColor: 'var(--color-blue)', color: 'white' }}
                            >
                                Start Practicing Now
                            </button>
                            <button
                                onClick={() => navigate('/')}
                                className="px-10 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 border-2"
                                style={{ borderColor: 'var(--color-green)', color: 'var(--color-green)' }}
                            >
                                Learn More
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Features Section */}
            <div className="py-20" style={{ backgroundColor: 'white' }}>
                <div className="container mx-auto px-4">
                    <div className="text-center mb-16">
                        <Text type="h2">Why Choose Our Platform?</Text>
                    </div>
                    <div className="grid md:grid-cols-3 gap-12">
                        {/* Feature 1 */}
                        <div className={`p-6 rounded-xl transition-all duration-700 ${showFeatures[0] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'} hover:scale-105 hover:shadow-lg`} style={{ backgroundColor: 'var(--color-background)' }}>
                            <div className="text-center mb-4">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-blue)' }}>
                                    <span className="text-2xl text-white">🎯</span>
                                </div>
                                <Text type="h3">Realistic Simulations</Text>
                            </div>
                            <Text type="p">
                                Practice with AI-powered interviews that mimic real-world scenarios and questions.
                            </Text>
                        </div>

                        {/* Feature 2 */}
                        <div className={`p-6 rounded-xl transition-all duration-700 ${showFeatures[1] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'} hover:scale-105 hover:shadow-lg`} style={{ backgroundColor: 'var(--color-background)' }}>
                            <div className="text-center mb-4">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-green)' }}>
                                    <span className="text-2xl text-white">💡</span>
                                </div>
                                <Text type="h3">Instant Feedback</Text>
                            </div>
                            <Text type="p">
                                Receive detailed feedback on your responses, body language, and communication skills.
                            </Text>
                        </div>

                        {/* Feature 3 */}
                        <div className={`p-6 rounded-xl transition-all duration-700 ${showFeatures[2] ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'} hover:scale-105 hover:shadow-lg`} style={{ backgroundColor: 'var(--color-background)' }}>
                            <div className="text-center mb-4">
                                <div className="w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--color-blue)' }}>
                                    <span className="text-2xl text-white">📈</span>
                                </div>
                                <Text type="h3">Track Progress</Text>
                            </div>
                            <Text type="p">
                                Monitor your improvement over time with detailed analytics and performance metrics.
                            </Text>
                        </div>
                    </div>
                </div>
            </div>

            {/* CTA Section */}
            <div className="py-20" style={{ backgroundColor: 'var(--color-background)' }}>
                <div className="container mx-auto px-4 text-center">
                    <div className="max-w-2xl mx-auto">
                        <div className="mb-6">
                            <Text type="h2">
                                Ready to Ace Your Next Interview?
                            </Text>
                        </div>
                        <div className="mb-8">
                            <Text type="p">
                                Join thousands of professionals who have improved their interview skills with our platform.
                            </Text>
                        </div>
                        <button
                            onClick={() => navigate('/login')}
                            className="px-12 py-4 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 shadow-lg"
                            style={{ backgroundColor: 'var(--color-green)', color: 'white' }}
                        >
                            Get Started for Free
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}; 