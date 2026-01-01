import { Clock, TrendingDown } from 'lucide-react'

export default function TimeSavedCard({ processingTimeSeconds }) {
  if (!processingTimeSeconds) return null

  // Manual takeoff typically takes 4-8 hours for a standard project
  const manualTimeHours = 6 // Average
  const manualTimeSeconds = manualTimeHours * 3600
  const timeSavedSeconds = manualTimeSeconds - processingTimeSeconds
  const timeSavedHours = timeSavedSeconds / 3600
  const efficiencyGain = ((timeSavedSeconds / manualTimeSeconds) * 100).toFixed(0)

  return (
    <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl p-6 border border-emerald-200">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TrendingDown className="h-5 w-5 text-emerald-600" />
          <h3 className="text-lg font-semibold text-gray-900">Time Saved</h3>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-emerald-700">{efficiencyGain}%</p>
          <p className="text-xs text-gray-600">Faster</p>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 flex items-center gap-1">
            <Clock className="h-4 w-4" />
            Manual Takeoff:
          </span>
          <span className="font-medium text-gray-900">{manualTimeHours} hours</span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">AI Processing:</span>
          <span className="font-medium text-emerald-700">
            {processingTimeSeconds < 60
              ? `${processingTimeSeconds.toFixed(1)}s`
              : `${(processingTimeSeconds / 60).toFixed(1)}min`}
          </span>
        </div>
        <div className="pt-2 border-t border-emerald-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Time Saved:</span>
            <span className="text-lg font-bold text-emerald-700">
              {timeSavedHours.toFixed(1)} hours
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

