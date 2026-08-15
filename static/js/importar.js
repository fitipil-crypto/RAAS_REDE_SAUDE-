// Importar RAAS — grade de até 6 arquivos com status individual + detalhe único
const MAX_ARQUIVOS = 6;

const PILL_META = {
    ok: { cls: 'ok', label: 'Processado' },
    warn: { cls: 'warn', label: 'Com avisos' },
    err: { cls: 'err', label: 'Erro' },
    busy: { cls: 'busy', label: 'Processando…' },
    pending: { cls: 'pending', label: 'Na fila' },
};

let slots = []; // { file, status: pending|busy|ok|warn|err, parsed, error }
let selectedIndex = -1;
let activeTab = 'pac';

function handleFile(e) {
    addFiles(Array.from(e.target.files || []));
}

function handleDrop(e) {
    e.preventDefault();
    document.querySelector('.drop-zone').classList.remove('drag-over');
    addFiles(Array.from(e.dataTransfer.files || []));
}

function addFiles(newFiles) {
    if (!newFiles.length) return;
    const espaco = MAX_ARQUIVOS - slots.length;
    if (newFiles.length > espaco) {
        showToast(`Só é possível adicionar mais ${espaco} arquivo(s) (limite de ${MAX_ARQUIVOS})`, 'error');
        newFiles = newFiles.slice(0, espaco);
    }
    if (!newFiles.length) return;

    const startIndex = slots.length;
    newFiles.forEach(file => slots.push({ file, status: 'pending', parsed: null, error: null }));

    document.getElementById('previewSection').style.display = 'block';
    renderAll();
    newFiles.forEach((file, i) => processSlot(startIndex + i));
}

async function processSlot(index) {
    const slot = slots[index];
    if (!slot) return;
    slot.status = 'busy';
    renderAll();

    const formData = new FormData();
    formData.append('files', slot.file);
    try {
        const resp = await fetch('/api/importacao/parse', { method: 'POST', body: formData });
        if (!resp.ok) throw new Error('Falha ao processar arquivo');
        const data = await resp.json();
        const arq = data.arquivos && data.arquivos[0];
        if (!arq) throw new Error('Resposta inválida do servidor');
        slot.parsed = arq;
        slot.status = (arq.warnings && arq.warnings.length) ? 'warn' : 'ok';
    } catch (err) {
        slot.status = 'err';
        slot.error = err.message || 'Erro ao processar arquivo';
    }

    if (selectedIndex === -1 && (slot.status === 'ok' || slot.status === 'warn')) {
        selectedIndex = index;
    }
    renderAll();
}

function removeSlot(i) {
    slots.splice(i, 1);
    if (selectedIndex === i) {
        selectedIndex = slots.findIndex(s => s.status === 'ok' || s.status === 'warn');
    } else if (selectedIndex > i) {
        selectedIndex -= 1;
    }
    if (!slots.length) {
        resetImport();
        return;
    }
    renderAll();
}

function renderAll() {
    renderSummary();
    renderSlots();
    renderDetail();
    updateConfirmState();
}

function renderSummary() {
    const prontos = slots.filter(s => s.status === 'ok' || s.status === 'warn').map(s => s.parsed.resumo);
    const soma = (chave) => prontos.reduce((acc, r) => acc + (r[chave] || 0), 0);

    document.getElementById('summaryBar').innerHTML = `
        <span class="cap">${slots.length} de ${MAX_ARQUIVOS} arquivos</span>
        <span class="sep">·</span>
        <span class="metric"><b>${soma('total_pacientes')}</b> pacientes</span>
        <span class="sep">·</span>
        <span class="metric"><b>${soma('total_procedimentos')}</b> procedimentos</span>
        <span class="sep">·</span>
        <span class="metric"><b>${soma('total_profissionais')}</b> profissionais</span>
        <span class="sep">·</span>
        <span class="metric"><b>${soma('total_registros')}</b> registros</span>
    `;
}

