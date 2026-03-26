/* ================================================================
   AI Document Assistant — Frontend Logic
   Calls Python backend via fetch() REST API
   ================================================================ */

// ── DOM refs ────────────────────────────────────────────────────────
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const navBtns = $$('.nav-btn');
const tabPanels = $$('.tab-panel');
const uploadZone = $('#upload-zone');
const browseBtn = $('#browse-btn');
const fileInput = $('#file-input');
const uploadStatus = $('#upload-status');
const searchInput = $('#search-input');
const searchBtn = $('#search-btn');
const resultsContainer = $('#results-container');
const libraryContainer = $('#library-container');
const loader = $('#loader');
const loaderText = $('#loader-text');
const toastContainer = $('#toast-container');
const filterFileType = $('#filter-file-type');
const filterSort = $('#filter-sort');

// ── Tab switching ───────────────────────────────────────────────────
navBtns.forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;

    navBtns.forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');

    tabPanels.forEach((p) => p.classList.remove('active'));
    $(`#tab-${target}`).classList.add('active');

    // Auto-refresh library when switching to that tab
    if (target === 'library') loadLibrary();
  });
});

// ── Toasts ──────────────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  toastContainer.appendChild(el);
  setTimeout(() => el.remove(), 5000);
}

// ── Loader ──────────────────────────────────────────────────────────
function showLoader(text = 'Processing …') {
  loaderText.textContent = text;
  loader.classList.add('visible');
}
function hideLoader() {
  loader.classList.remove('visible');
}

// ── Helpers ─────────────────────────────────────────────────────────
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]); // strip "data:…;base64,"
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function formatDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

function fileIcon(filename) {
  if (filename.toLowerCase().endsWith('.pdf')) return '📕';
  if (filename.toLowerCase().endsWith('.txt')) return '📝';
  return '📄';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function highlightKeywords(text, query) {
  if (!text || !query) return escapeHtml(text || '');

  // Match words longer than 2 chars from the query
  const words = query.split(/\s+/).filter(w => w.length > 2);
  if (words.length === 0) return escapeHtml(text);

  const escapedText = escapeHtml(text);
  // Optional: escape regex specials in words
  const safeWords = words.map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const regex = new RegExp(`(${safeWords.join('|')})`, 'gi');
  return escapedText.replace(regex, '<mark class="highlight">$1</mark>');
}

// ── UPLOAD ──────────────────────────────────────────────────────────
let isFirstUpload = true;

async function uploadFile(file) {
  const allowed = ['.pdf', '.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast(`Unsupported file type: ${ext}`, 'error');
    return;
  }

  showLoader(`Uploading "${file.name}" …`);

  if (isFirstUpload) {
    showToast("First upload may take 2-3 minutes to download the AI model. Subsequent uploads will be fast!", "info");
    isFirstUpload = false;
  }

  try {
    const b64 = await fileToBase64(file);
    const resp = await fetch('/api/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: file.name, base64_content: b64 }),
    });
    const res = await resp.json();

    if (res.success) {
      showToast(`"${file.name}" uploaded successfully!`, 'success');

      // Auto-switch to search tab
      setTimeout(() => {
        $('#nav-search').click();
      }, 1000);

    } else {
      showToast(res.error || 'Upload failed', 'error');
    }
  } catch (err) {
    showToast('Upload error: ' + err.message, 'error');
  } finally {
    hideLoader();
  }
}

// Drag & drop
uploadZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => {
  uploadZone.classList.remove('drag-over');
});
uploadZone.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadZone.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  for (const file of files) uploadFile(file);
});

// Browse button
browseBtn.addEventListener('click', (e) => {
  e.stopPropagation();
  fileInput.click();
});
fileInput.addEventListener('change', () => {
  const files = fileInput.files;
  for (const file of files) uploadFile(file);
  fileInput.value = '';
});

