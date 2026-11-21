'use strict';

const $ = (id) => document.getElementById(id);
const els = Object.fromEntries([
  'class', 'statement', 'code', 'highlight', 'syntax', 'question', 'history', 'empty',
  'compose', 'send', 'reset', 'feedback', 'stages', 'active-stage', 'model-state',
  'model-identity', 'model-detail',
].map((id) => [id, $(id)]));
const labels = ['Comprendre', 'Orienter', 'Expérimenter', 'Débloquer', 'Consolider'];
const themeButtons = [...document.querySelectorAll('button[data-theme]')];
const themeNames = ['light', 'dark', 'projector'];

function useTheme(name) {
  if (!themeNames.includes(name)) name = 'light';
  const log = els.history;
  const atEnd = log.scrollHeight - log.scrollTop - log.clientHeight < 12;
  document.documentElement.dataset.theme = name;
  for (const button of themeButtons) {
    button.setAttribute('aria-pressed', String(button.dataset.theme === name));
  }
  if (atEnd) log.scrollTop = log.scrollHeight;
  try { localStorage.setItem('nsi-theme', name); } catch { /* Le thème reste actif sans stockage. */ }
}
try { useTheme(localStorage.getItem('nsi-theme')); } catch { useTheme('light'); }
for (const button of themeButtons) {
  button.addEventListener('click', () => useTheme(button.dataset.theme));
}

const pythonTokens = /(?<comment>#[^\n]*)|(?<string>"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(?<keyword>\b(?:def|return|for|while|if|elif|else|in|is|not|and|or|class|try|except|finally|raise|from|import|as|pass|break|continue|None|True|False|with|assert|lambda|yield|global|nonlocal|del|async|await)\b)|(?<number>\b\d+(?:\.\d+)?\b)/g;

function syncEditor() {
  els.highlight.scrollTop = els.code.scrollTop;
  els.highlight.scrollLeft = els.code.scrollLeft;
}

function colorCode() {
  const text = els.code.value;
  const fragment = document.createDocumentFragment();
  let start = 0;
  for (const token of text.matchAll(pythonTokens)) {
    fragment.append(text.slice(start, token.index));
    const span = document.createElement('span');
    span.className = 'token-' + Object.keys(token.groups).find((kind) => token.groups[kind] !== undefined);
    span.textContent = token[0];
    fragment.append(span);
    start = token.index + token[0].length;
  }
  fragment.append(text.slice(start) + '\n');
  els.highlight.replaceChildren(fragment);
  syncEditor();
}

els.code.addEventListener('input', () => {
  colorCode();
  els.syntax.textContent = '';
  delete els.syntax.dataset.error;
});
els.code.addEventListener('scroll', syncEditor);
colorCode();

let history = [];
let busy = false;
let engineState = 'loading';

function updateActions() {
  els.send.disabled = busy || engineState !== 'ready';
  els.reset.disabled = busy || history.length === 0;
  els.class.disabled = busy;
  els.send.textContent = busy ? 'Génération en cours…' : 'Demander un indice';
}

async function updateModel() {
  try {
    const response = await fetch('/api/status', {cache: 'no-store'});
    if (!response.ok) throw new Error();
    const status = await response.json();
    const states = {
      absent: 'Modèle absent', loading: 'Chargement du modèle',
      ready: 'Modèle prêt', error: 'Erreur du modèle',
    };
    engineState = status.state;
    const label = states[status.state];
    if (els['model-state'].textContent !== label) els['model-state'].textContent = label;
    els['model-state'].dataset.state = status.state;
    els['model-identity'].textContent = `${status.name} · ${status.quantization} · ${status.revision.slice(0, 8)}`;
    els['model-identity'].title = `Révision ${status.revision} · llama.cpp ${status.runtime}`;
    els['model-detail'].textContent = status.detail;
  } catch {
    engineState = 'error';
    els['model-state'].textContent = 'Service local indisponible';
    els['model-state'].dataset.state = 'error';
    els['model-detail'].textContent = 'Ouvre l’atelier depuis le lanceur local, puis recharge cette page.';
  } finally {
    updateActions();
  }
}

function showStage(stage) {
  els['active-stage'].textContent = `Niveau d’aide ${stage}/5 · ${labels[stage - 1]}`;
  [...els.stages.children].forEach((step, index) => {
    if (stage - 1 === index) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  });
}

function addMessage(kind, who, ...parts) {
  const message = document.createElement('article');
  message.className = 'message ' + kind;
  const name = document.createElement('strong');
  name.textContent = who;
  message.append(name);
  for (const text of parts) {
    const paragraph = document.createElement('p');
    paragraph.textContent = text;
    message.append(paragraph);
  }
  els.history.append(message);
  els.history.scrollTop = els.history.scrollHeight;
}

function reset() {
  history = [];
  els.history.replaceChildren(els.empty);
  els.empty.hidden = false;
  els.feedback.textContent = '';
  els.syntax.textContent = '';
  delete els.syntax.dataset.error;
  showStage(1);
  updateActions();
}

els.reset.addEventListener('click', reset);
els.class.addEventListener('change', reset);
els.compose.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || engineState !== 'ready') return;
  const question = els.question.value.trim();
  const statement = els.statement.value.trim();
  if (!statement || !question) {
    els.feedback.dataset.error = 'true';
    els.feedback.textContent = 'Renseigne un énoncé et une question.';
    return;
  }
  const code = els.code.value;
  busy = true;
  els.feedback.dataset.error = 'false';
  els.feedback.textContent = 'Le modèle prépare un indice sur cet ordinateur.';
  updateActions();
  try {
    const response = await fetch('/api/tutor', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({class: els.class.value, statement, code, question, history: history.slice(-3)}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    els.empty.hidden = true;
    addMessage('learner', 'Toi', question);
    addMessage('assistant', 'Professeur virtuel', data.indice, data.question);
    history.push({
      learner: question,
      assistant: data.indice + ' ' + data.question,
      stage: data.stage,
      digest: data.analysis.digest,
    });
    showStage(data.stage);
    if (els.code.value === code) {
      els.syntax.dataset.error = String(data.analysis.syntax !== null);
      els.syntax.textContent = data.analysis.syntax === null
        ? 'Syntaxe analysée'
        : `Vérifie la syntaxe vers la ligne ${data.analysis.syntax}.`;
    }
    if (els.question.value.trim() === question) els.question.value = '';
    els.feedback.textContent = `Réponse locale en ${data.seconds.toFixed(1).replace('.', ',')} s`;
  } catch (error) {
    els.feedback.dataset.error = 'true';
    els.feedback.textContent = error instanceof TypeError
      ? 'Le service local ne répond plus. Relance l’atelier puis réessaie.'
      : error.message;
  } finally {
    busy = false;
    updateActions();
  }
});

showStage(1);
updateModel();
setInterval(updateModel, 3500);
