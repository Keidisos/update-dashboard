import { Outlet, NavLink, useLocation } from 'react-router-dom'
import {
    LayoutDashboard,
    Server,
    Container,
    Monitor,
    Settings,
    RefreshCw,
    Shield
} from 'lucide-react'
import { useHostStore } from '../../store/hostStore'
import { useEffect } from 'react'
import HostSelector from '../Hosts/HostSelector'

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/hosts', icon: Server, label: 'Hosts' },
    { path: '/containers', icon: Container, label: 'Containers' },
    { path: '/system', icon: Monitor, label: 'System' },
    { path: '/soc', icon: Shield, label: 'SOC' },
]

function Layout() {
    const location = useLocation()
    const { fetchHosts, loading } = useHostStore()

    useEffect(() => {
        fetchHosts()
    }, [fetchHosts])

    return (
        <div className="flex h-screen bg-dark-950">
            {/* Sidebar */}
            <aside className="w-64 bg-dark-900/50 border-r border-dark-800 flex flex-col">
                {/* Logo */}
                <div className="p-6 border-b border-dark-800">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
                            <RefreshCw className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-lg font-bold text-white">Update</h1>
                            <p className="text-xs text-dark-400">Dashboard</p>
                        </div>
                    </div>
                </div>

                {/* Host Selector */}
                <div className="p-4 border-b border-dark-800">
                    <HostSelector />
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon
                        const isActive = location.pathname === item.path ||
                            (item.path !== '/' && location.pathname.startsWith(item.path))

                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition-all duration-200 ${isActive
                                    ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                                    : 'text-dark-300 hover:bg-dark-800 hover:text-white'
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                <span className="font-medium">{item.label}</span>
                            </NavLink>
                        )
                    })}
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-dark-800">
                    <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-dark-400 hover:bg-dark-800 hover:text-white transition-all duration-200">
                        <Settings className="w-5 h-5" />
                        <span className="font-medium">Settings</span>
                    </button>
                </div>
            </aside>

            {/* Main content */}
            <main className="flex-1 overflow-auto">
                <div className="p-8">
                    <Outlet />
                </div>
            </main>
        </div>
    )
}

export default Layout
