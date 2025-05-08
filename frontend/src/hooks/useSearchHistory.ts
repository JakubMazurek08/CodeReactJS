// hooks/useSearchHistory.js
import { useState, useEffect } from 'react';

export const useSearchHistory = () => {
    const [searchHistory, setSearchHistory] = useState([]);

    // Load history from localStorage on mount
    useEffect(() => {
        const savedHistory = localStorage.getItem('searchHistory');
        if (savedHistory) {
            setSearchHistory(JSON.parse(savedHistory));
        }
    }, []);

    // Save to localStorage whenever history changes
    useEffect(() => {
        localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    }, [searchHistory]);

    // Add a new search to history
    const addSearch = (search) => {
        // Limit to 10 most recent searches
        const updatedHistory = [search, ...searchHistory.slice(0, 9)];
        setSearchHistory(updatedHistory);
    };

    // Clear all search history
    const clearHistory = () => {
        setSearchHistory([]);
        localStorage.removeItem('searchHistory');
    };

    return { searchHistory, addSearch, clearHistory };
};