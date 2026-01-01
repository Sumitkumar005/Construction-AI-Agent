import { CheckCircle, Loader2, AlertCircle, Brain, Eye, FileText, Sparkles, CheckSquare } from 'lucide-react'

const stages = [
  { key: 'upload', label: 'Upload', icon: CheckCircle, agent: null },
  { key: 'extraction', label: 'Extraction', icon: FileText, agent: 'ExtractionAgent' },
  { key: 'quantity', label: 'Quantity', icon: Sparkles, agent: 'TradeExtractor' },
  { key: 'cv', label: 'CV', icon: Eye, agent: 'Moondream AI' },
  { key: 'specs', label: 'Spec', icon: Brain, agent: 'RAG System' },
  { key: 'verification', label: 'Verify', icon: CheckSquare, agent: 'VerificationAgent' },
  { key: 'complete', label: 'Complete', icon: CheckCircle, agent: null },
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

      {/* Current Message with Active Agent */}
      {message && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-blue-900">{message}</p>
              {stages.find(s => s.key === stage)?.agent && (
                <p className="text-xs text-blue-600 mt-1 flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Active: {stages.find(s => s.key === stage)?.agent}
                </p>
              )}
            </div>
            <div className="ml-4">
              <span className="text-lg font-bold text-blue-700">{progress}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

