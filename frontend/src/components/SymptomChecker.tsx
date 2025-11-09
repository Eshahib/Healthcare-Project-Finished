import { useState } from 'react'
import { Checkbox } from './ui/checkbox'
import { Button } from './ui/button'
import { 
  Thermometer, 
  Wind, 
  Heart, 
  Brain, 
  Zap, 
  AlertCircle,
  Loader2,
  LogOut,
  User
} from 'lucide-react'
import { createSymptomEntry, type SymptomEntryResponse, type UserResponse } from '@/lib/api'

interface SymptomCheckerProps {
  user: UserResponse | null
  onLogout?: () => void
  onAnalyzeComplete: (entryId: number) => void
}

interface SymptomCategory {
  id: string
  name: string
  icon: React.ComponentType<{ className?: string }>
  symptoms: string[]
  highlighted?: boolean
}

const symptomCategories: SymptomCategory[] = [
  {
    id: 'general',
    name: 'General',
    icon: Thermometer,
    symptoms: ['Fever', 'Chills', 'Loss of appetite', 'Fatigue', 'Night sweats', 'Weight loss']
  },
  {
    id: 'respiratory',
    name: 'Respiratory',
    icon: Wind,
    symptoms: ['Cough', 'Sore throat', 'Congestion', 'Shortness of breath', 'Runny nose', 'Sneezing']
  },
  {
    id: 'digestive',
    name: 'Digestive',
    icon: Heart,
    symptoms: ['Nausea', 'Diarrhea', 'Bloating', 'Vomiting', 'Abdominal pain', 'Constipation']
  },
  {
    id: 'neurological',
    name: 'Neurological',
    icon: Brain,
    symptoms: ['Headache', 'Confusion', 'Vision changes', 'Dizziness', 'Memory problems', 'Numbness']
  },
  {
    id: 'musculoskeletal',
    name: 'Musculoskeletal',
    icon: Zap,
    symptoms: ['Muscle aches', 'Back pain', 'Swelling', 'Joint pain', 'Stiffness', 'Weakness']
  }
]

export default function SymptomChecker({ user, onLogout, onAnalyzeComplete }: SymptomCheckerProps) {
  const [selectedSymptoms, setSelectedSymptoms] = useState<Set<string>>(new Set())
  const [patientComments, setPatientComments] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSymptomToggle = (symptom: string) => {
    const newSelected = new Set(selectedSymptoms)
    if (newSelected.has(symptom)) {
      newSelected.delete(symptom)
    } else {
      newSelected.add(symptom)
    }
    setSelectedSymptoms(newSelected)
    // Clear messages when user changes selection
    setError(null)

  }

  const handleAnalyze = async () => {
    if (selectedSymptoms.size === 0) return

    setIsLoading(true)
    setError(null)
    console.log(user?.email);

    try {
      const response: SymptomEntryResponse = await createSymptomEntry({
        symptoms: Array.from(selectedSymptoms),
        comments: patientComments.trim() || undefined,
        user_email: user?.email ?? undefined,      
      })
      console.log(response.id)
      // Navigate to results page
      onAnalyzeComplete(response.id)
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to submit symptoms'
      setError(errorMessage)
      console.error('Error creating symptom entry:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header with user info and logout */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">HealthCheck AI</h1>
            {user && (
              <p className="text-gray-600 mt-1 flex items-center gap-2">
                <User className="h-4 w-4" />
                Welcome, {user.username}
              </p>
            )}
          </div>
          {user && (
            <Button
              onClick={onLogout}
              variant="outline"
              className="flex items-center gap-2 px-4 py-2"
            >
              <LogOut className="h-4 w-4" />
              Logout
            </Button>
          )}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel - Symptom Selection */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm p-6 border border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Select Your Symptoms</h1>
            <p className="text-gray-600 mb-6">Choose all symptoms you're currently experiencing</p>

            <div className="space-y-6">
              {symptomCategories.map((category) => {
                const Icon = category.icon
                return (
                  <div key={category.id} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
                    <div
                      className={`flex items-center gap-3 mb-4 ${
                        category.highlighted
                          ? 'bg-blue-50 px-3 py-2 rounded-lg border border-blue-200'
                          : ''
                      }`}
                    >
                      <Icon className="h-5 w-5 text-gray-700" />
                      <h2 className="text-lg font-semibold text-gray-900">
                        {category.name}
                      </h2>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {category.symptoms.map((symptom) => (
                        <label
                          key={symptom}
                          className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-2 rounded"
                        >
                          <Checkbox
                            checked={selectedSymptoms.has(symptom)}
                            onChange={() => handleSymptomToggle(symptom)}
                          />
                          <span className="text-sm text-gray-700">{symptom}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Right Panel - Actions and Info */}
          <div className="space-y-6">
            {/* Patient Comments */}
            <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Additional Comments
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Share any additional details about your symptoms, duration, or concerns
              </p>
              <textarea
                placeholder="Enter any additional information about your symptoms, when they started, severity, or any other relevant details..."
                value={patientComments}
                onChange={(e) => setPatientComments(e.target.value)}
                className="w-full min-h-[120px] rounded-md border border-gray-300 bg-white text-gray-900 px-3 py-2 text-sm ring-offset-white placeholder:text-gray-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:cursor-not-allowed disabled:opacity-50 resize-y"
                rows={5}
              />
            </div>

            {/* Ready to Analyze */}
            <div className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg shadow-sm p-6 text-white border border-purple-500">
              <h2 className="text-lg font-semibold mb-2">Ready to Analyze?</h2>
              <p className="text-sm text-purple-100 mb-4">
                Select at least one symptom to continue
              </p>
              <Button
                onClick={handleAnalyze}
                disabled={selectedSymptoms.size === 0 || isLoading}
                className="w-full bg-white text-purple-600 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed py-3 text-base font-medium flex items-center justify-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Analyze Symptoms'
                )}
              </Button>
              
              {/* Error Message */}
              {error && (
                <div className="mt-4 p-3 bg-red-500/20 rounded-md border border-red-400/50">
                  <p className="text-sm text-white">{error}</p>
                </div>
              )}
            </div>

            {/* Disclaimer */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-yellow-600 shrink-0 mt-0.5" />
                <p className="text-sm text-yellow-800">
                  This tool provides educational information only. Always consult a healthcare
                  professional for medical advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

