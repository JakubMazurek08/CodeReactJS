// src/firebase/summaryService.ts
import { db, auth } from '../lib/firebase';
import { 
    collection, 
    serverTimestamp, 
    query, 
    getDocs, 
    doc, 
    setDoc 
} from 'firebase/firestore';

export interface InterviewSummary {
    passed: boolean;
    rating: number;
    improvements: string[];
    summary: string;
    learning_roadmap?: {
        key_areas: string[];
        resources: Array<{
            title: string;
            type: string;
            description: string;
            difficulty: string;
            url?: string;
        }>;
        suggested_timeline: string;
    };
}

export interface SavedInterview {
    id?: string;
    userId: string;
    jobId: string;
    jobTitle: string;
    company: string;
    date: any; // Firestore timestamp
    summary: InterviewSummary;
    messages: Array<{
        id: string;
        message: string;
        isUser: boolean;
    }>;
}

export const saveSummary = async (jobData: any, messages: any[], summary: InterviewSummary): Promise<string | null> => {
    try {
        // Make sure user is logged in
        const currentUser = auth.currentUser;
        if (!currentUser) {
            console.error("No user logged in");
            return null;
        }

        // Generate a unique ID for this interview
        const interviewId = `interview_${Date.now().toString()}`;
        
        const interviewData: SavedInterview = {
            userId: currentUser.uid,
            jobId: jobData.id || 'unknown',
            jobTitle: jobData.title || 'Unknown Position',
            company: jobData.company || 'Unknown Company',
            date: serverTimestamp(),
            summary: summary,
            messages: messages
        };

        // Create path to user's interviews collection
        const userInterviewRef = doc(db, 'users', currentUser.uid, 'interviews', interviewId);
        
        // Save the interview document under the user's interviews subcollection
        await setDoc(userInterviewRef, interviewData);
        
        console.log("Interview saved with ID: ", interviewId);
        return interviewId;
    } catch (error) {
        console.error("Error saving interview: ", error);
        return null;
    }
};

export const getUserInterviews = async (): Promise<SavedInterview[]> => {
    try {
        const currentUser = auth.currentUser;
        if (!currentUser) {
            console.error("No user logged in");
            return [];
        }

        // Query the user's interviews subcollection
        const interviewsQuery = query(
            collection(db, 'users', currentUser.uid, 'interviews')
        );

        const querySnapshot = await getDocs(interviewsQuery);
        const interviews: SavedInterview[] = [];

        querySnapshot.forEach((doc) => {
            interviews.push({
                id: doc.id,
                ...doc.data()
            } as SavedInterview);
        });

        return interviews;
    } catch (error) {
        console.error("Error getting interviews: ", error);
        return [];
    }
};