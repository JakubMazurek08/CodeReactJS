import React, { useEffect, useState } from 'react';
import { Navbar } from "../components/Navbar";
import { Text } from "../components/Text";

const Progress: React.FC = () => {
  const [show, setShow] = useState(false);

  useEffect(() => {
    // Animation for the component entrance
    setShow(true);
  }, []);

  // Performance data points
  const performanceData = [
    { session: '1', score: 20, average: 20 },
    { session: '2', score: 45, average: 50 },
    { session: '3', score: 35, average: 30 },
    { session: '4', score: 60, average: 65 },
    { session: '5', score: 80, average: 65 },
    { session: '6', score: 75, average: 70 },
    { session: '7', score: 80, average: 75 },
  ];

  // Mock data for skills breakdown
  const skillsData = [
    { name: 'Communication', score: 85, color: 'rgb(54, 162, 235)' },
    { name: 'Technical Knowledge', score: 78, color: 'rgb(255, 99, 132)' },
    { name: 'Problem Solving', score: 92, color: 'rgb(75, 192, 192)' },
    { name: 'Cultural Fit', score: 88, color: 'rgb(255, 159, 64)' },
    { name: 'Leadership', score: 72, color: 'rgb(153, 102, 255)' }
  ];

  // Generate line segments with dynamic coloring based on average trend
  const generateLineSegments = () => {
    const segments = [];
    
    for (let i = 0; i < performanceData.length - 1; i++) {
      const currentPoint = performanceData[i];
      const nextPoint = performanceData[i + 1];
      
      // Determine if average is increasing or decreasing
      const isIncreasing = nextPoint.average >= currentPoint.average;
      const color = isIncreasing ? "rgb(75, 192, 192)" : "rgb(255, 99, 132)"; // Green if increasing, red if decreasing
      
      // Calculate positions
      const x1 = (i / (performanceData.length - 1)) * 100 + "%";
      const y1 = (100 - currentPoint.score) + "%";
      const x2 = ((i + 1) / (performanceData.length - 1)) * 100 + "%";
      const y2 = (100 - nextPoint.score) + "%";
      
      segments.push(
        <line
          key={`segment-${i}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
        />
      );
    }
    
    return segments;
  };
  
  // Generate average line segments with dynamic coloring
  const generateAverageLineSegments = () => {
    const segments = [];
    
    for (let i = 0; i < performanceData.length - 1; i++) {
      const currentPoint = performanceData[i];
      const nextPoint = performanceData[i + 1];
      
      // Determine if average is increasing or decreasing
      const isIncreasing = nextPoint.average >= currentPoint.average;
      const color = isIncreasing ? "rgb(75, 192, 192)" : "rgb(255, 99, 132)"; // Green if increasing, red if decreasing
      
      // Calculate positions
      const x1 = (i / (performanceData.length - 1)) * 100 + "%";
      const y1 = (100 - currentPoint.average) + "%";
      const x2 = ((i + 1) / (performanceData.length - 1)) * 100 + "%";
      const y2 = (100 - nextPoint.average) + "%";
      
      segments.push(
        <line
          key={`avg-segment-${i}`}
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke={color}
          strokeWidth="3"
          strokeDasharray="5,5"
          strokeLinecap="round"
        />
      );
    }
    
    return segments;
  };

  return (
    <>
      <Navbar />
      <main className="px-6 sm:px-12 md:px-24 lg:px-32 pt-20 min-h-screen bg-background">
        <div className={`max-w-6xl mx-auto transition-all duration-700 ${show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mb-12 text-center">
            <Text type="h2">Your Interview Progress</Text>
            <Text type="p" className="mt-4 max-w-2xl mx-auto">
              Track your improvement over time. See how your interview performance has evolved with each practice session.
            </Text>
          </div>

          {/* Main Chart Section */}
          <div className="bg-white p-8 rounded-lg shadow-lg mb-12">
            <Text type="h3" className="mb-8 text-center font-bold text-2xl">Performance Trend</Text>
            <div className="h-[450px] w-full relative">
              {/* Custom Chart Implementation */}
              <div className="w-full h-full flex flex-col">
                {/* Y-axis labels */}
                <div className="absolute left-0 top-0 bottom-0 w-16 flex flex-col justify-between text-sm font-medium text-gray-600 py-4">
                  <div>100%</div>
                  <div>80%</div>
                  <div>60%</div>
                  <div>40%</div>
                  <div>20%</div>
                  <div>0%</div>
                </div>
                
                {/* Chart area */}
                <div className="absolute left-16 right-4 top-4 bottom-16 border-l border-b border-gray-300 bg-gray-50/30">
                  {/* Horizontal grid lines */}
                  <div className="absolute w-full h-1/5 border-t border-gray-200"></div>
                  <div className="absolute w-full h-2/5 border-t border-gray-200"></div>
                  <div className="absolute w-full h-3/5 border-t border-gray-200"></div>
                  <div className="absolute w-full h-4/5 border-t border-gray-200"></div>
                  
                  {/* Performance Line with dynamically colored segments */}
                  <svg className="absolute inset-0 overflow-visible" preserveAspectRatio="none">
                    {generateLineSegments()}
                    
                    {/* Data points (circles) */}
                    {performanceData.map((point, index) => (
                      <circle
                        key={`perf-${index}`}
                        cx={(index / (performanceData.length - 1)) * 100 + "%"}
                        cy={(100 - point.score) + "%"}
                        r="8"
                        fill={index < performanceData.length - 1 && performanceData[index + 1].average >= point.average ? 
                          "rgb(75, 192, 192)" : "rgb(255, 99, 132)"}
                        stroke="white"
                        strokeWidth="2.5"
                      />
                    ))}
                  </svg>
                  
                  {/* Average Line with dynamically colored segments */}
                  <svg className="absolute inset-0 overflow-visible">
                    {generateAverageLineSegments()}
                    
                    {/* Average data points (circles) */}
                    {performanceData.map((point, index) => (
                      <circle
                        key={`avg-${index}`}
                        cx={(index / (performanceData.length - 1)) * 100 + "%"}
                        cy={(100 - point.average) + "%"}
                        r="8"
                        fill={index < performanceData.length - 1 && performanceData[index + 1].average >= point.average ? 
                          "rgb(75, 192, 192)" : "rgb(255, 99, 132)"}
                        stroke="white"
                        strokeWidth="2.5"
                      />
                    ))}
                  </svg>
                </div>
                
                {/* X-axis labels */}
                <div className="absolute left-16 right-4 bottom-0 h-16 flex justify-between items-center">
                  {performanceData.map((point, index) => (
                    <div 
                      key={`x-label-${index}`} 
                      className="text-center font-medium text-gray-600 px-2 flex-1"
                    >
                      Day {point.session}
                    </div>
                  ))}
                </div>
                
                {/* Legend */}
                <div className="absolute top-4 right-8 flex items-center gap-6 text-sm font-medium bg-white/80 p-3 rounded-lg shadow-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-[rgb(75,192,192)]"></div>
                    <span>Increasing Trend</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-[rgb(255,99,132)]"></div>
                    <span>Decreasing Trend</span>
                  </div>
                </div>

                {/* Solid line indicator */}
                <div className="absolute top-16 right-8 flex items-center gap-2 text-sm font-medium">
                  <div className="w-10 h-0.5 bg-gray-800"></div>
                  <span>Your Score</span>
                </div>
                
                {/* Dashed line indicator */}
                <div className="absolute top-24 right-8 flex items-center gap-2 text-sm font-medium">
                  <div className="w-10 h-0.5 bg-gray-800" style={{ borderTop: '2px dashed #333' }}></div>
                  <span>Industry Average</span>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
            {/* Skills Breakdown */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <Text type="h3" className="mb-6">Skills Breakdown</Text>
              <div className="space-y-6">
                {skillsData.map((skill) => (
                  <div key={skill.name}>
                    <div className="flex justify-between mb-2">
                      <span className="font-medium">{skill.name}</span>
                      <span className="font-medium">{skill.score}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
                      <div 
                        className="h-full rounded-full transition-all duration-1000 ease-out"
                        style={{ 
                          width: `${skill.score}%`, 
                          backgroundColor: skill.color 
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Activity & Tips */}
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <Text type="h3" className="mb-6">Recent Activity & Tips</Text>
              <div className="space-y-4">
                <div className="border-l-4 border-blue pl-4 py-2">
                  <Text type="h4" className="text-blue">Most Recent Practice</Text>
                  <p className="mt-2">Software Developer Interview - May 5, 2025</p>
                  <p className="text-gray-600 mt-1">Score: 78/100 - Good job! Your technical answers were strong.</p>
                </div>
                <div className="mt-6">
                  <Text type="h4">Areas to Improve</Text>
                  <ul className="list-disc list-inside mt-2 space-y-2 text-gray-600">
                    <li>Practice discussing team conflicts with more specific examples</li>
                    <li>Work on explaining complex technical concepts more clearly</li>
                    <li>Strengthen your closing statements in interviews</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Upcoming Interviews Section */}
          <div className="bg-white p-6 rounded-lg shadow-lg mb-10">
            <Text type="h3" className="mb-6">Scheduled Practice Sessions</Text>
            {/* Empty state */}
            <div className="text-center py-8">
              <p className="text-gray-500 mb-4">You don't have any upcoming practice sessions scheduled.</p>
              <button 
                className="px-6 py-3 rounded-lg font-semibold transition-transform duration-300 hover:scale-105 hover:shadow-lg active:scale-95 hover:cursor-pointer shadow-lg"
                style={{
                  backgroundColor: "var(--color-green)",
                  color: "white",
                }}
              >
                Schedule New Session
              </button>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};

export default Progress;