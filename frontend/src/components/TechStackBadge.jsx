import { Brain, Database, Eye, Sparkles } from 'lucide-react'

export default function TechStackBadge({ compact = false }) {
  const techs = [
    { name: 'LangGraph', icon: Sparkles, color: 'text-purple-600' },
    { name: 'RAG', icon: Brain, color: 'text-blue-600' },
    { name: 'YOLO', icon: Eye, color: 'text-green-600' },
    { name: 'Qdrant', icon: Database, color: 'text-orange-600' },
  ]

  if (compact) {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        {techs.map((tech, idx) => {
          const Icon = tech.icon
          return (
            <div
              key={idx}
              className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 rounded-md text-xs font-medium text-gray-700"
            >
              <Icon className={`h-3 w-3 ${tech.color}`} />
              <span>{tech.name}</span>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Powered By</p>
      <div className="flex items-center gap-3 flex-wrap">
        {techs.map((tech, idx) => {
          const Icon = tech.icon
          return (
            <div
              key={idx}
              className="inline-flex items-center gap-2 px-3 py-2 bg-white rounded-lg shadow-sm border border-gray-200"
            >
              <Icon className={`h-4 w-4 ${tech.color}`} />
              <span className="text-sm font-medium text-gray-700">{tech.name}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

