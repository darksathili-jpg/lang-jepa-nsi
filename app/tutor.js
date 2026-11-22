'use strict';

const $ = (id) => document.getElementById(id);
const els = Object.fromEntries([
  'class', 'statement', 'code', 'highlight', 'line-numbers', 'syntax', 'question', 'history', 'empty',
  'compose', 'send', 'reset', 'feedback', 'stages', 'active-stage', 'model-state',
  'model-identity', 'model-detail', 'jepa-status', 'mode', 'exercise-field', 'exercise', 'objective',
  'pedagogical-objective', 'teacher-panel', 'teacher-content', 'example', 'chat-tools', 'progress-example',
  'jepa-line', 'llm-state', 'llm-line', 'hybrid-badge', 'editor-feedback', 'execute', 'reset-code', 'copy',
  'attach', 'file', 'scene', 'scene-prompt', 'fullscreen', 'settings', 'preferences', 'close-settings', 'parcours-link',
].map((id) => [id, $(id)]));
const labels = ['Comprendre', 'Orienter', 'Expérimenter', 'Débloquer', 'Consolider'];
const themeButtons = [...document.querySelectorAll('button[data-theme]')];
const themeNames = ['light', 'dark', 'projector'];

function useTheme(name) {
  if (!themeNames.includes(name)) name = 'dark';
  const log = els.history;
  const atEnd = log.scrollHeight - log.scrollTop - log.clientHeight < 12;
  document.documentElement.dataset.theme = name;
  for (const button of themeButtons) {
    button.setAttribute('aria-pressed', String(button.dataset.theme === name));
  }
  if (atEnd) log.scrollTop = log.scrollHeight;
  try { localStorage.setItem('nsi-theme', name); } catch { /* Le thème reste actif sans stockage. */ }
}
try { useTheme(localStorage.getItem('nsi-theme')); } catch { useTheme('dark'); }
for (const button of themeButtons) {
  button.addEventListener('click', () => useTheme(button.dataset.theme));
}

