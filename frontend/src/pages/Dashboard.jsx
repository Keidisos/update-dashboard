import { useState, useEffect } from 'react'
import {
    Container,
    Server,
    Monitor,
    ArrowUpCircle,
    RefreshCw,
    AlertCircle,
    CheckCircle2,
    Clock
} from 'lucide-react'
import { useHostStore } from '../store/hostStore'
import { containersApi, systemApi } from '../services/api'

function StatCard({ icon: Icon, label, value, subvalue, color = 'primary' }) {
    const colorClasses = {
        primary: 'from-primary-500 to-primary-700',
        emerald: 'from-emerald-500 to-emerald-700',
        amber: 'from-amber-500 to-amber-700',
        red: 'from-red-500 to-red-700',
    }

    return (
        <div className="card p-6 flex items-center gap-4">
            <div className={`w-14 h-14 bg-gradient-to-br ${colorClasses[color]} rounded-xl flex items-center justify-center shadow-lg`}>
                <Icon className="w-7 h-7 text-white" />
            </div>
            <div>
                <p className="text-dark-400 text-sm font-medium">{label}</p>
                <p className="text-2xl font-bold text-white">{value}</p>
                {subvalue && <p className="text-xs text-dark-500">{subvalue}</p>}
            </div>
        </div>
    )
}

function Dashboard() {
    const { hosts, selectedHostId, getSelectedHost } = useHostStore()
    const [stats, setStats] = useState({
        containers: { total: 0, running: 0, updates: 0 },
        system: { updates: 0 },
        loading: true,
    })
    const [recentActivity, setRecentActivity] = useState([])

    const selectedHost = getSelectedHost()

    useEffect(() => {
        if (!selectedHostId) return

        const fetchStats = async () => {
            setStats(prev => ({ ...prev, loading: true }))

            try {
                // Fetch containers
                const containersRes = await containersApi.list(selectedHostId, {
                    all: true,
                    checkUpdates: true
                })
                const containers = containersRes.data

                const containerStats = {
                    total: containers.length,
                    running: containers.filter(c => c.state === 'running').length,
                    updates: containers.filter(c => c.update_available).length,
                }

                // Fetch system updates
                let systemUpdates = 0
                try {
                    const systemRes = await systemApi.checkUpdates(selectedHostId)
                    systemUpdates = systemRes.data.updates_available
                } catch (e) {
                    console.warn('Could not fetch system updates:', e)
                }

                setStats({
                    containers: containerStats,
                    system: { updates: systemUpdates },
                    loading: false,
                })

                // Set recent containers with updates as activity
                setRecentActivity(
                    containers
                        .filter(c => c.update_available)
                        .slice(0, 5)
                        .map(c => ({
                            type: 'container_update',
                            name: c.name,
                            image: c.image,
                            time: new Date().toISOString(),
                        }))
                )
            } catch (error) {
                console.error('Failed to fetch stats:', error)
                setStats(prev => ({ ...prev, loading: false }))
            }
        }

        fetchStats()
    }, [selectedHostId])

    if (!selectedHost) {
        return (
            <div className="flex flex-col items-center justify-center h-96">
                <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mb-4">
                    <Server className="w-10 h-10 text-dark-500" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">No host selected</h2>
                <p className="text-dark-400 mb-4">Select a host from the sidebar or add a new one</p>
                <a href="/hosts" className="btn btn-primary">
                    Manage Hosts
                </a>
            </div>
        )
    }

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                <p className="text-dark-400">
                    Overview for <span className="text-primary-400 font-medium">{selectedHost.name}</span>
                </p>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={Container}
                    label="Total Containers"
                    value={stats.loading ? '...' : stats.containers.total}
                    subvalue={`${stats.containers.running} running`}
                    color="primary"
                />
                <StatCard
                    icon={CheckCircle2}
                    label="Running"
                    value={stats.loading ? '...' : stats.containers.running}
                    subvalue="Healthy containers"
                    color="emerald"
                />
                <StatCard
                    icon={ArrowUpCircle}
                    label="Container Updates"
                    value={stats.loading ? '...' : stats.containers.updates}
                    subvalue="Available updates"
                    color={stats.containers.updates > 0 ? 'amber' : 'primary'}
                />
                <StatCard
                    icon={Monitor}
                    label="System Updates"
                    value={stats.loading ? '...' : stats.system.updates}
                    subvalue="Package updates"
                    color={stats.system.updates > 0 ? 'amber' : 'primary'}
                />
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Containers with updates */}
                <div className="card">
                    <div className="p-4 border-b border-dark-700/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <ArrowUpCircle className="w-5 h-5 text-amber-400" />
                            <h3 className="font-semibold text-white">Available Updates</h3>
                        </div>
                        <a
                            href="/containers"
                            className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
                        >
                            View all →
                        </a>
                    </div>
                    <div className="p-4">
                        {stats.loading ? (
                            <div className="flex items-center justify-center py-8">
                                <RefreshCw className="w-6 h-6 text-dark-500 animate-spin" />
                            </div>
                        ) : recentActivity.length === 0 ? (
                            <div className="text-center py-8">
                                <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
                                <p className="text-dark-400">All containers are up to date!</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recentActivity.map((item, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center justify-between p-3 bg-dark-800/50 rounded-lg"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 bg-amber-500/20 rounded-lg flex items-center justify-center">
                                                <Container className="w-4 h-4 text-amber-400" />
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-white">{item.name}</p>
                                                <p className="text-xs text-dark-400">{item.image}</p>
                                            </div>
                                        </div>
                                        <span className="badge badge-update">Update</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Host Info */}
                <div className="card">
                    <div className="p-4 border-b border-dark-700/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Server className="w-5 h-5 text-primary-400" />
                            <h3 className="font-semibold text-white">Host Information</h3>
                        </div>
                    </div>
                    <div className="p-4 space-y-3">
                        <div className="flex justify-between items-center p-3 bg-dark-800/50 rounded-lg">
                            <span className="text-dark-400">Hostname</span>
                            <span className="text-white font-mono text-sm">{selectedHost.hostname}</span>
                        </div>
                        <div className="flex justify-between items-center p-3 bg-dark-800/50 rounded-lg">
                            <span className="text-dark-400">Connection</span>
                            <span className="text-white text-sm capitalize">{selectedHost.connection_type}</span>
                        </div>
                        {selectedHost.os_type && (
                            <div className="flex justify-between items-center p-3 bg-dark-800/50 rounded-lg">
                                <span className="text-dark-400">OS</span>
                                <span className="text-white text-sm">
                                    {selectedHost.os_type} {selectedHost.os_version}
                                </span>
                            </div>
                        )}
                        <div className="flex justify-between items-center p-3 bg-dark-800/50 rounded-lg">
                            <span className="text-dark-400">Last Connected</span>
                            <span className="text-white text-sm">
                                {selectedHost.last_connected
                                    ? new Date(selectedHost.last_connected).toLocaleString()
                                    : 'Never'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
