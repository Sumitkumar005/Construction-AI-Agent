import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import ErrorBoundary from './components/ErrorBoundary'
import DashboardNew from './pages/DashboardNew'
import NewProject from './pages/NewProject'
import ProjectProcessing from './pages/ProjectProcessing'
import ProjectResults from './pages/ProjectResults'
import ProjectsList from './pages/ProjectsList'
import './App.css'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <Routes>
            <Route path="/" element={<DashboardNew />} />
            <Route path="/projects/new" element={<NewProject />} />
            <Route path="/projects" element={<ProjectsList />} />
            <Route path="/projects/:id/process" element={<ProjectProcessing />} />
            <Route path="/projects/:id" element={<ProjectResults />} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/analyze" element={<NewProject />} />
            <Route path="/results/:id" element={<ProjectResults />} />
          </Routes>
        </div>
      </Router>
    </ErrorBoundary>
  )
}

export default App

