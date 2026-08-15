// Pacientes — CRUD
const digitOnlyFields = [
    'prontuario',
    'cns',
    'cpf',
    'phone',
    'cell_phone',
    'cep',
    'cnes_usf',
    'authorization_number',
];

function onlyDigits(value) {
    return String(value || '').replace(/\D/g, '');
}

const NATIONALITY_MAP = {
    '010': 'BRASIL', '020': 'NATURALIZADO BRASILEIRO', '021': 'ARGENTINA', '022': 'BOLIVIA',
    '023': 'CHILE', '024': 'PARAGUAI', '025': 'URUGUAI', '030': 'ALEMANHA', '031': 'BELGICA',
    '032': 'REINO UNIDO', '034': 'CANADA', '035': 'ESPANHA', '036': 'ESTADOS UNIDOS',
    '037': 'FRANCA', '038': 'SUICA', '039': 'ITALIA', '041': 'JAPAO', '042': 'CHINA',
    '043': 'COREIA', '045': 'PORTUGAL', '048': 'OUTROS LATINO-AMERICANOS', '049': 'OUTROS ASIATICOS',
    '050': 'OUTROS',
};

const STREET_TYPE_MAP = {
    '004': 'ALAMEDA', '008': 'AVENIDA', '011': 'BECO', '028': 'DISTRITO', '031': 'ESTRADA',
    '037': 'FAZENDA', '081': 'RUA', '090': 'RODOVIA', '092': 'SITIO', '100': 'TRAVESSA',
    '105': 'VIELA',
};

function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

// Digitação livre no formato "CÓD-NOME" (ex: 051-ROMENIA): os 3 primeiros
// dígitos formam o código, o traço é inserido automaticamente, e o restante
// (até 16 caracteres no total) é o nome digitado pelo usuário.
function formatManualCode(raw) {
    const cleaned = String(raw || '').toUpperCase().replace(/-/g, '');
    let code = '';
    let label = '';
    for (const ch of cleaned) {
        if (code.length < 3) {
            if (/[0-9]/.test(ch)) code += ch;
        } else {
            label += ch;
        }
    }
    const formatted = code.length === 3 ? `${code}-${label}` : code;
    return formatted.slice(0, 16);
}

function parseManualCode(formatted) {
    const idx = formatted.indexOf('-');
    if (idx === -1) return { code: formatted, label: '' };
    return { code: formatted.slice(0, idx), label: formatted.slice(idx + 1).trim() };
}

