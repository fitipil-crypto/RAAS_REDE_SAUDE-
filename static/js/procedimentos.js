// Procedimentos — CRUD
document.addEventListener('DOMContentLoaded', () => {
    blockEnterSubmit(document.getElementById('procForm'));
});

function openModal(id = null) {
    document.getElementById('procModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Procedimento' : 'Novo Procedimento';
    document.getElementById('procForm').reset();
    document.getElementById('form-id').value = '';
    if (id) {
        fetch(`/api/procedimentos/${id}`).then(r => r.json()).then(p => {
            for (const [k, v] of Object.entries(p)) {
                const el = document.querySelector(`[name="${k}"]`);
                if (el) el.value = v ?? '';
            }
        });
    }
}

function editProc(id) {
    openModal(id);
}

function closeModal() {
    document.getElementById('procModal').style.display = 'none';
}

async function saveProc(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const id = data.id;
    delete data.id;
    data.active = data.active === 'true';
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const url = id ? `/api/procedimentos/${id}` : '/api/procedimentos/';
    const method = id ? 'PUT' : 'POST';
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (resp.ok) {
        showToast(id ? 'Procedimento atualizado' : 'Procedimento criado');
        closeModal();
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao salvar', 'error');
    }
}

async function deleteProc(id) {
    if (!confirm('Excluir este procedimento?')) return;
    const resp = await fetch(`/api/procedimentos/${id}`, { method: 'DELETE' });
    if (resp.ok) {
        showToast('Procedimento excluído');
        setTimeout(() => location.reload(), 800);
    }
}

async function importarProcedimentosCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/api/procedimentos/importar/csv', { method: 'POST', body: formData });
    const data = await resp.json();
    if (resp.ok) {
        showToast(data.mensagem, 'success');
        setTimeout(() => location.reload(), 1200);
    } else {
        showToast(data.detail || 'Erro ao importar procedimentos', 'error');
    }
    e.target.value = '';
}
