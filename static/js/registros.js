// Registros RAAS — CRUD
function changeMonth() {
    const m = document.getElementById('monthPicker').value;
    window.location.href = '/registros?month=' + m;
}

function toggleGrupo(header) {
    const body = header.nextElementSibling;
    const chevron = header.querySelector('.grupo-chevron');
    const isOpen = body.style.display !== 'none';
    body.style.display = isOpen ? 'none' : '';
    if (chevron) chevron.textContent = isOpen ? '▸' : '▾';
}

function clearRegistroDateSearch() {
    const dateInput = document.getElementById('registroDateSearch');
    if (!dateInput) return;
    dateInput.value = '';
    filterRegistros();
}

function filterRegistros() {
    const nameQ = (document.getElementById('registroSearch')?.value || '').toLowerCase().trim();
    const dateQ = document.getElementById('registroDateSearch')?.value || '';
    const groups = document.querySelectorAll('.registro-group');
    const noMatch = document.getElementById('registroNoMatch');
    let firstMatch = null;
    let matchCount = 0;

    groups.forEach(group => {
        const name = group.dataset.patientName || '';
        const prontuario = group.dataset.patientProntuario || '';
        const nameMatches = !nameQ || name.includes(nameQ) || prontuario.includes(nameQ);

        let dateMatches = !dateQ;
        const rows = group.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const rowMatches = !dateQ || row.dataset.date === dateQ;
            row.style.display = rowMatches ? '' : 'none';
            if (dateQ && row.dataset.date === dateQ) dateMatches = true;
        });

        const matches = nameMatches && dateMatches;
        group.style.display = matches ? '' : 'none';
        if (matches) {
            matchCount++;
            if (!firstMatch) firstMatch = group;
            if (dateQ) {
                const header = group.querySelector('.registro-group-header');
                const body = header.nextElementSibling;
                const chevron = header.querySelector('.grupo-chevron');
                body.style.display = '';
                if (chevron) chevron.textContent = '▾';
            }
        }
    });

    if (noMatch) noMatch.style.display = ((nameQ || dateQ) && matchCount === 0) ? '' : 'none';

    if (firstMatch && nameQ && !dateQ) {
        const header = firstMatch.querySelector('.registro-group-header');
        const body = header.nextElementSibling;
        const chevron = header.querySelector('.grupo-chevron');
        if (body.style.display === 'none') {
            body.style.display = '';
            if (chevron) chevron.textContent = '▾';
        }
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function searchPatient(query) {
    const results = document.getElementById('patientResults');
    const hidden = document.getElementById('form-patient-id');
    const q = (query || '').toLowerCase().trim();

    if (!q) {
        hidden.value = '';
        results.style.display = 'none';
        return;
    }

    const matches = PACIENTES_DATA.filter(p =>
        p.name.toLowerCase().includes(q) ||
        (p.cns && p.cns.includes(q)) ||
        (p.prontuario && p.prontuario.toLowerCase().includes(q))
    ).slice(0, 20);
    results._matches = matches;

    if (matches.length === 0) {
        hidden.value = '';
        results.innerHTML = '<div class="autocomplete-empty">Nenhum paciente encontrado</div>';
        results.style.display = 'block';
        return;
    }

    results.innerHTML = matches.map(p =>
        `<div class="autocomplete-item" data-patient-id="${escapeHtml(p.id)}" data-patient-name="${escapeHtml(p.name)}">
            <div class="item-name">${escapeHtml(p.name)}${p.prontuario ? ` <span style="color:var(--muted);font-weight:600;">- Pront: ${escapeHtml(p.prontuario)}</span>` : ''}</div>
            <div class="item-sub">CNS: ${escapeHtml(p.cns) || 's/doc'} · Mãe: ${escapeHtml(p.motherName) || 's/info'} · Nasc: ${formatBirthDate(p.birthDate)}</div>
        </div>`
    ).join('');
    results.style.display = 'block';
}

function formatBirthDate(iso) {
    if (!iso || iso.length !== 10) return 's/info';
    const [y, m, d] = iso.split('-');
    return `${d}/${m}/${y}`;
}

function clearPatient() {
    document.getElementById('patientSearch').value = '';
    document.getElementById('form-patient-id').value = '';
    document.getElementById('patientResults').style.display = 'none';
    document.getElementById('patientSearch').focus();
}

function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function selectPatient(id, name) {
    document.getElementById('patientSearch').value = name;
    document.getElementById('form-patient-id').value = id;
    document.getElementById('patientResults').style.display = 'none';
}

document.getElementById('patientResults').addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (!item || !item.dataset.patientId) return;
    selectPatient(item.dataset.patientId, item.dataset.patientName);
});

