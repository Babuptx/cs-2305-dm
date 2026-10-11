import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {checkMidterm} from '../scripts/midterm-oracles.mjs';
const read=async p=>JSON.parse(await readFile(new URL(p,import.meta.url),'utf8'));
const manifest=await read('../data/manifest.json');
const pillar=manifest.pillars.find(p=>p.id==='utd-fall-midterm');
const blocks=await Promise.all(pillar.blocks.map(b=>read('../'+b.path)));
const questions=blocks.flatMap(b=>b.questions);
test('midterm contains 400 items across the 19 mapped sections, with odd-exercise study pointers',()=>{
  assert.equal(blocks.length,8);assert.equal(questions.length,400);
  assert.equal(questions.filter(q=>q.difficulty==='intermediate').length,240);
  assert.equal(questions.filter(q=>q.difficulty==='advanced').length,160);
  const sections=['1.1','1.3','1.4','1.5','1.6','1.7','1.8','2.1','2.2','2.3','2.4','2.5','2.6','3.1','3.2','3.3','4.1','4.2','4.3'];
  assert.deepEqual([...new Set(questions.map(q=>q.curriculum.section))].sort(),sections);
  for(const q of questions)assert.ok(q.curriculum.odd_exercises.every(n=>n>0&&n%2===1));
});
test('independent midterm calculations reject every deliberately corrupted key',()=>{
  const verified=questions.filter(q=>q.verification?.kind==='midterm');
  assert.ok(verified.length>=140);
  for(const q of verified){
    assert.equal(checkMidterm(q),true,q.id);
    assert.throws(()=>checkMidterm({...q,correct_index:(q.correct_index+1)%4}),undefined,q.id);
  }
});
test('publication sources contain no PDF embeds or local course paths',async()=>{
  const [html,reference]=await Promise.all(['../index.html','../js/reference.js'].map(p=>readFile(new URL(p,import.meta.url),'utf8')));
  assert.ok(!/(?:src|href)=["'][^"']*(?:\.pdf|refer\/)/i.test(html+reference));
  assert.ok(!/C:\\Users\\|OneDrive/.test(JSON.stringify(questions)));
});
