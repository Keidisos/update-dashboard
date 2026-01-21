import { useState } from 'react'
import {
    Play,
    Square,
    RefreshCw,
    ArrowUpCircle,
    ChevronDown,
    ChevronUp,
    Box,
    HardDrive,
    Network,
    Clock
} from 'lucide-react'
import clsx from 'clsx'

function ContainerCard({ container, onUpdate, isUpdating }) {
    const [isExpanded, setIsExpanded] = useState(false)

    const stateColors = {
        running: 'bg-emerald-500',
        exited: 'bg-slate-500',
        paused: 'bg-amber-500',
        restarting: 'bg-blue-500',
        dead: 'bg-red-500',
        created: 'bg-purple-500',
    }

    const stateLabels = {
        running: 'Running',
        exited: 'Stopped',
        paused: 'Paused',
        restarting: 'Restarting',
        dead: 'Dead',
        created: 'Created',
    }

    return (
        <div className="card card-hover overflow-hidden animate-fadeIn">
            {/* Header */}
            <div className="p-4">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center gap-3 min-w-0">
                        <div className="w-10 h-10 bg-dark-800 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Box className="w-5 h-5 text-primary-400" />
                        </div>
                        <div className="min-w-0">
                            <h3 className="font-semibold text-white truncate">
                                {container.name}
                            </h3>
                            <p className="text-sm text-dark-400 truncate">
                                {container.image}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                        {/* Update badge */}
                        {container.update_available && (
                            <span className="badge badge-update flex items-center gap-1">
                                <ArrowUpCircle className="w-3 h-3" />
                                Update
                            </span>
                        )}

                        {/* Status badge */}
                        <span className={clsx('badge', {
                            'badge-running': container.state === 'running',
                            'badge-stopped': container.state !== 'running',
                        })}>
                            <span className={clsx('w-1.5 h-1.5 rounded-full mr-1.5', stateColors[container.state])} />
                            {stateLabels[container.state] || container.state}
                        </span>
                    </div>
                </div>

                {/* Quick stats */}
                <div className="flex items-center gap-4 mt-4 text-sm text-dark-400">
                    {container.ports.length > 0 && (
                        <div className="flex items-center gap-1.5">
                            <Network className="w-4 h-4" />
                            <span>
                                {container.ports.map(p =>
                                    p.host_port ? `${p.host_port}:${p.container_port}` : p.container_port
                                ).join(', ')}
                            </span>
                        </div>
                    )}
                    {container.volumes.length > 0 && (
                        <div className="flex items-center gap-1.5">
                            <HardDrive className="w-4 h-4" />
                            <span>{container.volumes.length} volume(s)</span>
                        </div>
                    )}
                    <div className="flex items-center gap-1.5">
                        <Clock className="w-4 h-4" />
                        <span>{container.status}</span>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="px-4 py-3 bg-dark-800/30 border-t border-dark-700/50 flex items-center justify-between">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex items-center gap-1.5 text-sm text-dark-400 hover:text-white transition-colors"
                >
                    {isExpanded ? (
                        <>
                            <ChevronUp className="w-4 h-4" />
                            Hide details
                        </>
                    ) : (
                        <>
                            <ChevronDown className="w-4 h-4" />
                            Show details
                        </>
                    )}
                </button>

                <div className="flex items-center gap-2">
                    {container.update_available && (
                        <button
                            onClick={() => onUpdate(container.id)}
                            disabled={isUpdating}
                            className="btn btn-primary text-sm py-1.5 px-3"
                        >
                            {isUpdating ? (
                                <>
                                    <RefreshCw className="w-4 h-4 animate-spin" />
                                    Updating...
                                </>
                            ) : (
                                <>
                                    <ArrowUpCircle className="w-4 h-4" />
                                    Update
                                </>
                            )}
                        </button>
                    )}
                </div>
            </div>

            {/* Expanded details */}
            {isExpanded && (
                <div className="px-4 py-4 border-t border-dark-700/50 space-y-4 animate-fadeIn">
                    {/* Image info */}
                    <div>
                        <h4 className="text-xs font-medium text-dark-500 uppercase tracking-wide mb-2">
                            Image
                        </h4>
                        <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                                <span className="text-dark-400">Image</span>
                                <span className="text-dark-200 font-mono">{container.image}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-dark-400">Image ID</span>
                                <span className="text-dark-200 font-mono text-xs">
                                    {container.image_id.substring(0, 20)}...
                                </span>
                            </div>
                            {container.local_digest && (
                                <div className="flex justify-between">
                                    <span className="text-dark-400">Local Digest</span>
                                    <span className="text-dark-200 font-mono text-xs">
                                        {container.local_digest.substring(0, 20)}...
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Environment variables */}
                    {Object.keys(container.environment).length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-dark-500 uppercase tracking-wide mb-2">
                                Environment ({Object.keys(container.environment).length})
                            </h4>
                            <div className="bg-dark-800 rounded-lg p-3 max-h-32 overflow-auto">
                                {Object.entries(container.environment).map(([key, value]) => (
                                    <div key={key} className="text-xs font-mono">
                                        <span className="text-primary-400">{key}</span>
                                        <span className="text-dark-500">=</span>
                                        <span className="text-dark-300">{value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Volumes */}
                    {container.volumes.length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-dark-500 uppercase tracking-wide mb-2">
                                Volumes ({container.volumes.length})
                            </h4>
                            <div className="space-y-1">
                                {container.volumes.map((vol, idx) => (
                                    <div key={idx} className="text-sm font-mono flex items-center gap-2">
                                        <span className="text-dark-300">{vol.source}</span>
                                        <span className="text-dark-600">→</span>
                                        <span className="text-primary-400">{vol.destination}</span>
                                        <span className="text-xs text-dark-500">({vol.mode})</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Networks */}
                    {container.networks.length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-dark-500 uppercase tracking-wide mb-2">
                                Networks
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {container.networks.map((net) => (
                                    <span key={net} className="px-2 py-1 bg-dark-800 rounded text-xs text-dark-300">
                                        {net}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Labels */}
                    {Object.keys(container.labels).length > 0 && (
                        <div>
                            <h4 className="text-xs font-medium text-dark-500 uppercase tracking-wide mb-2">
                                Labels ({Object.keys(container.labels).length})
                            </h4>
                            <div className="flex flex-wrap gap-1">
                                {Object.entries(container.labels).slice(0, 5).map(([key, value]) => (
                                    <span key={key} className="px-2 py-0.5 bg-dark-800 rounded text-xs">
                                        <span className="text-dark-400">{key}</span>
                                        {value && <span className="text-dark-500">={value.substring(0, 20)}</span>}
                                    </span>
                                ))}
                                {Object.keys(container.labels).length > 5 && (
                                    <span className="px-2 py-0.5 text-xs text-dark-500">
                                        +{Object.keys(container.labels).length - 5} more
                                    </span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default ContainerCard
