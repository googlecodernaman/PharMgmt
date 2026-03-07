/* Alerts Page */
async function renderAlerts(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Expiry Alerts</h2><p>Products nearing or past expiry date</p></div>
    <div class="grid-4 mb-6" id="alert-stats">${'<div class="skeleton skeleton-card"></div>'.repeat(4)}</div>
    <div id="alerts-list"><div class="skeleton skeleton-card" style="height:300px"></div></div>`;

    try {
        const data = await API.request('/api/alerts/expiry?days=90');

        document.getElementById('alert-stats').innerHTML = `
      <div class="stat-card" style="border-left:3px solid var(--danger)"><div class="stat-icon">🔴</div><div class="stat-value">${data.expired.length}</div><div class="stat-label">Expired</div></div>
      <div class="stat-card" style="border-left:3px solid var(--warning)"><div class="stat-icon">🟠</div><div class="stat-value">${data.warning_30d.length}</div><div class="stat-label">&lt; 30 Days</div></div>
      <div class="stat-card" style="border-left:3px solid #eab308"><div class="stat-icon">🟡</div><div class="stat-value">${data.warning_60d.length}</div><div class="stat-label">&lt; 60 Days</div></div>
      <div class="stat-card" style="border-left:3px solid var(--info)"><div class="stat-icon">🔵</div><div class="stat-value">${data.warning_90d.length}</div><div class="stat-label">&lt; 90 Days</div></div>`;

        if (data.total_alerts === 0) {
            document.getElementById('alerts-list').innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><h3>No expiry alerts</h3><p>All products are within safe expiry range</p></div>`;
            return;
        }

        let html = '';
        const sections = [
            { key: 'expired', title: '🔴 Expired', color: 'var(--danger)' },
            { key: 'warning_30d', title: '🟠 Expiring within 30 days', color: 'var(--warning)' },
            { key: 'warning_60d', title: '🟡 Expiring within 60 days', color: '#eab308' },
            { key: 'warning_90d', title: '🔵 Expiring within 90 days', color: 'var(--info)' },
        ];

        for (const sec of sections) {
            if (data[sec.key].length === 0) continue;
            html += `<div class="card mb-4" style="border-left:3px solid ${sec.color}"><h3 class="mb-4">${sec.title} (${data[sec.key].length})</h3>
        <div class="table-container"><table class="data-table"><thead><tr><th>Product</th><th>Batch</th><th>Expiry</th><th>Days Left</th><th>Bill</th><th></th></tr></thead><tbody>`;
            for (const a of data[sec.key]) {
                html += `<tr>
          <td><strong>${a.product_name || '—'}</strong></td><td>${a.batch_no || '—'}</td>
          <td>${a.expiry_date}</td><td style="color:${sec.color};font-weight:600">${a.days_remaining}d</td>
          <td>${a.file_name || '—'}</td>
          <td><a href="#/bills/${a.document_id}" class="btn btn-ghost btn-sm">View →</a></td>
        </tr>`;
            }
            html += `</tbody></table></div></div>`;
        }

        document.getElementById('alerts-list').innerHTML = html;
    } catch (e) {
        document.getElementById('alerts-list').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
    }
}
