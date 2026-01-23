import { useState, useEffect } from 'react'
import {
    Shield,
    AlertTriangle,
    AlertOctagon,
    AlertCircle,
    Info,
    CheckCircle,
    Clock,
    Filter,
    RefreshCw,
    Server,
    Eye,
    X
} from 'lucide-react'
import { socApi } from '../services/api'

const SEVERITY_CONFIG = {
    critical: { color: 'red', icon: AlertOctagon, label: 'Critical' },
    high: { color: 'orange', icon: AlertTriangle, label: 'High' },
    medium: { color: 'yellow', icon: AlertCircle, label: 'Medium' },
    low: { color: 'blue', icon: Info, label: 'Low' }
}

const CATEGORY_LABELS = {
    brute_force: 'Brute Force',
    ssh_intrusion: 'SSH Intrusion',
    privilege_escalation: 'Privilege Escalation',
    unauthorized_access: 'Unauthorized Access',
    suspicious_command: 'Suspicious Command',
    malware_detection: 'Malware Detection',
    anomaly: 'Anomaly',
    other: 'Other'
}

function IncidentCard({ incident, onClick }) {
    const SeverityIcon = SEVERITY_CONFIG[incident.severity]?.icon || AlertCircle
    const severityColor = SEVERITY_CONFIG[incident.severity]?.color || 'gray'

    return (
        <div
            onClick={() => onClick(incident)}
            className="bg-gray-800/40 border border-gray-700 rounded-lg p-4 hover:border-purple-500/50 transition-all cursor-pointer group"
        >
            <div className="flex items-start gap-4">
                <div className={`p-2 bg-${severityColor}-500/10 rounded-lg group-hover:scale-110 transition-transform`}>
                    <SeverityIcon className={`w-6 h-6 text-${severityColor}-400`} />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="font-medium text-white">{incident.title}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full bg-${severityColor}-500/20 text-${severityColor}-300 whitespace-nowrap`}>
                            {SEVERITY_CONFIG[incident.severity]?.label}
                        </span>
                    </div>

                    <p className="text-sm text-gray-400 mb-3 line-clamp-2">{incident.description}</p>

                    <div className="flex items-center flex-wrap gap-4 text-xs text-gray-500">
                        <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(incident.detected_at).toLocaleString()}
                        </div>
                        {incident.event_count > 0 && (
                            <div className="flex items-center gap-1">
                                <span>{incident.event_count} events</span>
                            </div>
                        )}
                        <span className="px-2 py-0.5 bg-gray-700/50 rounded">
                            {CATEGORY_LABELS[incident.category]}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    )
}

function IncidentDetailsModal({ incident, onClose }) {
    if (!incident) return null

    const SeverityIcon = SEVERITY_CONFIG[incident.severity]?.icon || AlertCircle
    const severityColor = SEVERITY_CONFIG[incident.severity]?.color || 'gray'

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-3xl w-full max-h-[90vh] overflow-auto">
                <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-6 flex items-start justify-between">
                    <div className="flex items-start gap-4">
                        <div className={`p-3 bg-${severityColor}-500/10 rounded-lg`}>
                            <SeverityIcon className={`w-8 h-8 text-${severityColor}-400`} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white mb-1">{incident.title}</h2>
                            <span className={`inline-block px-3 py-1 text-sm rounded-full bg-${severityColor}-500/20 text-${severityColor}-300`}>
                                {SEVERITY_CONFIG[incident.severity]?.label}
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Description */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">Description</h3>
                        <p className="text-white">{incident.description}</p>
                    </div>

                    {/* Recommendations */}
                    {incident.ai_recommendations && (
                        <div>
                            <h3 className="text-sm font-medium text-gray-400 mb-2">🤖 AI Recommendations</h3>
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                <p className="text-blue-200">{incident.ai_recommendations}</p>
                            </div>
                        </div>
                    )}

                    {/* Technical Details */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Category</h3>
                            <span className="px-3 py-1 bg-gray-800 rounded-lg text-white">
                                {CATEGORY_LABELS[incident.category]}
                            </span>
                        </div>
                        <div>
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Event Count</h3>
                            <span className="text-white">{incident.event_count}</span>
                        </div>
                    </div>

                    {/* Source IPs */}
                    {incident.source_ips && incident.source_ips.length > 0 && (
                        <div>
                            <h3 className="text-sm font-medium text-gray-400 mb-2">Source IPs</h3>
                            <div className="flex flex-wrap gap-2">
                                {incident.source_ips.map(ip => (
                                    <span key={ip} className="px-3 py-1 bg-red-500/20 text-red-300 rounded-lg text-sm font-mono">
                                        {ip}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* MITRE ATT&CK */}
                    {incident.mitre_techniques && incident.mitre_techniques.length > 0 && (
                        <div>
                            <h3 className="text-sm font-medium text-gray-400 mb-2">MITRE ATT&CK Techniques</h3>
                            <div className="flex flex-wrap gap-2">
                                {incident.mitre_techniques.map(tech => (
                                    <a
                                        key={tech}
                                        href={`https://attack.mitre.org/techniques/${tech}/`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-lg text-sm font-mono hover:bg-purple-500/30 transition-colors"
                                    >
                                        {tech}
                                    </a>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Timeline */}
                    <div>
                        <h3 className="text-sm font-medium text-gray-400 mb-2">Timeline</h3>
                        <div className="flex items-center gap-2 text-gray-300">
                            <Clock className="w-4 h-4" />
                            <span>Detected: {new Date(incident.detected_at).toLocaleString()}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default function SOC() {
    const [incidents, setIncidents] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(true)
    const [selectedIncident, setSelectedIncident] = useState(null)
    const [filter, setFilter] = useState('all') // all, unresolved, critical

    const loadData = async () => {
        setLoading(true)
        try {
            const [incidentsData, statsData] = await Promise.all([
                socApi.getIncidents(),
                socApi.getStats()
            ])
            setIncidents(incidentsData)
            setStats(statsData)
        } catch (error) {
            console.error('Failed to load SOC data:', error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadData()
        const interval = setInterval(loadData, 60000) // Refresh every minute
        return () => clearInterval(interval)
    }, [])

    const filteredIncidents = incidents.filter(inc => {
        if (filter === 'unresolved') return !inc.resolved
        if (filter === 'critical') return inc.severity === 'critical'
        return true
    })

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Shield className="w-8 h-8 text-purple-400" />
                        Security Operations Center
                    </h1>
                    <p className="text-gray-400 mt-1">AI-powered threat detection and analysis</p>
                </div>
                <button
                    onClick={loadData}
                    disabled={loading}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                </button>
            </div>

            {/* Stats Cards */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gray-800/40 border border-gray-700 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Total Incidents</span>
                            <Shield className="w-5 h-5 text-gray-500" />
                        </div>
                        <div className="text-2xl font-bold text-white">{stats.total_incidents}</div>
                    </div>

                    <div className="bg-gray-800/40 border border-red-500/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Critical</span>
                            <AlertOctagon className="w-5 h-5 text-red-400" />
                        </div>
                        <div className="text-2xl font-bold text-red-400">{stats.critical_incidents}</div>
                    </div>

                    <div className="bg-gray-800/40 border border-yellow-500/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Unresolved</span>
                            <AlertTriangle className="w-5 h-5 text-yellow-400" />
                        </div>
                        <div className="text-2xl font-bold text-yellow-400">{stats.unresolved_incidents}</div>
                    </div>

                    <div className="bg-gray-800/40 border border-green-500/30 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-gray-400 text-sm">Resolved</span>
                            <CheckCircle className="w-5 h-5 text-green-400" />
                        </div>
                        <div className="text-2xl font-bold text-green-400">{stats.total_incidents - stats.unresolved_incidents}</div>
                    </div>
                </div>
            )}

            {/* Filters */}
            <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <button
                    onClick={() => setFilter('all')}
                    className={`px-3 py-1 rounded-lg transition-colors ${filter === 'all' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                    All
                </button>
                <button
                    onClick={() => setFilter('unresolved')}
                    className={`px-3 py-1 rounded-lg transition-colors ${filter === 'unresolved' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                    Unresolved
                </button>
                <button
                    onClick={() => setFilter('critical')}
                    className={`px-3 py-1 rounded-lg transition-colors ${filter === 'critical' ? 'bg-purple-600 text-white' : 'bg-gray-800 text-gray-400 hover:bg-gray-700'}`}
                >
                    Critical Only
                </button>
            </div>

            {/* Incidents List */}
            {loading ? (
                <div className="text-center py-12 text-gray-400">
                    <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2" />
                    Analyzing security events...
                </div>
            ) : filteredIncidents.length === 0 ? (
                <div className="text-center py-12">
                    <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
                    <p className="text-gray-400">No security incidents detected</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {filteredIncidents.map(incident => (
                        <IncidentCard
                            key={incident.id}
                            incident={incident}
                            onClick={setSelectedIncident}
                        />
                    ))}
                </div>
            )}

            {/* Details Modal */}
            {selectedIncident && (
                <IncidentDetailsModal
                    incident={selectedIncident}
                    onClose={() => setSelectedIncident(null)}
                />
            )}
        </div>
    )
}
