import { useState, useEffect } from 'react'
import {
    Server,
    Plus,
    Trash2,
    Edit2,
    Wifi,
    WifiOff,
    RefreshCw,
    X,
    Check,
    Key,
    Lock
} from 'lucide-react'
import { useHostStore } from '../store/hostStore'
import { hostsApi } from '../services/api'

function HostForm({ host, onSave, onCancel }) {
    const [formData, setFormData] = useState({
        name: host?.name || '',
        hostname: host?.hostname || '',
        connection_type: host?.connection_type || 'ssh',
        ssh_port: host?.ssh_port || 22,
        ssh_user: host?.ssh_user || 'update-manager',
        ssh_key: '',
        ssh_password: '',
        docker_port: host?.docker_port || 2376,
        docker_tls: host?.docker_tls ?? true,
    })
    const [saving, setSaving] = useState(false)
    const [error, setError] = useState(null)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setSaving(true)
        setError(null)

        try {
            await onSave(formData)
        } catch (err) {
            setError(err.response?.data?.detail || err.message)
        } finally {
            setSaving(false)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="input-label">Name</label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input"
                        placeholder="My Server"
                        required
                    />
                </div>
                <div>
                    <label className="input-label">Hostname / IP</label>
                    <input
                        type="text"
                        value={formData.hostname}
                        onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
                        className="input"
                        placeholder="192.168.1.100"
                        required
                    />
                </div>
            </div>

            <div>
                <label className="input-label">Connection Type</label>
                <div className="flex gap-4">
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="connection_type"
                            value="ssh"
                            checked={formData.connection_type === 'ssh'}
                            onChange={(e) => setFormData({ ...formData, connection_type: e.target.value })}
                            className="text-primary-500"
                        />
                        <span className="text-sm text-dark-200">SSH Tunnel</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                        <input
                            type="radio"
                            name="connection_type"
                            value="tcp"
                            checked={formData.connection_type === 'tcp'}
                            onChange={(e) => setFormData({ ...formData, connection_type: e.target.value })}
                            className="text-primary-500"
                        />
                        <span className="text-sm text-dark-200">Docker TCP</span>
                    </label>
                </div>
            </div>

            {formData.connection_type === 'ssh' && (
                <>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="input-label">SSH Port</label>
                            <input
                                type="number"
                                value={formData.ssh_port}
                                onChange={(e) => setFormData({ ...formData, ssh_port: parseInt(e.target.value) })}
                                className="input"
                                min="1"
                                max="65535"
                            />
                        </div>
                        <div>
                            <label className="input-label">SSH User</label>
                            <input
                                type="text"
                                value={formData.ssh_user}
                                onChange={(e) => setFormData({ ...formData, ssh_user: e.target.value })}
                                className="input"
                                placeholder="root"
                            />
                        </div>
                    </div>

                    <div>
                        <label className="input-label flex items-center gap-2">
                            <Key className="w-4 h-4" />
                            SSH Private Key
                        </label>
                        <textarea
                            value={formData.ssh_key}
                            onChange={(e) => setFormData({ ...formData, ssh_key: e.target.value })}
                            className="input font-mono text-xs h-32"
                            placeholder="-----BEGIN OPENSSH PRIVATE KEY-----..."
                        />
                    </div>

                    <div>
                        <label className="input-label flex items-center gap-2">
                            <Lock className="w-4 h-4" />
                            SSH Password (alternative)
                        </label>
                        <input
                            type="password"
                            value={formData.ssh_password}
                            onChange={(e) => setFormData({ ...formData, ssh_password: e.target.value })}
                            className="input"
                            placeholder="Leave empty if using key"
                        />
                    </div>
                </>
            )}

            {formData.connection_type === 'tcp' && (
                <>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="input-label">Docker Port</label>
                            <input
                                type="number"
                                value={formData.docker_port}
                                onChange={(e) => setFormData({ ...formData, docker_port: parseInt(e.target.value) })}
                                className="input"
                                min="1"
                                max="65535"
                            />
                        </div>
                        <div className="flex items-end pb-2">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={formData.docker_tls}
                                    onChange={(e) => setFormData({ ...formData, docker_tls: e.target.checked })}
                                    className="w-4 h-4 text-primary-500 rounded"
                                />
                                <span className="text-sm text-dark-200">Use TLS</span>
                            </label>
                        </div>
                    </div>
                </>
            )}

            <div className="flex justify-end gap-3 pt-4">
                <button type="button" onClick={onCancel} className="btn btn-secondary">
                    Cancel
                </button>
                <button type="submit" disabled={saving} className="btn btn-primary">
                    {saving ? (
                        <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Saving...
                        </>
                    ) : (
                        <>
                            <Check className="w-4 h-4" />
                            {host ? 'Update' : 'Create'}
                        </>
                    )}
                </button>
            </div>
        </form>
    )
}

