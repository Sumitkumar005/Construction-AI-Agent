import { CheckCircle, XCircle, Brain, Eye, Sparkles, FileText } from 'lucide-react'

export default function AgentExecutionLog({ metadata }) {
  if (!metadata) return null

  const agents = [
    {
      name: 'Extraction Agent',
      icon: FileText,
      used: true, // Always runs
      description: 'Extracted text and images from PDF'
    },
    {
      name: 'Moondream AI',
      icon: Sparkles,
      used: metadata.moondream_used || false,
      description: 'Analyzed floor plan dimensions'
    },
    {
      name: 'Computer Vision',
      icon: Eye,
      used: metadata.cv_used || false,
      description: 'Detected rooms and objects (fallback)'
    },
    {
      name: 'RAG System',
      icon: Brain,
      used: metadata.rag_used || false,
      description: 'Validated against construction specs'
    }
  ]

  const activeAgents = agents.filter(a => a.used)
  const totalAgents = agents.length

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-6 border border-indigo-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Multi-Agent Execution</h3>
        <span className="text-sm font-medium text-indigo-700 bg-indigo-100 px-3 py-1 rounded-full">
          {activeAgents.length}/{totalAgents} Agents Active
        </span>
      </div>
      <div className="space-y-3">
        {agents.map((agent, idx) => {
          const Icon = agent.icon
          return (
            <div
              key={idx}
              className={`flex items-center justify-between p-3 rounded-lg transition-all ${
                agent.used
                  ? 'bg-white border border-green-200 shadow-sm'
                  : 'bg-gray-50 border border-gray-200 opacity-60'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    agent.used ? 'bg-indigo-100' : 'bg-gray-200'
                  }`}
                >
                  <Icon
                    className={`h-4 w-4 ${
                      agent.used ? 'text-indigo-600' : 'text-gray-400'
                    }`}
                  />
                </div>
                <div>
                  <p
                    className={`text-sm font-medium ${
                      agent.used ? 'text-gray-900' : 'text-gray-500'
                    }`}
                  >
                    {agent.name}
                  </p>
                  <p className="text-xs text-gray-500">{agent.description}</p>
                </div>
              </div>
              {agent.used ? (
                <CheckCircle className="h-5 w-5 text-green-500" />
              ) : (
                <XCircle className="h-5 w-5 text-gray-300" />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

