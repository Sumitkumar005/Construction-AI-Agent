import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Download, ArrowLeft, CheckCircle, AlertTriangle, FileSpreadsheet, FileText, File, Clock, Zap, Home, Ruler } from 'lucide-react'
import { getProject, getTakeoff, exportTakeoff } from '../services/api'
import QuantityChart from '../components/QuantityChart'
import VerificationCard from '../components/VerificationCard'
import LoadingSpinner from '../components/LoadingSpinner'
import ConfidenceGauge from '../components/ConfidenceGauge'
import TechStackBadge from '../components/TechStackBadge'

export default function ProjectResults() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [takeoff, setTakeoff] = useState(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    loadData()
  }, [id])

  const loadData = async () => {
    try {
      const [projectData, takeoffData] = await Promise.all([
        getProject(id),
        getTakeoff(id).catch(() => null) // Takeoff might not exist yet
      ])
      setProject(projectData)
      setTakeoff(takeoffData)
    } catch (err) {
      console.error('Error loading data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    setExporting(true)
    try {
      const blob = await exportTakeoff(id, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `takeoff_${id}.${format === 'excel' ? 'xlsx' : format === 'csv' ? 'csv' : 'html'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error exporting:', error)
      alert('Failed to export takeoff')
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <LoadingSpinner />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <p className="text-lg font-medium text-yellow-900">Project not found</p>
          <button
            onClick={() => navigate('/projects', { replace: true })}
            className="mt-4 inline-block px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Back to Projects
          </button>
        </div>
      </div>
    )
  }

  const quantities = takeoff?.quantities || {}
  const verification = takeoff?.verification_results || {}

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate('/projects', { replace: true })}
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4 transition-colors"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Projects
        </button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{project.name || project.file_name}</h1>
            <p className="text-gray-600 mt-1">
              {project.selected_trades?.length || 0} trades • Created {new Date(project.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => handleExport('excel')}
              disabled={exporting || !takeoff}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
            >
              <FileSpreadsheet className="h-4 w-4 mr-2" />
              Excel
            </button>
            <button
              onClick={() => handleExport('csv')}
              disabled={exporting || !takeoff}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <FileText className="h-4 w-4 mr-2" />
              CSV
            </button>
            <button
              onClick={() => handleExport('pdf')}
              disabled={exporting || !takeoff}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
            >
              <File className="h-4 w-4 mr-2" />
              PDF
            </button>
          </div>
        </div>
      </div>

      {/* Status Card with Processing Time & Confidence */}
      {takeoff && (
        <div className={`rounded-xl shadow-lg p-6 mb-6 ${
          takeoff.status === 'completed'
            ? 'bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200'
            : 'bg-gradient-to-r from-blue-50 to-primary-50 border border-blue-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {takeoff.status === 'completed' ? (
                <CheckCircle className="h-8 w-8 text-green-600 mr-4" />
              ) : (
                <AlertTriangle className="h-8 w-8 text-blue-600 mr-4" />
              )}
              <div>
                <p className={`font-semibold text-lg ${
                  takeoff.status === 'completed' ? 'text-green-900' : 'text-blue-900'
                }`}>
                  {takeoff.status === 'completed' ? 'Takeoff Completed' : 'Takeoff in Progress'}
                </p>
                <p className={`text-sm mt-1 ${
                  takeoff.status === 'completed' ? 'text-green-700' : 'text-blue-700'
                }`}>
                  {takeoff.processing_time_seconds && (
                    <span className="inline-flex items-center">
                      <Zap className="h-4 w-4 mr-1" />
                      {takeoff.processing_time_seconds < 60 
                        ? `Processed in ${takeoff.processing_time_seconds.toFixed(1)}s`
                        : `Processed in ${(takeoff.processing_time_seconds / 60).toFixed(1)}min`
                      }
                    </span>
                  )}
                </p>
              </div>
            </div>
            {/* Animated Confidence Gauge */}
            {verification.overall_confidence && (
              <ConfidenceGauge confidence={(verification.overall_confidence * 100)} size={100} />
            )}
          </div>
        </div>
      )}

      {/* Quick Stats Card */}
      {takeoff && quantities && Object.keys(quantities).length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Total Area Analyzed */}
          {(() => {
            const totalSqft = Object.values(quantities).reduce((sum, trade) => {
              if (trade.total_sqft) return sum + (trade.total_sqft || 0)
              return sum
            }, 0)
            return totalSqft > 0 ? (
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6 border border-blue-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-700 mb-1">Total Area Analyzed</p>
                    <p className="text-2xl font-bold text-blue-900">{totalSqft.toLocaleString()} sqft</p>
                  </div>
                  <Ruler className="h-8 w-8 text-blue-600" />
                </div>
              </div>
            ) : null
          })()}
          
          {/* Rooms Detected */}
          {(() => {
            const roomCount = Object.values(quantities).reduce((count, trade) => {
              if (trade.rooms) return count + Object.keys(trade.rooms).length
              return count
            }, 0)
            return roomCount > 0 ? (
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-700 mb-1">Rooms Detected</p>
                    <p className="text-2xl font-bold text-purple-900">{roomCount}</p>
                  </div>
                  <Home className="h-8 w-8 text-purple-600" />
                </div>
              </div>
            ) : null
          })()}
          
          {/* Trades Processed */}
          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6 border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-700 mb-1">Trades Processed</p>
                <p className="text-2xl font-bold text-green-900">{Object.keys(quantities).length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </div>
        </div>
      )}

      {!takeoff ? (
        <div className="bg-white rounded-xl shadow border border-gray-200 p-12 text-center">
          <Clock className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Takeoff Not Ready</h3>
          <p className="text-gray-600 mb-6">Your takeoff is still being processed</p>
          <Link
            to={`/projects/${id}/process`}
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white rounded-lg font-semibold hover:bg-primary-700 transition-colors"
          >
            View Processing Status
          </Link>
        </div>
      ) : (
        <>
          {/* Quantities Section */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Extracted Quantities</h2>
            <QuantityChart quantities={quantities} />
          </div>

          {/* Verification Section */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-8 mb-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Verification Results</h2>
            <VerificationCard verification={verification} />
          </div>

          {/* Tech Stack Badge */}
          <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6">
            <TechStackBadge />
          </div>
        </>
      )}
    </div>
  )
}

