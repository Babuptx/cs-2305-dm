export const STATS_KEY = 'dm:stats:v1';
export const SESSION_KEY = 'dm:session:v1';
const text = x => typeof x === 'string' && x.trim().length > 0;
const browserStorage = () => {try {return globalThis.localStorage;} catch {return undefined;}};
export function validateBlock(block) {
  if (!block || block.schema_version !== 1 || !text(block.block_id) || !text(block.pillar_id) || !text(block.block_title) || !Array.isArray(block.questions) || !block.questions.length) throw Error('Invalid or empty question block.');
  const ids = new Set();
  for (const q of block.questions) {
    if (!text(q.id) || ids.has(q.id)) throw Error('Missing or duplicate question ID.');
    ids.add(q.id);
    if (!text(q.prompt) || !text(q.topic) || !['foundational', 'intermediate', 'advanced'].includes(q.difficulty) || q.question_type !== 'single_choice' || !Array.isArray(q.options) || q.options.length < 2 || !q.options.every(text) || new Set(q.options).size !== q.options.length) throw Error(`Invalid question ${q.id}.`);
    if (!Number.isInteger(q.correct_index) || q.correct_index < 0 || q.correct_index >= q.options.length) throw Error(`Invalid key ${q.id}.`);
    const e = q.explanation;
    if (!Array.isArray(q.hints) || !q.hints.length || !q.hints.every(text) || !e || !text(e.learning_objective) || !text(e.correct_rationale) || !Array.isArray(e.incorrect_rationales)) throw Error(`Missing teaching material ${q.id}.`);
    const expected = q.options.map((_, i) => i).filter(i => i !== q.correct_index);
    if (e.incorrect_rationales.length !== expected.length || new Set(e.incorrect_rationales.map(r => r.option_index)).size !== expected.length || !expected.every(i => e.incorrect_rationales.some(r => r.option_index === i && text(r.rationale)))) throw Error(`Invalid distractor coverage ${q.id}.`);
    if (typeof q.context !== 'string' || !Array.isArray(q.source_notes) || !q.source_notes.length || !q.source_notes.every(text) || typeof q.exhibit_url !== 'string' || typeof q.has_exhibit !== 'boolean' || (q.has_exhibit && !text(q.exhibit_url))) throw Error(`Invalid metadata or exhibit ${q.id}.`);
  }
  return block;
}
export function gradeBlock(questions, answers) {
  let correct = 0, incorrect = 0, unanswered = 0;
  for (const q of questions) {
    if (!Number.isInteger(answers[q.id])) unanswered++;
    else if (answers[q.id] === q.correct_index) correct++;
    else incorrect++;
  }
  return {correct, incorrect, unanswered, total: questions.length, percent: Math.round(100 * correct / questions.length)};
}
export function readStats(storage) {
  const empty = {version: 1, correct: 0, total: 0, completedAttempts: 0, byBlock: {}};
  try {
    const s = JSON.parse(storage?.getItem(STATS_KEY));
    const valid = v => v && ['correct', 'total', 'attempts'].every(k => Number.isInteger(v[k]) && v[k] >= 0) && v.correct <= v.total;
    if (s?.version === 1 && [s.correct, s.total, s.completedAttempts].every(n => Number.isInteger(n) && n >= 0) && s.correct <= s.total && s.byBlock && typeof s.byBlock === 'object' && !Array.isArray(s.byBlock) && Object.values(s.byBlock).every(valid)) return s;
  } catch {}
  return empty;
}
export class QuizEngine {
  constructor({onChange = () => {}, onComplete = () => {}, now = () => Date.now(), storage = browserStorage(), fetcher = (...args) => globalThis.fetch(...args), setIntervalFn = (...args) => globalThis.setInterval(...args), clearIntervalFn = (...args) => globalThis.clearInterval(...args)} = {}) {
    Object.assign(this, {onChange, onComplete, now, storage, fetcher, setIntervalFn, clearIntervalFn});
    this.timer = null; this.generation = 0; this.state = null;
  }
  async loadBlock(url, {mode = 'study', durationSeconds = null, resume = false} = {}) {
    if (!['study', 'exam'].includes(mode)) throw Error('Unknown mode.');
    this.stopTimer(); this.state = null;
    const generation = ++this.generation;
    const response = await this.fetcher(url);
    if (!response.ok) throw Error(`Unable to load questions (${response.status}).`);
    const block = validateBlock(await response.json());
    if (generation !== this.generation) return null;
    this.block = block; this.byId = new Map(block.questions.map(q => [q.id, q]));
    const time = this.now();
    this.state = {phase: 'active', mode, order: [...this.byId.keys()], currentId: block.questions[0].id, answers: {}, flagged: [], revealed: [], hintsShown: {}, started: time, deadline: Number.isFinite(durationSeconds) && durationSeconds > 0 ? time + durationSeconds * 1000 : null, completed: null, result: null};
    if (resume) this.restore();
    if (this.state.phase === 'active' && this.state.deadline !== null) {
      this.timer = this.setIntervalFn(() => this.tick(), 250);
      if (this.remainingSeconds() === 0) return this.submit(true);
    }
    this.emit(); return this.snapshot();
  }
  restore() {
    try {
      const saved = JSON.parse(this.storage?.getItem(SESSION_KEY));
      const s = saved?.state;
      if (saved?.version !== 1 || saved.blockId !== this.block.block_id || !s || !['active', 'review'].includes(s.phase) || !['study', 'exam'].includes(s.mode)) return;
      if (!Array.isArray(s.order) || s.order.length !== this.byId.size || new Set(s.order).size !== this.byId.size || !s.order.every(id => this.byId.has(id)) || !s.order.includes(s.currentId)) return;
      if (!s.answers || typeof s.answers !== 'object' || Array.isArray(s.answers) || !Object.entries(s.answers).every(([id, a]) => this.byId.has(id) && Number.isInteger(a) && a >= 0 && a < this.byId.get(id).options.length)) return;
      if (![s.flagged, s.revealed].every(a => Array.isArray(a) && new Set(a).size === a.length && a.every(id => this.byId.has(id))) || (s.mode === 'exam' && s.revealed.length)) return;
      if (!s.hintsShown || typeof s.hintsShown !== 'object' || !Object.entries(s.hintsShown).every(([id,n]) => this.byId.has(id) && Number.isInteger(n) && n >= 0 && n <= this.byId.get(id).hints.length)) return;
      if (!Number.isFinite(s.started) || s.started > this.now() || (s.deadline !== null && (!Number.isFinite(s.deadline) || s.deadline < s.started)) || (s.phase === 'review' && (!Number.isFinite(s.completed) || s.completed < s.started))) return;
      this.state = s;
      this.state.result = s.phase === 'review' ? gradeBlock(this.block.questions, s.answers) : null;
    } catch {}
  }
  save() { try { this.storage?.setItem(SESSION_KEY, JSON.stringify({version: 1, blockId: this.block.block_id, state: this.state})); } catch {} }
  answer(index) {
    const s = this.state, q = this.byId?.get(s?.currentId);
    if (!q || s.phase !== 'active' || s.revealed.includes(q.id) || !Number.isInteger(index) || index < 0 || index >= q.options.length) return false;
    s.answers[q.id] = index; this.emit(); return true;
  }
  revealAnswer() {
    const s = this.state;
    if (!s || s.mode !== 'study' || s.phase !== 'active') return false;
    if (!s.revealed.includes(s.currentId)) s.revealed.push(s.currentId);
    this.emit(); return true;
  }
  revealNextHint() {
    const s = this.state;
    if (!s || s.phase !== 'active' || s.mode === 'exam') return false;
    const n = s.hintsShown[s.currentId] || 0;
    if (n >= this.byId.get(s.currentId).hints.length) return false;
    s.hintsShown[s.currentId] = n + 1; this.emit(); return true;
  }
  toggleFlag() {
    const s = this.state; if (!s || s.phase !== 'active') return;
    s.flagged = s.flagged.includes(s.currentId) ? s.flagged.filter(id => id !== s.currentId) : [...s.flagged, s.currentId]; this.emit();
  }
  goTo(id) { if (!this.state?.order.includes(id)) return false; this.state.currentId = id; this.emit(); return true; }
  move(delta) { const s = this.state; if (s) this.goTo(s.order[Math.max(0, Math.min(s.order.length - 1, s.order.indexOf(s.currentId) + delta))]); }
  shuffle(random = Math.random) {
    const s = this.state; if (!s || s.phase !== 'active') return;
    for (let i = s.order.length - 1; i > 0; i--) { const j = Math.floor(random() * (i + 1)); [s.order[i], s.order[j]] = [s.order[j], s.order[i]]; }
    this.emit();
  }
  submit(expired = false) {
    const s = this.state; if (!s || s.phase !== 'active') return null;
    this.stopTimer(); s.phase = 'review'; s.completed = this.now(); s.result = gradeBlock(this.block.questions, s.answers);
    const stats = readStats(this.storage), r = s.result;
    const prior = stats.byBlock[this.block.block_id] || {correct: 0, total: 0, attempts: 0};
    stats.correct += r.correct; stats.total += r.total; stats.completedAttempts++;
    stats.byBlock[this.block.block_id] = {correct: prior.correct + r.correct, total: prior.total + r.total, attempts: prior.attempts + 1};
    try { this.storage?.setItem(STATS_KEY, JSON.stringify(stats)); } catch {}
    this.emit(); this.onComplete({...r, expired}); return r;
  }
  remainingSeconds() { return this.state?.deadline == null ? null : Math.max(0, Math.ceil((this.state.deadline - this.now()) / 1000)); }
  tick() { if (this.state?.phase !== 'active') return this.stopTimer(); if (this.remainingSeconds() === 0) this.submit(true); else this.emit(); }
  stopTimer() { if (this.timer !== null) this.clearIntervalFn(this.timer); this.timer = null; }
  destroy() { this.stopTimer(); ++this.generation; }
  snapshot() {
    const s = this.state; if (!s) return null;
    const q = this.byId.get(s.currentId), showAnswer = s.phase === 'review' || s.revealed.includes(q.id);
    const {correct_index, explanation, hints, source_notes, ...display} = q;
    return {block: {id: this.block.block_id, title: this.block.block_title, pillar: this.block.pillar_id}, phase: s.phase, mode: s.mode, question: showAnswer ? {...display, correct_index, explanation, source_notes} : display, showAnswer, hints: hints.slice(0, s.hintsShown[q.id] || 0), hintCount: hints.length, answer: s.answers[q.id] ?? null, flagged: s.flagged.includes(q.id), questionNumber: s.order.indexOf(q.id) + 1, questionCount: s.order.length, remainingSeconds: this.remainingSeconds(), elapsedSeconds: Math.floor(((s.completed ?? this.now()) - s.started) / 1000), result: s.result, navigation: s.order.map((id, i) => ({id, number: i + 1, current: id === s.currentId, answered: Number.isInteger(s.answers[id]), flagged: s.flagged.includes(id)}))};
  }
  emit() { this.save(); this.onChange(this.snapshot()); }
}
