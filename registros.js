// Registros RAAS — CRUD
function changeMonth() {
    const m = document.getElementById('monthPicker').value;
    window.location.href = '/registros?month=' + m;
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
        (p.cns && p.cns.includes(q))
    ).slice(0, 20);

    if (matches.length === 0) {
        hidden.value = '';
        results.innerHTML = '<div class="autocomplete-empty">Nenhum paciente encontrado</div>';
        results.style.display = 'block';
        return;
    }

    results.innerHTML = matches.map(p =>
        `<div class="autocomplete-item" onclick="selectPatient('${p.id}')">
            <div class="item-name">${p.name}</div>
            <div class="item-sub">CNS: ${p.cns || 's/doc'}</div>
        </div>`
    ).join('');
    results.style.display = 'block';
}

function selectPatient(id) {
    const p = PACIENTES_DATA.find(p => String(p.id) === String(id));
    document.getElementById('patientSearch').value = p ? p.name : '';
    document.getElementById('form-patient-id').value = id;
    document.getElementById('patientResults').style.display = 'none';
}

document.addEventListener('click', (e) => {
    if (!e.target.closest('#patientSearch') && !e.target.closest('#patientResults')) {
        document.getElementById('patientResults').style.display = 'none';
    }
});

function openModal(id = null) {
    document.getElementById('regModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Registro' : 'Novo Registro RAAS';
    document.getElementById('regForm').reset();
    document.getElementById('form-id').value = '';
    document.getElementById('form-patient-id').value = '';
    document.getElementById('patientSearch').value = '';
    document.getElementById('patientResults').style.display = 'none';
    const month = document.getElementById('monthPicker').value;
    document.getElementById('form-month').value = month;
    if (id) {
        fetch(`/api/registros/${id}`).then(r => r.json()).then(r => {
            for (const [k, v] of Object.entries(r)) {
                if (k === 'patient_id') {
                    document.getElementById('form-patient-id').value = v;
                    const p = PACIENTES_DATA.find(p => String(p.id) === String(v));
                    if (p) document.getElementById('patientSearch').value = p.name;
                    continue;
                }
                const el = document.querySelector(`[name="${k}"]`);
                if (el) el.value = v ?? '';
            }
        });
    }
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
    data.quantity = parseInt(data.quantity) || 1;
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const url = id ? `/api/registros/${id}` : '/api/registros/';
    const method = id ? 'PUT' : 'POST';
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (resp.ok) {
        showToast(id ? 'Registro atualizado' : 'Registro criado');
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
