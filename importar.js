// Importar RAAS
let selectedFile = null;

function handleFile(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        parseFile(file);
    }
}

function handleDrop(e) {
    e.preventDefault();
    document.querySelector('.drop-zone').classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) {
        selectedFile = file;
        parseFile(file);
    }
}

async function parseFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    try {
        const resp = await fetch('/api/importacao/parse', { method: 'POST', body: formData });
        const data = await resp.json();
        showPreview(data);
    } catch (err) {
        showToast('Erro ao processar arquivo', 'error');
    }
}

function showPreview(data) {
    const section = document.getElementById('previewSection');
    const content = document.getElementById('previewContent');
    const warnings = document.getElementById('warningsBox');

    const resumo = data.resumo || {};
    const pacientes = data.pacientes || [];
    const procedimentos = data.procedimentos || [];
    const profissionais = data.profissionais || [];

    let html = '';

    if (data.header) {
        html += `<div style="background:var(--muted-bg);border-radius:8px;padding:14px;margin-bottom:16px;">
            <strong>Cabeçalho (Registro 01)</strong><br>
            Competência: ${data.header.comp || '—'} · Órgão: ${data.header.organ_name || '—'} · CNES: ${data.header.codcnes || '—'}
        </div>`;
    }

    // Cards de resumo
    html += `<div class="stats-grid" style="margin-bottom:20px;">
        <div class="stat-card stat-primary"><div class="stat-value">${resumo.total_pacientes ?? pacientes.length}</div><div class="stat-label">Pacientes</div></div>
        <div class="stat-card stat-secondary"><div class="stat-value">${resumo.total_procedimentos ?? procedimentos.length}</div><div class="stat-label">Procedimentos</div></div>
        <div class="stat-card stat-accent"><div class="stat-value">${resumo.total_profissionais ?? profissionais.length}</div><div class="stat-label">Profissionais</div></div>
        <div class="stat-card stat-warning"><div class="stat-value">${resumo.total_registros ?? data.records16.length}</div><div class="stat-label">Registros RAAS</div></div>
    </div>`;

    // Abas para alternar entre as três listas
    html += `<div class="import-tabs" style="display:flex;gap:6px;margin-bottom:14px;">
        <button type="button" class="import-tab active" data-tab="pac" onclick="switchImportTab('pac')">👥 Pacientes (${pacientes.length})</button>
        <button type="button" class="import-tab" data-tab="proc" onclick="switchImportTab('proc')">📋 Procedimentos (${procedimentos.length})</button>
        <button type="button" class="import-tab" data-tab="prof" onclick="switchImportTab('prof')">👨‍⚕️ Profissionais (${profissionais.length})</button>
    </div>`;

    // Lista de PACIENTES
    html += `<div class="import-list" id="import-list-pac">
        <table class="data-table"><thead><tr>
            <th>#</th><th>Nome</th><th>CNS</th><th>Nascimento</th><th>Sexo</th><th>CID</th><th>Competência</th>
        </tr></thead><tbody>`;
    pacientes.forEach((p, i) => {
        const nasc = p.nasc && p.nasc.length >= 8 ? `${p.nasc.slice(6,8)}/${p.nasc.slice(4,6)}/${p.nasc.slice(0,4)}` : '—';
        const cmp = p.cmp && p.cmp.length === 6 ? `${p.cmp.slice(4,6)}/${p.cmp.slice(0,4)}` : '—';
        html += `<tr>
            <td>${i+1}</td>
            <td><strong>${p.nome || '—'}</strong></td>
            <td style="font-family:monospace;font-size:12px;">${p.cns || '—'}</td>
            <td>${nasc}</td>
            <td>${p.sexo || '—'}</td>
            <td>${p.cidp || '—'}</td>
            <td>${cmp}</td>
        </tr>`;
    });
    if (!pacientes.length) html += `<tr><td colspan="7" style="text-align:center;color:var(--muted);">Nenhum paciente</td></tr>`;
    html += `</tbody></table></div>`;

    // Lista de PROCEDIMENTOS
    html += `<div class="import-list" id="import-list-proc" style="display:none;">
        <table class="data-table"><thead><tr>
            <th>#</th><th>Código SIGTAP</th><th>Nome do Procedimento</th><th>Ocorrências</th>
        </tr></thead><tbody>`;
    procedimentos.forEach((p, i) => {
        html += `<tr>
            <td>${i+1}</td>
            <td style="font-family:monospace;font-weight:600;">${p.codigo || '—'}</td>
            <td>${p.nome || '<span style="color:var(--muted);font-style:italic;">(sem nome)</span>'}</td>
            <td style="text-align:center;font-weight:600;">${p.ocorrencias || 1}</td>
        </tr>`;
    });
    if (!procedimentos.length) html += `<tr><td colspan="4" style="text-align:center;color:var(--muted);">Nenhum procedimento</td></tr>`;
    html += `</tbody></table></div>`;

    // Lista de PROFISSIONAIS
    html += `<div class="import-list" id="import-list-prof" style="display:none;">
        <table class="data-table"><thead><tr>
            <th>#</th><th>CNS</th><th>CBO</th><th>Cargo</th><th>Atendimentos</th>
        </tr></thead><tbody>`;
    profissionais.forEach((p, i) => {
        html += `<tr>
            <td>${i+1}</td>
            <td style="font-family:monospace;font-size:12px;">${p.cns || '—'}</td>
            <td>${p.cbo || '—'}</td>
            <td>${p.cargo || '—'}</td>
            <td style="text-align:center;font-weight:600;">${p.atendimentos || 1}</td>
        </tr>`;
    });
    if (!profissionais.length) html += `<tr><td colspan="5" style="text-align:center;color:var(--muted);">Nenhum profissional</td></tr>`;
    html += `</tbody></table></div>`;

    content.innerHTML = html;

    if (data.warnings && data.warnings.length > 0) {
        warnings.style.display = 'block';
        warnings.innerHTML = `<div class="alert alert-error" style="margin-top:16px;"><strong>Avisos:</strong><ul style="margin:8px 0 0 20px;">${data.warnings.map(w => `<li>${w}</li>`).join('')}</ul></div>`;
    } else {
        warnings.style.display = 'none';
    }

    section.style.display = 'block';
}

