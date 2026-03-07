/* Upload Page */
async function renderUpload(container) {
    container.innerHTML = `
    <div class="page-header"><h2>Upload Bill</h2><p>Drag and drop a PDF bill to parse and ingest</p></div>
    <div class="card mb-6">
      <div class="file-drop" id="file-drop">
        <div class="drop-icon">📤</div>
        <div class="drop-text">Drop PDF file here or click to browse</div>
        <div class="drop-hint">Accepts .pdf files up to 50MB</div>
        <input type="file" id="file-input" accept=".pdf" style="display:none">
      </div>
      <div id="upload-progress" class="hidden mt-4">
        <div class="flex justify-between mb-2"><span id="upload-filename" style="font-weight:500"></span><span id="upload-status" style="font-size:0.85rem;color:var(--text-secondary)">Uploading...</span></div>
        <div class="progress-bar"><div class="progress-fill" id="progress-fill" style="width:0%"></div></div>
      </div>
      <div id="parse-result" class="hidden mt-6"></div>
    </div>`;

    const dropZone = document.getElementById('file-drop');
    const fileInput = document.getElementById('file-input');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); handleFile(e.dataTransfer.files[0]); });
    fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

    async function handleFile(file) {
        if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
            Toast.show('Please select a PDF file', 'error');
            return;
        }
        if (file.size > 50 * 1024 * 1024) {
            Toast.show('File too large (max 50MB)', 'error');
            return;
        }

        const progress = document.getElementById('upload-progress');
        const progressFill = document.getElementById('progress-fill');
        const resultDiv = document.getElementById('parse-result');

        document.getElementById('upload-filename').textContent = file.name;
        document.getElementById('upload-status').textContent = 'Uploading...';
        progress.classList.remove('hidden');
        resultDiv.classList.add('hidden');
        progressFill.style.width = '30%';

        try {
            progressFill.style.width = '60%';
            const result = await API.uploadPdf(file);
            progressFill.style.width = '100%';
            document.getElementById('upload-status').textContent = 'Complete!';
            document.getElementById('upload-status').style.color = 'var(--success)';
            Toast.show('Bill uploaded and parsed successfully', 'success');

            const meta = result.meta || {};
            const doc = result.document || {};
            resultDiv.classList.remove('hidden');
            resultDiv.innerHTML = `
        <h3 class="mb-4">Parse Result</h3>
        <div class="grid-4 mb-4">
          <div class="stat-card"><div class="stat-value">${meta.rows_parsed || 0}</div><div class="stat-label">Rows Parsed</div></div>
          <div class="stat-card"><div class="stat-value">${Math.round((meta.avg_confidence || 0) * 100)}%</div><div class="stat-label">Confidence</div></div>
          <div class="stat-card"><div class="stat-value">${meta.rows_flagged || 0}</div><div class="stat-label">Flagged</div></div>
          <div class="stat-card"><div class="stat-value">${billTypeBadge(meta.bill_type)}</div><div class="stat-label">Bill Type</div></div>
        </div>
        ${(meta.error_flags || []).length > 0 ? `<div class="card" style="border-color:var(--warning);margin-bottom:var(--sp-4)"><strong style="color:var(--warning)">⚠️ Warnings:</strong> ${meta.error_flags.join(', ')}</div>` : ''}
        <div class="flex gap-4">
          <a href="#/bills/${doc.document_id}" class="btn btn-primary">View Bill →</a>
          <button class="btn btn-secondary" onclick="document.getElementById('upload-progress').classList.add('hidden');document.getElementById('parse-result').classList.add('hidden');">Upload Another</button>
        </div>`;
        } catch (e) {
            progressFill.style.width = '100%';
            progressFill.style.background = 'var(--danger)';
            document.getElementById('upload-status').textContent = 'Failed';
            document.getElementById('upload-status').style.color = 'var(--danger)';
            Toast.show(`Upload failed: ${e.message}`, 'error');
        }
    }
}
