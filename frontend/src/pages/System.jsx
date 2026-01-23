import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
    Monitor,
    RefreshCw,
    Package,
    ArrowUpCircle,
    CheckCircle,
    AlertCircle,
    Server,
    Terminal
} from 'lucide-react'
import { useHostStore } from '../store/hostStore'
import { systemApi } from '../services/api'

function System() {
    const { hostId } = useParams()
    const [searchParams] = useSearchParams()
    const { hosts, selectedHostId, selectHost, getSelectedHost } = useHostStore()
    const [systemStatus, setSystemStatus] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [updating, setUpdating] = useState(false)
    const [updateResult, setUpdateResult] = useState(null)

    // Handle host from URL path parameter
    useEffect(() => {
        if (hostId && hosts.length > 0) {
            const hostIdNum = parseInt(hostId)
            if (hostIdNum && hostIdNum !== selectedHostId) {
                selectHost(hostIdNum)
            }
        }
    }, [hostId, hosts, selectedHostId, selectHost])

    // Handle host from URL query param (fallback)
    const urlHostId = searchParams.get('host')
    useEffect(() => {
        if (urlHostId && hosts.length > 0 && !hostId) {
            const hostIdNum = parseInt(urlHostId)
            if (hostIdNum && hostIdNum !== selectedHostId) {
                selectHost(hostIdNum)
            }
        }
    }, [urlHostId, hosts, selectedHostId, selectHost, hostId])

    const currentHostId = hostId || selectedHostId
    const selectedHost = getSelectedHost()

    const checkUpdates = async () => {
        if (!currentHostId) return

        setLoading(true)
        setError(null)

        try {
            const response = await systemApi.checkUpdates(currentHostId)
            setSystemStatus(response.data)
        } catch (err) {
            setError(err.response?.data?.detail || err.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        checkUpdates()
    }, [currentHostId])

    const handleApplyUpdates = async () => {
        setUpdating(true)
        setUpdateResult(null)

        try {
            const response = await systemApi.applyUpdates(currentHostId)
            setUpdateResult(response.data)
            // Refresh status
            await checkUpdates()
        } catch (err) {
            setUpdateResult({
                success: false,
                error: err.response?.data?.detail || err.message,
            })
        } finally {
            setUpdating(false)
        }
    }

    if (!currentHostId) {
        return (
            <div className="flex flex-col items-center justify-center h-96">
                <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mb-4">
                    <Server className="w-10 h-10 text-dark-500" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">No host selected</h2>
                <p className="text-dark-400">Select a host from the sidebar to manage system updates</p>
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">System Updates</h1>
                    <p className="text-dark-400">
                        {selectedHost?.name && (
                            <span>
                                Managing updates on{' '}
                                <span className="text-primary-400 font-medium">{selectedHost.name}</span>
                            </span>
                        )}
                    </p>
                </div>
                <button
                    onClick={checkUpdates}
                    disabled={loading}
                    className="btn btn-secondary"
                >
                    {loading ? (
                        <>
                            <RefreshCw className="w-5 h-5 animate-spin" />
                            Checking...
                        </>
                    ) : (
                        <>
                            <RefreshCw className="w-5 h-5" />
                            Refresh
                        </>
                    )}
                </button>
            </div>

            {/* Error state */}
            {error && (
                <div className="card p-4 bg-red-500/10 border-red-500/30">
                    <div className="flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400" />
                        <p className="text-red-400">{error}</p>
                    </div>
                </div>
            )}

            {/* Loading state */}
            {loading && !systemStatus && (
                <div className="flex items-center justify-center py-20">
                    <RefreshCw className="w-8 h-8 text-primary-500 animate-spin" />
                </div>
            )}

            {/* System info */}
            {systemStatus && (
                <>
                    {/* OS Info Card */}
                    <div className="card p-6">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center">
                                <Monitor className="w-6 h-6 text-primary-400" />
                            </div>
                            <div>
                                <h3 className="text-lg font-semibold text-white">Operating System</h3>
                                <p className="text-dark-400">
                                    {systemStatus.os_type} {systemStatus.os_version}
                                </p>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-dark-800/50 rounded-lg p-4">
                                <p className="text-dark-400 text-sm">Distribution</p>
                                <p className="text-white font-medium capitalize">{systemStatus.os_type}</p>
                            </div>
                            <div className="bg-dark-800/50 rounded-lg p-4">
                                <p className="text-dark-400 text-sm">Version</p>
                                <p className="text-white font-medium">{systemStatus.os_version}</p>
                            </div>
                            <div className="bg-dark-800/50 rounded-lg p-4">
                                <p className="text-dark-400 text-sm">Updates Available</p>
                                <p className={`font-medium ${systemStatus.updates_available > 0 ? 'text-amber-400' : 'text-emerald-400'
                                    }`}>
                                    {systemStatus.updates_available}
                                </p>
                            </div>
                            <div className="bg-dark-800/50 rounded-lg p-4">
                                <p className="text-dark-400 text-sm">Last Checked</p>
                                <p className="text-white font-medium">
                                    {new Date(systemStatus.last_checked).toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Update Result */}
                    {updateResult && (
                        <div className={`card p-6 ${updateResult.success
                            ? 'bg-emerald-500/10 border-emerald-500/30'
                            : 'bg-red-500/10 border-red-500/30'
                            }`}>
                            <div className="flex items-center gap-3 mb-4">
                                {updateResult.success ? (
                                    <>
                                        <CheckCircle className="w-6 h-6 text-emerald-400" />
                                        <h3 className="text-lg font-semibold text-emerald-400">Update Successful</h3>
                                    </>
                                ) : (
                                    <>
                                        <AlertCircle className="w-6 h-6 text-red-400" />
                                        <h3 className="text-lg font-semibold text-red-400">Update Failed</h3>
                                    </>
                                )}
                            </div>

                            {updateResult.logs && (
                                <div className="bg-dark-950 rounded-lg p-4 font-mono text-xs max-h-48 overflow-auto">
                                    <pre className="text-dark-300 whitespace-pre-wrap">{updateResult.logs}</pre>
                                </div>
                            )}

                            {updateResult.error && (
                                <p className="text-red-400 mt-2">{updateResult.error}</p>
                            )}
                        </div>
                    )}

                    {/* Packages list */}
                    {systemStatus.updates_available > 0 ? (
                        <div className="card">
                            <div className="p-4 border-b border-dark-700/50 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                    <Package className="w-5 h-5 text-amber-400" />
                                    <h3 className="font-semibold text-white">
                                        {systemStatus.updates_available} Package(s) to Update
                                    </h3>
                                </div>
                                <button
                                    onClick={handleApplyUpdates}
                                    disabled={updating}
                                    className="btn btn-primary"
                                >
                                    {updating ? (
                                        <>
                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                            Updating...
                                        </>
                                    ) : (
                                        <>
                                            <ArrowUpCircle className="w-4 h-4" />
                                            Update All
                                        </>
                                    )}
                                </button>
                            </div>
                            <div className="p-4">
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-dark-400 text-left">
                                                <th className="pb-3 font-medium">Package</th>
                                                <th className="pb-3 font-medium">Current</th>
                                                <th className="pb-3 font-medium">New</th>
                                                <th className="pb-3 font-medium">Repository</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-dark-700/50">
                                            {systemStatus.packages.map((pkg, idx) => (
                                                <tr key={idx} className="text-dark-200">
                                                    <td className="py-3 font-medium text-white">{pkg.name}</td>
                                                    <td className="py-3 font-mono text-xs">{pkg.current_version}</td>
                                                    <td className="py-3 font-mono text-xs text-emerald-400">
                                                        {pkg.new_version}
                                                    </td>
                                                    <td className="py-3 text-dark-400">{pkg.repository || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="card p-12 text-center">
                            <div className="w-20 h-20 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <CheckCircle className="w-10 h-10 text-emerald-500" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">System is up to date</h3>
                            <p className="text-dark-400">All packages are at their latest versions</p>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default System
