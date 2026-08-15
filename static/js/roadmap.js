// Roadmap — CRUD
function openModal(id = null) {
    document.getElementById('itemModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Item' : 'Novo Item';
    document.getElementById('itemForm').reset();
    document.getElementById('form-id').value = '';
    if (id) {
        fetch(`/api/roadmap/${id}`).then(r => r.json()).then(item => {
            for (const [k, v] of Object.entries(item)) {
                const el = document.querySelector(`[name="${k}"]`);
                if (el) {
                    if (el.type === 'checkbox') el.checked = !!v;
                    else el.value = v ?? '';
                }
            }
        });
    }
}

function closeModal() {
    document.getElementById('itemModal').style.display = 'none';
}

async function saveItem(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const id = data.id;
    delete data.id;
    data.done = data.done === 'true';
    data.order = parseInt(data.order) || 0;
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const url = id ? `/api/roadmap/${id}` : '/api/roadmap/';
    const method = id ? 'PUT' : 'POST';
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (resp.ok) {
        showToast(id ? 'Item atualizado' : 'Item criado');
        closeModal();
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao salvar', 'error');
    }
}

async function editItem(id) {
    openModal(id);
}

async function deleteItem(id) {
    if (!confirm('Excluir este item do roadmap?')) return;
    const resp = await fetch(`/api/roadmap/${id}`, { method: 'DELETE' });
    if (resp.ok) {
        showToast('Item excluído');
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao excluir', 'error');
    }
}

async function toggleDone(id) {
    const resp = await fetch(`/api/roadmap/${id}/toggle`, { method: 'PATCH' });
    if (resp.ok) {
        const item = await resp.json();
        const row = document.querySelector(`.roadmap-item[data-id="${id}"]`);
        if (row) {
            const checkbox = row.querySelector('input[type="checkbox"]');
            const title = row.querySelector('.roadmap-title');
            checkbox.checked = item.done;
            if (item.done) title.classList.add('roadmap-done');
            else title.classList.remove('roadmap-done');
        }
        showToast(item.done ? 'Item concluído' : 'Item reaberto');
    } else {
        showToast('Erro ao atualizar', 'error');
    }
}
