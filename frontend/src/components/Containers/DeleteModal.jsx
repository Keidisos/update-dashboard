import { useState } from 'react'
import { X, Trash2, AlertTriangle } from 'lucide-react'

function DeleteModal({ container, onConfirm, onCancel, isDeleting }) {
    const [removeImage, setRemoveImage] = useState(true)
    const [force, setForce] = useState(false)

    const handleConfirm = () => {
        onConfirm(removeImage, force)
    }

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-dark-900 border border-dark-700 rounded-2xl w-full max-w-md shadow-2xl">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-dark-700">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-red-500/20 rounded-lg flex items-center justify-center">
                            <Trash2 className="w-5 h-5 text-red-400" />
                        </div>
                        <h3 className="text-lg font-semibold text-white">Delete Container</h3>
                    </div>
                    <button
                        onClick={onCancel}
                        disabled={isDeleting}
                        className="p-2 hover:bg-dark-800 rounded-lg transition-colors"
                    >
                        <X className="w-5 h-5 text-dark-400" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {/* Warning */}
                    <div className="flex gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-red-200">
                            <p className="font-semibold mb-1">This action cannot be undone</p>
                            <p className="text-red-300/80">The container and optionally its image will be permanently deleted.</p>
                        </div>
                    </div>

                    {/* Container Info */}
                    <div className="space-y-2">
                        <div>
                            <span className="text-xs text-dark-500 uppercase tracking-wide">Container</span>
                            <p className="text-white font-medium">{container.name}</p>
                        </div>
                        <div>
                            <span className="text-xs text-dark-500 uppercase tracking-wide">Image</span>
                            <p className="text-dark-200 text-sm font-mono">{container.image}</p>
                        </div>
                        {container.state === 'running' && (
                            <div className="flex items-center gap-2 text-sm text-orange-400">
                                <AlertTriangle className="w-4 h-4" />
                                <span>Container is currently running</span>
                            </div>
                        )}
                    </div>

                    {/* Options */}
                    <div className="space-y-3 pt-2">
                        <label className="flex items-start gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={removeImage}
                                onChange={(e) => setRemoveImage(e.target.checked)}
                                disabled={isDeleting}
                                className="w-5 h-5 mt-0.5 text-primary-500 rounded border-dark-600 focus:ring-2 focus:ring-primary-500/50"
                            />
                            <div className="flex-1">
                                <span className="text-sm text-white group-hover:text-primary-400 transition-colors">
                                    Also remove image
                                </span>
                                <p className="text-xs text-dark-400 mt-0.5">
                                    Delete the Docker image if not used by other containers
                                </p>
                            </div>
                        </label>

                        {container.state === 'running' && (
                            <label className="flex items-start gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    checked={force}
                                    onChange={(e) => setForce(e.target.checked)}
                                    disabled={isDeleting}
                                    className="w-5 h-5 mt-0.5 text-primary-500 rounded border-dark-600 focus:ring-2 focus:ring-primary-500/50"
                                />
                                <div className="flex-1">
                                    <span className="text-sm text-white group-hover:text-primary-400 transition-colors">
                                        Force delete (running container)
                                    </span>
                                    <p className="text-xs text-dark-400 mt-0.5">
                                        Remove the container even though it's running
                                    </p>
                                </div>
                            </label>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 p-6 border-t border-dark-700">
                    <button
                        onClick={onCancel}
                        disabled={isDeleting}
                        className="btn btn-secondary"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleConfirm}
                        disabled={isDeleting}
                        className="btn bg-red-600 hover:bg-red-700 text-white"
                    >
                        {isDeleting ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Deleting...
                            </>
                        ) : (
                            <>
                                <Trash2 className="w-4 h-4" />
                                Delete Container
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}

export default DeleteModal