function renderSlots() {
    const el = document.getElementById('fileSlots');
    el.innerHTML = '';

    slots.forEach((s, i) => {
        const p = PILL_META[s.status];
        const sizeKb = Math.max(1, Math.round(s.file.size / 1024));
        const statsLine = (s.status === 'ok' || s.status === 'warn')
            ? `<div class="file-slot-stats">${s.parsed.resumo.total_pacientes} pac · ${s.parsed.resumo.total_procedimentos} proc · ${s.parsed.resumo.total_registros} reg</div>`
            : (s.status === 'err' ? `<div class="file-slot-stats" style="color:var(--danger);">${s.error}</div>` : '');

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'file-slot' + (i === selectedIndex ? ' selected' : '');
        btn.innerHTML = `
            <div class="file-slot-top">
                <div>
                    <div class="file-slot-name" title="${s.file.name}">${s.file.name}</div>
                    <div class="file-slot-size">${sizeKb} KB</div>
                </div>
                <button type="button" class="file-slot-remove" title="Remover arquivo" aria-label="Remover ${s.file.name}">✕</button>
            </div>
            <span class="status-pill ${p.cls}"><span class="status-pill-dot"></span>${p.label}</span>
            ${statsLine}
        `;
        btn.addEventListener('click', (e) => {
            if (e.target.closest('.file-slot-remove')) return;
            if (s.status === 'ok' || s.status === 'warn') {
                selectedIndex = i;
                activeTab = 'pac';
                renderAll();
            }
        });
        btn.querySelector('.file-slot-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            removeSlot(i);
        });
        el.appendChild(btn);
    });

    for (let i = slots.length; i < MAX_ARQUIVOS; i++) {
        const empty = document.createElement('button');
        empty.type = 'button';
        empty.className = 'file-slot empty';
        empty.innerHTML = `<span class="plus">+</span> Adicionar arquivo`;
        empty.addEventListener('click', () => document.getElementById('fileInput').click());
        el.appendChild(empty);
    }
}

function renderDetail() {
    const area = document.getElementById('detailArea');
    const slot = slots[selectedIndex];

    if (!slot || !(slot.status === 'ok' || slot.status === 'warn')) {
        area.innerHTML = `<div style="text-align:center;color:var(--muted);padding:26px 20px;">Aguardando o processamento para mostrar o detalhe de um arquivo.</div>`;
        return;
    }

    const arq = slot.parsed;
    const header = arq.header || {};
    const p = PILL_META[slot.status];

    let html = `
        <div class="detail-head">
            <div>
                <div class="fname">📄 ${arq.nome}</div>
                <div class="fmeta">Competência: ${header.comp || '—'} · Órgão: ${header.organ_name || '—'} · CNES: ${header.codcnes || '—'}</div>
            </div>
            <span class="status-pill ${p.cls}"><span class="status-pill-dot"></span>${p.label}</span>
        </div>
        <div class="import-tabs">
            <button type="button" class="import-tab ${activeTab === 'pac' ? 'active' : ''}" data-tab="pac">👥 Pacientes (${arq.pacientes.length})</button>
            <button type="button" class="import-tab ${activeTab === 'proc' ? 'active' : ''}" data-tab="proc">📋 Procedimentos (${arq.procedimentos.length})</button>
            <button type="button" class="import-tab ${activeTab === 'prof' ? 'active' : ''}" data-tab="prof">👨‍⚕️ Profissionais (${arq.profissionais.length})</button>
        </div>
        <div class="import-tab-panel" id="importTabPanel"></div>
    `;

    if (arq.warnings && arq.warnings.length > 0) {
        html += `<div class="alert alert-error" style="margin:0 20px 20px;"><strong>Avisos deste arquivo:</strong><ul style="margin:8px 0 0 20px;">${arq.warnings.map(w => `<li>${w}</li>`).join('')}</ul></div>`;
    }

    area.innerHTML = html;
    area.querySelectorAll('.import-tab').forEach(btn => {
        btn.addEventListener('click', () => { activeTab = btn.dataset.tab; renderDetail(); });
    });
    renderTabPanel(arq);
}

