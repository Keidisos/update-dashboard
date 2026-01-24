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

// ============== SOC API ==============

export const socApi = {
    getIncidents: (hostId = null, resolved = null) =>
        api.get('/soc/incidents', { params: { host_id: hostId, resolved } })
            .then(res => res.data),

    getStats: () =>
        api.get('/soc/stats')
            .then(res => res.data),

    analyzeHost: (hostId) =>
        api.post(`/soc/analyze/${hostId}`)
            .then(res => res.data),

    resolveIncident: (incidentId, notes) =>
        api.post(`/soc/incidents/${incidentId}/resolve`, { resolution_notes: notes })
            .then(res => res.data),

    getHealth: () =>
        api.get('/soc/health')
            .then(res => res.data),

    // Phase 2 endpoints
    getSchedulerStatus: () =>
        api.get('/soc/scheduler/status')
            .then(res => res.data),

    startScheduler: () =>
        api.post('/soc/scheduler/start')
            .then(res => res.data),

    stopScheduler: () =>
        api.post('/soc/scheduler/stop')
            .then(res => res.data),

    getCorrelations: (limit = 10) =>
        api.get('/soc/correlations', { params: { limit } })
            .then(res => res.data.correlations),

    resolveCorrelation: (correlationId, notes) =>
        api.post(`/soc/correlations/${correlationId}/resolve`, { resolution_notes: notes })
            .then(res => res.data),

    testDiscord: () =>
        api.post('/soc/test-discord')
            .then(res => res.data),

    getTimeline: (hours = 24) =>
        api.get('/soc/timeline', { params: { hours } })
            .then(res => res.data.timeline),
}

export default api
