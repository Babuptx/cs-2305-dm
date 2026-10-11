import {QuizEngine, readStats, STATS_KEY, SESSION_KEY} from './engine.js';
import {openReference} from './reference.js';
const $ = id => document.getElementById(id);
const make = (tag, value, className) => {const e = document.createElement(tag); if (value != null) e.textContent = value; if (className) e.className = className; return e;};
let storage; try {storage = localStorage;} catch {}
let manifest, busy = false, lastQuestion = null, navBuilt = false;
const status = (message, error = false) => { $('status').textContent = message; $('status').classList.toggle('error', error); };
const engine = new QuizEngine({storage, onChange: render, onComplete: r => {status(r.expired ? 'Time is up. Your block has been submitted once; review every answer below.' : 'Block submitted. Select any question to review your reasoning.'); updateStats();}});
const fmt = seconds => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,'0')}`;
function updateStats() {
  const s = readStats(storage);
  $('overall').textContent = s.total ? `${Math.round(s.correct / s.total * 100)}% · ${s.correct} / ${s.total} correct` : 'No completed blocks yet';
  const block = engine.block && s.byBlock[engine.block.block_id];
  $('attempts').textContent = `${s.completedAttempts} completed attempts.${block ? ` This block: ${block.correct}/${block.total} across ${block.attempts} attempts.` : ' Progress stays in this browser.'}`;
}
function updateNav(s) {
  if (!navBuilt) {
    $('navigation').replaceChildren(...s.navigation.map(n => {const b = make('button'); b.dataset.id = n.id; b.onclick = () => {engine.goTo(n.id); $('workspace').focus();}; return b;})); navBuilt = true;
  }
  for (const n of s.navigation) {
    const b = [...$('navigation').children].find(b => b.dataset.id === n.id);
    b.textContent = `${n.number}${n.answered ? ' ✓' : ''}`;
    b.className = [n.current && 'current', n.answered && 'answered', n.flagged && 'flagged'].filter(Boolean).join(' ');
    b.setAttribute('aria-label', `Question ${n.number}, ${n.answered ? 'answered' : 'unanswered'}${n.flagged ? ', flagged' : ''}`);
    if (n.current) b.setAttribute('aria-current', 'step'); else b.removeAttribute('aria-current');
    if ($('navigation').children[n.number-1] !== b) $('navigation').insertBefore(b,$('navigation').children[n.number-1] || null);
  }
}
function render(s) {
  if (!s) return;
  $('timer').textContent = s.remainingSeconds === null ? `Elapsed ${fmt(s.elapsedSeconds)}` : `${fmt(s.remainingSeconds)} remaining`;
  $('block-title').textContent = s.block.title;
  $('answered').textContent = `${s.navigation.filter(n => n.answered).length} / ${s.questionCount} answered`;
  updateNav(s);
  const signature = JSON.stringify([s.question.id,s.phase,s.showAnswer,s.answer,s.hints]);
  $('position').textContent = `${s.phase === 'review' ? 'REVIEW' : s.mode.toUpperCase()} / QUESTION ${s.questionNumber} OF ${s.questionCount}`;
  $('flag').textContent = s.flagged ? '⚑ Unflag' : '⚑ Flag'; $('flag').setAttribute('aria-pressed', String(s.flagged));
  for (const id of ['flag','shuffle','finish']) $(id).disabled = s.phase !== 'active';
  $('previous').disabled = s.questionNumber === 1; $('next').disabled = s.questionNumber === s.questionCount;
  $('hint').disabled = s.phase !== 'active' || s.mode === 'exam' || s.hints.length >= s.hintCount;
  $('reveal').hidden = s.mode === 'exam'; $('reveal').disabled = s.phase !== 'active' || s.showAnswer;
  $('hint-count').textContent = s.mode === 'exam' ? 'Hints unavailable in exam mode' : `${s.hints.length} / ${s.hintCount} hints used`;
  $('result').hidden = !s.result;
  if (s.result) {const r = s.result; $('result').replaceChildren(make('strong',`${r.percent}% · ${r.correct} / ${r.total}`), make('span',`${r.correct} correct · ${r.incorrect} incorrect · ${r.unanswered} unanswered · ${fmt(s.elapsedSeconds)} elapsed. Use the block map to review.`));}
  if (signature === lastQuestion) return;
  lastQuestion = signature;
  const q = s.question;
  const focusedAnswer = document.activeElement?.name === 'answer' ? document.activeElement.value : null;
  $('tags').replaceChildren(make('span',q.topic,'tag'), make('span',q.difficulty,'tag'));
  $('prompt').textContent = q.prompt; $('context').textContent = q.context || ''; $('context').hidden = !q.context;
  $('exhibit').replaceChildren();
  if (q.has_exhibit) {const img = make('img'); img.src = q.exhibit_url; img.alt = q.exhibit_alt || 'Question exhibit'; img.onerror = () => {img.replaceWith(make('p','Exhibit failed to load. Do not score this item until the exhibit is available.'));}; $('exhibit').append(img);}
  $('choices').replaceChildren(make('legend','Select one answer','sr-only'), ...q.options.map((value,i) => {
    const label = make('label',null,'option'), input = make('input'); input.type = 'radio'; input.name = 'answer'; input.value = i; input.checked = s.answer === i; input.disabled = s.showAnswer || s.phase !== 'active'; input.onchange = () => engine.answer(i);
    let suffix = '';
    if (s.showAnswer && i === q.correct_index) {label.classList.add('correct'); suffix += ' — Correct answer';}
    if (s.showAnswer && i === s.answer) {suffix += ' — Your choice'; if (i !== q.correct_index) label.classList.add('incorrect');}
    label.append(input, make('span',`${String.fromCharCode(65+i)}. ${value}${suffix}`)); return label;
  }));
  $('hints').replaceChildren(...s.hints.map(h => make('li',h)));
  if (focusedAnswer !== null) $('choices').querySelector(`input[value="${focusedAnswer}"]:not(:disabled)`)?.focus();
  $('explanation').hidden = !s.showAnswer; $('explanation').replaceChildren();
  if (s.showAnswer) {
    const e = q.explanation, list = make('ul'); list.append(...e.incorrect_rationales.map(r => make('li',`${String.fromCharCode(65+r.option_index)}. ${q.options[r.option_index]}: ${r.rationale}`)));
    $('explanation').append(make('h3','Reasoning'),make('p',e.correct_rationale),make('p',`Learning objective: ${e.learning_objective}`),make('h3','Why the other choices fail'),list);
    if (q.source_notes?.length) $('explanation').append(make('p',q.source_notes.join(' ')));
  }
}
function populateBlocks() {
  const p = manifest.pillars.find(p => p.id === $('pillar').value);
  $('block').replaceChildren(...p.blocks.map(b => {const o = make('option',`${b.title} · ${b.count} questions`); o.value = b.path; return o;}));
  $('pillar-description').textContent=p.description||'';
  $('pillar-description').hidden=!p.description;
}
async function start(resume = false) {
  if (busy) return;
  if (!resume && engine.state?.phase === 'active' && !confirm('Replace the active block? Its unfinished responses will be cleared.')) return;
  busy = true; $('start').disabled = true; $('resume').disabled = true; status('Loading block…'); navBuilt = false; lastQuestion = null;
  try {
    let path = $('block').value;
    if (resume) {
      const saved = JSON.parse(storage?.getItem(SESSION_KEY) || 'null');
      const p = manifest.pillars.find(p => p.blocks.some(b => b.id === saved?.blockId));
      if (!p) throw Error('Saved block is unavailable.');
      $('pillar').value = p.id; populateBlocks(); path = p.blocks.find(b => b.id === saved.blockId).path; $('block').value = path;
    }
    await engine.loadBlock(path, {mode: $('mode').value, durationSeconds: Number($('duration').value), resume});
    $('mode').value = engine.state.mode;
    status('Block ready. Answer keys remain hidden until reveal or submission.'); updateStats(); $('workspace').focus();
  } catch (e) {
    status(`${e.message} Check your connection and retry Start block.`, true);
    $('prompt').textContent = 'This block could not be loaded.'; $('context').textContent = 'No questions are active. Choose another block or try again.'; $('context').hidden = false;
    for (const id of ['choices','tags','navigation','explanation','hints','exhibit']) $(id).replaceChildren();
    $('result').hidden = true;
    for (const id of ['flag','shuffle','finish','previous','next','hint','reveal']) $(id).disabled = true;
  } finally {busy = false; $('start').disabled = false; $('resume').disabled = false;}
}
$('pillar').onchange = populateBlocks; $('start').onclick = () => start(); $('resume').onclick = () => start(true);
$('flag').onclick = () => engine.toggleFlag(); $('previous').onclick = () => engine.move(-1); $('next').onclick = () => engine.move(1);
$('hint').onclick = () => engine.revealNextHint(); $('reveal').onclick = () => engine.revealAnswer(); $('shuffle').onclick = () => {navBuilt = false; engine.shuffle();};
$('finish').onclick = () => {const s = engine.snapshot(), remaining = s.navigation.filter(n => !n.answered).length; if (confirm(`Submit this block${remaining ? ` with ${remaining} unanswered questions` : ''}? Answers will be locked.`)) engine.submit();};
$('reset').onclick = () => {if (!confirm('Clear all saved attempts and active progress in this browser?')) return; engine.destroy(); engine.state = null; try {storage?.removeItem(STATS_KEY);storage?.removeItem(SESSION_KEY);} catch {} location.reload();};
function setTheme(theme) {document.documentElement.dataset.theme = theme; $('theme').textContent = theme === 'dark' ? 'Light theme' : 'Dark theme'; try {storage?.setItem('dm:theme:v1',theme);} catch {}}
let theme; try {theme = storage?.getItem('dm:theme:v1');} catch {} setTheme(['light','dark'].includes(theme) ? theme : matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
$('theme').onclick = () => setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
$('reference').onclick = () => openReference($('pillar').value==='utd-fall-midterm'); $('close-reference').onclick = () => $('reference-dialog').close();
document.addEventListener('keydown', e => {if (!engine.state || e.target.closest('input,select,textarea,dialog,button') || e.altKey || e.ctrlKey || e.metaKey) return; if (e.key === 'ArrowLeft') {e.preventDefault();engine.move(-1);} if (e.key === 'ArrowRight') {e.preventDefault();engine.move(1);}});
addEventListener('pagehide', () => engine.destroy());
addEventListener('pageshow', e => {if (e.persisted && engine.state?.phase === 'active' && engine.state.deadline !== null) {engine.timer = engine.setIntervalFn(() => engine.tick(),250);engine.tick();}});
try {
  const response = await fetch('data/manifest.json'); if (!response.ok) throw Error(`Inventory fetch failed (${response.status}).`);
  manifest = await response.json();
  if (manifest.version !== 1 || !Array.isArray(manifest.pillars) || !manifest.pillars.length || !manifest.pillars.every(p => typeof p.id === 'string' && typeof p.title === 'string' && Array.isArray(p.blocks) && p.blocks.length && p.blocks.every(b => typeof b.id === 'string' && typeof b.path === 'string' && typeof b.title === 'string' && Number.isInteger(b.count) && b.count > 0))) throw Error('Invalid or empty inventory.');
  $('pillar').replaceChildren(...manifest.pillars.map(p => {const o = make('option',p.title);o.value = p.id;return o;})); populateBlocks();
  $('pillar').disabled = $('block').disabled = $('start').disabled = false;
  try {const saved = JSON.parse(storage?.getItem(SESSION_KEY) || 'null'); $('resume').hidden = !(saved?.version === 1 && manifest.pillars.some(p => p.blocks.some(b => b.id === saved.blockId)));} catch {}
  status(`${manifest.total_questions} questions ready across ${manifest.pillars.length} pillars. Select your next challenge.`);
  $('inventory-summary').textContent=`${manifest.total_questions.toLocaleString()} questions · ${manifest.pillars.length} pillars · ${manifest.pillars.reduce((n,p)=>n+p.blocks.length,0)} blocks.`;
} catch (e) {status(`${e.message} Run the app through a local web server, then reload.`,true);}
updateStats();
