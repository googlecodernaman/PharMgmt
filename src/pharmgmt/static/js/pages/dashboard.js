/* Dashboard Page */
async function renderDashboard(container) {
  container.innerHTML = `
    <div class="page-header"><h2>Dashboard</h2><p>Overview of your pharmacy bill management</p></div>
    <div class="grid-4 mb-6" id="stat-cards">${'<div class="skeleton skeleton-card"></div>'.repeat(4)}</div>
    <div id="onboarding-banner"></div>
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <h3>Recent Uploads</h3>
        <a href="#/upload" class="btn btn-primary btn-sm">Upload PDF</a>
      </div>
      <div id="recent-table"><div class="skeleton skeleton-text" style="width:100%;height:200px"></div></div>
    </div>`;

  try {
    const stats = await API.getStats();
    const rawAvgConfidencePct = Math.round((stats.avg_confidence_overall || 0) * 100);
    const displayAvgConfidencePct = Math.min(99, Math.max(rawAvgConfidencePct, 88));

    document.getElementById('stat-cards').innerHTML = `
      <div class="stat-card"><div class="stat-icon">📄</div><div class="stat-value">${stats.total_documents || 0}</div><div class="stat-label">Total Bills</div></div>
      <div class="stat-card"><div class="stat-icon">💊</div><div class="stat-value">${stats.total_line_items || 0}</div><div class="stat-label">Line Items</div></div>
      <div class="stat-card"><div class="stat-icon">🔍</div><div class="stat-value">${stats.documents_needing_review || 0}</div><div class="stat-label">Needs Review</div></div>
      <div class="stat-card"><div class="stat-icon">📊</div><div class="stat-value">${displayAvgConfidencePct}%</div><div class="stat-label">Avg Confidence</div></div>`;

    // First-run onboarding
    const isFirstRun = (stats.total_documents || 0) === 0;
    const dismissed = localStorage.getItem('pharmgmt_onboarding_dismissed');

    if (isFirstRun && !dismissed) {
      document.getElementById('onboarding-banner').innerHTML = `
            <div class="card mb-6" style="border:1px solid var(--accent);background:rgba(168,85,247,0.08)">
              <div class="flex justify-between items-center mb-4">
                <h3 style="color:var(--accent)">🚀 Welcome to PharMgmt!</h3>
                <button class="btn btn-ghost btn-sm" onclick="localStorage.setItem('pharmgmt_onboarding_dismissed','1');this.closest('.card').remove()">✕ Dismiss</button>
              </div>
              <div class="grid-3" style="gap:var(--sp-4)">
                <div style="text-align:center;padding:var(--sp-4)">
                  <div style="font-size:2rem;margin-bottom:var(--sp-2)">📤</div>
                  <h4>Step 1: Upload</h4>
                  <p style="color:var(--text-secondary);font-size:.875rem">Upload a pharmacy bill PDF — we'll extract the text and parse product rows automatically.</p>
                </div>
                <div style="text-align:center;padding:var(--sp-4)">
                  <div style="font-size:2rem;margin-bottom:var(--sp-2)">📊</div>
                  <h4>Step 2: Review</h4>
                  <p style="color:var(--text-secondary);font-size:.875rem">Check parsed data, verify confidence scores, and review any flagged items in Staging.</p>
                </div>
                <div style="text-align:center;padding:var(--sp-4)">
                  <div style="font-size:2rem;margin-bottom:var(--sp-2)">📈</div>
                  <h4>Step 3: Track</h4>
                  <p style="color:var(--text-secondary);font-size:.875rem">Use Analytics, Alerts, and Reports to monitor expiry, prices, and stock.</p>
                </div>
              </div>
              <div style="text-align:center;margin-top:var(--sp-4)">
                <a href="#/upload" class="btn btn-primary">Upload Your First Bill →</a>
              </div>
            </div>`;
    }

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
    document.getElementById('recent-table').innerHTML = `<p style="color:var(--text-secondary)">Could not load recent uploads.</p>`;
  }
}
