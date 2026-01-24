import { useAuth } from '../../context/AuthContext'
import LoginModal from './LoginModal'

export default function ProtectedRoute({ children }) {
    const { isAuthenticated, loading } = useAuth()

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-gray-400">Chargement...</div>
            </div>
        )
    }

    if (!isAuthenticated) {
        return <LoginModal />
    }

    return children
}
