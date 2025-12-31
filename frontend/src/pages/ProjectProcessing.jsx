import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { CheckCircle, Loader2, AlertCircle, ArrowRight, X } from 'lucide-react'
import { processTakeoff, getTakeoff, getProject, cancelTakeoff } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import ProgressIndicator from '../components/ProgressIndicator'

const STAGES = [
  { key: 'upload', label: 'Upload', icon: CheckCircle },
  { key: 'extraction', label: 'Extraction', icon: Loader2 },
  { key: 'quantity', label: 'Quantity', icon: Loader2 },
  { key: 'cv', label: 'CV', icon: Loader2 },
  { key: 'specs', label: 'Spec', icon: Loader2 },
  { key: 'verification', label: 'Verify', icon: Loader2 },
  { key: 'expert_review', label: 'Expert', icon: Loader2 },
  { key: 'complete', label: 'Complete', icon: CheckCircle },
]

export default function ProjectProcessing() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [project, setProject] = useState(location.state?.project || null)
  const [progress, setProgress] = useState({ stage: 'upload', progress: 0, message: 'Initializing...' })
  const [isProcessing, setIsProcessing] = useState(false)
  const [isCancelling, setIsCancelling] = useState(false)
  const [error, setError] = useState(null)
  const pollingIntervalRef = useRef(null)

  const clientId = `client_${id}`
  const wsUrl = import.meta.env.VITE_API_URL 
    ? import.meta.env.VITE_API_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    : 'ws://localhost:8000'
  const { connected, lastMessage } = useWebSocket(`${wsUrl}/ws/${clientId}`)

  useEffect(() => {
    // Load project if not in state
    if (!project && id) {
      getProject(id).then(setProject).catch(err => {
        setError('Failed to load project')
        console.error(err)
      })
    }
  }, [id, project])

  useEffect(() => {
    // Handle WebSocket messages
    if (lastMessage && lastMessage.type === 'progress') {
      setProgress(prev => {
        const newProgressValue = Math.max(0, Math.min(100, lastMessage.progress || 0))
        // Only update if new progress is greater than or equal to current progress
        // This prevents progress from jumping backwards
        if (newProgressValue >= prev.progress) {
          return {
            stage: lastMessage.stage || prev.stage,
            progress: newProgressValue,
            message: lastMessage.message || prev.message || 'Processing...'
          }
        }
        // If progress is lower, keep current progress but update stage/message if provided
        return {
          stage: lastMessage.stage || prev.stage,
          progress: prev.progress,
          message: lastMessage.message || prev.message || 'Processing...'
        }
      })
    }
  }, [lastMessage])

  useEffect(() => {
    // Start processing when component mounts
    if (project && !isProcessing) {
      startProcessing()
    }
  }, [project])

  const startProcessing = async () => {
    if (!project) return

    setIsProcessing(true)
    setError(null)

    try {
      // Start takeoff processing
      await processTakeoff(project.project_id)

      // Poll for completion
      pollForCompletion()
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to start processing')
      setIsProcessing(false)
    }
  }

  const pollForCompletion = async () => {
    pollingIntervalRef.current = setInterval(async () => {
      try {
        // Check project status instead of takeoff result
        const project = await getProject(id)
        
        if (!project) {
          return
        }
        
        const status = project.status || project.project_status
        
        // Check for completion states
        if (status === 'completed' || status === 'expert_review' || status === 'ai_complete') {
          clearInterval(pollingIntervalRef.current)
          setIsProcessing(false)
          
          // Navigate to results
          setTimeout(() => {
            navigate(`/projects/${id}`)
          }, 2000)
        } else if (status === 'cancelled' || status === 'failed') {
          clearInterval(pollingIntervalRef.current)
          setIsProcessing(false)
          setError(status === 'cancelled' ? 'Processing was cancelled' : 'Processing failed')
        } else if (status === 'processing') {
          // Still processing, update progress if available
          if (project.takeoff_result) {
            // Processing is complete but status hasn't updated yet
            clearInterval(pollingIntervalRef.current)
            setIsProcessing(false)
            setTimeout(() => {
              navigate(`/projects/${id}`)
            }, 2000)
          }
        }
      } catch (err) {
        // Try to get takeoff status as fallback
        try {
          const takeoff = await getTakeoff(id)
          const status = takeoff.status || takeoff.project_status
          
          if (status === 'completed' || status === 'expert_review' || status === 'ai_complete') {
            clearInterval(pollingIntervalRef.current)
            setIsProcessing(false)
            setTimeout(() => {
              navigate(`/projects/${id}`)
            }, 2000)
          } else if (status === 'cancelled' || status === 'failed') {
            clearInterval(pollingIntervalRef.current)
            setIsProcessing(false)
            setError(status === 'cancelled' ? 'Processing was cancelled' : 'Processing failed')
          }
        } catch (takeoffErr) {
          // Both failed, just log and continue polling
          console.log('Polling for project status...')
        }
      }
    }, 3000) // Poll every 3 seconds

    // Clear after 5 minutes
    setTimeout(() => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }, 5 * 60 * 1000)
  }

  const handleCancel = async () => {
    if (!project || !isProcessing) return
    
    if (!window.confirm('Are you sure you want to cancel this processing job? This action cannot be undone.')) {
      return
    }
    
    setIsCancelling(true)
    setError(null)
    
    try {
      await cancelTakeoff(project.project_id)
      
      // Clear polling interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      
      setIsProcessing(false)
      setProgress({
        stage: 'cancelled',
        progress: 0,
        message: 'Processing cancelled'
      })
      
      // Navigate back after a moment
      setTimeout(() => {
        navigate(`/projects/${id}`)
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to cancel processing')
      setIsCancelling(false)
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [])

  const currentStageIndex = STAGES.findIndex(s => s.key === progress.stage) || 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Processing Takeoff
          </h1>
          <p className="text-lg text-gray-600">
            {project?.name || 'Your project is being processed'}
          </p>
        </div>

        {/* Progress Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 mb-8">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Processing Status</h2>
              <div className="flex items-center gap-4">
                <div className="flex items-center">
                  <div className={`h-2 w-2 rounded-full mr-2 ${connected ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                  <span className="text-sm text-gray-600">
                    {connected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
                {isProcessing && (
                  <button
                    onClick={handleCancel}
                    disabled={isCancelling}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <X className="h-4 w-4" />
                    {isCancelling ? 'Cancelling...' : 'Cancel'}
                  </button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-4 mb-8 overflow-hidden">
              <div
                className="bg-gradient-to-r from-primary-500 to-primary-600 h-4 rounded-full transition-all duration-500 ease-out flex items-center justify-end pr-2"
                style={{ width: `${progress.progress}%` }}
              >
                {progress.progress > 10 && (
                  <span className="text-xs font-semibold text-white">
                    {Math.round(progress.progress)}%
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Stage Indicators */}
          <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mb-6">
            {STAGES.map((stage, index) => {
              const isActive = index <= currentStageIndex
              const isCurrent = stage.key === progress.stage
              const Icon = stage.icon

              return (
                <div key={stage.key} className="flex flex-col items-center">
                  <div
                    className={`w-12 h-12 rounded-xl flex items-center justify-center mb-2 transition-all ${
                      isActive
                        ? 'bg-gradient-to-br from-primary-500 to-primary-600 text-white shadow-lg scale-110'
                        : 'bg-gray-100 text-gray-400'
                    } ${isCurrent && 'ring-4 ring-primary-200'}`}
                  >
                    {isCurrent && stage.key !== 'complete' ? (
                      <Loader2 className="h-6 w-6 animate-spin" />
                    ) : (
                      <Icon className="h-6 w-6" />
                    )}
                  </div>
                  <span
                    className={`text-xs text-center font-medium ${
                      isActive ? 'text-gray-900' : 'text-gray-400'
                    }`}
                  >
                    {stage.label.split(' ')[0]}
                  </span>
                </div>
              )
            })}
          </div>

          {/* Current Message */}
          <div className="bg-gradient-to-r from-blue-50 to-primary-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start">
              <Loader2 className="h-5 w-5 text-primary-600 mr-3 mt-0.5 animate-spin" />
              <div>
                <p className="font-semibold text-gray-900 mb-1">{progress.message}</p>
                <p className="text-sm text-gray-600">
                  Stage: {STAGES[currentStageIndex]?.label || 'Processing'} • Progress: {progress.progress}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="text-2xl font-bold text-primary-600 mb-1">1 Day</div>
            <div className="text-sm text-gray-600">Turnaround Time</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="text-2xl font-bold text-green-600 mb-1">99%+</div>
            <div className="text-sm text-gray-600">Accuracy</div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="text-2xl font-bold text-blue-600 mb-1">Expert</div>
            <div className="text-sm text-gray-600">Verified</div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-8 bg-red-50 border border-red-200 rounded-xl p-6 flex items-start">
            <AlertCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5" />
            <div>
              <p className="font-semibold text-red-900">Error</p>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Success Message */}
        {!isProcessing && progress.stage === 'complete' && (
          <div className="mt-8 bg-green-50 border border-green-200 rounded-xl p-6">
            <div className="flex items-center">
              <CheckCircle className="h-6 w-6 text-green-600 mr-3" />
              <div>
                <p className="font-semibold text-green-900">Processing Complete!</p>
                <p className="text-sm text-green-700 mt-1">
                  Redirecting to results...
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

