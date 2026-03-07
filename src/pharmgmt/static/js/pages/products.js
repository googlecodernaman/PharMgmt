/* Products Page */
async function renderProducts(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Products</h2><p>Inventory aggregated across all bills</p></div>
    <div class="card mb-4">
      <div class="search-box" style="max-width:400px"><span class="search-icon">🔍</span><input class="input" id="products-search" placeholder="Search products..."></div>
    </div>
    <div id="products-table"><div class="skeleton skeleton-card" style="height:300px"></div></div>`;

    try {
        const data = await API.getProducts();
        let products = data.items || [];

        function render() {
            const search = (document.getElementById('products-search')?.value || '').toLowerCase();
            const filtered = products.filter(p => !search || (p.name || '').toLowerCase().includes(search));

            if (filtered.length === 0) {
                document.getElementById('products-table').innerHTML = `<div class="empty-state"><div class="empty-icon">💊</div><h3>No products found</h3><p>${search ? 'Try a different search' : 'Upload bills to see products'}</p></div>`;
                return;
            }

            document.getElementById('products-table').innerHTML = `
        <div class="table-container"><table class="data-table"><thead><tr>
          <th>Product</th><th>Pack</th><th>Last Stock</th><th>Price</th><th>Bills</th><th>Expiry</th>
        </tr></thead><tbody>${filtered.map(p => {
                const expClass = p.expiry_warning ? (p.expired ? 'danger' : 'warning') : '';
                return `<tr>
            <td><strong>${p.name || '—'}</strong></td>
            <td>${p.packing || '—'}</td>
            <td>${p.latest_closing ?? '—'}</td>
            <td>${p.latest_price != null ? formatMoney(p.latest_price) : '—'}</td>
            <td>${p.bill_count || 0}</td>
            <td>${expClass ? `<span class="badge badge-${expClass}">${p.latest_expiry || '—'}</span>` : (p.latest_expiry || '—')}</td>
          </tr>`;
            }).join('')}</tbody></table></div>`;
        }

        document.getElementById('products-search').addEventListener('input', render);
        render();
    } catch (e) {
        document.getElementById('products-table').innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
    }
}
