import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import SymptomChecker from './components/SymptomChecker'
import ResultsPage from './components/ResultsPage'

function App() {
  const [symptomEntryId, setSymptomEntryId] = useState<number | null>(null)

  const handleAnalyzeComplete = (entryId: number) => {
    setSymptomEntryId(entryId)
  }

  const handleBackToSymptoms = () => {
    setSymptomEntryId(null)
  }

  return (
    <Router>
      <Routes>
        {/* Symptom Checker Route */}
        <Route
          path="/symptoms"
          element={
            <SymptomChecker
              user={null}
              onAnalyzeComplete={handleAnalyzeComplete}
            />
          }
        />

        {/* Results Route */}
        <Route
          path="/results"
          element={
            symptomEntryId ? (
            <ResultsPage
              symptomEntryId={symptomEntryId}
              user={null}
              onBack={handleBackToSymptoms}
            />
            ) : (
              <Navigate to="/symptoms" replace />
            )
          }
        />

        {/* Default / catch-all */}
        <Route path="*" element={<Navigate to="/symptoms" replace />} />
      </Routes>
    </Router>
  )
}

export default App
