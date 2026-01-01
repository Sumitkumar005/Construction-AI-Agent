import { CheckCircle, Zap, Brain, Eye, FileText, Shield } from 'lucide-react'

export default function SystemCapabilities() {
  const capabilities = [
    {
      icon: FileText,
      title: 'Document Extraction',
      description: 'Extracts text and images from PDFs up to 1GB+'
    },
    {
      icon: Eye,
      title: 'Computer Vision',
      description: 'Detects rooms, doors, windows using YOLO + ViT'
    },
    {
      icon: Brain,
      title: 'RAG Reasoning',
      description: 'Validates quantities against construction specifications'
    },
    {
      icon: Zap,
      title: 'Multi-Agent System',
      description: '5 specialized AI agents orchestrated with LangGraph'
    },
    {
      icon: Shield,
      title: 'Expert Verification',
      description: 'Human-in-the-loop review for accuracy'
    }
  ]

  return (
    <div className="bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl p-6 border border-gray-200">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">System Capabilities</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {capabilities.map((cap, idx) => {
          const Icon = cap.icon
          return (
            <div
              key={idx}
              className="flex items-start gap-3 p-3 bg-white rounded-lg border border-gray-100 hover:border-primary-200 transition-colors"
            >
              <div className="p-2 bg-primary-100 rounded-lg flex-shrink-0">
                <Icon className="h-4 w-4 text-primary-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 mb-0.5">{cap.title}</p>
                <p className="text-xs text-gray-600">{cap.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

