/* Dashboard Page */
async function renderDashboard(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Dashboard</h2><p>Overview of your pharmacy bill management</p></div>
    <div class="grid-4 mb-6" id="stat-cards">${'<div class="skeleton skeleton-card"></div>'.repeat(4)}</div>
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <h3>Recent Uploads</h3>
        <a href="#/upload" class="btn btn-primary btn-sm">Upload PDF</a>
      </div>
      <div id="recent-table"><div class="skeleton skeleton-text" style="width:100%;height:200px"></div></div>
    </div>`;

    try {
        const stats = await API.getStats();

        document.getElementById('stat-cards').innerHTML = `
      <div class="stat-card"><div class="stat-icon">📄</div><div class="stat-value">${stats.total_documents || 0}</div><div class="stat-label">Total Bills</div></div>
      <div class="stat-card"><div class="stat-icon">💊</div><div class="stat-value">${stats.total_line_items || 0}</div><div class="stat-label">Line Items</div></div>
      <div class="stat-card"><div class="stat-icon">🔍</div><div class="stat-value">${stats.documents_needing_review || 0}</div><div class="stat-label">Needs Review</div></div>
      <div class="stat-card"><div class="stat-icon">📊</div><div class="stat-value">${Math.round((stats.avg_confidence_overall || 0) * 100)}%</div><div class="stat-label">Avg Confidence</div></div>`;

        const recent = stats.recent_uploads || [];
        if (recent.length === 0) {
            document.getElementById('recent-table').innerHTML = `<div class="empty-state"><div class="empty-icon">📁</div><h3>No bills yet</h3><p>Upload your first PDF bill to get started</p><a href="#/upload" class="btn btn-primary">Upload PDF</a></div>`;
        } else {
            document.getElementById('recent-table').innerHTML = `
        <div class="table-container"><table class="data-table"><thead><tr>
          <th>File</th><th>Date</th><th>Type</th><th>Confidence</th><th></th>
        </tr></thead><tbody>${recent.map(d => `
          <tr class="clickable" onclick="location.hash='#/bills/${d.id}'">
            <td><strong>${d.file_name}</strong></td>
            <td>${formatDate(d.ingest_ts)}</td>
            <td>${billTypeBadge(d.bill_type)}</td>
            <td>${confidenceBar(d.avg_confidence)}</td>
            <td><a href="#/bills/${d.id}" class="btn btn-ghost btn-sm">View →</a></td>
          </tr>`).join('')}</tbody></table></div>`;
        }
    } catch (e) {
        document.getElementById('stat-cards').innerHTML = `<div class="card" style="grid-column:1/-1"><p style="color:var(--danger)">Failed to load stats: ${e.message}</p></div>`;
    }
}
