// App — utilidades globais
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('mainContent');
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('show');
    } else {
        sidebar.classList.toggle('collapsed');
        main.classList.toggle('expanded');
    }
}

document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.menu-toggle');
    if (window.innerWidth <= 768 && sidebar.classList.contains('show')) {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('show');
        }
    }
});

function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function filterTable() {
    const q = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('#pacientesTable tbody tr, #profTable tbody tr, #procTable tbody tr');
    rows.forEach(row => {
        const text = (row.dataset.search || row.textContent || '').toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
}

function uppercaseInput(el) {
    const pos = el.selectionStart;
    el.value = el.value.toUpperCase();
    if (pos !== null && typeof el.setSelectionRange === 'function') {
        el.setSelectionRange(pos, pos);
    }
}

function blockEnterSubmit(form) {
    form.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
        }
    });
}

function switchTab(tabId, btn) {
    const target = btn || (typeof event !== 'undefined' ? event.target : null);
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    if (target) target.classList.add('active');
    document.getElementById(tabId).classList.add('active');
}

// Date display
document.addEventListener('DOMContentLoaded', () => {
    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        dateEl.textContent = new Date().toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' });
    }
});
