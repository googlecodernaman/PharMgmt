/* Reports Page */
async function renderReports(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Reports</h2><p>Purchase reports, stock summaries, and sanity checks</p></div>

    <div class="card mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3>📦 Purchase Report</h3>
        <div class="flex gap-4">
          <a href="/api/reports/purchases/csv" class="btn btn-secondary btn-sm" target="_blank">📥 CSV</a>
          <button class="btn btn-ghost btn-sm" onclick="window.print()">🖨 Print</button>
        </div>
      </div>
      <div id="purchase-report"><div class="skeleton skeleton-card" style="height:150px"></div></div>
    </div>

    <div class="card mb-6">
      <div class="flex justify-between items-center mb-4">
        <h3>📊 Stock Summary</h3>
        <div class="flex gap-4">
          <a href="/api/reports/stock/csv" class="btn btn-secondary btn-sm" target="_blank">📥 CSV</a>
        </div>
      </div>
      <div id="stock-report"><div class="skeleton skeleton-card" style="height:150px"></div></div>
    </div>

    <div class="card mb-6">
      <h3 class="mb-4">🔍 Sanity Report</h3>
      <div id="sanity-report"><div class="skeleton skeleton-card" style="height:150px"></div></div>
    </div>`;

    // Purchase Report
    try {
        const pr = await API.request('/api/reports/purchases');
        if ((pr.items || []).length === 0) {
            document.getElementById('purchase-report').innerHTML = `<p style="color:var(--text-secondary)">No purchase data yet</p>`;
        } else {
            document.getElementById('purchase-report').innerHTML = `
        <div class="grid-2 mb-4">
          <div class="stat-card"><div class="stat-value">${pr.total_items}</div><div class="stat-label">Items</div></div>
          <div class="stat-card"><div class="stat-value">${formatMoney(pr.total_value_paise)}</div><div class="stat-label">Total Value</div></div>
        </div>
        <div class="table-container" style="max-height:300px;overflow-y:auto"><table class="data-table"><thead><tr>
          <th>File</th><th>Product</th><th>Pack</th><th>Qty</th><th>Price</th><th>Value</th>
        </tr></thead><tbody>${pr.items.slice(0, 50).map(i => `<tr>
          <td>${i.file_name || '—'}</td><td>${i.product || '—'}</td><td>${i.packing || '—'}</td>
          <td>${i.quantity || 0}</td><td>${formatMoney(i.price_paise)}</td><td>${formatMoney(i.value_paise)}</td>
        </tr>`).join('')}</tbody></table></div>`;
        }
    } catch (e) { document.getElementById('purchase-report').innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`; }

    // Stock Summary
    try {
        const st = await API.request('/api/reports/stock');
        if ((st.items || []).length === 0) {
            document.getElementById('stock-report').innerHTML = `<p style="color:var(--text-secondary)">No stock data yet</p>`;
        } else {
            document.getElementById('stock-report').innerHTML = `
        <div class="grid-2 mb-4">
          <div class="stat-card"><div class="stat-value">${st.total_products}</div><div class="stat-label">Products</div></div>
          <div class="stat-card"><div class="stat-value">${formatMoney(st.total_value_paise)}</div><div class="stat-label">Total Value</div></div>
        </div>
        <div class="table-container" style="max-height:300px;overflow-y:auto"><table class="data-table"><thead><tr>
          <th>Product</th><th>Pack</th><th>Stock</th><th>Price</th><th>Value</th><th>Expiry</th>
        </tr></thead><tbody>${st.items.map(i => `<tr>
          <td>${i.product || '—'}</td><td>${i.packing || '—'}</td>
          <td>${i.closing_qty || 0}</td><td>${formatMoney(i.price_paise)}</td>
          <td>${formatMoney(i.value_paise)}</td><td>${i.expiry || '—'}</td>
        </tr>`).join('')}</tbody></table></div>`;
        }
    } catch (e) { document.getElementById('stock-report').innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`; }

    // Sanity Report
    try {
        const san = await API.request('/api/reports/sanity');
        if ((san.flagged_documents || []).length === 0) {
            document.getElementById('sanity-report').innerHTML = `<div class="flex items-center gap-4"><span style="color:var(--success);font-size:1.5rem">✅</span><span>No issues found — all documents parsed cleanly</span></div>`;
        } else {
            document.getElementById('sanity-report').innerHTML = `
        <div class="grid-2 mb-4">
          <div class="stat-card"><div class="stat-value">${san.total_flagged_docs}</div><div class="stat-label">Flagged Docs</div></div>
          <div class="stat-card"><div class="stat-value">${san.total_flagged_rows}</div><div class="stat-label">Flagged Rows</div></div>
        </div>
        <div class="table-container"><table class="data-table"><thead><tr><th>File</th><th>Confidence</th><th>Flagged Rows</th><th>Issues</th><th></th></tr></thead><tbody>
        ${san.flagged_documents.map(d => `<tr>
          <td>${d.file_name || '—'}</td>
          <td>${confidenceBar(d.avg_confidence)}</td>
          <td>${d.rows_flagged}</td>
          <td>${(d.error_flags || []).map(f => `<span class="badge badge-warning">${f}</span>`).join(' ')}</td>
          <td><a href="#/bills/${d.document_id}" class="btn btn-ghost btn-sm">View →</a></td>
        </tr>`).join('')}</tbody></table></div>`;
        }
    } catch (e) { document.getElementById('sanity-report').innerHTML = `<p style="color:var(--danger)">Error: ${e.message}</p>`; }
}