// Combobox com lista estilizada (código + nome) para campos codificados do
// SUS (Nacionalidade, Tipo de Logradouro). Sempre inclui, no início da lista,
// a opção "Digitar código" — clicá-la abre uma pequena caixa de texto dentro
// da própria lista, no mesmo formato dos demais itens, para quem não
// encontrar a opção desejada digitar o código (e opcionalmente o nome)
// manualmente. Enter na busca principal seleciona a primeira opção da lista.
function makeCodedSelect({ inputId, resultsId, hiddenId, clearBtnId, optionsMap, manualPlaceholder }) {
    const input = document.getElementById(inputId);
    const results = document.getElementById(resultsId);
    const hidden = document.getElementById(hiddenId);
    if (!input || !results || !hidden) return;

    const options = Object.entries(optionsMap).map(([code, label]) => ({ code, label }));

    function selectOption(code, label) {
        hidden.value = code;
        input.value = label ? `${code}-${label}` : code;
        results.style.display = 'none';
    }

    function renderManualRow(row) {
        row.innerHTML = `<input type="text" class="manual-code-input" placeholder="${escapeHtml(manualPlaceholder)}" autocomplete="off">`;
        const manualInput = row.querySelector('.manual-code-input');
        manualInput.focus();
        manualInput.addEventListener('click', (e) => e.stopPropagation());
        manualInput.addEventListener('input', () => {
            manualInput.value = formatManualCode(manualInput.value);
        });
        manualInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const { code, label } = parseManualCode(manualInput.value);
                if (code.length !== 3) return;
                selectOption(code, label || optionsMap[code] || null);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                renderResults(input.value);
                input.focus();
            }
        });
    }

    function renderResults(query) {
        const q = (query || '').toLowerCase().trim();
        const matches = q
            ? options.filter(o => `${o.code}-${o.label}`.toLowerCase().includes(q))
            : options;
        results._matches = matches;

        const matchesHtml = matches.map(o =>
            `<div class="autocomplete-item" data-code="${escapeHtml(o.code)}" data-label="${escapeHtml(o.label)}">
                <div class="item-name">${escapeHtml(o.code)} - ${escapeHtml(o.label)}</div>
            </div>`
        ).join('') || `<div class="autocomplete-empty">Nenhuma opção encontrada</div>`;

        results.innerHTML = `<div class="autocomplete-item autocomplete-item-manual" data-manual="1">
            <div class="item-name">✎ Digitar código manualmente</div>
        </div>` + matchesHtml;
        results.style.display = 'block';
    }

    // 'click' cobre o caso de clicar no campo já focado (ex: reabrir a lista
    // após selecionar algo) — só 'focus' não dispara de novo nesse caso.
    input.addEventListener('focus', () => renderResults(''));
    input.addEventListener('click', () => renderResults(''));
    input.addEventListener('input', () => {
        hidden.value = '';
        renderResults(input.value);
    });
    input.addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        e.preventDefault();
        const matches = results._matches || [];
        if (matches.length > 0) selectOption(matches[0].code, matches[0].label);
    });

    results.addEventListener('click', (e) => {
        // Evita que o listener de "clique fora" (no document) avalie e.target
        // depois que renderManualRow() já o desmontou do DOM ao trocar o innerHTML.
        e.stopPropagation();
        const manualRow = e.target.closest('[data-manual]');
        if (manualRow) {
            renderManualRow(manualRow);
            return;
        }
        const item = e.target.closest('.autocomplete-item[data-code]');
        if (item) selectOption(item.dataset.code, item.dataset.label);
    });

    if (clearBtnId) {
        document.getElementById(clearBtnId)?.addEventListener('click', () => {
            input.value = '';
            hidden.value = '';
            input.focus();
            renderResults('');
        });
    }

    document.addEventListener('click', (e) => {
        if (!e.target.closest(`#${inputId}`) && !e.target.closest(`#${resultsId}`)) {
            results.style.display = 'none';
        }
    });
}

let municipioSearchTimer = null;

function searchMunicipio(query) {
    const results = document.getElementById('municipioResults');
    const q = (query || '').trim();
    clearTimeout(municipioSearchTimer);

    if (q.length < 2) {
        results.style.display = 'none';
        return;
    }

    municipioSearchTimer = setTimeout(() => {
        const ufSelect = document.querySelector('select[name="state"]');
        const params = new URLSearchParams({ q });
        if (ufSelect && ufSelect.value) params.set('uf', ufSelect.value);
        fetch(`/api/pacientes/municipios/buscar?${params}`)
            .then(r => r.json())
            .then(matches => {
                results._matches = matches;
                if (matches.length === 0) {
                    results.innerHTML = '<div class="autocomplete-empty">Nenhum município encontrado</div>';
                    results.style.display = 'block';
                    return;
                }
                results.innerHTML = matches.map(m =>
                    `<div class="autocomplete-item" data-codigo="${escapeHtml(m.codigo)}" data-nome="${escapeHtml(m.nome)}" data-uf="${escapeHtml(m.uf)}">
                        <div class="item-name">${escapeHtml(m.nome)}</div>
                        <div class="item-sub">${escapeHtml(m.uf)}</div>
                    </div>`
                ).join('');
                results.style.display = 'block';
            });
    }, 250);
}

function selectMunicipio(codigo, nome, uf) {
    document.getElementById('cityText').value = nome.toUpperCase();
    document.getElementById('municipalityCode').value = codigo;
    const ufSelect = document.querySelector('select[name="state"]');
    if (ufSelect) ufSelect.value = uf;
    document.getElementById('municipioResults').style.display = 'none';
    updateCityDefaultCheck();
}

document.addEventListener('click', (e) => {
    const results = document.getElementById('municipioResults');
    if (!results) return;
    const item = e.target.closest('.autocomplete-item');
    if (item && results.contains(item)) {
        selectMunicipio(item.dataset.codigo, item.dataset.nome, item.dataset.uf);
        return;
    }
    if (!e.target.closest('#cityText') && !e.target.closest('#municipioResults')) {
        results.style.display = 'none';
    }
});

