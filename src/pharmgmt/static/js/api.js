/* API Client — fetch wrapper for PharMgmt backend */

const API = {
    baseUrl: '',
    _navAbort: null,  // Set by Router on each navigation to cancel stale requests

    async request(path, options = {}) {
        const { headers = {}, signal: callerSignal, ...rest } = options;
        const signal = callerSignal ?? this._navAbort?.signal;
        try {
            const res = await fetch(`${this.baseUrl}${path}`, {
                signal,
                headers: { 'Content-Type': 'application/json', ...headers },
                ...rest,
            });
            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }
            return await res.json();
        } catch (e) {
            if (e.name === 'AbortError') return new Promise(() => {}); // silently cancel
            console.error(`API ${path}:`, e);
            throw e;
        }
    },

    getHealth() { return this.request('/health'); },

    getDocuments(skip = 0, limit = 50) {
        return this.request(`/api/documents?skip=${skip}&limit=${limit}`);
    },

    getDocument(id) { return this.request(`/api/documents/${id}`); },

    getStats() { return this.request('/api/stats'); },

    getProducts(search = '', skip = 0, limit = 50) {
        const params = new URLSearchParams({ skip, limit });
        if (search) params.set('search', search);
        return this.request(`/api/products?${params}`);
    },

    getStaging() { return this.request('/api/staging'); },

    getStagingDoc(docId) { return this.request(`/api/staging/${docId}`); },

    acceptStaging(docId) {
        return this.request(`/api/staging/${docId}/accept`, { method: 'POST' });
    },

    rejectStaging(docId) {
        return this.request(`/api/staging/${docId}/reject`, { method: 'POST' });
    },

    async uploadPdf(file) {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch(`${this.baseUrl}/api/upload`, { method: 'POST', body: form });
        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }
        return await res.json();
    },
};
