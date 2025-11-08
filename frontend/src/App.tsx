import { useState, useEffect } from 'react'
import SymptomChecker from './components/SymptomChecker'
import AuthPage from './components/AuthPage'
import ResultsPage from './components/ResultsPage'
import { getToken, getCurrentUser, type UserResponse } from '@/lib/api'

type Page = 'auth' | 'symptoms' | 'results'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('auth')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [symptomEntryId, setSymptomEntryId] = useState<number | null>(null)

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      const token = getToken()
      if (token) {
        try {
          const userData = await getCurrentUser()
          setUser(userData)
          setIsAuthenticated(true)
          setCurrentPage('symptoms')
        } catch (error) {
          // Token is invalid, clear it
          console.error('Auth check failed:', error)
        }
      }
      setIsLoading(false)
    }

    checkAuth()
  }, [])

  const handleAuthSuccess = (userData: UserResponse, token: string) => {
    setUser(userData)
    setIsAuthenticated(true)
    setCurrentPage('symptoms')
  }

  const handleLogout = () => {
    setUser(null)
    setIsAuthenticated(false)
    setSymptomEntryId(null)
    setCurrentPage('auth')
    localStorage.removeItem('auth_token')
  }

  const handleAnalyzeComplete = (entryId: number) => {
    setSymptomEntryId(entryId)
    setCurrentPage('results')
  }

  const handleBackToSymptoms = () => {
    setCurrentPage('symptoms')
    setSymptomEntryId(null)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (currentPage === 'auth' || !isAuthenticated) {
    return <AuthPage onAuthSuccess={handleAuthSuccess} />
  }

  if (currentPage === 'results' && symptomEntryId) {
    return (
      <ResultsPage
        symptomEntryId={symptomEntryId}
        user={user}
        onBack={handleBackToSymptoms}
        onLogout={handleLogout}
      />
    )
  }

  return (
    <SymptomChecker
      user={user}
      onLogout={handleLogout}
      onAnalyzeComplete={handleAnalyzeComplete}
    />
  )
}

export default App
