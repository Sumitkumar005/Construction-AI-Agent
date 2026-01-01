import { useEffect, useState } from 'react'

export default function ConfidenceGauge({ confidence, size = 120 }) {
  const [animatedConfidence, setAnimatedConfidence] = useState(0)
  
  useEffect(() => {
    // Animate from 0 to target confidence
    const duration = 1500 // 1.5 seconds
    const steps = 60
    const increment = confidence / steps
    const stepDuration = duration / steps
    
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= confidence) {
        setAnimatedConfidence(confidence)
        clearInterval(timer)
      } else {
        setAnimatedConfidence(current)
      }
    }, stepDuration)
    
    return () => clearInterval(timer)
  }, [confidence])
  
  const radius = (size - 20) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (animatedConfidence / 100) * circumference
  
  const getColor = (conf) => {
    if (conf >= 80) return '#10b981' // green
    if (conf >= 60) return '#f59e0b' // amber
    return '#ef4444' // red
  }
  
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#e5e7eb"
          strokeWidth="12"
          fill="none"
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor(animatedConfidence)}
          strokeWidth="12"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-300"
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold" style={{ color: getColor(animatedConfidence) }}>
          {Math.round(animatedConfidence)}%
        </span>
        <span className="text-xs text-gray-500 mt-1">Confidence</span>
      </div>
    </div>
  )
}

