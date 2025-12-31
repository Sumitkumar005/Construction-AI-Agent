import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { processDocument } from '../services/api'
import { useWebSocket } from '../hooks/useWebSocket'
import ProgressIndicator from '../components/ProgressIndicator'

export default function Analysis() {
  const navigate = useNavigate()
  const [files, setFiles] = useState([])
  const [specFiles, setSpecFiles] = useState([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState({ stage: '', progress: 0, message: '' })
  const [error, setError] = useState(null)
  const [clientId] = useState(() => `client_${Date.now()}`)

  // WebSocket connection for real-time updates
  const wsUrl = import.meta.env.VITE_API_URL 
    ? import.meta.env.VITE_API_URL.replace('http://', 'ws://').replace('https://', 'wss://')
    : 'ws://localhost:8000'
  const { connected, lastMessage } = useWebSocket(`${wsUrl}/ws/${clientId}`)

  // Handle progress updates from WebSocket
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'progress') {
      setProgress({
        stage: lastMessage.stage,
        progress: lastMessage.progress,
        message: lastMessage.message
      })
    }
  }, [lastMessage])

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(acceptedFiles)
    setError(null)
  }, [])

  const onSpecDrop = useCallback((acceptedFiles) => {
    setSpecFiles(acceptedFiles)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  })

  const { getRootProps: getSpecRootProps, getInputProps: getSpecInputProps } = useDropzone({
    onDrop: onSpecDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  })

  const handleRemoveFile = () => {
    setFiles([])
  }

  const handleRemoveSpecFile = (index) => {
    setSpecFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    if (files.length === 0) {
      setError('Please upload a document to analyze')
      return
    }

    setIsProcessing(true)
    setError(null)
    setProgress({ stage: 'upload', progress: 0, message: 'Starting analysis...' })

    try {
      const formData = new FormData()
      formData.append('file', files[0])
      specFiles.forEach((file, index) => {
        formData.append('spec_docs', file)
      })
      formData.append('client_id', clientId)

      const result = await processDocument(formData)
      
      // Navigate to results page
      navigate(`/results/${result.file_id || result.client_id}`, { 
        state: { results: result } 
      })
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
      setIsProcessing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Analyze Construction Document</h2>
        <p className="text-gray-600">
          Upload a construction PDF to extract quantities, analyze floor plans, and verify against specifications
        </p>
      </div>

      {/* Main Document Upload */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Construction Document</h3>
        
        {files.length === 0 ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-primary-500 bg-primary-50'
                : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">
              {isDragActive ? 'Drop the file here' : 'Drag & drop a PDF file here, or click to select'}
            </p>
            <p className="text-sm text-gray-500">PDF files only (max 1GB)</p>
          </div>
        ) : (
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center">
              <FileText className="h-5 w-5 text-primary-600 mr-3" />
              <div>
                <p className="font-medium text-gray-900">{files[0].name}</p>
                <p className="text-sm text-gray-500">
                  {(files[0].size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={handleRemoveFile}
              className="p-2 text-gray-400 hover:text-red-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>

      {/* Specification Documents (Optional) */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Specification Documents (Optional)
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          Upload Division 8/9 specification documents for compliance checking
        </p>

        <div
          {...getSpecRootProps()}
          className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-400 hover:bg-gray-50 transition-colors"
        >
          <input {...getSpecInputProps()} />
          <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600">
            Click to upload or drag & drop specification PDFs
          </p>
        </div>

        {specFiles.length > 0 && (
          <div className="mt-4 space-y-2">
            {specFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center">
                  <FileText className="h-4 w-4 text-gray-600 mr-2" />
                  <span className="text-sm text-gray-900">{file.name}</span>
                </div>
                <button
                  onClick={() => handleRemoveSpecFile(index)}
                  className="p-1 text-gray-400 hover:text-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Progress Indicator */}
      {isProcessing && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <ProgressIndicator
            stage={progress.stage}
            progress={progress.progress}
            message={progress.message}
            connected={connected}
          />
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
          <AlertCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Submit Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={files.length === 0 || isProcessing}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center"
        >
          {isProcessing ? (
            <>
              <Loader2 className="h-5 w-5 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <CheckCircle className="h-5 w-5 mr-2" />
              Start Analysis
            </>
          )}
        </button>
      </div>
    </div>
  )
}

