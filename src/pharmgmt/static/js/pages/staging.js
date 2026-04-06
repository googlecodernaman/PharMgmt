/* Staging Review Page — with expandable row preview */

// Column definitions for staging preview (reuses same pattern as bill-detail)
const _STAGING_COLS = [
    { key: 'product_name_raw', label: 'Product',   fmt: v => `<strong>${v || '\u2014'}</strong>` },
    { key: 'packing',          label: 'Pack',       fmt: v => v || '\u2014' },
    { key: 'batch_no',         label: 'Batch',      fmt: v => v || '\u2014' },
    { key: 'expiry',           label: 'Expiry',     fmt: v => v || '\u2014' },
    { key: 'opening_qty',      label: 'Open',       fmt: v => v ?? '\u2014' },
    { key: 'receipt_qty',      label: 'Receipt',    fmt: v => v ?? '\u2014' },
    { key: 'total_qty',        label: 'Total',      fmt: v => v ?? '\u2014' },
    { key: 'issue_qty',        label: 'Issue',      fmt: v => v ?? '\u2014' },
    { key: 'closing_qty',      label: 'Close',      fmt: v => v ?? '\u2014' },
    { key: 'near_expiry_qty',  label: 'Near Exp',   fmt: v => v ?? '\u2014' },
    { key: 'price_paise',      label: 'MRP',        fmt: v => v != null ? formatMoney(v) : '\u2014' },
];

function _stagingVisibleCols(rows) {
    return _STAGING_COLS.filter(col => {
        if (col.key === 'product_name_raw') return true;
        return rows.some(r => {
            const v = r.fields[col.key];
            return v != null && v !== '' && v !== 0;
        });
    });
}

async function renderStaging(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Staging Review</h2><p>Documents flagged for human review (confidence &lt; 75%)</p></div>
    <div id="staging-list"><div class="skeleton skeleton-card" style="height:200px"></div></div>`;

    try {
        const data = await API.getStaging();
        const docs = data.items || [];

        if (docs.length === 0) {
            document.getElementById('staging-list').innerHTML = `<div class="empty-state"><h3>All clear!</h3><p>No documents need review</p><a href="#/upload" class="btn btn-primary">Upload More Bills</a></div>`;
            return;
        }

        document.getElementById('staging-list').innerHTML = docs.map(doc => `
      <div class="card mb-4" id="staging-doc-${doc.id}">
        <div class="flex justify-between items-center mb-4">
          <div>
            <h3>${doc.file_name}</h3>
            <span style="color:var(--text-secondary);font-size:0.85rem">${formatDate(doc.ingest_ts)} \u00b7 ${doc.rows_count || 0} rows</span>
          </div>
          <div class="flex gap-4 items-center">
            ${confidenceBar(doc.avg_confidence)}
            <button class="btn btn-ghost btn-sm" onclick="togglePreview('${doc.id}')">Preview</button>
            <button class="btn btn-success btn-sm" onclick="acceptDoc('${doc.id}')">Accept</button>
            <button class="btn btn-danger btn-sm" onclick="rejectDoc('${doc.id}')">Reject</button>
            <a href="#/bills/${doc.id}" class="btn btn-ghost btn-sm">View \u2192</a>
          </div>
        </div>
        <div id="staging-preview-${doc.id}" class="hidden" style="margin-top:8px"></div>
      </div>`).join('');

    } catch (e) {
        document.getElementById('staging-list').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
    }
}

// Toggle row preview for a staging document
async function togglePreview(docId) {
    const el = document.getElementById(`staging-preview-${docId}`);
    if (!el) return;

    // Toggle visibility if already loaded
    if (el.dataset.loaded === '1') {
        el.classList.toggle('hidden');
        return;
    }

    el.innerHTML = `<div class="skeleton" style="height:80px"></div>`;
    el.classList.remove('hidden');

    try {
        const data = await API.getStagingDoc(docId);
        const rows = data.rows || [];

        if (rows.length === 0) {
            el.innerHTML = `<p style="color:var(--text-secondary)">No staged rows</p>`;
            el.dataset.loaded = '1';
            return;
        }

        const cols = _stagingVisibleCols(rows);

        el.innerHTML = `
        <div class="table-container" style="max-height:400px;overflow-y:auto">
          <table class="data-table" style="font-size:0.85rem">
            <thead><tr>
              <th>#</th>${cols.map(c => `<th>${c.label}</th>`).join('')}<th>Conf</th>
            </tr></thead>
            <tbody>${rows.map((r, i) => `<tr>
              <td style="color:var(--text-muted)">${i + 1}</td>
              ${cols.map(c => `<td>${c.fmt(r.fields[c.key])}</td>`).join('')}
              <td>${confidenceBar(r.confidence)}</td>
            </tr>`).join('')}</tbody>
          </table>
        </div>`;
        el.dataset.loaded = '1';
    } catch (e) {
        el.innerHTML = `<p style="color:var(--danger)">Error loading preview: ${e.message}</p>`;
    }
}

// Staging actions
async function acceptDoc(docId) {
    if (!confirm('Accept all staged rows and create line items?')) return;
    try {
        await API.acceptStaging(docId);
        Toast.show('Document accepted', 'success');
        const el = document.getElementById(`staging-doc-${docId}`);
        if (el) {
            el.style.opacity = '0';
            el.style.transition = '0.3s';
            setTimeout(() => { el.remove(); _checkStagingEmpty(); }, 300);
        }
    } catch (e) { Toast.show(`Error: ${e.message}`, 'error'); }
}

async function rejectDoc(docId) {
    if (!confirm('Reject this document? Staged rows will be discarded.')) return;
    try {
        await API.rejectStaging(docId);
        Toast.show('Document rejected', 'warning');
        const el = document.getElementById(`staging-doc-${docId}`);
        if (el) {
            el.style.opacity = '0';
            el.style.transition = '0.3s';
            setTimeout(() => { el.remove(); _checkStagingEmpty(); }, 300);
        }
    } catch (e) { Toast.show(`Error: ${e.message}`, 'error'); }
}

function _checkStagingEmpty() {
    const list = document.getElementById('staging-list');
    if (list && !list.querySelector('[id^="staging-doc-"]')) {
        list.innerHTML = `<div class="empty-state"><h3>All clear!</h3><p>All documents have been reviewed</p><a href="#/upload" class="btn btn-primary">Upload More Bills</a></div>`;
    }
}
