import { useState, useEffect } from 'react'
import { Server, ChevronDown, Plus, Check, Wifi, WifiOff } from 'lucide-react'
import { useHostStore } from '../../store/hostStore'
import { hostsApi } from '../../services/api'

function HostSelector() {
    const { hosts, selectedHostId, selectHost, loading } = useHostStore()
    const [isOpen, setIsOpen] = useState(false)
    const [hostStatuses, setHostStatuses] = useState({})

    const selectedHost = hosts.find((h) => h.id === selectedHostId)

    // Check host status on load
    useEffect(() => {
        hosts.forEach(async (host) => {
            try {
                const response = await hostsApi.getStatus(host.id)
                setHostStatuses((prev) => ({
                    ...prev,
                    [host.id]: response.data.connected,
                }))
            } catch {
                setHostStatuses((prev) => ({
                    ...prev,
                    [host.id]: false,
                }))
            }
        })
    }, [hosts])

    if (loading) {
        return (
            <div className="animate-pulse">
                <div className="h-10 bg-dark-800 rounded-lg"></div>
            </div>
        )
    }

    if (hosts.length === 0) {
        return (
            <a
                href="/hosts"
                className="flex items-center gap-2 px-3 py-2 text-sm text-dark-400 hover:text-white bg-dark-800 rounded-lg border border-dashed border-dark-600 hover:border-primary-500 transition-all duration-200"
            >
                <Plus className="w-4 h-4" />
                <span>Add your first host</span>
            </a>
        )
    }

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between gap-2 px-3 py-2.5 bg-dark-800 hover:bg-dark-700 rounded-lg border border-dark-700 transition-all duration-200"
            >
                <div className="flex items-center gap-2 min-w-0">
                    <Server className="w-4 h-4 text-dark-400 flex-shrink-0" />
                    <span className="text-sm font-medium text-white truncate">
                        {selectedHost?.name || 'Select host'}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    {selectedHost && (
                        <span
                            className={`w-2 h-2 rounded-full ${hostStatuses[selectedHost.id]
                                    ? 'bg-emerald-500'
                                    : 'bg-slate-500'
                                }`}
                        />
                    )}
                    <ChevronDown
                        className={`w-4 h-4 text-dark-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''
                            }`}
                    />
                </div>
            </button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div
                        className="fixed inset-0 z-10"
                        onClick={() => setIsOpen(false)}
                    />

                    {/* Dropdown */}
                    <div className="absolute top-full left-0 right-0 mt-2 py-1 bg-dark-800 border border-dark-700 rounded-lg shadow-xl z-20 animate-fadeIn">
                        {hosts.map((host) => (
                            <button
                                key={host.id}
                                onClick={() => {
                                    selectHost(host.id)
                                    setIsOpen(false)
                                }}
                                className={`w-full flex items-center justify-between px-3 py-2 text-sm transition-colors ${host.id === selectedHostId
                                        ? 'bg-primary-600/20 text-primary-400'
                                        : 'text-dark-200 hover:bg-dark-700'
                                    }`}
                            >
                                <div className="flex items-center gap-2">
                                    <Server className="w-4 h-4" />
                                    <span>{host.name}</span>
                                    <span className="text-xs text-dark-500">({host.hostname})</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    {hostStatuses[host.id] ? (
                                        <Wifi className="w-3.5 h-3.5 text-emerald-500" />
                                    ) : (
                                        <WifiOff className="w-3.5 h-3.5 text-slate-500" />
                                    )}
                                    {host.id === selectedHostId && (
                                        <Check className="w-4 h-4 text-primary-400" />
                                    )}
                                </div>
                            </button>
                        ))}

                        <div className="border-t border-dark-700 mt-1 pt-1">
                            <a
                                href="/hosts"
                                className="flex items-center gap-2 px-3 py-2 text-sm text-dark-400 hover:text-white hover:bg-dark-700 transition-colors"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Manage hosts</span>
                            </a>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default HostSelector
