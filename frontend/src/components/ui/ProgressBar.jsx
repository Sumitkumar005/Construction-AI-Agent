import { clsx } from 'clsx'

export default function ProgressBar({ 
  value, 
  max = 100, 
  showLabel = true,
  size = 'md',
  color = 'primary',
  className 
}) {
  const percentage = Math.min((value / max) * 100, 100)
  
  const sizes = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  }
  
  const colors = {
    primary: 'bg-gradient-to-r from-primary-500 to-primary-600',
    success: 'bg-gradient-to-r from-green-500 to-green-600',
    warning: 'bg-gradient-to-r from-yellow-500 to-yellow-600',
    error: 'bg-gradient-to-r from-red-500 to-red-600',
  }
  
  return (
    <div className={clsx('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-sm font-medium text-gray-700">Progress</span>
          <span className="text-sm font-semibold text-gray-900">{Math.round(percentage)}%</span>
        </div>
      )}
      <div className={clsx('w-full bg-gray-200 rounded-full overflow-hidden', sizes[size])}>
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-500 ease-out',
            colors[color]
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}


