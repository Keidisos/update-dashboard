import axios from 'axios'

const api = axios.create({
    baseURL: '/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'An error occurred'
        console.error('API Error:', message)
        return Promise.reject(error)
    }
)

// ============== Hosts API ==============

export const hostsApi = {
    list: (includeInactive = false) =>
        api.get('/hosts', { params: { include_inactive: includeInactive } }),

    get: (hostId) =>
        api.get(`/hosts/${hostId}`),

    create: (data) =>
        api.post('/hosts', data),

    update: (hostId, data) =>
        api.patch(`/hosts/${hostId}`, data),

    delete: (hostId) =>
        api.delete(`/hosts/${hostId}`),

    getStatus: (hostId) =>
        api.get(`/hosts/${hostId}/status`),
}

// ============== Containers API ==============

export const containersApi = {
    list: (hostId, { all = true, checkUpdates = false } = {}) =>
        api.get(`/containers/${hostId}`, {
            params: { all, check_updates: checkUpdates }
        }),

    get: (hostId, containerId, checkUpdates = true) =>
        api.get(`/containers/${hostId}/${containerId}`, {
            params: { check_updates: checkUpdates }
        }),

    update: (hostId, containerId, force = false) =>
        api.post(`/containers/${hostId}/update`, {
            container_id: containerId,
            force
        }),

    checkUpdates: (hostId) =>
        api.post(`/containers/${hostId}/check-updates`),

    delete: (hostId, containerId, removeImage = true, force = false) =>
        api.delete(`/containers/${hostId}/${containerId}`, {
            params: { remove_image: removeImage, force }
        }),
}

// ============== System API ==============

export const systemApi = {
    checkUpdates: (hostId) =>
        api.get(`/system/${hostId}/updates`),

    applyUpdates: (hostId, packages = null) =>
        api.post(`/system/${hostId}/updates`, packages ? { packages } : null),

    getInfo: (hostId) =>
        api.get(`/system/${hostId}/info`),
}

export default api
