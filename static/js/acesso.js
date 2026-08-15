// Controle de Acesso — Usuários
function openModal(id = null) {
    document.getElementById('userModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Usuário' : 'Novo Usuário';
    document.getElementById('userForm').reset();
    document.getElementById('form-id').value = '';
    document.getElementById('passwordField').style.display = id ? 'none' : 'block';
    if (id) {
        fetch(`/api/usuarios/${id}`).then(r => r.json()).then(u => {
            document.querySelector('[name="name"]').value = u.name;
            document.querySelector('[name="username"]').value = u.username;
            document.querySelector('[name="role"]').value = u.role;
            document.querySelector('[name="active"]').value = u.active ? 'true' : 'false';
            document.getElementById('form-id').value = u.id;
        });
    }
}

function closeModal() {
    document.getElementById('userModal').style.display = 'none';
}

async function saveUser(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const id = data.id;
    delete data.id;
    data.active = data.active === 'true';
    if (id) {
        delete data.password;
        const resp = await fetch(`/api/usuarios/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (resp.ok) { showToast('Usuário atualizado'); closeModal(); setTimeout(() => location.reload(), 800); }
        else { showToast('Erro ao atualizar', 'error'); }
    } else {
        const resp = await fetch('/api/usuarios/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (resp.ok) { showToast('Usuário criado'); closeModal(); setTimeout(() => location.reload(), 800); }
        else { const err = await resp.json(); showToast(err.detail || 'Erro ao criar', 'error'); }
    }
}

async function deleteUser(id) {
    if (!confirm('Excluir este usuário? Esta ação não pode ser desfeita.')) return;
    const resp = await fetch(`/api/usuarios/${id}`, { method: 'DELETE' });
    if (resp.ok) { showToast('Usuário excluído'); setTimeout(() => location.reload(), 800); }
    else { const err = await resp.json(); showToast(err.detail || 'Erro', 'error'); }
}

function changePassword(userId, userName) {
    document.getElementById('passModal').style.display = 'flex';
    document.getElementById('passModalTitle').textContent = `Alterar Senha — ${userName}`;
    document.getElementById('pass-user-id').value = userId;
    document.getElementById('passForm').reset();
    const currentField = document.getElementById('currentPassField');
    currentField.style.display = (userId === currentUserId) ? 'block' : 'none';
}

function changeOwnPassword() {
    changePassword(currentUserId, currentUserName);
}

function closePassModal() {
    document.getElementById('passModal').style.display = 'none';
}

async function savePassword(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    const userId = data.user_id;
    delete data.user_id;
    if (!data.current_password) delete data.current_password;

    const resp = await fetch(`/api/usuarios/${userId}/senha`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (resp.ok) { showToast('Senha alterada'); closePassModal(); }
    else { const err = await resp.json(); showToast(err.detail || 'Erro', 'error'); }
}

const currentUserId = document.querySelector('.user-badge')?.dataset?.userId || '';
const currentUserName = document.querySelector('.user-name')?.textContent || '';
