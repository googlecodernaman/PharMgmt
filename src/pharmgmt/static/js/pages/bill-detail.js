/* Bill Detail Page */
async function renderBillDetail(container, params) {
    const docId = params.id;
    container.innerHTML = `<div class="skeleton skeleton-card" style="height:400px"></div>`;

    try {
        const doc = await API.getDocument(docId);

        const items = doc.line_items || [];
        container.innerHTML = `
      <div class="flex justify-between items-center mb-6">
        <div>
          <a href="#/bills" class="btn btn-ghost btn-sm mb-2">← Back to Bills</a>
          <h2>${doc.file_name}</h2>
          <div class="flex gap-4 items-center mt-2">
            ${doc.parser_version ? `<span class="badge badge-info">v${doc.parser_version}</span>` : ''}
            <span style="color:var(--text-secondary);font-size:0.85rem">${formatDate(doc.ingest_ts)}</span>
          </div>
        </div>
        <button class="btn btn-secondary" id="btn-export-csv">📥 Export CSV</button>
      </div>

      <div class="grid-4 mb-6">
        <div class="stat-card"><div class="stat-icon">📄</div><div class="stat-value">${doc.title || '—'}</div><div class="stat-label">Title</div></div>
        <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${items.length}</div><div class="stat-label">Line Items</div></div>
        <div class="stat-card"><div class="stat-icon">${doc.is_scanned ? '📷' : '📝'}</div><div class="stat-value">${doc.is_scanned ? 'Scanned' : 'Text'}</div><div class="stat-label">PDF Type</div></div>
        <div class="stat-card"><div class="stat-icon">📅</div><div class="stat-value">${doc.report_from || '—'}</div><div class="stat-label">Report Period</div></div>
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
              <th>#</th><th>Product</th><th>Pack</th><th>Batch</th><th>Expiry</th>
              <th>Open</th><th>Close</th><th>MRP</th><th>Confidence</th>
            </tr></thead>
            <tbody>${items.map((li, i) => {
            const conf = li.parser_confidence || 0;
            const confLevel = conf >= 0.8 ? 'high' : conf >= 0.5 ? 'medium' : 'low';
            return `<tr>
                <td style="color:var(--text-muted)">${i + 1}</td>
                <td><strong>${li.product_name_raw || '—'}</strong></td>
                <td>${li.packing || '—'}</td>
                <td>${li.batch_no || '—'}</td>
                <td>${li.expiry || '—'}</td>
                <td>${li.opening_qty ?? '—'}</td>
                <td>${li.closing_qty ?? '—'}</td>
                <td>${li.price_paise != null ? formatMoney(li.price_paise) : '—'}</td>
                <td>${confidenceBar(conf)}</td>
              </tr>`;
        }).join('')}</tbody>
          </table>
        </div>` : `<div class="empty-state"><div class="empty-icon">📋</div><h3>No line items</h3><p>This document may need review in the staging area</p></div>`}
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

        // CSV export
        document.getElementById('btn-export-csv').addEventListener('click', () => {
            const headers = ['Product', 'Pack', 'Batch', 'Expiry', 'Opening', 'Closing', 'MRP', 'Confidence'];
            const rows = items.map(li => [
                li.product_name_raw, li.packing, li.batch_no, li.expiry,
                li.opening_qty, li.closing_qty, li.price_paise != null ? (li.price_paise / 100).toFixed(2) : '',
                li.parser_confidence,
            ]);
            downloadCSV(`${doc.file_name.replace('.pdf', '')}_export.csv`, headers, rows);
            Toast.show('CSV exported', 'success');
        });

    } catch (e) {
        container.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Document not found</h3><p>${e.message}</p><a href="#/bills" class="btn btn-primary">Back to Bills</a></div>`;
    }
}
