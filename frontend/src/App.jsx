import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import Hosts from './pages/Hosts'
import Containers from './pages/Containers'
import System from './pages/System'
import SOC from './pages/SOC'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/Auth/ProtectedRoute'

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Layout />}>
                        <Route index element={<Dashboard />} />
                        <Route path="hosts" element={<Hosts />} />
                        <Route path="containers/:hostId?" element={<Containers />} />
                        <Route path="system/:hostId?" element={<System />} />
                        <Route
                            path="soc"
                            element={
                                <ProtectedRoute>
                                    <SOC />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Route>
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    )
}

export default App
