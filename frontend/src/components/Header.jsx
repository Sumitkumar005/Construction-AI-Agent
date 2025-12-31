import { Link, useLocation } from 'react-router-dom'
import { FileText, Home, Plus, FolderOpen, Sparkles } from 'lucide-react'

export default function Header() {
  const location = useLocation()

  const isActive = (path) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname.startsWith(path)
  }

  return (
    <header className="bg-white/80 backdrop-blur-sm shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="flex items-center group">
            <div className="p-2 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg mr-3 group-hover:scale-110 transition-transform">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Construction AI</h1>
              <p className="text-xs text-gray-500 -mt-1">Takeoffs in a Day</p>
            </div>
          </Link>
          
          <nav className="flex items-center space-x-2">
            <Link
              to="/"
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/') && location.pathname === '/'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Home className="h-4 w-4 mr-2" />
              Dashboard
            </Link>
            <Link
              to="/projects"
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive('/projects') && location.pathname !== '/projects/new'
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <FolderOpen className="h-4 w-4 mr-2" />
              Projects
            </Link>
            <Link
              to="/projects/new"
              className="flex items-center px-4 py-2 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg text-sm font-semibold hover:from-primary-700 hover:to-primary-800 transition-all shadow-md hover:shadow-lg"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Takeoff
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

