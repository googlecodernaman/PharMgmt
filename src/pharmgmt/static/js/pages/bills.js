/* Bills List Page */
async function renderBills(container) {
    container.innerHTML = `
    <div class="page-header flex justify-between items-center">
      <div><h2>Bills</h2><p>All ingested documents</p></div>
      <a href="#/upload" class="btn btn-primary">Upload PDF</a>
    </div>
    <div class="card mb-4 flex gap-4 items-center flex-wrap">
      <div class="search-box flex-1" style="min-width:200px"><span class="search-icon">🔍</span><input class="input" id="bills-search" placeholder="Search bills..."></div>
      <select class="select" id="bills-filter" style="width:auto;min-width:140px">
        <option value="all">All Bills</option>
        <option value="review">Needs Review</option>
        <option value="high">High Confidence</option>
      </select>
      <select class="select" id="bills-sort" style="width:auto;min-width:150px">
        <option value="newest">Newest First</option>
        <option value="oldest">Oldest First</option>
        <option value="conf-high">Confidence ↑</option>
        <option value="conf-low">Confidence ↓</option>
      </select>
    </div>
    <div id="bills-table"><div class="skeleton skeleton-card" style="height:300px"></div></div>
    <div id="bills-pagination" class="flex justify-between items-center mt-4"></div>`;

    let allDocs = [];
    let page = 0;
    const perPage = 20;

    // Expose page changer globally so inline pagination buttons can reach it
    window._billsChangePage = (n) => { page = n; renderTable(); };

    async function loadBills() {
        try {
            // Fetch up to 500 docs; server paginates beyond that
            const data = await API.getDocuments(0, 200);
            allDocs = data.items || [];
            renderTable();
        } catch (e) {
            document.getElementById('bills-table').innerHTML = `<div class="card"><p style="color:var(--danger)">Failed to load: ${e.message}</p></div>`;
        }
    }

    function renderTable() {
        const search = document.getElementById('bills-search').value.toLowerCase();
        const filter = document.getElementById('bills-filter').value;
        const sort = document.getElementById('bills-sort').value;

        let filtered = allDocs.filter(d => {
            if (search && !d.file_name.toLowerCase().includes(search) && !(d.title || '').toLowerCase().includes(search)) return false;
            if (filter === 'review' && !d.needs_review) return false;
            if (filter === 'high' && (d.avg_confidence || 0) < 0.75) return false;
            return true;
        });

        if (sort === 'newest') filtered.sort((a, b) => new Date(b.ingest_ts) - new Date(a.ingest_ts));
        if (sort === 'oldest') filtered.sort((a, b) => new Date(a.ingest_ts) - new Date(b.ingest_ts));
        if (sort === 'conf-high') filtered.sort((a, b) => (b.avg_confidence || 0) - (a.avg_confidence || 0));
        if (sort === 'conf-low') filtered.sort((a, b) => (a.avg_confidence || 0) - (b.avg_confidence || 0));

        const totalPages = Math.ceil(filtered.length / perPage);
        // Keep page in valid range after filter change
        if (page >= totalPages) page = Math.max(0, totalPages - 1);
        const paged = filtered.slice(page * perPage, (page + 1) * perPage);

        if (paged.length === 0) {
            document.getElementById('bills-table').innerHTML = `<div class="empty-state"><div class="empty-icon">📁</div><h3>No bills found</h3><p>${search || filter !== 'all' ? 'Try a different search term or filter' : 'Upload your first PDF bill'}</p>${filter === 'all' && !search ? '<a href="#/upload" class="btn btn-primary">Upload PDF</a>' : ''}</div>`;
            document.getElementById('bills-pagination').innerHTML = '';
            return;
        }

        document.getElementById('bills-table').innerHTML = `
      <div class="table-container"><table class="data-table"><thead><tr>
        <th>File Name</th><th>Title</th><th>Type</th><th>Date</th><th>Items</th><th>Confidence</th><th></th>
      </tr></thead><tbody>${paged.map(d => `
        <tr class="clickable" onclick="location.hash='#/bills/${d.id}'">
          <td><strong>${d.file_name}</strong></td>
          <td style="color:var(--text-secondary)">${d.title || '—'}</td>
          <td>${billTypeBadge(d.bill_type)}</td>
          <td>${formatDate(d.ingest_ts)}</td>
          <td>${d.line_item_count || 0}</td>
          <td>${confidenceBar(d.avg_confidence || 0)}${d.needs_review ? ' <span class="badge badge-warning" style="font-size:0.7rem">Review</span>' : ''}</td>
          <td><a href="#/bills/${d.id}" class="btn btn-ghost btn-sm">View →</a></td>
        </tr>`).join('')}</tbody></table></div>`;

        document.getElementById('bills-pagination').innerHTML = totalPages > 1 ? `
      <button class="btn btn-secondary btn-sm" ${page === 0 ? 'disabled' : ''} onclick="window._billsChangePage(${page - 1})">← Prev</button>
      <span style="color:var(--text-secondary);font-size:0.85rem">Page ${page + 1} of ${totalPages} (${filtered.length} bills)</span>
      <button class="btn btn-secondary btn-sm" ${page >= totalPages - 1 ? 'disabled' : ''} onclick="window._billsChangePage(${page + 1})">Next →</button>` : '';
    }

    let searchTimer;
    document.getElementById('bills-search').addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => { page = 0; renderTable(); }, 300);
    });
    document.getElementById('bills-filter').addEventListener('change', () => { page = 0; renderTable(); });
    document.getElementById('bills-sort').addEventListener('change', renderTable);

    await loadBills();
}