document.getElementById('patientSearch').addEventListener('keydown', (e) => {
    if (e.key !== 'Tab' || e.shiftKey) return;
    const results = document.getElementById('patientResults');
    if (results.style.display === 'none') return;
    const matches = results._matches || [];
    if (matches.length > 0) selectPatient(matches[0].id, matches[0].name);
});

function searchProf(query) {
    const results = document.getElementById('profResults');
    const hidden = document.getElementById('form-professional-id');
    const q = (query || '').toLowerCase().trim();

    if (!q) {
        hidden.value = '';
        results.style.display = 'none';
        return;
    }

    const matches = PROFISSIONAIS_DATA.filter(p => p.name.toLowerCase().includes(q)).slice(0, 20);
    results._matches = matches;

    if (matches.length === 0) {
        hidden.value = '';
        results.innerHTML = '<div class="autocomplete-empty">Nenhum profissional encontrado</div>';
        results.style.display = 'block';
        return;
    }

    results.innerHTML = matches.map(p =>
        `<div class="autocomplete-item" data-prof-id="${escapeHtml(p.id)}" data-prof-name="${escapeHtml(p.name)}" data-prof-cbo="${escapeHtml(p.cbo)}">
            <div class="item-name">${escapeHtml(p.name)}</div>
            <div class="item-sub">${escapeHtml(p.cbo) || 's/CBO'}</div>
        </div>`
    ).join('');
    results.style.display = 'block';
}

function selectProf(id, name, cbo) {
    document.getElementById('profSearch').value = name;
    document.getElementById('form-professional-id').value = id;
    document.getElementById('cboInput').value = cbo || '';
    document.getElementById('profResults').style.display = 'none';
}

function clearProf() {
    document.getElementById('profSearch').value = '';
    document.getElementById('form-professional-id').value = '';
    document.getElementById('cboInput').value = '';
    document.getElementById('profResults').style.display = 'none';
    document.getElementById('profSearch').focus();
}

document.getElementById('profResults').addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (!item || !item.dataset.profId) return;
    selectProf(item.dataset.profId, item.dataset.profName, item.dataset.profCbo);
});

document.getElementById('profSearch').addEventListener('keydown', (e) => {
    if (e.key !== 'Tab' || e.shiftKey) return;
    const results = document.getElementById('profResults');
    if (results.style.display === 'none') return;
    const matches = results._matches || [];
    if (matches.length > 0) selectProf(matches[0].id, matches[0].name, matches[0].cbo);
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('#patientSearch') && !e.target.closest('#patientResults')) {
        document.getElementById('patientResults').style.display = 'none';
    }
    if (!e.target.closest('#profSearch') && !e.target.closest('#profResults')) {
        document.getElementById('profResults').style.display = 'none';
    }
    if (!e.target.closest('.proc-select-group')) {
        document.querySelectorAll('.proc-results').forEach(el => el.style.display = 'none');
    }
});

const MAX_PROC_ROWS = 5;

function searchProc(inputEl) {
    const row = inputEl.closest('.proc-row');
    const results = row.querySelector('.proc-results');
    const hidden = row.querySelector('.proc-hidden-id');
    const q = (inputEl.value || '').toLowerCase().trim();

    if (!q) {
        hidden.value = '';
        results.style.display = 'none';
        return;
    }

    const matches = PROCEDIMENTOS_DATA.filter(p => p.label.toLowerCase().includes(q)).slice(0, 20);
    results._matches = matches;

    if (matches.length === 0) {
        hidden.value = '';
        results.innerHTML = '<div class="autocomplete-empty">Nenhum procedimento encontrado</div>';
        results.style.display = 'block';
        return;
    }

    results.innerHTML = matches.map(p =>
        `<div class="autocomplete-item" data-proc-id="${escapeHtml(p.id)}" data-proc-label="${escapeHtml(p.label)}">
            <div class="item-name">${escapeHtml(p.label)}</div>
        </div>`
    ).join('');
    results.style.display = 'block';
}

// O procedimento de acompanhamento infanto-juvenil exige informar o número
// da autorização no RAAS — o campo fica oculto/desabilitado até ser escolhido.
const AUTH_REQUIRED_PROC_CODE = '03.01.08.038-0';

function updateAuthorizationVisibility() {
    const row = document.getElementById('authorizationRow');
    const input = document.getElementById('authorizationInput');
    if (!row || !input) return;
    const selectedIds = Array.from(document.querySelectorAll('#procRows .proc-hidden-id'))
        .map((el) => el.value)
        .filter(Boolean);
    const needsAuth = selectedIds.some((id) => {
        const proc = PROCEDIMENTOS_DATA.find((p) => p.id === id);
        return proc && proc.code === AUTH_REQUIRED_PROC_CODE;
    });
    row.style.display = needsAuth ? '' : 'none';
    input.disabled = !needsAuth;
    if (!needsAuth) input.value = '';
}

