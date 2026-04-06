/* Products Page — server-side search and pagination */
async function renderProducts(container) {
    const limit = 50;
    let skip = 0;
    let currentSearch = '';
    let totalProducts = 0;

    container.innerHTML = `
    <div class="page-header"><h2>Products</h2><p>Inventory aggregated across all bills</p></div>
    <div class="card mb-4">
      <div class="search-box" style="max-width:400px"><span class="search-icon">🔍</span><input class="input" id="products-search" placeholder="Search products..."></div>
    </div>
    <div id="products-table"><div class="skeleton skeleton-card" style="height:300px"></div></div>
    <div id="products-pagination" class="flex justify-between items-center mt-4"></div>`;

    window._productsChangePage = (newSkip) => { skip = newSkip; load(); };

    async function load() {
        const tableEl = document.getElementById('products-table');
        tableEl.innerHTML = `<div class="skeleton skeleton-card" style="height:300px"></div>`;
        try {
            const data = await API.getProducts(currentSearch, skip, limit);
            const products = data.items || [];
            totalProducts = data.total || 0;

            if (products.length === 0) {
                tableEl.innerHTML = `<div class="empty-state"><div class="empty-icon">💊</div><h3>No products found</h3><p>${currentSearch ? 'Try a different search' : 'Upload bills to see products'}</p></div>`;
                document.getElementById('products-pagination').innerHTML = '';
                return;
            }

            tableEl.innerHTML = `
        <div class="table-container"><table class="data-table"><thead><tr>
          <th>Product</th><th>Pack</th><th>Last Stock</th><th>Price</th><th>Bills</th><th>Expiry</th>
        </tr></thead><tbody>${products.map(p => {
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

            const totalPages = Math.ceil(totalProducts / limit);
            const currentPage = Math.floor(skip / limit);
            document.getElementById('products-pagination').innerHTML = totalPages > 1 ? `
        <button class="btn btn-secondary btn-sm" ${skip === 0 ? 'disabled' : ''} onclick="window._productsChangePage(${skip - limit})">← Prev</button>
        <span style="color:var(--text-secondary);font-size:0.85rem">Page ${currentPage + 1} of ${totalPages} (${totalProducts} products)</span>
        <button class="btn btn-secondary btn-sm" ${skip + limit >= totalProducts ? 'disabled' : ''} onclick="window._productsChangePage(${skip + limit})">Next →</button>` : '';
        } catch (e) {
            tableEl.innerHTML = `<div class="card"><p style="color:var(--danger)">Error: ${e.message}</p></div>`;
        }
    }

    let searchTimer;
    document.getElementById('products-search').addEventListener('input', (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            currentSearch = e.target.value.trim();
            skip = 0;
            load();
        }, 300);
    });

    load();
}
