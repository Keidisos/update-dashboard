import { useState } from 'react'
import { X, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'

function UpdateModal({ container, onConfirm, onCancel, isUpdating, result }) {
    if (result) {
        return (
            <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                <div className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-lg shadow-2xl animate-fadeIn">
                    <div className="p-6">
                        <div className="flex items-center gap-3 mb-4">
                            {result.success ? (
                                <div className="w-12 h-12 bg-emerald-500/20 rounded-full flex items-center justify-center">
                                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                                </div>
                            ) : (
                                <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center">
                                    <AlertTriangle className="w-6 h-6 text-red-500" />
                                </div>
                            )}
                            <div>
                                <h3 className="text-lg font-semibold text-white">
                                    {result.success ? 'Update Successful' : 'Update Failed'}
                                </h3>
                                <p className="text-sm text-dark-400">
                                    {container.name}
                                </p>
                            </div>
                        </div>

                        {/* Logs */}
                        {result.logs && result.logs.length > 0 && (
                            <div className="bg-dark-950 rounded-lg p-4 max-h-64 overflow-auto font-mono text-xs">
                                {result.logs.map((log, idx) => (
                                    <div
                                        key={idx}
                                        className={`${log.startsWith('ERROR')
                                                ? 'text-red-400'
                                                : log.startsWith('[')
                                                    ? 'text-primary-400'
                                                    : 'text-dark-300'
                                            }`}
                                    >
                                        {log}
                                    </div>
                                ))}
                            </div>
                        )}

                        {result.error && (
                            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400">
                                {result.error}
                            </div>
                        )}
                    </div>

                    <div className="px-6 py-4 border-t border-dark-700 flex justify-end">
                        <button onClick={onCancel} className="btn btn-secondary">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-lg shadow-2xl animate-fadeIn">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-dark-700">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
                            <AlertTriangle className="w-5 h-5 text-amber-500" />
                        </div>
                        <div>
                            <h3 className="text-lg font-semibold text-white">Confirm Update</h3>
                            <p className="text-sm text-dark-400">This action cannot be undone</p>
                        </div>
                    </div>
                    <button
                        onClick={onCancel}
                        disabled={isUpdating}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-dark-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    <p className="text-dark-200 mb-4">
                        Are you sure you want to update <strong className="text-white">{container.name}</strong>?
                    </p>

                    <div className="bg-dark-800 rounded-lg p-4 space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-dark-400">Container</span>
                            <span className="text-white font-medium">{container.name}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-dark-400">Current Image</span>
                            <span className="text-dark-200 font-mono text-xs">{container.image}</span>
                        </div>
                        {container.local_digest && container.remote_digest && (
                            <>
                                <div className="flex justify-between">
                                    <span className="text-dark-400">Current Digest</span>
                                    <span className="text-dark-200 font-mono text-xs">
                                        {container.local_digest.substring(0, 16)}...
                                    </span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-dark-400">New Digest</span>
                                    <span className="text-emerald-400 font-mono text-xs">
                                        {container.remote_digest.substring(0, 16)}...
                                    </span>
                                </div>
                            </>
                        )}
                    </div>

                    <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-sm text-amber-200">
                        <strong>Note:</strong> The container will be stopped, recreated with the new image,
                        and restarted. All configuration (ports, volumes, environment, networks) will be preserved.
                    </div>
                </div>

                {/* Actions */}
                <div className="px-6 py-4 border-t border-dark-700 flex justify-end gap-3">
                    <button
                        onClick={onCancel}
                        disabled={isUpdating}
                        className="btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={onConfirm}
                        disabled={isUpdating}
                        className="btn btn-primary"
                    >
                        {isUpdating ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Updating...
                            </>
                        ) : (
                            'Confirm Update'
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default UpdateModal
