/* Analytics Page */
async function renderAnalytics(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Analytics</h2><p>Price tracking and supplier comparison</p></div>
    <div class="tabs" id="analytics-tabs">
      <div class="tab active" data-tab="changes">Price Changes</div>
      <div class="tab" data-tab="comparison">Product Prices</div>
    </div>
    <div id="tab-changes"><div class="skeleton skeleton-card" style="height:300px"></div></div>
    <div id="tab-comparison" class="hidden">
      <div class="card mb-4"><div class="search-box" style="max-width:400px"><span class="search-icon">🔍</span><input class="input" id="price-product-search" placeholder="Enter product name..."></div></div>
      <div id="price-history-result"></div>
    </div>`;

    // Tab switching
    document.querySelectorAll('#analytics-tabs .tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#analytics-tabs .tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-changes').classList.toggle('hidden', tab.dataset.tab !== 'changes');
            document.getElementById('tab-comparison').classList.toggle('hidden', tab.dataset.tab !== 'comparison');
        });
    });

    // Load price changes
    try {
        const data = await API.request('/api/analytics/price-changes');
        const items = data.items || [];

        if (items.length === 0) {
            document.getElementById('tab-changes').innerHTML = `<div class="empty-state"><div class="empty-icon">📊</div><h3>No price changes detected</h3><p>Upload more bills to track price trends</p></div>`;
        } else {
            document.getElementById('tab-changes').innerHTML = `
        <div class="table-container"><table class="data-table"><thead><tr>
          <th>Product</th><th>Previous MRP</th><th>Current MRP</th><th>Change</th><th>Trend</th>
        </tr></thead><tbody>${items.map(i => `
          <tr>
            <td><strong>${i.product}</strong></td>
            <td>${formatMoney(i.old_price)}</td>
            <td>${formatMoney(i.new_price)}</td>
            <td style="color:${i.direction === 'up' ? 'var(--danger)' : 'var(--success)'}; font-weight:600">${i.change_pct > 0 ? '+' : ''}${i.change_pct}%</td>
            <td style="font-size:1.2rem">${i.direction === 'up' ? '📈' : '📉'}</td>
          </tr>`).join('')}</tbody></table></div>`;
        }
    } catch (e) {
        document.getElementById('tab-changes').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
    }

    // Price search
    const searchInput = document.getElementById('price-product-search');
    if (searchInput) {
        let timer;
        searchInput.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(async () => {
                if (!searchInput.isConnected) return; // navigated away
                const q = searchInput.value.trim();
                if (!q) { document.getElementById('price-history-result').innerHTML = ''; return; }
                try {
                    const data = await API.request(`/api/analytics/prices?product=${encodeURIComponent(q)}`);
                    const items = data.items || [];
                    if (items.length === 0) {
                        document.getElementById('price-history-result').innerHTML = `<div class="card"><p style="color:var(--text-secondary)">No price data found for "${q}"</p></div>`;
                    } else {
                        document.getElementById('price-history-result').innerHTML = `
              <div class="card"><h3 class="mb-4">Price History: ${q}</h3>
              <div class="table-container"><table class="data-table"><thead><tr><th>Date</th><th>Price</th><th>Bill</th></tr></thead><tbody>
              ${items.map(i => `<tr><td>${formatDate(i.date)}</td><td>${formatMoney(i.price_paise)}</td><td>${i.file_name}</td></tr>`).join('')}
              </tbody></table></div></div>`;
                    }
                } catch (e) {
                    document.getElementById('price-history-result').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
                }
            }, 500);
        });
    }
}
