import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout/Layout'
import Dashboard from './pages/Dashboard'
import Hosts from './pages/Hosts'
import Containers from './pages/Containers'
import System from './pages/System'
import SOC from './pages/SOC'

function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<Layout />}>
                    <Route index element={<Dashboard />} />
                    <Route path="hosts" element={<Hosts />} />
                    <Route path="containers/:hostId?" element={<Containers />} />
                    <Route path="system/:hostId?" element={<System />} />
                    <Route path="soc" element={<SOC />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                </Route>
            </Routes>
        </BrowserRouter>
    )
}

export default App
