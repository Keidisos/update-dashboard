import { useState } from 'react'
import { Shield, Lock, X, AlertCircle } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function LoginModal({ onClose }) {
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const { login } = useAuth()

    const handleSubmit = (e) => {
        e.preventDefault()
        setError('')
        setLoading(true)

        // Small delay for UX
        setTimeout(() => {
            const success = login(password)

            if (success) {
                setPassword('')
                if (onClose) onClose()
            } else {
                setError('Mot de passe incorrect')
                setPassword('')
            }
            setLoading(false)
        }, 500)
    }

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full p-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-3 bg-purple-500/10 rounded-lg">
                            <Shield className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">SOC Access</h2>
                            <p className="text-sm text-gray-400">Authentication requise</p>
                        </div>
                    </div>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Mot de passe SOC
                        </label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition-colors"
                                placeholder="Entrez le mot de passe"
                                autoFocus
                                disabled={loading}
                            />
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="flex items-center gap-2 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                            <AlertCircle className="w-4 h-4" />
                            {error}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3">
                        <button
                            type="submit"
                            disabled={!password || loading}
                            className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white rounded-lg transition-colors font-medium"
                        >
                            {loading ? 'Vérification...' : 'Se connecter'}
                        </button>
                    </div>
                </form>

                {/* Info */}
                <div className="mt-6 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                    <p className="text-xs text-blue-300">
                        🔐 L'accès au SOC est protégé. Le mot de passe est défini dans la configuration serveur.
                    </p>
                </div>
            </div>
        </div>
    )
}