function maskCpf(value) {
    return onlyDigits(value)
        .slice(0, 11)
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

function maskPhone(value) {
    const digits = onlyDigits(value).slice(0, 11);
    return digits.replace(/(\d+)(\d{4})$/, '$1-$2');
}

function isValidCpf(value) {
    const cpf = onlyDigits(value);
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;

    let sum = 0;
    for (let i = 0; i < 9; i++) sum += Number(cpf[i]) * (10 - i);
    let firstDigit = (sum * 10) % 11;
    if (firstDigit === 10) firstDigit = 0;
    if (firstDigit !== Number(cpf[9])) return false;

    sum = 0;
    for (let i = 0; i < 10; i++) sum += Number(cpf[i]) * (11 - i);
    let secondDigit = (sum * 10) % 11;
    if (secondDigit === 10) secondDigit = 0;
    return secondDigit === Number(cpf[10]);
}

function validateCpfField(input, showIncomplete = false) {
    if (!input || input.name !== 'cpf') return true;

    const cpf = onlyDigits(input.value);
    const formGroup = input.closest('.form-group');
    let message = formGroup?.querySelector('.field-error');

    const invalid = cpf.length === 11 && !isValidCpf(cpf);
    const incomplete = showIncomplete && cpf.length > 0 && cpf.length < 11;

    if (!message && formGroup && (invalid || incomplete)) {
        message = document.createElement('div');
        message.className = 'field-error';
        formGroup.appendChild(message);
    }

    input.classList.toggle('input-invalid', invalid || incomplete);
    if (message) {
        message.textContent = invalid ? 'CPF invalido' : (incomplete ? 'CPF incompleto' : '');
    }

    return !invalid && !incomplete;
}

function applyFieldMask(input) {
    if (input.name === 'cpf') {
        input.value = maskCpf(input.value);
        validateCpfField(input);
        return;
    }
    if (input.name === 'phone' || input.name === 'cell_phone') {
        input.value = maskPhone(input.value);
        return;
    }
    input.value = onlyDigits(input.value);
}

function initDigitOnlyInputs(root = document) {
    root.querySelectorAll('[data-digits-only]').forEach((input) => {
        applyFieldMask(input);
        if (input.dataset.digitsBound) return;
        input.dataset.digitsBound = 'true';
        input.addEventListener('input', () => {
            applyFieldMask(input);
        });
        if (input.name === 'cpf') {
            input.addEventListener('blur', () => {
                validateCpfField(input, true);
            });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initDigitOnlyInputs();
    blockEnterSubmit(document.getElementById('pacienteForm'));
    makeCodedSelect({
        inputId: 'nationalityText', resultsId: 'nationalityResults', hiddenId: 'nationalityCode',
        clearBtnId: 'nationalityClearBtn', optionsMap: NATIONALITY_MAP, manualPlaceholder: 'Ex: 051-ROMENIA',
    });
    makeCodedSelect({
        inputId: 'streetTypeText', resultsId: 'streetTypeResults', hiddenId: 'streetTypeCode',
        clearBtnId: 'streetTypeClearBtn', optionsMap: STREET_TYPE_MAP, manualPlaceholder: 'Ex: 999-QUADRA',
    });
});

const checkboxFields = ['alcohol_user', 'crack_user', 'other_drugs_user'];

function updateCityDefaultCheck() {
    const checkbox = document.getElementById('cityDefaultCheck');
    const ufSelect = document.querySelector('select[name="state"]');
    const city = (document.getElementById('cityText').value || '').trim().toUpperCase();
    const uf = ufSelect ? ufSelect.value : '';
    checkbox.checked = !!DEFAULT_CITY && city === DEFAULT_CITY.toUpperCase() && uf === DEFAULT_STATE;
}

// Etnia só faz sentido quando Raça/Cor = Indígena (código 05).
function updateEthnicityField() {
    const raceSelect = document.querySelector('select[name="race"]');
    const ethnicityInput = document.querySelector('input[name="ethnicity"]');
    if (!raceSelect || !ethnicityInput) return;
    const isIndigena = raceSelect.value === '05';
    ethnicityInput.disabled = !isIndigena;
    ethnicityInput.placeholder = isIndigena ? 'Buscar ou digitar...' : 'Disponível apenas para Raça/Cor = Indígena';
    if (!isIndigena) ethnicityInput.value = '';
}

// Aponta o primeiro campo obrigatório vazio, troca para a aba correspondente
// e avisa o usuário — evita falha silenciosa quando o campo está numa aba oculta.
function validateRequiredFields(form) {
    const invalid = Array.from(form.querySelectorAll('[required]')).find((el) => !el.checkValidity());
    if (!invalid) return true;

    const tabContent = invalid.closest('.tab-content');
    if (tabContent && !tabContent.classList.contains('active')) {
        const tabBtn = form.querySelector(`.tab-btn[data-tab="${tabContent.id}"]`);
        if (tabBtn) switchTab(tabContent.id, tabBtn);
    }

    const label = invalid.closest('.form-group')?.querySelector('label')?.textContent?.replace('*', '').trim();
    showToast(`Preencha o campo obrigatório${label ? ': ' + label : ''}`, 'error');
    invalid.focus();
    invalid.reportValidity();
    return false;
}

// Nacionalidade e Tipo de Logradouro aceitam texto livre via datalist, mas o
// valor salvo precisa ser sempre o código numérico de 3 dígitos do SUS — se o
// usuário digitou algo que não bateu com nenhuma opção (código não resolvido
// pelo sync*), bloqueia o salvamento em vez de gravar um código vazio/inválido.
function validateCodedFields(form) {
    const codedInputs = form.querySelectorAll('[data-code-for]');
    for (const textInput of codedInputs) {
        const codeInput = document.getElementById(textInput.dataset.codeFor);
        const hasText = !!textInput.value.trim();
        const hasCode = !!(codeInput && codeInput.value.trim());
        if (!hasText || hasCode) continue;

        const tabContent = textInput.closest('.tab-content');
        if (tabContent && !tabContent.classList.contains('active')) {
            const tabBtn = form.querySelector(`.tab-btn[data-tab="${tabContent.id}"]`);
            if (tabBtn) switchTab(tabContent.id, tabBtn);
        }
        const label = textInput.closest('.form-group')?.querySelector('label')?.textContent?.trim();
        showToast(`${label || 'Campo'}: não reconhecido. Selecione uma opção da lista ou digite o código de 3 dígitos.`, 'error');
        textInput.focus();
        return false;
    }
    return true;
}

function openModal(id = null) {
    document.getElementById('pacienteModal').style.display = 'flex';
    document.getElementById('modalTitle').textContent = id ? 'Editar Paciente' : 'Novo Paciente';
    document.getElementById('pacienteForm').reset();
    document.getElementById('form-id').value = '';
    updateEthnicityField();
    // O checkbox de cidade padrão só faz sentido ao cadastrar um paciente novo.
    const cityDefaultRow = document.getElementById('cityDefaultRow');
    if (cityDefaultRow) cityDefaultRow.style.display = id ? 'none' : '';
    // Lista extra de campos obrigatórios só se aplica ao cadastrar paciente novo —
    // editar um paciente já existente não deve travar por causa de dados antigos incompletos.
    document.querySelectorAll('#pacienteForm [data-required-new]').forEach((el) => {
        el.required = !id;
    });
    if (!id && DEFAULT_CITY) {
        document.getElementById('cityText').value = DEFAULT_CITY;
        document.getElementById('municipalityCode').value = DEFAULT_MUNICIPALITY_CODE;
        const ufSelect = document.querySelector('select[name="state"]');
        if (ufSelect) ufSelect.value = DEFAULT_STATE;
        updateCityDefaultCheck();
    }
    if (id) {
        fetch(`/api/pacientes/${id}`).then(r => r.json()).then(p => {
            for (const [k, v] of Object.entries(p)) {
                if (checkboxFields.includes(k)) {
                    const checkbox = document.querySelector(`input[type="checkbox"][name="${k}"]`);
                    if (checkbox) checkbox.checked = !!v;
                    continue;
                }
                if (k === 'nationality') {
                    const code = (v || '010').padStart(3, '0');
                    const label = NATIONALITY_MAP[code];
                    document.getElementById('nationalityCode').value = v || '010';
                    document.getElementById('nationalityText').value = label ? `${code}-${label}` : (v || '010-BRASIL');
                    continue;
                }
                if (k === 'street_code') {
                    const code = (v || '').padStart(3, '0');
                    const label = STREET_TYPE_MAP[code];
                    document.getElementById('streetTypeCode').value = v || '';
                    document.getElementById('streetTypeText').value = v ? (label ? `${code}-${label}` : v) : '';
                    continue;
                }
                const el = document.querySelector(`[name="${k}"]`);
                if (el) el.value = v || '';
            }
            initDigitOnlyInputs(document.getElementById('pacienteForm'));
            updateCityDefaultCheck();
            updateEthnicityField();

            // Pacientes importados via RAAS/CSV tem municipality_code mas
            // nunca tiveram city/state digitados manualmente - resolve pelo
            // codigo pra nao mostrar Cidade/UF vazias na edicao.
            const cityField = document.getElementById('cityText');
            const codeField = document.getElementById('municipalityCode');
            if (!cityField.value && codeField.value) {
                fetch(`/api/pacientes/municipios/codigo/${codeField.value}`)
                    .then(r => r.ok ? r.json() : null)
                    .then(m => {
                        if (!m) return;
                        cityField.value = m.nome.toUpperCase();
                        const ufSelect = document.querySelector('select[name="state"]');
                        if (ufSelect && !ufSelect.value) ufSelect.value = m.uf;
                        updateCityDefaultCheck();
                    });
            }
        });
    }
}

function editPaciente(id) {
    openModal(id);
}

function closeModal() {
    document.getElementById('pacienteModal').style.display = 'none';
}

async function savePaciente(e) {
    e.preventDefault();
    const form = e.target;
    if (!validateRequiredFields(form)) return;
    if (!validateCodedFields(form)) return;
    // Cidade padrão só se aplica ao cadastrar paciente novo (linha fica oculta na edição).
    const cityDefaultRowVisible = document.getElementById('cityDefaultRow')?.style.display !== 'none';
    const saveCidadePadrao = cityDefaultRowVisible && document.getElementById('cityDefaultCheck')?.checked;
    const cidadePadraoPayload = {
        city: form.querySelector('[name="city"]').value,
        state: form.querySelector('[name="state"]').value,
        municipality_code: form.querySelector('[name="municipality_code"]').value,
    };
    const data = Object.fromEntries(new FormData(form));
    digitOnlyFields.forEach((field) => {
        if (data[field]) data[field] = onlyDigits(data[field]);
    });
    checkboxFields.forEach((field) => {
        if (field in data) data[field] = data[field] === 'true';
    });
    if (data.cpf && !isValidCpf(data.cpf)) {
        validateCpfField(form.querySelector('[name="cpf"]'), true);
        showToast('CPF invalido', 'error');
        return;
    }
    const id = data.id;
    delete data.id;
    for (const k in data) { if (data[k] === '') delete data[k]; }

    const url = id ? `/api/pacientes/${id}` : '/api/pacientes/';
    const method = id ? 'PUT' : 'POST';
    const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });

    if (resp.ok) {
        if (saveCidadePadrao) {
            fetch('/api/pacientes/cidade-padrao', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cidadePadraoPayload),
            });
        }
        showToast(id ? 'Paciente atualizado' : 'Paciente criado com sucesso');
        closeModal();
        setTimeout(() => location.reload(), 800);
    } else {
        const err = await resp.json().catch(() => null);
        const msg = Array.isArray(err?.detail)
            ? err.detail.map((item) => item.msg).join(' ')
            : err?.detail || 'Erro ao salvar paciente';
        showToast(msg, 'error');
    }
}

async function deletePaciente(id) {
    if (!confirm('Excluir este paciente? Esta ação não pode ser desfeita.')) return;
    const resp = await fetch(`/api/pacientes/${id}`, { method: 'DELETE' });
    if (resp.ok) {
        showToast('Paciente excluído');
        setTimeout(() => location.reload(), 800);
    } else {
        showToast('Erro ao excluir', 'error');
    }
}

async function importarPacientesCSV(e) {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    const resp = await fetch('/api/pacientes/importar/csv', { method: 'POST', body: formData });
    const data = await resp.json();
    if (resp.ok) {
        showToast(data.mensagem, 'success');
        setTimeout(() => location.reload(), 1200);
    } else {
        showToast(data.detail || 'Erro ao importar pacientes', 'error');
    }
    e.target.value = '';
}