// Alterna entre as listas de pacientes, procedimentos e profissionais
function switchImportTab(tab) {
    document.querySelectorAll('.import-tab').forEach(b => {
        b.classList.toggle('active', b.dataset.tab === tab);
    });
    document.getElementById('import-list-pac').style.display = tab === 'pac' ? 'block' : 'none';
    document.getElementById('import-list-proc').style.display = tab === 'proc' ? 'block' : 'none';
    document.getElementById('import-list-prof').style.display = tab === 'prof' ? 'block' : 'none';
}

async function doImport() {
    if (!selectedFile) return;
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
        const resp = await fetch('/api/importacao/importar', { method: 'POST', body: formData });
        const data = await resp.json();
        showLog(data);
    } catch (err) {
        showToast('Erro ao importar', 'error');
    }
}

function showLog(data) {
    document.getElementById('previewSection').style.display = 'none';
    const section = document.getElementById('logSection');
    const content = document.getElementById('logContent');

    let html = '';
    if (data.stats) {
        html += `<div class="stats-grid" style="margin-bottom:16px;">
            <div class="stat-card stat-primary"><div class="stat-value">${data.stats.pacientes_novos}</div><div class="stat-label">Pacientes Novos</div></div>
            <div class="stat-card stat-secondary"><div class="stat-value">${data.stats.pacientes_atualizados}</div><div class="stat-label">Pacientes Atualizados</div></div>
            <div class="stat-card stat-accent"><div class="stat-value">${data.stats.profissionais_novos}</div><div class="stat-label">Profissionais Novos</div></div>
            <div class="stat-card stat-warning"><div class="stat-value">${data.stats.registros_novos}</div><div class="stat-label">Registros Novos</div></div>
        </div>`;
    }
    if (data.log) {
        html += data.log.map(l => `<div>${l}</div>`).join('');
    }
    content.innerHTML = html;
    section.style.display = 'block';
    showToast('Importação concluída', 'success');
}

function resetImport() {
    selectedFile = null;
    document.getElementById('previewSection').style.display = 'none';
    document.getElementById('logSection').style.display = 'none';
    document.getElementById('fileInput').value = '';
}
