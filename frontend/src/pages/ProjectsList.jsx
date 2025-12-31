import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FolderOpen, Plus, Clock, CheckCircle, AlertCircle, FileText } from 'lucide-react'
import { listProjects } from '../services/api'

const STATUS_COLORS = {
  uploaded: 'bg-gray-100 text-gray-700',
  processing: 'bg-blue-100 text-blue-700',
  ai_complete: 'bg-yellow-100 text-yellow-700',
  expert_review: 'bg-orange-100 text-orange-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700'
}

export default function ProjectsList() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      const data = await listProjects()
      setProjects(data.projects || [])
    } catch (err) {
      console.error('Error loading projects:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading projects...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-600 mt-1">Manage your takeoff projects</p>
        </div>
        <Link
          to="/projects/new"
          className="flex items-center px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg font-semibold hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg hover:shadow-xl"
        >
          <Plus className="h-5 w-5 mr-2" />
          New Takeoff
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="bg-white rounded-2xl shadow border border-gray-200 p-12 text-center">
          <FolderOpen className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-600 mb-6">Create your first takeoff to get started</p>
          <Link
            to="/projects/new"
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
          >
            <Plus className="h-5 w-5 mr-2" />
            Create New Takeoff
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((project) => (
            <Link
              key={project.project_id}
              to={`/projects/${project.project_id}`}
              className="bg-white rounded-xl shadow border border-gray-200 p-6 hover:shadow-lg transition-all group"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="p-3 bg-primary-100 rounded-lg group-hover:bg-primary-200 transition-colors">
                    <FileText className="h-6 w-6 text-primary-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                      {project.name || project.file_name}
                    </h3>
                    <p className="text-sm text-gray-600 mt-1">
                      {project.selected_trades?.length || 0} trades • {project.file_size_mb?.toFixed(2) || 0} MB
                    </p>
                    <div className="flex items-center space-x-4 mt-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[project.status] || STATUS_COLORS.uploaded}`}>
                        {project.status?.replace('_', ' ').toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500">
                        {new Date(project.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="ml-4">
                  {project.status === 'completed' ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : project.status === 'failed' ? (
                    <AlertCircle className="h-6 w-6 text-red-600" />
                  ) : (
                    <Clock className="h-6 w-6 text-blue-600" />
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

