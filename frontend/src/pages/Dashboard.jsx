import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
    Container,
    Server,
    Monitor,
    ArrowUpCircle,
    RefreshCw,
    AlertCircle,
    CheckCircle2,
    Wifi,
    WifiOff,
    ChevronRight
} from 'lucide-react'
import { useHostStore } from '../store/hostStore'
import { containersApi, systemApi, hostsApi } from '../services/api'

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

function HostCard({ host, stats, loading, onRefresh }) {
    const isConnected = stats?.connected !== false
    const hasUpdates = (stats?.containerUpdates || 0) + (stats?.systemUpdates || 0) > 0

    return (
        <div className="card p-5 hover:border-dark-600 transition-colors">
            <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${isConnected ? 'bg-emerald-500/20' : 'bg-red-500/20'
                        }`}>
                        <Server className={`w-5 h-5 ${isConnected ? 'text-emerald-400' : 'text-red-400'}`} />
                    </div>
                    <div>
                        <h3 className="font-semibold text-white">{host.name}</h3>
                        <p className="text-xs text-dark-400">{host.hostname}</p>
                    </div>
                </div>
                <button
                    onClick={() => onRefresh(host.id)}
                    disabled={loading}
                    className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    title="Refresh"
                >
                    <RefreshCw className={`w-4 h-4 text-dark-400 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {loading ? (
                <div className="flex items-center justify-center py-6">
                    <RefreshCw className="w-5 h-5 text-dark-500 animate-spin" />
                </div>
            ) : !isConnected ? (
                <div className="flex items-center gap-2 text-red-400 text-sm py-4">
                    <WifiOff className="w-4 h-4" />
                    <span>Connection failed</span>
                </div>
            ) : (
                <div className="space-y-3">
                    {/* Stats Row */}
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-dark-800/50 rounded-lg py-2">
                            <p className="text-lg font-bold text-white">{stats?.totalContainers || 0}</p>
                            <p className="text-xs text-dark-400">Containers</p>
                        </div>
                        <div className="bg-dark-800/50 rounded-lg py-2">
                            <p className="text-lg font-bold text-emerald-400">{stats?.runningContainers || 0}</p>
                            <p className="text-xs text-dark-400">Running</p>
                        </div>
                        <div className={`rounded-lg py-2 ${hasUpdates ? 'bg-amber-500/20' : 'bg-dark-800/50'}`}>
                            <p className={`text-lg font-bold ${hasUpdates ? 'text-amber-400' : 'text-white'}`}>
                                {(stats?.containerUpdates || 0) + (stats?.systemUpdates || 0)}
                            </p>
                            <p className="text-xs text-dark-400">Updates</p>
                        </div>
                    </div>

                    {/* Quick Links */}
                    <div className="flex gap-2 pt-2">
                        <Link
                            to={`/containers/${host.id}`}
                            className="flex-1 flex items-center justify-center gap-1 text-xs text-primary-400 hover:text-primary-300 py-2 bg-dark-800/50 rounded-lg transition-colors"
                        >
                            <Container className="w-3 h-3" />
                            Containers
                            <ChevronRight className="w-3 h-3" />
                        </Link>
                        <Link
                            to={`/system/${host.id}`}
                            className="flex-1 flex items-center justify-center gap-1 text-xs text-primary-400 hover:text-primary-300 py-2 bg-dark-800/50 rounded-lg transition-colors"
                        >
                            <Monitor className="w-3 h-3" />
                            System
                            <ChevronRight className="w-3 h-3" />
                        </Link>
                    </div>
                </div>
            )}
        </div>
    )
}