function renderTabPanel(arq) {
    const panel = document.getElementById('importTabPanel');
    if (!panel) return;

    if (activeTab === 'pac') {
        let html = `<table class="data-table"><thead><tr><th>#</th><th>Nome</th><th>CNS</th><th>Nascimento</th><th>Sexo</th><th>CID</th><th>Competência</th></tr></thead><tbody>`;
        arq.pacientes.forEach((pac, idx) => {
            const nasc = pac.nasc && pac.nasc.length >= 8 ? `${pac.nasc.slice(6,8)}/${pac.nasc.slice(4,6)}/${pac.nasc.slice(0,4)}` : '—';
            const cmp = pac.cmp && pac.cmp.length === 6 ? `${pac.cmp.slice(4,6)}/${pac.cmp.slice(0,4)}` : '—';
            html += `<tr>
                <td>${idx+1}</td>
                <td><strong>${pac.nome || '—'}</strong></td>
                <td style="font-family:monospace;font-size:12px;">${pac.cns || '—'}</td>
                <td>${nasc}</td>
                <td>${pac.sexo || '—'}</td>
                <td>${pac.cidp || '—'}</td>
                <td>${cmp}</td>
            </tr>`;
        });
        if (!arq.pacientes.length) html += `<tr><td colspan="7" style="text-align:center;color:var(--muted);">Nenhum paciente</td></tr>`;
        panel.innerHTML = html + `</tbody></table>`;
    } else if (activeTab === 'proc') {
        let html = `<table class="data-table"><thead><tr><th>#</th><th>Código SIGTAP</th><th>Nome do Procedimento</th><th>Ocorrências</th></tr></thead><tbody>`;
        arq.procedimentos.forEach((proc, idx) => {
            html += `<tr>
                <td>${idx+1}</td>
                <td style="font-family:monospace;font-weight:600;">${proc.codigo || '—'}</td>
                <td>${proc.nome || '<span style="color:var(--muted);font-style:italic;">(sem nome)</span>'}</td>
                <td style="text-align:center;font-weight:600;">${proc.ocorrencias || 1}</td>
            </tr>`;
        });
        if (!arq.procedimentos.length) html += `<tr><td colspan="4" style="text-align:center;color:var(--muted);">Nenhum procedimento</td></tr>`;
        panel.innerHTML = html + `</tbody></table>`;
    } else {
        let html = `<table class="data-table"><thead><tr><th>#</th><th>CNS</th><th>CBO</th><th>Cargo</th><th>Atendimentos</th></tr></thead><tbody>`;
        arq.profissionais.forEach((prof, idx) => {
            html += `<tr>
                <td>${idx+1}</td>
                <td style="font-family:monospace;font-size:12px;">${prof.cns || '—'}</td>
                <td>${prof.cbo || '—'}</td>
                <td>${prof.cargo || '—'}</td>
                <td style="text-align:center;font-weight:600;">${prof.atendimentos || 1}</td>
            </tr>`;
        });
        if (!arq.profissionais.length) html += `<tr><td colspan="5" style="text-align:center;color:var(--muted);">Nenhum profissional</td></tr>`;
        panel.innerHTML = html + `</tbody></table>`;
    }
}

function updateConfirmState() {
    const btn = document.getElementById('btnConfirmar');
    const aindaProcessando = slots.some(s => s.status === 'busy' || s.status === 'pending');
    const temAlgumPronto = slots.some(s => s.status === 'ok' || s.status === 'warn');
    const desabilitado = aindaProcessando || !temAlgumPronto;
    btn.disabled = desabilitado;
    btn.style.opacity = desabilitado ? '0.5' : '1';
    btn.style.cursor = desabilitado ? 'not-allowed' : 'pointer';
}

async function doImport() {
    const prontos = slots.filter(s => s.status === 'ok' || s.status === 'warn');
    if (!prontos.length) return;

    const formData = new FormData();
    prontos.forEach(s => formData.append('files', s.file));
    try {
        const resp = await fetch('/api/importacao/importar', { method: 'POST', body: formData });
        if (!resp.ok) throw new Error('Falha ao importar');
        const data = await resp.json();
        showLog(data);
    } catch (err) {
        showToast('Erro ao importar', 'error');
    }
}

function showLog(data) {
    document.getElementById('previewSection').style.display = 'none';
    const section = document.getElementById('logSection');
    const statsGeral = data.stats_geral || {};
    const arquivos = data.arquivos || [];

    document.getElementById('logStatsGeral').innerHTML = `
        <div class="stats-grid">
            <div class="stat-card stat-primary"><div class="stat-value">${statsGeral.pacientes_novos || 0}</div><div class="stat-label">Pacientes Novos</div></div>
            <div class="stat-card stat-secondary"><div class="stat-value">${statsGeral.pacientes_atualizados || 0}</div><div class="stat-label">Pacientes Atualizados</div></div>
            <div class="stat-card stat-accent"><div class="stat-value">${statsGeral.profissionais_novos || 0}</div><div class="stat-label">Profissionais Novos</div></div>
            <div class="stat-card stat-warning"><div class="stat-value">${statsGeral.registros_novos || 0}</div><div class="stat-label">Registros Novos</div></div>
        </div>
    `;

    document.getElementById('logContent').innerHTML = arquivos.map(arq => {
        const stats = arq.stats || {};
        let html = `<div style="margin-top:14px;margin-bottom:6px;font-weight:600;">📄 ${arq.nome} — ${stats.registros_novos || 0} registro(s) novo(s), ${stats.registros_ignorados || 0} ignorado(s)</div>`;
        html += (arq.log || []).map(l => `<div>${l}</div>`).join('');
        return html;
    }).join('');

    section.style.display = 'block';
    showToast('Importação concluída', 'success');
}

function resetImport() {
    slots = [];
    selectedIndex = -1;
    activeTab = 'pac';
    document.getElementById('previewSection').style.display = 'none';
    document.getElementById('logSection').style.display = 'none';
    document.getElementById('fileInput').value = '';
}
