import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Upload, FileText, CheckCircle, AlertCircle, Sparkles, ArrowRight, Clock } from 'lucide-react'
import { listProjects } from '../services/api'

export default function Dashboard() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    pending: 0
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await listProjects({ limit: 10 })
      const projectsList = data.projects || []
      setProjects(projectsList)
      
      // Calculate stats
      const total = projectsList.length
      const successful = projectsList.filter(p => p.status === 'completed').length
      const pending = projectsList.filter(p => 
        ['uploaded', 'processing', 'expert_review'].includes(p.status)
      ).length
      
      setStats({ total, successful, pending })
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl mb-6 shadow-lg">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Accurate Takeoffs. Ready Within a Day.
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
          No clicks. No guesswork. Just fast, expert-verified takeoffs powered by AI.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link
            to="/projects/new"
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-semibold hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <Upload className="h-5 w-5 mr-2" />
            Upload a Plan
          </Link>
          <Link
            to="/projects"
            className="inline-flex items-center px-8 py-4 bg-white text-gray-700 border-2 border-gray-300 rounded-xl font-semibold hover:border-primary-500 hover:text-primary-600 transition-all"
          >
            View Projects
            <ArrowRight className="h-5 w-5 ml-2" />
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 rounded-lg">
              <FileText className="h-6 w-6 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Analyses</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Successful</p>
              <p className="text-2xl font-bold text-gray-900">{stats.successful}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 rounded-lg">
              <AlertCircle className="h-6 w-6 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Value Props */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 text-center">
          <div className="text-3xl font-bold text-primary-600 mb-2">1-Day</div>
          <div className="text-sm text-gray-600 mb-4">Turnaround</div>
          <p className="text-sm text-gray-500">Done-for-you takeoffs delivered within hours</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 text-center">
          <div className="text-3xl font-bold text-green-600 mb-2">3x</div>
          <div className="text-sm text-gray-600 mb-4">More Bids</div>
          <p className="text-sm text-gray-500">Quote faster. Win more.</p>
        </div>
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 text-center">
          <div className="text-3xl font-bold text-blue-600 mb-2">99%+</div>
          <div className="text-sm text-gray-600 mb-4">Accuracy</div>
          <p className="text-sm text-gray-500">AI precision + expert checks</p>
        </div>
      </div>

      {/* Recent Projects */}
      {projects.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Projects</h3>
            <Link
              to="/projects"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium"
            >
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => (
              <Link
                key={project.project_id}
                to={`/projects/${project.project_id}`}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
              >
                <div className="flex items-center space-x-4">
                  <FileText className="h-5 w-5 text-gray-400 group-hover:text-primary-600" />
                  <div>
                    <p className="font-medium text-gray-900 group-hover:text-primary-600">
                      {project.name || project.file_name}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(project.created_at).toLocaleDateString()} • {project.selected_trades?.length || 0} trades
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {project.status === 'completed' ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <Clock className="h-5 w-5 text-blue-600" />
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* How It Works */}
      <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-2xl p-8 mb-8 border border-primary-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
              1
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Upload Plans</h3>
            <p className="text-sm text-gray-600">Simply upload your PDF blueprints</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
              2
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Select Trades</h3>
            <p className="text-sm text-gray-600">Choose what trades you need</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
              3
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">AI Processing</h3>
            <p className="text-sm text-gray-600">AI extracts quantities, experts verify</p>
          </div>
          <div className="text-center">
            <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-3 text-xl font-bold">
              4
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Get Takeoff</h3>
            <p className="text-sm text-gray-600">Receive within 1 day, ready to use</p>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">AI-Powered Analysis</h3>
          <p className="text-gray-600 mb-4">
            Multi-agent system extracts quantities, analyzes floor plans, and reasons over specifications.
          </p>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Quantity take-off (doors, windows, hardware)
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Computer vision floor plan analysis
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Specification reasoning with RAG
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Comprehensive verification & validation
            </li>
          </ul>
        </div>

        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Real-Time Processing</h3>
          <p className="text-gray-600 mb-4">
            Monitor analysis progress in real-time with WebSocket updates and live status tracking.
          </p>
          <ul className="space-y-2 text-sm text-gray-600">
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Live progress updates
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Interactive visualizations
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Professional report generation
            </li>
            <li className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              Export results (Excel, CSV, PDF)
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