function selectProc(row, id, label) {
    row.querySelector('.proc-search-input').value = label;
    row.querySelector('.proc-hidden-id').value = id;
    row.querySelector('.proc-results').style.display = 'none';
    updateAuthorizationVisibility();
}

function clearProc(btn) {
    const row = btn.closest('.proc-row');
    row.querySelector('.proc-search-input').value = '';
    row.querySelector('.proc-hidden-id').value = '';
    row.querySelector('.proc-results').style.display = 'none';
    row.querySelector('.proc-search-input').focus();
    updateAuthorizationVisibility();
}

document.getElementById('procRows').addEventListener('click', (e) => {
    const item = e.target.closest('.autocomplete-item');
    if (!item || !item.dataset.procId) return;
    const row = item.closest('.proc-row');
    selectProc(row, item.dataset.procId, item.dataset.procLabel);
});

document.getElementById('procRows').addEventListener('keydown', (e) => {
    if (e.key !== 'Tab' || e.shiftKey) return;
    const input = e.target.closest('.proc-search-input');
    if (!input) return;
    const row = input.closest('.proc-row');
    const results = row.querySelector('.proc-results');
    if (results.style.display === 'none') return;
    const matches = results._matches || [];
    if (matches.length > 0) selectProc(row, matches[0].id, matches[0].label);
});

function addProcRow(selectedId = '', qty = 1) {
    const rows = document.getElementById('procRows');
    if (rows.children.length >= MAX_PROC_ROWS) return;
    const idx = rows.children.length;
    const selected = selectedId ? PROCEDIMENTOS_DATA.find(p => p.id === selectedId) : null;
    const div = document.createElement('div');
    div.className = 'proc-row';
    div.innerHTML = `
        <div class="form-group proc-select-group" style="position:relative;">
            <input type="text" class="proc-search-input autocomplete-input" placeholder="Buscar procedimento..." autocomplete="off"
                   value="${selected ? escapeHtml(selected.label) : ''}"
                   oninput="searchProc(this)" onfocus="searchProc(this)"${idx === 0 ? ' required' : ''}>
            <button type="button" class="input-clear-btn" tabindex="-1" onclick="clearProc(this)" title="Limpar seleção">✕</button>
            <input type="hidden" name="procedure_id_${idx}" class="proc-hidden-id" value="${escapeHtml(selectedId)}">
            <div class="proc-results autocomplete-results" style="display:none;"></div>
        </div>
        <div class="form-group proc-qty-group">
            <input type="number" name="quantity_${idx}" min="1" value="${qty}" placeholder="Qtd" tabindex="-1">
        </div>
        <button type="button" class="btn btn-ghost btn-sm proc-remove-btn" tabindex="-1" onclick="removeProcRow(this)"${idx === 0 ? ' style="visibility:hidden;"' : ''}>🗑</button>
    `;
    rows.appendChild(div);
    updateAddProcBtn();
}

function removeProcRow(btn) {
    btn.closest('.proc-row').remove();
    updateAddProcBtn();
    updateAuthorizationVisibility();
}

function updateAddProcBtn() {
    const rows = document.getElementById('procRows');
    const btn = document.getElementById('addProcBtn');
    if (btn.dataset.forceHidden === '1') return;
    btn.style.display = rows.children.length >= MAX_PROC_ROWS ? 'none' : '';
}

function resetProcRows() {
    document.getElementById('procRows').innerHTML = '';
    addProcRow();
}

function todayIso() {
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}

