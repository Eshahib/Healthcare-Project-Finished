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
        const symptomEntryData = await getSymptomEntry(symptomEntryId);
        console.log(symptomEntryData)
        let newArr = [...symptomEntryData.symptoms];
        if (symptomEntryData.comments) {
          if (Array.isArray(symptomEntryData.comments)) {
            newArr.push(...symptomEntryData.comments);
          } else {
            newArr.push(symptomEntryData.comments);
          }
        }
        console.log(newArr);
        const res = await fetch(`${API_BASE_URL}/make/diagnose`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            symptoms: newArr, 
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
    
  }, [symptomEntryId, user?.username]);

  console.log(symptomEntry?.diagnosis?.diagnosis_text);
  console.log(user?.username)
  console.log(symptomEntryId)

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-12 text-center border border-gray-200">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
            <p className="text-gray-900">Loading your results...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
            <div className="flex items-center gap-3 text-red-600 mb-4">
              <AlertCircle className="h-6 w-6" />
              <h2 className="text-xl font-semibold">Error Loading Results</h2>
            </div>
            <p className="text-gray-900 mb-6">{error}</p>
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
        <p className="text-gray-700 whitespace-pre-wrap">
          {symptomEntry?.diagnosis?.diagnosis_text || "No diagnosis available."}
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
          <p className="text-sm text-yellow-800">
            This tool provides educational information only. Always consult a healthcare
            professional for medical advice and proper diagnosis.
          </p>
        </div>
      </div>

      {/* Recommendations if present */}
      {symptomEntry?.diagnosis?.recommendations ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">Recommendations</h3>
          <p className="text-gray-700 whitespace-pre-wrap">
            {symptomEntry.diagnosis.recommendations}
          </p>
        </div>
      ) : (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center mb-6">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-sm text-gray-500">
            Your symptoms have been submitted. Analysis results will appear here once processing is complete.
          </p>
        </div>
      )}

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