function Dashboard() {
    const { hosts, fetchHosts } = useHostStore()
    const [hostStats, setHostStats] = useState({})
    const [loadingHosts, setLoadingHosts] = useState({})
    const [globalStats, setGlobalStats] = useState({
        totalHosts: 0,
        connectedHosts: 0,
        totalContainers: 0,
        runningContainers: 0,
        containerUpdates: 0,
        systemUpdates: 0,
    })

    // Fetch hosts on mount
    useEffect(() => {
        fetchHosts()
    }, [fetchHosts])

    // Fetch stats for all hosts
    useEffect(() => {
        if (hosts.length === 0) return

        const fetchAllStats = async () => {
            const newHostStats = {}
            let global = {
                totalHosts: hosts.length,
                connectedHosts: 0,
                totalContainers: 0,
                runningContainers: 0,
                containerUpdates: 0,
                systemUpdates: 0,
            }

            // Mark all as loading
            const loadingState = {}
            hosts.forEach(h => { loadingState[h.id] = true })
            setLoadingHosts(loadingState)

            // Fetch in parallel
            await Promise.all(hosts.map(async (host) => {
                try {
                    // Test connection first
                    const statusRes = await hostsApi.getStatus(host.id)
                    if (!statusRes.data.connected) {
                        newHostStats[host.id] = { connected: false }
                        return
                    }

                    // Fetch containers
                    const containersRes = await containersApi.list(host.id, { all: true, checkUpdates: true })
                    const containers = containersRes.data

                    const stats = {
                        connected: true,
                        totalContainers: containers.length,
                        runningContainers: containers.filter(c => c.state === 'running').length,
                        containerUpdates: containers.filter(c => c.update_available).length,
                        systemUpdates: 0,
                    }

                    // Fetch system updates
                    try {
                        const systemRes = await systemApi.checkUpdates(host.id)
                        stats.systemUpdates = systemRes.data.updates_available || 0
                    } catch (e) {
                        console.warn(`Could not fetch system updates for ${host.name}:`, e)
                    }

                    newHostStats[host.id] = stats

                    // Update global
                    global.connectedHosts++
                    global.totalContainers += stats.totalContainers
                    global.runningContainers += stats.runningContainers
                    global.containerUpdates += stats.containerUpdates
                    global.systemUpdates += stats.systemUpdates
                } catch (error) {
                    console.error(`Failed to fetch stats for ${host.name}:`, error)
                    newHostStats[host.id] = { connected: false, error: error.message }
                } finally {
                    setLoadingHosts(prev => ({ ...prev, [host.id]: false }))
                }
            }))

            setHostStats(newHostStats)
            setGlobalStats(global)
        }

        fetchAllStats()
    }, [hosts])

    // Refresh single host
    const refreshHost = async (hostId) => {
        setLoadingHosts(prev => ({ ...prev, [hostId]: true }))
        const host = hosts.find(h => h.id === hostId)
        if (!host) return

        try {
            const statusRes = await hostsApi.getStatus(hostId)
            if (!statusRes.data.connected) {
                setHostStats(prev => ({ ...prev, [hostId]: { connected: false } }))
                return
            }

            const containersRes = await containersApi.list(hostId, { all: true, checkUpdates: true })
            const containers = containersRes.data

            const stats = {
                connected: true,
                totalContainers: containers.length,
                runningContainers: containers.filter(c => c.state === 'running').length,
                containerUpdates: containers.filter(c => c.update_available).length,
                systemUpdates: 0,
            }

            try {
                const systemRes = await systemApi.checkUpdates(hostId)
                stats.systemUpdates = systemRes.data.updates_available || 0
            } catch (e) { /* ignore */ }

            setHostStats(prev => ({ ...prev, [hostId]: stats }))

            // Recalculate global stats
            setGlobalStats(prev => {
                const oldStats = hostStats[hostId] || {}
                return {
                    ...prev,
                    connectedHosts: prev.connectedHosts + (stats.connected && !oldStats.connected ? 1 : 0),
                    totalContainers: prev.totalContainers - (oldStats.totalContainers || 0) + stats.totalContainers,
                    runningContainers: prev.runningContainers - (oldStats.runningContainers || 0) + stats.runningContainers,
                    containerUpdates: prev.containerUpdates - (oldStats.containerUpdates || 0) + stats.containerUpdates,
                    systemUpdates: prev.systemUpdates - (oldStats.systemUpdates || 0) + stats.systemUpdates,
                }
            })
        } catch (error) {
            setHostStats(prev => ({ ...prev, [hostId]: { connected: false, error: error.message } }))
        } finally {
            setLoadingHosts(prev => ({ ...prev, [hostId]: false }))
        }
    }

    if (hosts.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-96">
                <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mb-4">
                    <Server className="w-10 h-10 text-dark-500" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">No hosts configured</h2>
                <p className="text-dark-400 mb-4">Add your first Docker host to get started</p>
                <a href="/hosts" className="btn btn-primary">
                    Manage Hosts
                </a>
            </div>
        )
    }

    const totalUpdates = globalStats.containerUpdates + globalStats.systemUpdates

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
                <p className="text-dark-400">
                    Overview of all your hosts ({globalStats.connectedHosts}/{globalStats.totalHosts} connected)
                </p>
            </div>

            {/* Global Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    icon={Server}
                    label="Hosts"
                    value={globalStats.totalHosts}
                    subvalue={`${globalStats.connectedHosts} connected`}
                    color="primary"
                />
                <StatCard
                    icon={Container}
                    label="Total Containers"
                    value={globalStats.totalContainers}
                    subvalue={`${globalStats.runningContainers} running`}
                    color="emerald"
                />
                <StatCard
                    icon={ArrowUpCircle}
                    label="Container Updates"
                    value={globalStats.containerUpdates}
                    subvalue="Available updates"
                    color={globalStats.containerUpdates > 0 ? 'amber' : 'primary'}
                />
                <StatCard
                    icon={Monitor}
                    label="System Updates"
                    value={globalStats.systemUpdates}
                    subvalue="Package updates"
                    color={globalStats.systemUpdates > 0 ? 'amber' : 'primary'}
                />
            </div>

            {/* Hosts Grid */}
            <div>
                <h2 className="text-xl font-semibold text-white mb-4">Hosts Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {hosts.map(host => (
                        <HostCard
                            key={host.id}
                            host={host}
                            stats={hostStats[host.id]}
                            loading={loadingHosts[host.id]}
                            onRefresh={refreshHost}
                        />
                    ))}
                </div>
            </div>

            {/* Updates Summary */}
            {totalUpdates > 0 && (
                <div className="card p-6 border-amber-500/30 bg-amber-500/5">
                    <div className="flex items-center gap-3 mb-4">
                        <AlertCircle className="w-6 h-6 text-amber-400" />
                        <h3 className="text-lg font-semibold text-white">
                            {totalUpdates} Update{totalUpdates > 1 ? 's' : ''} Available
                        </h3>
                    </div>
                    <p className="text-dark-400 text-sm mb-4">
                        {globalStats.containerUpdates > 0 && `${globalStats.containerUpdates} container update${globalStats.containerUpdates > 1 ? 's' : ''}`}
                        {globalStats.containerUpdates > 0 && globalStats.systemUpdates > 0 && ' and '}
                        {globalStats.systemUpdates > 0 && `${globalStats.systemUpdates} system package${globalStats.systemUpdates > 1 ? 's' : ''}`}
                        {' '}across your hosts.
                    </p>
                    <div className="flex gap-3">
                        <a href="/containers" className="btn btn-primary">
                            <Container className="w-4 h-4" />
                            View Containers
                        </a>
                        <a href="/system" className="btn btn-secondary">
                            <Monitor className="w-4 h-4" />
                            View System Updates
                        </a>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Dashboard
