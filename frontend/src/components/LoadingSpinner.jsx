import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="h-12 w-12 text-primary-600 animate-spin mb-4" />
      <p className="text-gray-600">{message}</p>
    </div>
  )
}

