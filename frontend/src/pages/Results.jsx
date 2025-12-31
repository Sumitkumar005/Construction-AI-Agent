import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { Download, ArrowLeft, FileText, BarChart3, CheckCircle, AlertTriangle } from 'lucide-react'
import { generateReport } from '../services/api'
import QuantityChart from '../components/QuantityChart'
import VerificationCard from '../components/VerificationCard'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Results() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [results, setResults] = useState(location.state?.results || null)
  const [loading, setLoading] = useState(!location.state?.results)
  const [generatingReport, setGeneratingReport] = useState(false)

  useEffect(() => {
    // If no results in state, fetch from API
    if (!results && id) {
      // In production, fetch from API
      // fetchResults(id).then(setResults).finally(() => setLoading(false))
      setLoading(false)
    }
  }, [id, results])

  const handleDownloadReport = async (format) => {
    if (!results) return

    setGeneratingReport(true)
    try {
      const blob = await generateReport(results, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${id}.${format === 'pdf' ? 'pdf' : 'html'}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Error generating report:', error)
      alert('Failed to generate report')
    } finally {
      setGeneratingReport(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (!results) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
          <p className="text-lg font-medium text-yellow-900">Results not found</p>
          <p className="text-sm text-yellow-700 mt-2">
            The analysis results could not be loaded.
          </p>
          <button
            onClick={() => navigate('/analyze')}
            className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Start New Analysis
          </button>
        </div>
      </div>
    )
  }

  const quantities = results.quantities?.quantities || {}
  const verification = results.verification || {}
  const extraction = results.extraction || {}

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <button
            onClick={() => navigate('/analyze')}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Analysis
          </button>
          <h2 className="text-3xl font-bold text-gray-900">Analysis Results</h2>
          <p className="text-gray-600 mt-1">
            Document: {extraction.document_path?.split('/').pop() || 'Unknown'}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => handleDownloadReport('html')}
            disabled={generatingReport}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 transition-colors"
          >
            <Download className="h-4 w-4 mr-2" />
            {generatingReport ? 'Generating...' : 'Download Report'}
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className={`rounded-lg shadow p-6 mb-6 ${
        results.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
      }`}>
        <div className="flex items-center">
          {results.success ? (
            <CheckCircle className="h-6 w-6 text-green-600 mr-3" />
          ) : (
            <AlertTriangle className="h-6 w-6 text-red-600 mr-3" />
          )}
          <div>
            <p className={`font-semibold ${results.success ? 'text-green-900' : 'text-red-900'}`}>
              {results.success ? 'Analysis Completed Successfully' : 'Analysis Failed'}
            </p>
            <p className={`text-sm ${results.success ? 'text-green-700' : 'text-red-700'}`}>
              Overall Confidence: {((verification.overall_confidence || 0) * 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Quantities Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center mb-4">
          <BarChart3 className="h-6 w-6 text-primary-600 mr-2" />
          <h3 className="text-xl font-semibold text-gray-900">Extracted Quantities</h3>
        </div>
        <QuantityChart quantities={quantities} />
      </div>

      {/* Verification Section */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center mb-4">
          <CheckCircle className="h-6 w-6 text-green-600 mr-2" />
          <h3 className="text-xl font-semibold text-gray-900">Verification Results</h3>
        </div>
        <VerificationCard verification={verification} />
      </div>

      {/* Recommendations */}
      {verification.recommendations && verification.recommendations.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">Recommendations</h3>
          <ul className="space-y-2">
            {verification.recommendations.map((rec, index) => (
              <li key={index} className="flex items-start text-blue-800">
                <span className="mr-2">•</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

