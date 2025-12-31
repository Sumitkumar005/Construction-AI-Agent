import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { 
  Upload, FileText, CheckCircle, Clock, TrendingUp, 
  Sparkles, ArrowRight, Plus, FolderOpen, BarChart3,
  Zap, Shield, Target
} from 'lucide-react'
import { listProjects } from '../services/api'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import EmptyState from '../components/ui/EmptyState'

export default function DashboardNew() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    pending: 0,
    accuracy: 99.2
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await listProjects({ limit: 5 })
      const projectsList = data.projects || []
      setProjects(projectsList)
      
      const total = projectsList.length
      const successful = projectsList.filter(p => p.status === 'completed').length
      const pending = projectsList.filter(p => 
        ['uploaded', 'processing', 'expert_review'].includes(p.status)
      ).length
      
      setStats({ total, successful, pending, accuracy: 99.2 })
    } catch (error) {
      console.error('Error loading dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      completed: { variant: 'success', label: 'Completed' },
      processing: { variant: 'info', label: 'Processing' },
      expert_review: { variant: 'warning', label: 'Review' },
      uploaded: { variant: 'default', label: 'Uploaded' },
      failed: { variant: 'error', label: 'Failed' },
    }
    const config = statusMap[status] || statusMap.uploaded
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 via-primary-700 to-blue-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-sm rounded-2xl mb-6">
              <Sparkles className="h-10 w-10" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-4">
              Accurate Takeoffs.
              <br />
              <span className="text-primary-200">Ready Within a Day.</span>
            </h1>
            <p className="text-xl text-primary-100 mb-8 max-w-2xl mx-auto">
              No clicks. No guesswork. Just fast, expert-verified takeoffs powered by AI.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/projects/new">
                <Button size="xl" variant="secondary" className="bg-white text-primary-700 hover:bg-gray-50">
                  <Upload className="h-5 w-5 mr-2" />
                  Upload a Plan
                </Button>
              </Link>
              <Link to="/projects">
                <Button size="xl" variant="outline" className="border-white/30 text-white hover:bg-white/10">
                  View Projects
                  <ArrowRight className="h-5 w-5 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card hover>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Total Projects</p>
                <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <div className="p-3 bg-primary-100 rounded-xl">
                <FolderOpen className="h-6 w-6 text-primary-600" />
              </div>
            </div>
          </Card>

          <Card hover>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Completed</p>
                <p className="text-3xl font-bold text-green-600">{stats.successful}</p>
              </div>
              <div className="p-3 bg-green-100 rounded-xl">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </Card>

          <Card hover>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">In Progress</p>
                <p className="text-3xl font-bold text-blue-600">{stats.pending}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-xl">
                <Clock className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </Card>

          <Card hover>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Accuracy</p>
                <p className="text-3xl font-bold text-purple-600">{stats.accuracy}%</p>
              </div>
              <div className="p-3 bg-purple-100 rounded-xl">
                <Target className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </Card>
        </div>

        {/* Value Props */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <Card className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl mb-4 text-white">
              <Zap className="h-7 w-7" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">1-Day Turnaround</h3>
            <p className="text-gray-600">Done-for-you takeoffs delivered within hours</p>
          </Card>

          <Card className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-green-500 to-green-600 rounded-xl mb-4 text-white">
              <TrendingUp className="h-7 w-7" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">3x More Bids</h3>
            <p className="text-gray-600">Quote faster. Win more projects.</p>
          </Card>

          <Card className="text-center">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl mb-4 text-white">
              <Shield className="h-7 w-7" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">99%+ Accuracy</h3>
            <p className="text-gray-600">AI precision + expert verification</p>
          </Card>
        </div>

        {/* Recent Projects */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Recent Projects</h2>
            <Link to="/projects">
              <Button variant="ghost" size="sm">
                View All
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="grid gap-4">
              {[1, 2, 3].map(i => (
                <Card key={i} className="animate-pulse">
                  <div className="h-20 bg-gray-200 rounded"></div>
                </Card>
              ))}
            </div>
          ) : projects.length === 0 ? (
            <Card>
              <EmptyState
                icon={FolderOpen}
                title="No projects yet"
                description="Create your first takeoff to get started"
                action={
                  <Link to="/projects/new">
                    <Button>
                      <Plus className="h-4 w-4 mr-2" />
                      Create New Takeoff
                    </Button>
                  </Link>
                }
              />
            </Card>
          ) : (
            <div className="grid gap-4">
              {projects.map((project) => (
                <Link
                  key={project.project_id}
                  to={`/projects/${project.project_id}`}
                >
                  <Card hover className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="p-3 bg-primary-100 rounded-lg">
                        <FileText className="h-6 w-6 text-primary-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900 mb-1">
                          {project.name || project.file_name}
                        </h3>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>{project.selected_trades?.length || 0} trades</span>
                          <span>•</span>
                          <span>{new Date(project.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      {getStatusBadge(project.status)}
                      <ArrowRight className="h-5 w-5 text-gray-400" />
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* How It Works */}
        <Card className="bg-gradient-to-br from-primary-50 to-blue-50 border-primary-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">How It Works</h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: '1', title: 'Upload Plans', desc: 'Simply upload your PDF blueprints' },
              { step: '2', title: 'Select Trades', desc: 'Choose what trades you need' },
              { step: '3', title: 'AI Processing', desc: 'AI extracts quantities, experts verify' },
              { step: '4', title: 'Get Takeoff', desc: 'Receive within 1 day, ready to use' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 bg-white rounded-full shadow-md mb-4 text-xl font-bold text-primary-600">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}


