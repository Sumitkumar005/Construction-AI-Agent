import { CheckCircle, Loader2, AlertCircle } from 'lucide-react'

const stages = [
  { key: 'upload', label: 'Upload', icon: CheckCircle },
  { key: 'extraction', label: 'Extraction', icon: Loader2 },
  { key: 'quantity', label: 'Quantity Take-off', icon: Loader2 },
  { key: 'cv', label: 'CV Analysis', icon: Loader2 },
  { key: 'specs', label: 'Spec Reasoning', icon: Loader2 },
  { key: 'verification', label: 'Verification', icon: Loader2 },
  { key: 'complete', label: 'Complete', icon: CheckCircle },
]

export default function ProgressIndicator({ stage, progress, message, connected }) {
  const currentStageIndex = stages.findIndex(s => s.key === stage) || 0

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h4 className="text-lg font-semibold text-gray-900">Processing Status</h4>
        <div className="flex items-center">
          <div className={`h-2 w-2 rounded-full mr-2 ${connected ? 'bg-green-500' : 'bg-gray-400'}`} />
          <span className="text-sm text-gray-600">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-6">
        <div
          className="bg-primary-600 h-3 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Stage Indicators */}
      <div className="flex justify-between mb-4">
        {stages.map((stageItem, index) => {
          const isActive = index <= currentStageIndex
          const isCurrent = stageItem.key === stage
          const Icon = stageItem.icon

          return (
            <div key={stageItem.key} className="flex flex-col items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 transition-colors ${
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-400'
                }`}
              >
                {isCurrent && stageItem.key !== 'complete' ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Icon className="h-5 w-5" />
                )}
              </div>
              <span
                className={`text-xs text-center ${
                  isActive ? 'text-gray-900 font-medium' : 'text-gray-400'
                }`}
              >
                {stageItem.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Current Message */}
      {message && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">{message}</p>
          <p className="text-xs text-blue-700 mt-1">Progress: {progress}%</p>
        </div>
      )}
    </div>
  )
}

