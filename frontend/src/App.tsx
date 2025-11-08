import { useState, useEffect } from 'react'
import SymptomChecker from './components/SymptomChecker'
import AuthPage from './components/AuthPage'
import ResultsPage from './components/ResultsPage'
import { getToken, getCurrentUser, type UserResponse } from '@/lib/api'
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";


type Page = 'auth' | 'symptoms' | 'results'

function App() {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [symptomEntryId, setsymptomEntryId] = useState<number> (-1)

  const navigate = useNavigate();

  const handleAnalyzeComplete = (entryId: number) => {
    setsymptomEntryId(entryId);
    navigate(`/results/${entryId}`);
  }

  const handleBackToSymptoms = () => {
    setsymptomEntryId(-1);
    navigate("/symptoms");
  }

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch {
        setUser(null);
      }
      setIsLoading(false);
    };
    checkAuth();
  }, []);

  const logout = async () => {
    try {
      await fetch("http://localhost:8000/api/logout", {
        method: "POST",
        credentials: "include",  
      });
      
      setUser(null);
      
      // Redirect to login page or update UI accordingly
    } catch (err) {
      console.error("Logout failed", err);
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
      <Routes>
        <Route
          path="/"
          element={user ? <Navigate to="/symptoms" /> : <Navigate to="/login" />}
        />
        <Route
          path="/login"
          element={!user ? <AuthPage onAuthSuccess={setUser} /> : <Navigate to="/symptoms" />}
        />
        <Route
          path="/symptoms"
          element={user ?           
          <SymptomChecker
            user={user}
            onAnalyzeComplete={handleAnalyzeComplete}
            onLogout={logout}
          /> : <Navigate to="/login" />}
        />
        <Route
          path="/results/:entryId"
          element={user ?       
          <ResultsPage
            symptomEntryId={symptomEntryId}
            user={user}
            onLogout={logout}
            onBack={handleBackToSymptoms}
          /> : <Navigate to="/login" />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    
  );
}

export default App





