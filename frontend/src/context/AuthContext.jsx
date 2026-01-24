import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [isAuthenticated, setIsAuthenticated] = useState(false)
    const [loading, setLoading] = useState(true)

    // Check localStorage on mount
    useEffect(() => {
        const token = localStorage.getItem('soc_auth_token')
        if (token === 'authenticated') {
            setIsAuthenticated(true)
        }
        setLoading(false)
    }, [])

    const login = (password) => {
        // Simple password check - in production, this would be validated against backend
        // For now, we use a hardcoded password that should match env variable
        const SOC_PASSWORD = import.meta.env.VITE_SOC_PASSWORD || 'admin'

        if (password === SOC_PASSWORD) {
            setIsAuthenticated(true)
            localStorage.setItem('soc_auth_token', 'authenticated')
            return true
        }
        return false
    }

    const logout = () => {
        setIsAuthenticated(false)
        localStorage.removeItem('soc_auth_token')
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider')
    }
    return context
}
