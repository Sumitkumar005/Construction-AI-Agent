import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Check, ArrowRight, Sparkles } from 'lucide-react'
import { createProject, getSupportedTrades } from '../services/api'

const TRADE_ICONS = {
  painting: '🎨',
  drywall: '🧱',
  doors_windows: '🚪',
  flooring: '🧼',
  concrete: '🧱',
  roofing: '🏠',
  hvac: '🛠️',
  electrical: '🔌',
  plumbing: '🚿',
  earthwork: '⛏️',
  landscaping: '🌱'
}

export default function NewProject() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [selectedTrades, setSelectedTrades] = useState([])
  const [availableTrades, setAvailableTrades] = useState([])
  const [projectName, setProjectName] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Load supported trades
    getSupportedTrades().then(data => {
      setAvailableTrades(data.trades || [])
    }).catch(err => {
      console.error('Error loading trades:', err)
    })
  }, [])

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      setError(null)
      // Auto-generate project name from filename
      if (!projectName) {
        const name = acceptedFiles[0].name.replace(/\.[^/.]+$/, '')
        setProjectName(name)
      }
    }
  }, [projectName])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  const toggleTrade = (tradeId) => {
    setSelectedTrades(prev => 
      prev.includes(tradeId)
        ? prev.filter(t => t !== tradeId)
        : [...prev, tradeId]
    )
  }

  const handleSubmit = async () => {
    if (!file) {
      setError('Please upload a construction plan')
      return
    }

    if (selectedTrades.length === 0) {
      setError('Please select at least one trade')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('trades', selectedTrades.join(','))
      if (projectName) {
        formData.append('name', projectName)
      }

      const result = await createProject(formData)
      
      // Navigate to project processing page
      navigate(`/projects/${result.project_id}/process`, {
        state: { project: result }
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create project')
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-2xl mb-4">
            <Sparkles className="h-8 w-8 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Create New Takeoff
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Upload your construction plans and select trades. Get accurate takeoffs within a day.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-8 space-y-8">
          {/* Step 1: Upload */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full mr-3 text-sm font-bold">1</span>
              Upload Construction Plans
            </h2>
            
            {!file ? (
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
                  isDragActive
                    ? 'border-primary-500 bg-primary-50 scale-[1.02]'
                    : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
                }`}
              >
                <input {...getInputProps()} />
                <div className="flex flex-col items-center">
                  <div className="p-4 bg-primary-100 rounded-full mb-4">
                    <Upload className="h-8 w-8 text-primary-600" />
                  </div>
                  <p className="text-lg font-medium text-gray-900 mb-2">
                    {isDragActive ? 'Drop your file here' : 'Drag & drop your PDF plans'}
                  </p>
                  <p className="text-sm text-gray-500 mb-4">or click to browse</p>
                  <p className="text-xs text-gray-400">PDF files only • Max 1GB</p>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-between p-5 bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl border border-primary-200">
                <div className="flex items-center space-x-4">
                  <div className="p-3 bg-primary-600 rounded-lg">
                    <FileText className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900">{file.name}</p>
                    <p className="text-sm text-gray-600">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="p-2 text-gray-400 hover:text-red-600 transition-colors rounded-lg hover:bg-white"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            )}
          </div>

          {/* Step 2: Project Name */}
          {file && (
            <div className="animate-fade-in">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full mr-3 text-sm font-bold">2</span>
                Project Name (Optional)
              </h2>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="e.g., 50-Unit Apartment Building"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          )}

          {/* Step 3: Select Trades */}
          {file && (
            <div className="animate-fade-in">
              <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                <span className="flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full mr-3 text-sm font-bold">3</span>
                Select Trades
                <span className="ml-2 text-sm font-normal text-gray-500">
                  ({selectedTrades.length} selected)
                </span>
              </h2>
              
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {availableTrades.filter(t => t.enabled).map((trade) => {
                  const isSelected = selectedTrades.includes(trade.id)
                  return (
                    <button
                      key={trade.id}
                      onClick={() => toggleTrade(trade.id)}
                      className={`p-4 rounded-xl border-2 transition-all text-left ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 shadow-md scale-105'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-2xl">{TRADE_ICONS[trade.id] || '📋'}</span>
                        {isSelected && (
                          <div className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                            <Check className="h-3 w-3 text-white" />
                          </div>
                        )}
                      </div>
                      <p className="font-medium text-gray-900 text-sm">{trade.name}</p>
                      <p className="text-xs text-gray-500 mt-1">{trade.unit}</p>
                    </button>
                  )
                })}
              </div>

              {availableTrades.some(t => !t.enabled) && (
                <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    <strong>Coming Soon:</strong> {availableTrades.filter(t => !t.enabled).map(t => t.name).join(', ')}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start">
              <div className="flex-shrink-0">
                <X className="h-5 w-5 text-red-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-900">Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Submit Button */}
          {file && selectedTrades.length > 0 && (
            <div className="pt-6 border-t border-gray-200">
              <button
                onClick={handleSubmit}
                disabled={isLoading}
                className="w-full flex items-center justify-center px-6 py-4 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-semibold hover:from-primary-700 hover:to-primary-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl transform hover:scale-[1.02]"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Creating Project...
                  </>
                ) : (
                  <>
                    Start Takeoff
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h3 className="font-semibold text-blue-900 mb-2">What happens next?</h3>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <Check className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>AI agents extract quantities for selected trades</span>
            </li>
            <li className="flex items-start">
              <Check className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Expert review ensures 99%+ accuracy</span>
            </li>
            <li className="flex items-start">
              <Check className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
              <span>Receive your takeoff within 1 day</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

