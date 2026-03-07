/* Staging Review Page */
async function renderStaging(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Staging Review</h2><p>Documents flagged for human review (confidence &lt; 75%)</p></div>
    <div id="staging-list"><div class="skeleton skeleton-card" style="height:200px"></div></div>`;

    try {
        const data = await API.getStaging();
        const docs = data.items || [];

        if (docs.length === 0) {
            document.getElementById('staging-list').innerHTML = `<div class="empty-state"><div class="empty-icon">✅</div><h3>All clear!</h3><p>No documents need review</p><a href="#/upload" class="btn btn-primary">Upload More Bills</a></div>`;
            return;
        }

        document.getElementById('staging-list').innerHTML = docs.map(doc => `
      <div class="card mb-4" id="staging-doc-${doc.id}">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h3>${doc.file_name}</h3>
            <span style="color:var(--text-secondary);font-size:0.85rem">${formatDate(doc.ingest_ts)} · ${doc.rows_count || 0} rows</span>
          </div>
          <div class="flex gap-4 items-center">
            ${confidenceBar(doc.avg_confidence)}
            <button class="btn btn-success btn-sm" onclick="acceptDoc('${doc.id}')">✓ Accept</button>
            <button class="btn btn-danger btn-sm" onclick="rejectDoc('${doc.id}')">✗ Reject</button>
            <a href="#/bills/${doc.id}" class="btn btn-ghost btn-sm">View →</a>
          </div>
        </div>
      </div>`).join('');

    } catch (e) {
        document.getElementById('staging-list').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
    }
}

// Staging actions
async function acceptDoc(docId) {
    if (!confirm('Accept all staged rows and create line items?')) return;
    try {
        await API.acceptStaging(docId);
        Toast.show('Document accepted', 'success');
        const el = document.getElementById(`staging-doc-${docId}`);
        if (el) { el.style.opacity = '0'; el.style.transition = '0.3s'; setTimeout(() => el.remove(), 300); }
    } catch (e) { Toast.show(`Error: ${e.message}`, 'error'); }
}

async function rejectDoc(docId) {
    if (!confirm('Reject this document? Staged rows will be discarded.')) return;
    try {
        await API.rejectStaging(docId);
        Toast.show('Document rejected', 'warning');
        const el = document.getElementById(`staging-doc-${docId}`);
        if (el) { el.style.opacity = '0'; el.style.transition = '0.3s'; setTimeout(() => el.remove(), 300); }
    } catch (e) { Toast.show(`Error: ${e.message}`, 'error'); }
}
