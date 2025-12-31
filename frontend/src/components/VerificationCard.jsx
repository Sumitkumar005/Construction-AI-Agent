import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'

export default function VerificationCard({ verification }) {
  const checks = verification.checks || {}
  const flags = verification.flags || []

  const getStatusIcon = (isValid) => {
    if (isValid) {
      return <CheckCircle className="h-5 w-5 text-green-600" />
    }
    return <AlertTriangle className="h-5 w-5 text-yellow-600" />
  }

  const getStatusColor = (isValid) => {
    if (isValid) {
      return 'bg-green-50 border-green-200'
    }
    return 'bg-yellow-50 border-yellow-200'
  }

  return (
    <div className="space-y-4">
      {/* Overall Confidence */}
      <div className="bg-gray-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Overall Confidence</span>
          <span className="text-2xl font-bold text-gray-900">
            {(verification.overall_confidence || 0) * 100}%
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-primary-600 h-2 rounded-full transition-all"
            style={{ width: `${(verification.overall_confidence || 0) * 100}%` }}
          />
        </div>
      </div>

      {/* Individual Checks */}
      {Object.entries(checks).map(([checkName, checkResult]) => {
        const isValid = checkResult.is_consistent !== undefined
          ? checkResult.is_consistent
          : checkResult.all_within_bounds !== undefined
          ? checkResult.all_within_bounds
          : true

        return (
          <div
            key={checkName}
            className={`border rounded-lg p-4 ${getStatusColor(isValid)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start">
                {getStatusIcon(isValid)}
                <div className="ml-3">
                  <h4 className="text-sm font-semibold text-gray-900">
                    {checkName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </h4>
                  <p className="text-xs text-gray-600 mt-1">
                    Confidence: {(checkResult.confidence || 0) * 100}%
                  </p>
                </div>
              </div>
              <span className={`text-xs font-medium ${
                isValid ? 'text-green-700' : 'text-yellow-700'
              }`}>
                {isValid ? 'PASS' : 'REVIEW'}
              </span>
            </div>
          </div>
        )
      })}

      {/* Flags */}
      {flags.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <XCircle className="h-5 w-5 text-red-600 mr-2" />
            <h4 className="text-sm font-semibold text-red-900">
              Issues Detected ({flags.length})
            </h4>
          </div>
          <ul className="space-y-1">
            {flags.map((flag, index) => (
              <li key={index} className="text-sm text-red-700">
                • {flag.message || flag.type}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

