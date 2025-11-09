import { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { CheckCircle, AlertCircle, ArrowLeft, Loader2 } from 'lucide-react'
import { getSymptomEntry, type SymptomEntryWithDiagnosis } from '@/lib/api'
import type { UserResponse } from '@/lib/api'
const API_BASE_URL = 'http://localhost:8000/api';

interface ResultsPageProps {
  symptomEntryId: number
  user: UserResponse | null
  onBack: () => void
  onLogout?: () => void
}

export default function ResultsPage({ symptomEntryId, user, onBack, onLogout }: ResultsPageProps) {
  const [symptomEntry, setSymptomEntry] = useState<SymptomEntryWithDiagnosis | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const getResults = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/make/diagnose`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            symptoms: ["fever", "cough", "fatigue", "vomitting from head injury"], 
            username: user?.username,
            symptomEntry: symptomEntryId
          })
        });

        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        setSymptomEntry(data);
      } catch (error){
        console.log(error)
        setError(error instanceof Error ? error.message : "Failed to get diagnosis");
        } 
      finally {
        setIsLoading(false);
      }

    }
    getResults();
  }, [symptomEntryId]);

  console.log(symptomEntry?.diagnosis_text);
  console.log(user?.username)
  console.log(symptomEntryId)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-gray-600">Loading your results...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-8">
            <div className="flex items-center gap-3 text-red-600 mb-4">
              <AlertCircle className="h-6 w-6" />
              <h2 className="text-xl font-semibold">Error Loading Results</h2>
            </div>
            <p className="text-gray-600 mb-6">{error}</p>
            <Button onClick={onBack} variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Symptom Checker
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
      <div className="max-w-4xl w-full bg-white rounded-lg shadow-md p-8">

        {/* Diagnosis Text */}
        <div className="mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-3">Diagnosis</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{symptomEntry?.diagnosis_text || "No diagnosis available."}</p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <Button
            onClick={onBack}
            variant="outline"
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100 transition"
          >
            <ArrowLeft className="h-4 w-4" />
            Submit New Symptoms
          </Button>
        </div>

      </div>
    </div>
  )
}

