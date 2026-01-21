import { create } from 'zustand'
import { hostsApi } from '../services/api'

export const useHostStore = create((set, get) => ({
    hosts: [],
    selectedHostId: null,
    loading: false,
    error: null,

    // Fetch all hosts
    fetchHosts: async () => {
        set({ loading: true, error: null })
        try {
            const response = await hostsApi.list()
            set({ hosts: response.data, loading: false })

            // Auto-select first host if none selected
            if (!get().selectedHostId && response.data.length > 0) {
                set({ selectedHostId: response.data[0].id })
            }
        } catch (error) {
            set({ error: error.message, loading: false })
        }
    },

    // Select a host
    selectHost: (hostId) => {
        set({ selectedHostId: hostId })
    },

    // Add a new host
    addHost: async (hostData) => {
        try {
            const response = await hostsApi.create(hostData)
            set((state) => ({
                hosts: [...state.hosts, response.data]
            }))
            return response.data
        } catch (error) {
            throw error
        }
    },

    // Update a host
    updateHost: async (hostId, hostData) => {
        try {
            const response = await hostsApi.update(hostId, hostData)
            set((state) => ({
                hosts: state.hosts.map((h) =>
                    h.id === hostId ? response.data : h
                )
            }))
            return response.data
        } catch (error) {
            throw error
        }
    },

    // Delete a host
    deleteHost: async (hostId) => {
        try {
            await hostsApi.delete(hostId)
            set((state) => ({
                hosts: state.hosts.filter((h) => h.id !== hostId),
                selectedHostId: state.selectedHostId === hostId ? null : state.selectedHostId
            }))
        } catch (error) {
            throw error
        }
    },

    // Get selected host
    getSelectedHost: () => {
        const { hosts, selectedHostId } = get()
        return hosts.find((h) => h.id === selectedHostId)
    },
}))
