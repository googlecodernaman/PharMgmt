/* Bill Detail Page — dynamic columns, auto-hides empty ones */

// All possible line-item columns in display order
const _ALL_COLUMNS = [
    { key: 'product_name_raw', label: 'Product',   fmt: v => `<strong>${v || '—'}</strong>` },
    { key: 'packing',          label: 'Pack',       fmt: v => v || '—' },
    { key: 'batch_no',         label: 'Batch',      fmt: v => v || '—' },
    { key: 'expiry',           label: 'Expiry',     fmt: v => v || '—' },
    { key: 'opening_qty',      label: 'Open',       fmt: v => v ?? '—' },
    { key: 'receipt_qty',      label: 'Receipt',    fmt: v => v ?? '—' },
    { key: 'total_qty',        label: 'Total',      fmt: v => v ?? '—' },
    { key: 'issue_qty',        label: 'Issue',      fmt: v => v ?? '—' },
    { key: 'closing_qty',      label: 'Close',      fmt: v => v ?? '—' },
    { key: 'near_expiry_qty',  label: 'Near Exp',   fmt: v => v ?? '—' },
    { key: 'price_paise',      label: 'MRP',        fmt: v => v != null ? formatMoney(v) : '—' },
    { key: 'parser_confidence', label: 'Confidence', fmt: v => confidenceBar(v || 0) },
];

/** Return only columns that have data in at least one item. */
function _visibleColumns(items) {
    return _ALL_COLUMNS.filter(col => {
        // Always show product name and confidence
        if (col.key === 'product_name_raw' || col.key === 'parser_confidence') return true;
        return items.some(li => li[col.key] != null && li[col.key] !== '' && li[col.key] !== 0);
    });
}

async function renderBillDetail(container, params) {
    const docId = params.id;
    container.innerHTML = `<div class="skeleton skeleton-card" style="height:400px"></div>`;

    try {
        const doc = await API.getDocument(docId);

        const items = doc.line_items || [];
        const cols = _visibleColumns(items);

        container.innerHTML = `
      <div class="flex justify-between items-center mb-6">
        <div>
          <a href="#/bills" class="btn btn-ghost btn-sm mb-2">\u2190 Back to Bills</a>
          <h2>${doc.file_name}</h2>
          <div class="flex gap-4 items-center mt-2">
            ${doc.parser_version ? `<span class="badge badge-info">v${doc.parser_version}</span>` : ''}
            <span style="color:var(--text-secondary);font-size:0.85rem">${formatDate(doc.ingest_ts)}</span>
          </div>
        </div>
        <button class="btn btn-secondary" id="btn-export-csv">Export CSV</button>
      </div>

      <div class="grid-4 mb-6">
        <div class="stat-card"><div class="stat-value">${doc.title || '\u2014'}</div><div class="stat-label">Title</div></div>
        <div class="stat-card"><div class="stat-value">${items.length}</div><div class="stat-label">Line Items</div></div>
        <div class="stat-card"><div class="stat-value">${doc.is_scanned ? 'Scanned' : 'Text'}</div><div class="stat-label">PDF Type</div></div>
        <div class="stat-card"><div class="stat-value">${doc.report_from || '\u2014'}</div><div class="stat-label">Report Period</div></div>
      </div>

      <div class="tabs" id="detail-tabs">
        <div class="tab active" data-tab="items">Line Items (${items.length})</div>
        <div class="tab" data-tab="raw">Raw Text</div>
      </div>

      <div id="tab-items">
        ${items.length > 0 ? `
        <div class="table-container">
          <table class="data-table" id="items-table">
            <thead><tr>
              <th>#</th>${cols.map(c => `<th>${c.label}</th>`).join('')}
            </tr></thead>
            <tbody>${items.map((li, i) => `<tr>
                <td style="color:var(--text-muted)">${i + 1}</td>
                ${cols.map(c => `<td>${c.fmt(li[c.key])}</td>`).join('')}
              </tr>`).join('')}</tbody>
          </table>
        </div>` : `<div class="empty-state"><h3>No line items</h3><p>This document may need review in the staging area</p></div>`}
      </div>

      <div id="tab-raw" class="hidden">
        <div class="raw-text">${(doc.raw_text || 'No text extracted').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
      </div>`;

        // Tab switching
        document.querySelectorAll('#detail-tabs .tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('#detail-tabs .tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                const target = tab.dataset.tab;
                document.getElementById('tab-items').classList.toggle('hidden', target !== 'items');
                document.getElementById('tab-raw').classList.toggle('hidden', target !== 'raw');
            });
        });

        // CSV export — uses same visible columns
        document.getElementById('btn-export-csv').addEventListener('click', () => {
            const csvCols = cols.filter(c => c.key !== 'parser_confidence');
            const headers = csvCols.map(c => c.label);
            const rows = items.map(li => csvCols.map(c => {
                const v = li[c.key];
                if (c.key === 'price_paise' && v != null) return (v / 100).toFixed(2);
                return v ?? '';
            }));
            downloadCSV(`${doc.file_name.replace('.pdf', '')}_export.csv`, headers, rows);
            Toast.show('CSV exported', 'success');
        });

    } catch (e) {
        container.innerHTML = `<div class="empty-state"><h3>Document not found</h3><p>${e.message}</p><a href="#/bills" class="btn btn-primary">Back to Bills</a></div>`;
    }
}
