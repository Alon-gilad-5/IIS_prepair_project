import { Routes, Route } from 'react-router-dom'
import StartPage from './pages/StartPage'
import InterviewPage from './pages/InterviewPage'
import FeedbackPage from './pages/FeedbackPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<StartPage />} />
      <Route path="/interview/:sessionId" element={<InterviewPage />} />
      <Route path="/feedback/:sessionId" element={<FeedbackPage />} />
    </Routes>
  )
}

export default App
