import { useEffect, useState } from 'react'
import { Button } from './ui/button'
import { CheckCircle, AlertCircle, ArrowLeft, Loader2 } from 'lucide-react'
import { getSymptomEntry, type SymptomEntryWithDiagnosis } from '@/lib/api'
import type { UserResponse } from '@/lib/api'

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
    const fetchResults = async () => {
      try {
        setIsLoading(true)
        const data = await getSymptomEntry(symptomEntryId)
        setSymptomEntry(data)
        console.log(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load results'
        setError(errorMessage)
      } finally {
        console.log("runs");
        setIsLoading(false)
      }
    }

    if (symptomEntryId) {
      fetchResults()
    }
  }, [symptomEntryId])

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
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analysis Results</h1>
            {user && (
              <p className="text-gray-600 mt-1">Welcome, {user.username}</p>
            )}
          </div>
          <Button onClick={onLogout} variant="outline">
            Logout
          </Button>
        </div>

        {/* Results Card */}
        <div className="bg-white rounded-lg shadow-sm p-8">
          {/* Submitted Symptoms */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <CheckCircle className="h-6 w-6 text-green-600" />
              Your Submitted Symptoms
            </h2>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex flex-wrap gap-2 mb-4">
                {symptomEntry?.symptoms.map((symptom, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-medium"
                  >
                    {symptom}
                  </span>
                ))}
              </div>
              {symptomEntry?.comments && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Additional Comments:</p>
                  <p className="text-gray-600">{symptomEntry.comments}</p>
                </div>
              )}
            </div>
          </div>

          {/* Diagnosis Results */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Analysis Results</h2>
            {symptomEntry?.diagnosis ? (
              <div className="space-y-6">
                {/* Diagnosis Text */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Assessment</h3>
                  <p className="text-gray-700 whitespace-pre-wrap">
                    {symptomEntry.diagnosis.diagnosis_text}
                  </p>
                </div>

                {/* Possible Conditions */}
                {symptomEntry.diagnosis.possible_conditions && symptomEntry.diagnosis.possible_conditions.length > 0 && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-3">Possible Conditions</h3>
                    <ul className="space-y-2">
                      {symptomEntry.diagnosis.possible_conditions.map((condition, index) => (
                        <li key={index} className="flex items-center gap-2 text-gray-700">
                          <div className="h-2 w-2 bg-purple-600 rounded-full" />
                          {condition}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Confidence Score */}
                {symptomEntry.diagnosis.confidence_score && (
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-2">Confidence Level</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      symptomEntry.diagnosis.confidence_score === 'high' 
                        ? 'bg-green-100 text-green-800'
                        : symptomEntry.diagnosis.confidence_score === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      {symptomEntry.diagnosis.confidence_score.charAt(0).toUpperCase() + 
                       symptomEntry.diagnosis.confidence_score.slice(1)}
                    </span>
                  </div>
                )}

                {/* Recommendations */}
                {symptomEntry.diagnosis.recommendations && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                    <h3 className="font-semibold text-gray-900 mb-3">Recommendations</h3>
                    <p className="text-gray-700 whitespace-pre-wrap">
                      {symptomEntry.diagnosis.recommendations}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">Analysis is pending</p>
                <p className="text-sm text-gray-500">
                  Your symptoms have been submitted. Analysis results will appear here once processing is complete.
                </p>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-yellow-800">
                This tool provides educational information only. Always consult a healthcare
                professional for medical advice and proper diagnosis.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <Button
              onClick={onBack}
              variant="outline"
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Submit New Symptoms
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

