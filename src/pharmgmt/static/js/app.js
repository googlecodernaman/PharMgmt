/* PharMgmt App — initialization and utilities */

// Toast notifications
const Toast = {
    show(message, type = 'success', duration = 4000) {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const icons = { success: '✅', error: '❌', warning: '⚠️' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${icons[type] || ''}</span><span class="toast-msg">${message}</span><button class="toast-close" onclick="this.parentElement.remove()">×</button>`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    },
};

// Confidence bar helper
function confidenceBar(value) {
    const pct = Math.round((value || 0) * 100);
    const level = pct >= 80 ? 'high' : pct >= 50 ? 'medium' : 'low';
    return `<span class="confidence-bar"><span class="fill ${level}" style="width:${pct}%"></span></span> <span style="font-size:0.8rem;color:var(--text-secondary)">${pct}%</span>`;
}

// Badge helper
function billTypeBadge(type) {
    const labels = { sales_stock: 'Sales & Stock', batch_stock: 'Batch Stock', short_sales: 'Short Sales' };
    return `<span class="badge badge-info">${labels[type] || type || 'Unknown'}</span>`;
}

// Format date
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    if (isNaN(d)) return dateStr;
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

// Format money (paisa → rupees)
function formatMoney(paise) {
    if (paise == null) return '—';
    return `₹${(paise / 100).toFixed(2)}`;
}

// CSV export
function downloadCSV(filename, headers, rows) {
    const csv = [headers.join(','), ...rows.map(r => r.map(c => `"${String(c ?? '').replace(/"/g, '""')}"`).join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
}

// Sidebar toggle
function initSidebar() {
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (hamburger) {
        hamburger.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
        });
    }
    if (overlay) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        });
    }
    // Close sidebar on nav click (mobile)
    document.querySelectorAll('.nav-item').forEach(el => {
        el.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
            }
        });
    });
}

// App init
document.addEventListener('DOMContentLoaded', () => {
    initSidebar();

    // Register routes
    Router.add('/dashboard', renderDashboard);
    Router.add('/bills', renderBills);
    Router.add('/bills/:id', renderBillDetail);
    Router.add('/upload', renderUpload);
    Router.add('/products', renderProducts);
    Router.add('/staging', renderStaging);
    Router.add('/alerts', renderAlerts);
    Router.add('/analytics', renderAnalytics);
    Router.add('/reports', renderReports);

    Router.init();
});
