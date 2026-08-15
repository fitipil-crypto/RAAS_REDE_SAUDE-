// Profissionais — CRUD
document.addEventListener('DOMContentLoaded', () => {
    blockEnterSubmit(document.getElementById('profForm'));
});

function openModal(id = null) {
    document.getElementById('profModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Profissional' : 'Novo Profissional';
    document.getElementById('profForm').reset();
    document.getElementById('form-id').value = '';
    if (id) {
        fetch(`/api/profissionais/${id}`).then(r => r.json()).then(p => {
            for (const [k, v] of Object.entries(p)) {
                const el = document.querySelector(`[name="${k}"]`);
                if (el) el.value = v ?? '';
            }
        });
    }
}

function editProf(id) {
    openModal(id);
}

function closeModal() {
    document.getElementById('profModal').style.display = 'none';
}

async function saveProf(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const id = data.id;
    delete data.id;
    data.active = data.active === 'true';
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const url = id ? `/api/profissionais/${id}` : '/api/profissionais/';
    const method = id ? 'PUT' : 'POST';
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (resp.ok) {
        showToast(id ? 'Profissional atualizado' : 'Profissional criado');
        closeModal();
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao salvar', 'error');
    }
}

async function deleteProf(id) {
    if (!confirm('Excluir este profissional?')) return;
    const resp = await fetch(`/api/profissionais/${id}`, { method: 'DELETE' });
    if (resp.ok) {
        showToast('Profissional excluído');
        setTimeout(() => location.reload(), 800);
    }
}

async function importarProfissionaisCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/api/profissionais/importar/csv', { method: 'POST', body: formData });
    const data = await resp.json();
    if (resp.ok) {
        showToast(data.mensagem, 'success');
        setTimeout(() => location.reload(), 1200);
    } else {
        showToast(data.detail || 'Erro ao importar profissionais', 'error');
    }
    e.target.value = '';
}