const pythonTokens = /(?<comment>#[^\n]*)|(?<string>"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')|(?<keyword>\b(?:def|return|for|while|if|elif|else|in|is|not|and|or|class|try|except|finally|raise|from|import|as|pass|break|continue|None|True|False|with|assert|lambda|yield|global|nonlocal|del|async|await)\b)|(?<number>\b\d+(?:\.\d+)?\b)|(?<definition>(?<=\bdef )[\p{L}_][\p{L}\p{N}_]*)/gu;

function syncEditor() {
  els.highlight.scrollTop = els['line-numbers'].scrollTop = els.code.scrollTop;
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
  els['line-numbers'].textContent = text.split('\n').map((_, index) => index + 1).join('\n') + '\n';
  syncEditor();
}

els.code.addEventListener('input', () => {
  colorCode();
  els.syntax.textContent = '';
  delete els.syntax.dataset.error;
  els['editor-feedback'].hidden = true;
  setScene('ecoute');
});
els.code.addEventListener('scroll', syncEditor);
colorCode();

let session = null;
let turn = 0;
let busy = false;
let engineState = 'standby';
let jepaState = 'inactive';
let originalCode = els.code.value;
let modelRequest = 0;
const paths = {guided: '/api/guide', conversation: '/api/tutor', hybrid: '/api/hybrid'};
const greeting = [...els['scene-prompt'].childNodes].map((node) => node.cloneNode(true));
let catalogue = null;
let catalogueError = false;
const guided = () => els.mode.value === 'guided';

function updateActions() {
  const blocked = engineState !== 'ready' || (els.mode.value === 'hybrid' && jepaState !== 'ready');
  els.send.disabled = busy || (guided() ? !catalogue || !els.exercise.value : blocked);
  els.reset.disabled = busy || turn === 0;
  for (const id of ['class', 'mode', 'exercise', 'reset-code']) els[id].disabled = busy;
  els['hybrid-badge'].hidden = els.mode.value !== 'hybrid' || blocked;
}

async function updateModel() {
  const mode = els.mode.value;
  const request = ++modelRequest;
  const labels = {absent: 'Modèle absent', standby: 'En veille', loading: 'Chargement du modèle',
    ready: 'Modèle prêt', error: 'Erreur du modèle'};
  const jepa = {ready: 'JEPA prêt', absent: 'JEPA absent', error: 'JEPA indisponible', inactive: 'Indisponible'};
  const detail = els['model-detail'];
  try {
    const response = await fetch(mode === 'guided' ? '/api/engines' : '/api/status', {cache: 'no-store'});
    if (!response.ok) throw new Error();
    const status = await response.json();
    if (request !== modelRequest || mode !== els.mode.value) return;
    engineState = status.state;
    jepaState = status.jepa.state;
    els['llm-line'].dataset.state = engineState;
    els['jepa-line'].dataset.state = jepaState;
    els['llm-state'].textContent = labels[engineState];
    els['jepa-status'].textContent = jepa[jepaState];
    els['jepa-status'].title = [status.jepa.name, status.jepa.detail].filter(Boolean).join(' · ');
    els['model-identity'].textContent = status.name + ' · ' + status.quantization;
    els['model-identity'].title = 'Révision ' + status.revision + ' · llama.cpp ' + status.runtime;
    detail.textContent = mode === 'hybrid' && jepaState !== 'ready' ? status.jepa.detail
      : mode !== 'guided' && engineState !== 'ready' ? status.detail : '';
  } catch {
    if (request !== modelRequest || mode !== els.mode.value) return;
    engineState = jepaState = 'error';
    els['llm-line'].dataset.state = els['jepa-line'].dataset.state = 'error';
    els['llm-state'].textContent = 'Service local indisponible';
    els['jepa-status'].textContent = 'JEPA indisponible';
    detail.textContent = 'Ouvre l’atelier avec le lanceur local, puis recharge la page.';
  }
  detail.hidden = !detail.textContent;
  const label = guided() ? catalogue ? 'Parcours prêt' : catalogueError ? 'Exercices indisponibles' : 'Chargement des exercices'
    : els['llm-state'].textContent;
  if (els['model-state'].textContent !== label) els['model-state'].textContent = label;
  updateActions();
}

function showTeacherState(state, jepa) {
  const panel = els['teacher-panel'];
  const content = els['teacher-content'];
  panel.hidden = !state;
  content.replaceChildren();
  if (!state) return;
  const label = (key) => state.libelles_objectifs[key] ?? 'Parcours terminé';
  const evidence = (items) => Object.entries(items).map(([goal, item]) =>
    `${label(goal)} · tour ${item.tour} · ${item.critere}`);
  const add = (title, values) => {
    const heading = document.createElement('dt');
    heading.textContent = title;
    content.append(heading);
    for (const value of values.length ? values : ['Aucun élément consigné']) {
      const item = document.createElement('dd');
      item.textContent = value;
      content.append(item);
    }
  };
  add('Objectif en cours', [state.objectif_libelle]);
  add('Acquis confirmés par les critères de l’exercice', evidence(state.acquis));
  add('Objectifs à démontrer', state.acquis_non_demontres.map(label));
  add('Difficultés relevées', evidence(state.erreurs));
  add('Derniers changements d’objectif', state.changements_objectif.slice(-4).map((item) =>
    `Tour ${item.tour} · ${label(item.avant)} → ${label(item.apres)}`));
  const decision = state.derniere_intervention;
  add('Dernière intervention', decision ? [`${decision.approche} · ${decision.justification}`] : []);
  add('Contribution JEPA', [jepa]);
}

function applyExercise(preview = false) {
  const item = catalogue?.[els.class.value]?.find((exercise) => exercise.id === els.exercise.value);
  if (!item) return;
  els.statement.value = item.statement;
  originalCode = item.code;
  els.code.value = originalCode;
  els.objective.textContent = item.objective;
  colorCode();
  reset(preview);
}

function listExercises(preview = false) {
  if (!catalogue) return;
  const items = catalogue[els.class.value] ?? [];
  const previous = els.exercise.value;
  els.exercise.replaceChildren(...items.map((item) => new Option(item.title, item.id)));
  if (items.some((item) => item.id === previous)) els.exercise.value = previous;
  applyExercise(preview);
}

async function loadExercises() {
  try {
    const response = await fetch('/api/exercises', {cache: 'no-store'});
    if (!response.ok) throw new Error();
    catalogue = await response.json();
    if (guided()) listExercises(true);
  } catch {
    catalogueError = true;
  }
  updateModel();
}

function showStage(stage, state, example = false) {
  els['active-stage'].textContent = 'Niveau d’aide ' + stage + '/5 · ' + labels[stage - 1];
  els['progress-example'].hidden = !example;
  if (example) return;
  const acquisitions = ['Résultat observé', 'Résultat attendu', 'Comportement de m', 'Correction', 'Cas limites'];
  const goals = {observed: 0, expected: 1, trace: 2, assumption: 2, strategy: 3, verification: 3, contract: 4};
  const current = state ? goals[state.objectif] : stage - 1;
  const proved = state ? [state.acquis.observed, state.acquis.expected, state.acquis.trace && state.acquis.assumption,
    state.acquis.verification, state.acquis.contract] : [];
  [...els.stages.children].forEach((step, i) => {
    const name = state ? acquisitions[i] : labels[i];
    const dot = document.createElement('span');
    dot.setAttribute('aria-hidden', 'true');
    step.replaceChildren(dot, name);
    step.dataset.state = proved[i] ? 'done' : i === current ? 'current' : 'pending';
    step.setAttribute('aria-label', name + ' · ' + (proved[i] ? 'acquis' : i === current ? 'en cours' : 'à examiner'));
    if (i === current) step.setAttribute('aria-current', 'step');
    else step.removeAttribute('aria-current');
  });
}

function addMessage(kind, who, parts, provenance = '') {
  const message = document.createElement('article');
  message.className = 'message ' + (kind === 'assistant' ? 'tutor-message assistant' : 'learner');
  message.setAttribute('aria-label', who);
  const icon = els.example.querySelector(kind === 'learner' ? '.learner .avatar' : '.tutor-message .avatar');
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  for (const [style, text] of [...parts, ['provenance', provenance]]) {
    if (!text) continue;
    const paragraph = document.createElement('p');
    paragraph.className = style;
    paragraph.textContent = text;
    bubble.append(paragraph);
  }
  message.append(icon.cloneNode(true), bubble);
  els.history.append(message);
  const live = els.history.querySelectorAll('article.message');
  if (live.length > 60) live[0].remove();
  els.history.scrollTop = els.history.scrollHeight;
}

function displayProvenance(data) {
  const decision = data.pedagogie?.derniere_intervention;
  const reclasse = decision?.source === 'jepa' && decision.differe_des_regles === true;
  const jepa = reclasse ? 'Reclassement JEPA enregistré · ' + decision.modele
    : els.mode.value === 'hybrid' ? 'Aucun reclassement JEPA enregistré pour ce tour.' : data.provenance.jepa;
  const formulation = data.generation === 'affiche' && (data.indice || !data.provenance.question && data.question)
    ? data.provenance.hint
    : data.provenance.hint?.startsWith('Règle pédagogique') ? data.provenance.hint : '';
  return {jepa, source: [formulation, data.provenance.question, jepa].filter(Boolean).join(' · ')};
}

function setScene(pose, status) {
  els.scene.dataset.pose = pose;
  if (status) els['scene-prompt'].textContent = status;
  else els['scene-prompt'].replaceChildren(...greeting.map((node) => node.cloneNode(true)));
}

function editorFeedback(text) {
  els['editor-feedback'].hidden = false;
  els['editor-feedback'].textContent = text;
}

function reset(preview = false) {
  session = null;
  turn = 0;
  els.history.replaceChildren(els.example, els.empty);
  els.example.hidden = !preview;
  els.empty.hidden = preview;
  els['chat-tools'].hidden = true;
  els['editor-feedback'].hidden = true;
  els.feedback.textContent = '';
  els.syntax.textContent = '';
  delete els.syntax.dataset.error;
  els['pedagogical-objective'].hidden = true;
  els['pedagogical-objective'].textContent = '';
  showTeacherState(null);
  els['teacher-panel'].open = false;
  showStage(1, null, preview);
  setScene('accueil');
  updateActions();
}

els.execute.addEventListener('click', () => editorFeedback(
  'Exécution Python indisponible. L’atelier analyse ton code sans exécuter les instructions.'
));
els['reset-code'].addEventListener('click', () => {
  els.code.value = originalCode;
  colorCode();
  reset();
  editorFeedback('Code de départ rétabli.');
});
els.copy.addEventListener('click', async () => {
  try {
    await navigator.clipboard.writeText(els.code.value);
    editorFeedback('Code copié.');
  } catch {
    els.code.focus();
    els.code.select();
    editorFeedback('Utilise Ctrl+C ou ⌘+C pour copier la sélection.');
  }
});
els.attach.addEventListener('click', () => els.file.click());
els.file.addEventListener('change', async () => {
  const [file] = els.file.files;
  els.file.value = '';
  if (!file) return;
  const isPython = /\.py$/i.test(file.name);
  const target = isPython ? els.code : els.question;
  try {
    if (!/\.(py|txt)$/i.test(file.name) || file.size > 16 * 1024) throw new Error();
    const content = await file.text();
    if (content.length > target.maxLength || content.includes('\0')) throw new Error();
    target.value = content;
    target.dispatchEvent(new Event('input'));
    target.focus();
    els.feedback.textContent = isPython ? 'Fichier chargé dans l’éditeur.' : 'Texte chargé dans la réponse.';
    els.feedback.dataset.error = 'false';
  } catch {
    els.feedback.textContent = 'Choisis un fichier texte ou Python qui tient dans le champ.';
    els.feedback.dataset.error = 'true';
  }
});
els.settings.addEventListener('click', () => els.preferences.showModal());
els['close-settings'].addEventListener('click', () => els.preferences.close());
els.fullscreen.addEventListener('click', async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch {
    els.feedback.textContent = 'Le plein écran est indisponible dans ce navigateur.';
  }
});
document.addEventListener('fullscreenchange', () => {
  els.fullscreen.setAttribute('aria-pressed', String(Boolean(document.fullscreenElement)));
});
els['parcours-link'].addEventListener('click', (event) => {
  event.preventDefault();
  if (busy) return;
  if (!guided()) {
    els.mode.value = 'guided';
    els.mode.dispatchEvent(new Event('change'));
  }
  $('exercise-panel').scrollIntoView({block: 'nearest'});
  els.exercise.focus({preventScroll: true});
});
els.question.addEventListener('input', () => { if (!busy) setScene('ecoute'); });
els.question.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    els.compose.requestSubmit();
  }
});