function Hosts() {
    const { hosts, fetchHosts, addHost, updateHost, deleteHost } = useHostStore()
    const [showForm, setShowForm] = useState(false)
    const [editingHost, setEditingHost] = useState(null)
    const [hostStatuses, setHostStatuses] = useState({})
    const [testingHost, setTestingHost] = useState(null)

    useEffect(() => {
        fetchHosts()
    }, [fetchHosts])

    const testConnection = async (hostId) => {
        setTestingHost(hostId)
        try {
            const response = await hostsApi.getStatus(hostId)
            setHostStatuses((prev) => ({
                ...prev,
                [hostId]: response.data,
            }))
        } catch (error) {
            setHostStatuses((prev) => ({
                ...prev,
                [hostId]: { connected: false, error: error.message },
            }))
        } finally {
            setTestingHost(null)
        }
    }

    const handleSave = async (data) => {
        if (editingHost) {
            await updateHost(editingHost.id, data)
        } else {
            await addHost(data)
        }
        setShowForm(false)
        setEditingHost(null)
    }

    const handleDelete = async (hostId) => {
        if (confirm('Are you sure you want to delete this host?')) {
            await deleteHost(hostId)
        }
    }

    return (
        <div className="space-y-6 animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Hosts</h1>
                    <p className="text-dark-400">Manage your remote Docker hosts</p>
                </div>
                <button
                    onClick={() => {
                        setEditingHost(null)
                        setShowForm(true)
                    }}
                    className="btn btn-primary"
                >
                    <Plus className="w-5 h-5" />
                    Add Host
                </button>
            </div>

            {/* Form Modal */}
            {showForm && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-lg shadow-2xl">
                        <div className="flex items-center justify-between p-6 border-b border-dark-700">
                            <h3 className="text-lg font-semibold text-white">
                                {editingHost ? 'Edit Host' : 'Add New Host'}
                            </h3>
                            <button
                                onClick={() => {
                                    setShowForm(false)
                                    setEditingHost(null)
                                }}
                                className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-dark-400" />
                            </button>
                        </div>
                        <div className="p-6">
                            <HostForm
                                host={editingHost}
                                onSave={handleSave}
                                onCancel={() => {
                                    setShowForm(false)
                                    setEditingHost(null)
                                }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Hosts List */}
            {hosts.length === 0 ? (
                <div className="card p-12 text-center">
                    <div className="w-20 h-20 bg-dark-800 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Server className="w-10 h-10 text-dark-500" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-2">No hosts configured</h3>
                    <p className="text-dark-400 mb-6">Add your first Docker host to get started</p>
                    <button
                        onClick={() => setShowForm(true)}
                        className="btn btn-primary mx-auto"
                    >
                        <Plus className="w-5 h-5" />
                        Add Host
                    </button>
                </div>
            ) : (
                <div className="grid gap-4">
                    {hosts.map((host) => {
                        const status = hostStatuses[host.id]

                        return (
                            <div key={host.id} className="card p-6">
                                <div className="flex items-start justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="w-12 h-12 bg-dark-800 rounded-xl flex items-center justify-center">
                                            <Server className="w-6 h-6 text-primary-400" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-semibold text-white">{host.name}</h3>
                                            <p className="text-sm text-dark-400">{host.hostname}</p>
                                            <div className="flex items-center gap-3 mt-2">
                                                <span className="text-xs text-dark-500 uppercase">
                                                    {host.connection_type}
                                                </span>
                                                {host.os_type && (
                                                    <span className="text-xs text-dark-500">
                                                        {host.os_type} {host.os_version}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        {/* Status */}
                                        {status && (
                                            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm ${!status.connected
                                                    ? 'bg-red-500/20 text-red-400'
                                                    : status.error && status.error.includes('Docker')
                                                        ? 'bg-orange-500/20 text-orange-400'
                                                        : 'bg-emerald-500/20 text-emerald-400'
                                                }`}>
                                                {!status.connected ? (
                                                    <>
                                                        <WifiOff className="w-4 h-4" />
                                                        Disconnected
                                                    </>
                                                ) : status.error && status.error.includes('Docker') ? (
                                                    <>
                                                        <Wifi className="w-4 h-4" />
                                                        SSH Only
                                                    </>
                                                ) : (
                                                    <>
                                                        <Wifi className="w-4 h-4" />
                                                        Connected
                                                    </>
                                                )}
                                            </div>
                                        )}

                                        {/* Actions */}
                                        <button
                                            onClick={() => testConnection(host.id)}
                                            disabled={testingHost === host.id}
                                            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                                            title="Test Connection"
                                        >
                                            <RefreshCw className={`w-5 h-5 text-dark-400 ${testingHost === host.id ? 'animate-spin' : ''
                                                }`} />
                                        </button>
                                        <button
                                            onClick={() => {
                                                setEditingHost(host)
                                                setShowForm(true)
                                            }}
                                            className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                                            title="Edit"
                                        >
                                            <Edit2 className="w-5 h-5 text-dark-400" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(host.id)}
                                            className="p-2 hover:bg-red-500/20 rounded-lg transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 className="w-5 h-5 text-red-400" />
                                        </button>
                                    </div>
                                </div>

                                {/* Status details */}
                                {status && (
                                    <div className="mt-4 pt-4 border-t border-dark-700/50">
                                        {status.connected ? (
                                            <div className="flex items-center gap-6 text-sm text-dark-400">
                                                {status.docker_version ? (
                                                    <span>Docker {status.docker_version}</span>
                                                ) : (
                                                    <span className="text-orange-400/80 text-xs border border-orange-500/20 px-2 py-0.5 rounded">Docker unavailable</span>
                                                )}
                                                <span>{status.os_info}</span>
                                            </div>
                                        ) : status.error && (
                                            <p className="text-sm text-red-400">{status.error}</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export default Hosts