function openModal(id = null) {
    document.getElementById('regModal').style.display = 'flex';
    resetModalPosition();
    document.getElementById('modalTitle').textContent = id ? 'Editar Registro' : 'Novo Registro RAAS';
    document.getElementById('regForm').reset();
    document.getElementById('form-id').value = '';
    document.getElementById('form-patient-id').value = '';
    document.getElementById('patientSearch').value = '';
    document.getElementById('patientResults').style.display = 'none';
    document.getElementById('form-professional-id').value = '';
    document.getElementById('profSearch').value = '';
    document.getElementById('profResults').style.display = 'none';
    resetProcRows();
    updateAuthorizationVisibility();
    const addProcBtn = document.getElementById('addProcBtn');
    addProcBtn.dataset.forceHidden = id ? '1' : '0';
    addProcBtn.style.display = id ? 'none' : '';
    const month = document.getElementById('monthPicker').value;
    document.getElementById('form-month').value = month;
    if (!id) {
        document.querySelector('[name="service_date"]').value = todayIso();
    }
    if (id) {
        fetch(`/api/registros/${id}`).then(r => r.json()).then(r => {
            for (const [k, v] of Object.entries(r)) {
                if (k === 'patient_id') {
                    document.getElementById('form-patient-id').value = v;
                    const p = PACIENTES_DATA.find(p => p.id === v);
                    if (p) document.getElementById('patientSearch').value = p.name;
                    continue;
                }
                if (k === 'professional_id') {
                    document.getElementById('form-professional-id').value = v;
                    const prof = PROFISSIONAIS_DATA.find(p => p.id === v);
                    if (prof) document.getElementById('profSearch').value = prof.name;
                    continue;
                }
                if (k === 'procedure_id') {
                    const row = document.querySelector('#procRows .proc-row');
                    const proc = PROCEDIMENTOS_DATA.find(p => p.id === v);
                    row.querySelector('.proc-hidden-id').value = v;
                    row.querySelector('.proc-search-input').value = proc ? proc.label : '';
                    continue;
                }
                if (k === 'quantity') {
                    document.querySelector('#procRows .proc-row input[type="number"]').value = v;
                    continue;
                }
                const el = document.querySelector(`[name="${k}"]`);
                if (el) el.value = v ?? '';
            }
            updateAuthorizationVisibility();
        });
    }
}

function editReg(id) {
    openModal(id);
}

function closeModal() {
    document.getElementById('regModal').style.display = 'none';
}

async function saveReg(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const id = data.id;
    delete data.id;
    for (const k in data) {
        if (k.startsWith('procedure_id_') || k.startsWith('quantity_')) delete data[k];
    }
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const procRows = Array.from(document.querySelectorAll('#procRows .proc-row')).map(row => ({
        procedure_id: row.querySelector('.proc-hidden-id').value,
        quantity: parseInt(row.querySelector('input[type="number"]').value) || 1,
    })).filter(r => r.procedure_id);

    if (procRows.length === 0) {
        showToast('Selecione ao menos um procedimento', 'error');
        return;
    }

    let resp;
    if (procRows.length > 1 && !id) {
        const payloads = procRows.map(r => ({ ...data, procedure_id: r.procedure_id, quantity: r.quantity }));
        resp = await fetch('/api/registros/varios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payloads)
        });
    } else {
        const payload = { ...data, procedure_id: procRows[0].procedure_id, quantity: procRows[0].quantity };
        const url = id ? `/api/registros/${id}` : '/api/registros/';
        const method = id ? 'PUT' : 'POST';
        resp = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    }

    if (resp.ok) {
        showToast(id ? 'Registro atualizado' : 'Registro(s) criado(s)');
        closeModal();
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao salvar', 'error');
    }
}

async function deleteReg(id) {
    if (!confirm('Excluir este registro?')) return;
    const resp = await fetch(`/api/registros/${id}`, { method: 'DELETE' });
    if (resp.ok) {
        showToast('Registro excluído');
        setTimeout(() => location.reload(), 800);
    }
}

// Caixa "Novo Registro" arrastável — permite manter a lista de pacientes
// visível atrás dela enquanto o profissional preenche o formulário.
function resetModalPosition() {
    const modal = document.querySelector('#regModal .modal');
    if (!modal) return;
    modal.style.position = '';
    modal.style.left = '';
    modal.style.top = '';
    modal.style.margin = '';
}

(function initDraggableRegModal() {
    const modal = document.querySelector('#regModal .modal');
    const header = document.querySelector('#regModal .modal-header');
    if (!modal || !header) return;

    let dragging = false;
    let offsetX = 0;
    let offsetY = 0;

    header.addEventListener('mousedown', (e) => {
        if (e.target.closest('.modal-close')) return;
        const rect = modal.getBoundingClientRect();
        dragging = true;
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;
        modal.style.position = 'fixed';
        modal.style.margin = '0';
        modal.style.left = rect.left + 'px';
        modal.style.top = rect.top + 'px';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
        if (!dragging) return;
        const maxLeft = window.innerWidth - modal.offsetWidth;
        const maxTop = window.innerHeight - modal.offsetHeight;
        const left = Math.max(0, Math.min(e.clientX - offsetX, maxLeft));
        const top = Math.max(0, Math.min(e.clientY - offsetY, maxTop));
        modal.style.left = left + 'px';
        modal.style.top = top + 'px';
    });

    document.addEventListener('mouseup', () => {
        dragging = false;
        document.body.style.userSelect = '';
    });
})();
