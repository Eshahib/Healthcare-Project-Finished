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

  const handleAnalyzeComplete = (entryId: number) => {
    setsymptomEntryId(entryId)
  }

  const handleBackToSymptoms = () => {
    setsymptomEntryId(-1)
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

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <BrowserRouter>
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
          /> : <Navigate to="/login" />}
        />
        <Route
          path="/results/:entryId"
          element={user ?       
          <ResultsPage
            symptomEntryId={symptomEntryId}
            user={user}
            onBack={handleBackToSymptoms}
          /> : <Navigate to="/login" />}
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App





