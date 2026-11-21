'use strict';
const questions=[{q:'Que prédit principalement LANG-JEPA ?',options:['Le prochain token','Une représentation vectorielle','Une correction Python'],correct:1,explain:'Il prédit la représentation de la phrase suivante dans un espace latent.'},{q:'Un LLM utilise-t-il des vecteurs ?',options:['Oui','Non'],correct:0,explain:'Les LLM utilisent également des représentations vectorielles internes.'},{q:'LANG-JEPA est-il déjà un professeur de NSI validé ?',options:['Oui','Non, ses capacités doivent être évaluées'],correct:1,explain:'Il faut disposer de checkpoints entraînés et mesurer ses performances pédagogiques.'}];
const root=document.getElementById('questions');let answers={};
questions.forEach((q,i)=>{const field=document.createElement('fieldset');const legend=document.createElement('legend');legend.textContent=`${i+1}. ${q.q}`;field.append(legend);q.options.forEach((opt,j)=>{const label=document.createElement('label'),radio=document.createElement('input');radio.type='radio';radio.name=`q${i}`;radio.value=j;radio.addEventListener('change',()=>{answers[i]=j;const n=Object.keys(answers).length;document.getElementById('score').textContent=n===questions.length?`Résultat : ${questions.filter((v,k)=>answers[k]===v.correct).length}/${questions.length}. ${questions.map((v,k)=>v.explain).join(' ')}`:`${n}/${questions.length} réponses.`});label.append(radio,document.createTextNode(' '+opt));field.append(label)});root.append(field)});
document.getElementById('theme').addEventListener('click',()=>{const active=document.body.classList.toggle('dark');document.getElementById('theme').textContent=active?'Mode clair':'Mode sombre'});
const tutorRequest = document.getElementById('tutor-request');
tutorRequest.addEventListener('submit', (event) => event.preventDefault());

document.getElementById('diagnostic').addEventListener('click', () => {
  document.getElementById('status').textContent =
    'Tuteur indisponible. Dans ce laboratoire, aucun checkpoint LANG-JEPA n’est connecté.';
});
