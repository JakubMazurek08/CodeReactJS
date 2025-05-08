import { useState } from 'react';
import { Text } from '../components/Text.tsx';

interface Resource {
    title: string;
    type: string;
    description: string;
    difficulty: string;
    url?: string;
}

interface LearningRoadmap {
    key_areas: string[];
    resources: Resource[];
    suggested_timeline: string;
}

interface LearningRoadmapProps {
    roadmap: LearningRoadmap;
}

export const Roadmap = ({ roadmap }: LearningRoadmapProps) => {
    const [activeArea, setActiveArea] = useState<string>(roadmap.key_areas[0] || '');

    // Get icon for resource type
    const getResourceIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'article': return '📝';
            case 'course': return '🎓';
            case 'book': return '📚';
            case 'video': return '🎬';
            case 'practice': return '⚙️';
            default: return '📌';
        }
    };

    // Get color for difficulty
    const getDifficultyColor = (difficulty: string) => {
        switch (difficulty.toLowerCase()) {
            case 'beginner': return 'bg-green-100 text-green-800';
            case 'intermediate': return 'bg-blue-100 text-blue-800';
            case 'advanced': return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    // Filter resources by active area
    const filteredResources = roadmap.resources.filter(resource =>
        !activeArea || // Show all if no area selected
        resource.title.toLowerCase().includes(activeArea.toLowerCase()) ||
        resource.description.toLowerCase().includes(activeArea.toLowerCase())
    );

    return (
        <div className="bg-white rounded-lg shadow-xl p-8 mb-8">
            <Text type="h2" className="text-2xl font-bold mb-4">Your Learning Roadmap</Text>
            <Text type="p" className="text-gray-700 mb-6">
                Based on your interview performance, we've created a personalized learning path to help you improve your skills.
            </Text>

            {/* Timeline */}
            <div className="mb-8">
                <Text type="h3" className="font-semibold mb-3">Suggested Timeline</Text>
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                    <Text type="p">{roadmap.suggested_timeline}</Text>
                </div>
            </div>

            {/* Key Areas */}
            <div className="mb-6">
                <Text type="h3" className="font-semibold mb-3">Key Areas to Focus On</Text>
                <div className="flex flex-wrap gap-2 mb-6">
                    {roadmap.key_areas.map((area, index) => (
                        <button
                            key={index}
                            onClick={() => setActiveArea(area)}
                            className={`px-4 py-2 rounded-full text-sm font-medium ${
                                activeArea === area
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                            {area}
                        </button>
                    ))}
                    <button
                        onClick={() => setActiveArea('')}
                        className={`px-4 py-2 rounded-full text-sm font-medium ${
                            activeArea === ''
                                ? 'bg-blue-500 text-white'
                                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                    >
                        All Resources
                    </button>
                </div>
            </div>

            {/* Resources */}
            <div>
                <div className="flex justify-between items-center mb-4">
                    <Text type="h3" className="font-semibold">Learning Resources</Text>
                    <span className="text-sm text-gray-500">
                        {filteredResources.length} resources available
                    </span>
                </div>

                <div className="space-y-4">
                    {filteredResources.length > 0 ? (
                        filteredResources.map((resource, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                                <div className="flex items-start">
                                    <div className="text-2xl mr-4 flex-shrink-0">{getResourceIcon(resource.type)}</div>
                                    <div className="flex-1">
                                        <div className="flex justify-between items-start flex-wrap">
                                            <Text type="h4" className="font-semibold mr-2">{resource.title}</Text>
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium mt-1 ${getDifficultyColor(resource.difficulty)}`}>
                                                {resource.difficulty}
                                            </span>
                                        </div>
                                        <Text type="p" className="mt-2 text-gray-700">{resource.description}</Text>
                                        {resource.url && (
                                            <a
                                                href={resource.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="inline-block mt-3 text-blue-500 hover:text-blue-700 hover:underline"
                                            >
                                                Access resource →
                                            </a>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-6 bg-gray-50 rounded-lg">
                            <Text type="p" className="text-gray-500">No resources found for this area.</Text>
                            <Text type="p" className="text-gray-500 text-sm mt-1">
                                Try selecting a different focus area or view all resources.
                            </Text>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};