import { useState, useEffect } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import {
    Container as ContainerIcon,
    RefreshCw,
    Search,
    Filter,
    ArrowUpCircle,
    Server
} from 'lucide-react'
import { useHostStore } from '../store/hostStore'
import { containersApi } from '../services/api'
import ContainerCard from '../components/Containers/ContainerCard'
import UpdateModal from '../components/Containers/UpdateModal'

function Containers() {
    const { hostId } = useParams()
    const [searchParams] = useSearchParams()
    const { hosts, selectedHostId, selectHost, getSelectedHost } = useHostStore()
    const [containers, setContainers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [searchQuery, setSearchQuery] = useState('')
    const [filterState, setFilterState] = useState('all')
    const [showUpdatesOnly, setShowUpdatesOnly] = useState(false)
    const [checkingUpdates, setCheckingUpdates] = useState(false)

    // Update modal state
    const [selectedContainer, setSelectedContainer] = useState(null)
    const [isUpdating, setIsUpdating] = useState(false)
    const [updateResult, setUpdateResult] = useState(null)

    // Handle host from URL query param
    const urlHostId = searchParams.get('host')
    useEffect(() => {
        if (urlHostId && hosts.length > 0) {
            const hostIdNum = parseInt(urlHostId)
            if (hostIdNum && hostIdNum !== selectedHostId) {
                selectHost(hostIdNum)
            }
        }
    }, [urlHostId, hosts, selectedHostId, selectHost])

    const currentHostId = hostId || selectedHostId
    const selectedHost = getSelectedHost()

    const fetchContainers = async (checkUpdates = false) => {
        if (!currentHostId) return

        setLoading(true)
        setError(null)

        try {
            const response = await containersApi.list(currentHostId, {
                all: true,
                checkUpdates,
            })
            setContainers(response.data)
        } catch (err) {
            setError(err.response?.data?.detail || err.message)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchContainers(true)
    }, [currentHostId])

    const handleCheckUpdates = async () => {
        setCheckingUpdates(true)
        await fetchContainers(true)
        setCheckingUpdates(false)
    }

    const handleUpdate = (container) => {
        setSelectedContainer(container)
        setUpdateResult(null)
    }

    const handleConfirmUpdate = async () => {
        if (!selectedContainer) return

        setIsUpdating(true)
        try {
            const response = await containersApi.update(currentHostId, selectedContainer.id)
            setUpdateResult(response.data)
            // Refresh containers list
            await fetchContainers(true)
        } catch (err) {
            setUpdateResult({
                success: false,
                error: err.response?.data?.detail || err.message,
                logs: [],
            })
        } finally {
            setIsUpdating(false)
        }
    }

    const handleCloseModal = () => {
        setSelectedContainer(null)
        setUpdateResult(null)
    }

    // Filter containers
    const filteredContainers = containers.filter((c) => {
        if (searchQuery && !c.name.toLowerCase().includes(searchQuery.toLowerCase())) {
            return false
        }
        if (filterState !== 'all' && c.state !== filterState) {
            return false
        }
        if (showUpdatesOnly && !c.update_available) {
            return false
        }
        return true
    })

    const updatesCount = containers.filter((c) => c.update_available).length

    if (!currentHostId) {
        return (
            <div className="flex flex-col items-center justify-center h-96">
                <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mb-4">
                    <Server className="w-10 h-10 text-dark-500" />
                </div>
                <h2 className="text-xl font-semibold text-white mb-2">No host selected</h2>
                <p className="text-dark-400">Select a host from the sidebar to view containers</p>
            </div>
        )
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Containers</h1>
                    <p className="text-dark-400">
                        {selectedHost?.name && (
                            <span>
                                Managing containers on{' '}
                                <span className="text-primary-400 font-medium">{selectedHost.name}</span>
                            </span>
                        )}
                    </p>
                </div>
                <button
                    onClick={handleCheckUpdates}
                    disabled={checkingUpdates}
                    className="btn btn-secondary"
                >
                    {checkingUpdates ? (
                        <>
                            <RefreshCw className="w-5 h-5 animate-spin" />
                            Checking...
                        </>
                    ) : (
                        <>
                            <RefreshCw className="w-5 h-5" />
                            Check Updates
                        </>
                    )}
                </button>
            </div>

            {/* Filters */}
            <div className="flex flex-wrap items-center gap-4">
                {/* Search */}
                <div className="relative flex-1 min-w-[200px] max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search containers..."
                        className="input pl-10"
                    />
                </div>

                {/* State filter */}
                <select
                    value={filterState}
                    onChange={(e) => setFilterState(e.target.value)}
                    className="input w-auto"
                >
                    <option value="all">All States</option>
                    <option value="running">Running</option>
                    <option value="exited">Stopped</option>
                    <option value="paused">Paused</option>
                </select>

                {/* Updates filter */}
                <button
                    onClick={() => setShowUpdatesOnly(!showUpdatesOnly)}
                    className={`btn ${showUpdatesOnly ? 'btn-primary' : 'btn-secondary'}`}
                >
                    <ArrowUpCircle className="w-5 h-5" />
                    Updates ({updatesCount})
                </button>
            </div>

            {/* Error state */}
            {error && (
                <div className="card p-4 bg-red-500/10 border-red-500/30">
                    <p className="text-red-400">{error}</p>
                </div>
            )}

            {/* Loading state */}
            {loading && containers.length === 0 && (
                <div className="flex items-center justify-center py-20">
                    <RefreshCw className="w-8 h-8 text-primary-500 animate-spin" />
                </div>
            )}

            {/* Empty state */}
            {!loading && containers.length === 0 && (
                <div className="card p-12 text-center">
                    <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mx-auto mb-4">
                        <ContainerIcon className="w-10 h-10 text-dark-500" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">No containers found</h3>
                    <p className="text-dark-400">This host doesn't have any containers yet</p>
                </div>
            )}

            {/* No results */}
            {!loading && containers.length > 0 && filteredContainers.length === 0 && (
                <div className="card p-8 text-center">
                    <p className="text-dark-400">No containers match your filters</p>
                </div>
            )}

            {/* Containers grid */}
            {filteredContainers.length > 0 && (
                <div className="grid gap-4">
                    {filteredContainers.map((container) => (
                        <ContainerCard
                            key={container.id}
                            container={container}
                            onUpdate={() => handleUpdate(container)}
                            isUpdating={isUpdating && selectedContainer?.id === container.id}
                        />
                    ))}
                </div>
            )}

            {/* Update modal */}
            {selectedContainer && (
                <UpdateModal
                    container={selectedContainer}
                    onConfirm={handleConfirmUpdate}
                    onCancel={handleCloseModal}
                    isUpdating={isUpdating}
                    result={updateResult}
                />
            )}
        </div>
    )
}

export default Containers