els.reset.addEventListener('click', () => reset());
els.exercise.addEventListener('change', () => applyExercise());
els.class.addEventListener('change', () => {
  if (guided()) listExercises();
  else reset();
});
els.mode.addEventListener('change', () => {
  els['exercise-field'].hidden = !guided();
  reset();
  if (guided()) listExercises();
  updateModel();
});
els.compose.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy || els.send.disabled) return;
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
  els.feedback.textContent = guided() ? 'Sélection d’un indice rédigé.' : 'Le modèle prépare un indice sur cet ordinateur.';
  setScene('reflexion', 'Je regarde ton observation et l’objectif de ton exercice.');
  updateActions();
  try {
    const response = await fetch(paths[els.mode.value], {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({class: els.class.value, exercise: els.exercise.value,
        statement, code, question, session, turn}),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    session = data.session;
    turn = data.turn;
    els.empty.hidden = true;
    els.example.hidden = true;
    els['chat-tools'].hidden = false;
    const {jepa, source} = displayProvenance(data);
    addMessage('learner', 'Toi', [['', question]]);
    addMessage('assistant', 'Professeur virtuel',
      [['', data.feedback], ['', data.indice], ['question', data.question]], source);
    showStage(data.stage, data.pedagogie);
    const objective = els['pedagogical-objective'];
    objective.hidden = !data.pedagogie;
    objective.textContent = data.pedagogie?.objectif_libelle ?? '';
    showTeacherState(data.pedagogie, jepa);
    if (els.code.value === code) {
      els.syntax.dataset.error = String(data.analysis.syntax !== null);
      const diagnosis = data.diagnostic ?? (data.analysis.syntax === null
        ? 'Syntaxe analysée'
        : `Vérifie la syntaxe vers la ligne ${data.analysis.syntax}.`);
      els.syntax.textContent = data.provenance.diagnostic + ' · ' + diagnosis;
      if (data.analysis.syntax !== null) editorFeedback(els.syntax.textContent);
    }
    if (els.question.value.trim() === question) els.question.value = '';
    els.feedback.textContent = guided() ? 'Indice choisi localement.'
      : `Réponse locale en ${data.seconds.toFixed(1).replace('.', ',')} s`;
    const progressed = data.pedagogie?.evaluation.statut === 'correcte';
    setScene(progressed ? 'encouragement' : 'explication', progressed
      ? 'Tu avances ! Garde tes observations et essaie le prochain cas.'
      : 'Regarde la question proposée et ajoute ce que tu observes.');
  } catch (error) {
    els.feedback.dataset.error = 'true';
    els.feedback.textContent = error instanceof TypeError
      ? 'Le service local ne répond plus. Relance l’atelier puis réessaie.'
      : error.message;
    setScene('ecoute');
  } finally {
    busy = false;
    updateActions();
  }
});

showStage(1, null, true);
els['exercise-field'].hidden = !guided();
updateModel();
loadExercises();
setInterval(updateModel, 2500);