// ── SEARCH ──────────────────────────────────────────────────────────
async function performSearch(searchQuery = null) {
  let query = '';
  // If it's an Event object (from click/keydown), ignore it
  if (typeof searchQuery === 'string') {
    query = searchQuery;
  } else {
    query = searchInput.value.trim();
  }

  if (!query) {
    showToast('Please enter a search query', 'error');
    return;
  }

  searchInput.value = query; // update input box if clicked from chip
  saveRecentSearch(query);

  showLoader('Searching documents …');
  try {
    const resp = await fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, file_type: filterFileType.value, sort_by: filterSort.value }),
    });
    const res = await resp.json();

    if (!res.success) {
      showToast(res.error || 'Search failed', 'error');
      resultsContainer.innerHTML = '';
      hideLoader();
      return;
    }

    if (res.results.length === 0) {
      resultsContainer.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">🤷</span>
          <h3>No matches found</h3>
          <p>Try a different query or upload more documents</p>
        </div>`;
      hideLoader();
      return;
    }

    resultsContainer.innerHTML = res.results.map((r) => `
      <div class="doc-card" onclick="openPreview('${r.id}', '${escapeHtml(query).replace(/'/g, "\\'")}')" style="cursor: pointer;">
        <div class="doc-card-header">
          <span class="doc-card-title">
            <span class="file-icon">${fileIcon(r.filename)}</span>
            <span class="file-name-text">${escapeHtml(r.filename)}</span>
          </span>
          <div class="doc-card-meta">
            <div class="score-container" title="AI Confidence Score">
              <span class="score-badge">⚡ ${(r.score * 100).toFixed(0)}%</span>
              <div class="score-bar-wrapper">
                <div class="score-bar-fill" style="width: ${(r.score * 100).toFixed(0)}%;"></div>
              </div>
            </div>
            ${r.uploaded_at ? `<span>${formatDate(r.uploaded_at)}</span>` : ''}
          </div>
        </div>
        <div class="doc-card-snippet">${highlightKeywords(r.snippet, query)}</div>
      </div>
    `).join('');
  } catch (err) {
    showToast('Search error: ' + err.message, 'error');
  } finally {
    hideLoader();
  }
}

searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') performSearch();
});

// Re-search when filters change (only if there's already a query)
filterFileType.addEventListener('change', () => {
  if (searchInput.value.trim()) performSearch();
});
filterSort.addEventListener('change', () => {
  if (searchInput.value.trim()) performSearch();
});

// ── LIBRARY ─────────────────────────────────────────────────────────
async function loadLibrary() {
  try {
    const resp = await fetch('/api/documents');
    const res = await resp.json();

    if (!res.success) {
      showToast(res.error || 'Failed to load library', 'error');
      return;
    }

    const countSpan = $('#docs-count');
    if (countSpan) {
      countSpan.innerHTML = `(${res.documents.length}${isPro ? '' : ' / 25'} files)`;
    }

    if (res.documents.length === 0) {
      libraryContainer.innerHTML = `
        <div class="empty-state">
          <span class="empty-icon">📭</span>
          <h3>No documents yet</h3>
          <p>Upload files on the Upload tab to get started</p>
        </div>`;
      return;
    }

    libraryContainer.innerHTML = res.documents.map((d) => `
      <div class="doc-card" id="doc-${d.id}" onclick="openPreview('${d.id}')" style="cursor: pointer;">
        <div class="doc-card-header">
          <span class="doc-card-title">
            <span class="file-icon">${fileIcon(d.filename)}</span>
            <span class="file-name-text">${escapeHtml(d.filename)}</span>
          </span>
          <div class="doc-card-meta">
            ${d.uploaded_at ? `<span>${formatDate(d.uploaded_at)}</span>` : ''}
            <button class="delete-btn" onclick="event.stopPropagation(); deleteDoc('${d.id}', '${escapeHtml(d.filename).replace(/'/g, "\\'")}')">🗑️ Delete</button>
          </div>
        </div>
        ${d.summary ? `<div class="doc-card-snippet" style="font-style: italic; opacity: 0.8; margin-top: 12px; font-size: 14px;">✨ ${escapeHtml(d.summary)}</div>` : ''}
      </div>
    `).join('');
  } catch (err) {
    showToast('Library error: ' + err.message, 'error');
  }
}

// ── DELETE ───────────────────────────────────────────────────────────
async function deleteDoc(docId, filename) {
  if (!confirm(`Delete "${filename}"? This cannot be undone.`)) return;

  showLoader('Deleting document …');
  try {
    const resp = await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
    const res = await resp.json();

    if (res.success) {
      showToast(`"${filename}" deleted`, 'success');
      loadLibrary();
    } else {
      showToast(res.error || 'Delete failed', 'error');
    }
  } catch (err) {
    showToast('Delete error: ' + err.message, 'error');
  } finally {
    hideLoader();
  }
}

// ── PREVIEW PANEL ───────────────────────────────────────────────────
const previewPanel = document.getElementById('preview-panel');
const previewBackdrop = document.getElementById('preview-backdrop');
const previewTitle = document.getElementById('preview-title');
const previewContent = document.getElementById('preview-content');

document.getElementById('close-preview-btn').addEventListener('click', closePreview);
previewBackdrop.addEventListener('click', closePreview);

async function openPreview(docId, highlightQuery = null) {
  previewPanel.classList.add('open');
  previewBackdrop.classList.add('visible');
  previewTitle.textContent = "Loading Document...";
  previewContent.innerHTML = '<div class="spinner" style="margin: 0 auto;"></div><p style="text-align: center; margin-top: 16px;">Loading full text...</p>';

  try {
    const resp = await fetch(`/api/documents/${docId}/content`);
    const res = await resp.json();

    if (!res.success) {
      previewTitle.textContent = "Error";
      previewContent.textContent = res.error || "Failed to load document text.";
      return;
    }

    previewTitle.textContent = res.filename;

    if (highlightQuery) {
      previewContent.innerHTML = highlightKeywords(res.content, highlightQuery);

      // Auto-scroll to the first highlighted match
      setTimeout(() => {
        const firstMark = previewContent.querySelector('mark');
        if (firstMark) {
          firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });
          // Make all marks pulse to draw the user's eye
          previewContent.querySelectorAll('mark').forEach(m => m.classList.add('pulse-highlight'));
        }
      }, 300); // slight delay to ensure rendering is complete
    } else {
      previewContent.textContent = res.content;
    }
  } catch (err) {
    previewTitle.textContent = "Error";
    previewContent.textContent = "Something went wrong fetching the document.";
  }
}

function closePreview() {
  previewPanel.classList.remove('open');
  previewBackdrop.classList.remove('visible');
  setTimeout(() => { previewContent.textContent = "" }, 300); // Clear on close animation finish
}

// ── RECENT SEARCHES ─────────────────────────────────────────────────
const recentSearchesContainer = document.getElementById('recent-searches');

function renderRecentSearches() {
  const searches = JSON.parse(localStorage.getItem('docassist_recent_searches') || '[]');
  if (searches.length === 0) {
    recentSearchesContainer.innerHTML = '';
    return;
  }

  recentSearchesContainer.innerHTML = searches.map(s =>
    `<div class="search-chip" onclick="performSearch('${escapeHtml(s).replace(/'/g, "\\'")}')">
      🕒 ${escapeHtml(s)}
    </div>`
  ).join('');
}

function saveRecentSearch(query) {
  let searches = JSON.parse(localStorage.getItem('docassist_recent_searches') || '[]');
  searches = searches.filter(s => s.toLowerCase() !== query.toLowerCase()); // remove duplicate
  searches.unshift(query); // add to front
  if (searches.length > 6) searches.pop(); // keep only top 6
  localStorage.setItem('docassist_recent_searches', JSON.stringify(searches));
  renderRecentSearches();
}

// ── Settings ────────────────────────────────────────────────────────
const settingsBtn = $('#nav-settings');
const settingsBackdrop = $('#settings-backdrop');
const closeSettingsBtn = $('#close-settings-btn');
const toggleShortcut = $('#toggle-shortcut');
const toggleStartup = $('#toggle-startup');

settingsBtn.addEventListener('click', () => {
  settingsBackdrop.style.display = 'flex';
});

closeSettingsBtn.addEventListener('click', () => {
  settingsBackdrop.style.display = 'none';
});

settingsBackdrop.addEventListener('click', (e) => {
  if (e.target === settingsBackdrop) settingsBackdrop.style.display = 'none';
});

// Handle Toggles
toggleShortcut.addEventListener('change', async () => {
  const isChecked = toggleShortcut.checked;
  if (!isChecked) return; // ignore uncheck for now unless backend supports removing
  try {
    const resp = await fetch('/api/settings/create-shortcut', { method: 'POST' });
    const res = await resp.json();
    if (res.success) {
      showToast('Shortcut created on Desktop!', 'success');
    } else {
      showToast(res.error || 'Failed to create shortcut', 'error');
      toggleShortcut.checked = false;
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
    toggleShortcut.checked = false;
  }
});

toggleStartup.addEventListener('change', async () => {
  const isChecked = toggleStartup.checked;
  try {
    const resp = await fetch('/api/settings/toggle-startup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ enabled: isChecked })
    });
    const res = await resp.json();
    if (res.success) {
      showToast(isChecked ? 'Run at Startup enabled' : 'Run at Startup disabled', 'success');
    } else {
      showToast(res.error || 'Failed to update startup', 'error');
      toggleStartup.checked = !isChecked;
    }
  } catch (err) {
    showToast('Network error: ' + err.message, 'error');
    toggleStartup.checked = !isChecked;
  }
});

const btnWatchFolder = $('#btn-watch-folder');

btnWatchFolder.addEventListener('click', async () => {
  try {
    const resp = await fetch('/api/settings/choose-folder', { method: 'POST' });
    const res = await resp.json();
    if (res.success) {
      showToast(`Watch Folder updated!`, 'success');
      btnWatchFolder.textContent = res.folder_path.split('/').pop().split('\\').pop() || 'Selected';
    } else {
      showToast(res.error || 'No folder selected', 'info');
    }
  } catch (err) {
    showToast('Folder picking error: ' + err.message, 'error');
  }
});

// ── License Support ────────────────────────────────────────────────
const inputLicense = $('#input-license');
const btnActivateLicense = $('#btn-activate-license');
const btnDeactivateLicense = $('#btn-deactivate-license');
const licenseStatus = $('#license-status');
let isPro = false;

async function checkLicense() {
  try {
    const resp = await fetch('/api/settings/license');
    const res = await resp.json();
    isPro = res.is_pro;
    
    if (isPro) {
      if(licenseStatus) licenseStatus.innerHTML = '<span style="color: #34d399; font-weight:600;">Pro Active ✅</span>';
      if(inputLicense) inputLicense.style.display = 'none';
      if(btnActivateLicense) btnActivateLicense.style.display = 'none';
      if(btnBuyLicense) btnBuyLicense.style.display = 'none';
      if(btnDeactivateLicense) btnDeactivateLicense.style.display = 'inline-block';
      
      toggleShortcut.disabled = false;
      btnWatchFolder.disabled = false;
      toggleShortcut.closest('.settings-item').style.opacity = '1';
      btnWatchFolder.closest('.settings-item').style.opacity = '1';
    } else {
      if(licenseStatus) licenseStatus.innerHTML = 'Activate for unlimited uploads.';
      if(inputLicense) inputLicense.style.display = 'inline-block';
      if(btnActivateLicense) btnActivateLicense.style.display = 'inline-block';
      if(btnDeactivateLicense) btnDeactivateLicense.style.display = 'none';
      
      toggleShortcut.disabled = true;
      btnWatchFolder.disabled = true;
      toggleShortcut.closest('.settings-item').style.opacity = '0.5';
      btnWatchFolder.closest('.settings-item').style.opacity = '0.5';
      
      // Add lock icon
      const titles = $$('.settings-text h4');
      titles.forEach(t => {
        if ((t.textContent.includes('Shortcut') || t.textContent.includes('Watch Folder')) && !t.textContent.includes('🔒')) {
          t.innerHTML += ' <span style="font-size:12px; filter:grayscale(1);">🔒</span>';
        }
      });
    }
  } catch (err) { console.error('License fetch failed', err); }
}

if(btnActivateLicense) {
  btnActivateLicense.addEventListener('click', async () => {
    const key = inputLicense.value.trim();
    if(!key) return showToast('Please enter a key', 'error');
    try {
      const resp = await fetch('/api/settings/license', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
      const res = await resp.json();
      if (res.success) {
        showToast('Upgraded to Pro successfully!', 'success');
        checkLicense();
      } else {
        showToast(res.error || 'Invalid License Key', 'error');
      }
    } catch (err) { showToast('Error activating', 'error'); }
  });
}

if(btnDeactivateLicense) {
  btnDeactivateLicense.addEventListener('click', async () => {
    try {
      const resp = await fetch('/api/settings/license', { method: 'DELETE' });
      const res = await resp.json();
      if (res.success) {
        showToast('License deactivated. Reverted to Free tier.', 'info');
        checkLicense(); // reload
      }
    } catch (err) { showToast('Error deactivating', 'error'); }
  });
}

// Removed: Buy Pro functionality


// ── Init ────────────────────────────────────────────────────────────
console.log('[DocAssist] Frontend ready');
renderRecentSearches();
checkLicense();

// Auto-poll library every 10 seconds if the library tab is active
setInterval(() => {
  const activeTab = $('.nav-btn.active').dataset.tab;
  if (activeTab === 'library') {
    console.log('[DocAssist] Auto-refreshing library...');
    loadLibrary();
  }
}, 10000);


// ── Spotlight Mode ───────────────────────────────────────────────────
function toggleSpotlightMode() {
  const isActive = document.body.classList.toggle('spotlight-active');
  if (isActive) {
    // Switch to search tab automatically
    navBtns.forEach((b) => b.classList.remove('active'));
    $('#nav-search').classList.add('active');
    tabPanels.forEach((p) => p.classList.remove('active'));
    $('#tab-search').classList.add('active');
    
    // Smooth focus on search bar
    setTimeout(() => {
      searchInput.focus();
      searchInput.placeholder = "Type to search your brain...";
    }, 450);
  } else {
    searchInput.placeholder = "e.g. Find all mentions of Q3 revenue...";
  }
}

// Global keyboard shortcuts
document.addEventListener('keydown', (e) => {
  // Ctrl+Shift+S to toggle Spotlight manually for testing
  if (e.ctrlKey && e.shiftKey && e.code === 'KeyS') {
    e.preventDefault();
    toggleSpotlightMode();
  }
  
  // ESC to close spotlight
  if (e.code === 'Escape' && document.body.classList.contains('spotlight-active')) {
    toggleSpotlightMode();
  }
});
