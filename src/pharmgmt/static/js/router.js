/* Hash-based SPA Router */

const Router = {
    routes: [],
    currentRoute: null,
    _abortController: null,

    add(path, handler) {
        // path can be exact like '/dashboard' or parameterized like '/bills/:id'
        const parts = path.split('/').filter(Boolean);
        this.routes.push({ path, parts, handler });
    },

    match(hash) {
        const cleanHash = (hash || '#/dashboard').replace('#', '');
        const target = cleanHash.split('/').filter(Boolean);

        for (const route of this.routes) {
            if (route.parts.length !== target.length) continue;
            const params = {};
            let matched = true;
            for (let i = 0; i < route.parts.length; i++) {
                if (route.parts[i].startsWith(':')) {
                    params[route.parts[i].slice(1)] = target[i];
                } else if (route.parts[i] !== target[i]) {
                    matched = false; break;
                }
            }
            if (matched) return { route, params };
        }
        return null;
    },

    async navigate(hash) {
        // Cancel in-flight requests from the previous page
        if (this._abortController) this._abortController.abort();
        this._abortController = new AbortController();
        API._navAbort = this._abortController;

        const result = this.match(hash);
        const container = document.getElementById('page-content');

        // Update active nav
        document.querySelectorAll('.nav-item').forEach(el => {
            const href = el.getAttribute('href') || '';
            el.classList.toggle('active', hash.startsWith(href));
        });

        // Update header title
        const titles = { dashboard: 'Dashboard', bills: 'Bills', upload: 'Upload', products: 'Products', staging: 'Staging Review', alerts: 'Alerts', analytics: 'Analytics', reports: 'Reports' };
        const section = (hash.replace('#/', '') || 'dashboard').split('/')[0];
        const headerTitle = document.getElementById('header-title');
        if (headerTitle) headerTitle.textContent = titles[section] || '';

        if (result) {
            this.currentRoute = result;
            container.innerHTML = '<div class="skeleton skeleton-card" style="height:200px"></div>';
            try {
                await result.route.handler(container, result.params);
            } catch (e) {
                container.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Error loading page</h3><p>${e.message}</p><button class="btn btn-primary" onclick="location.reload()">Reload</button></div>`;
            }
        } else {
            container.innerHTML = '<div class="empty-state"><div class="empty-icon">🔍</div><h3>Page not found</h3><p>The page you\'re looking for doesn\'t exist.</p><a href="#/dashboard" class="btn btn-primary">Go to Dashboard</a></div>';
        }
    },

    init() {
        window.addEventListener('hashchange', () => this.navigate(location.hash));
        this.navigate(location.hash || '#/dashboard');
    },
};
