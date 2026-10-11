import {readFile, writeFile, access} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {validateBlock} from '../js/engine.js';
import {checkQuestion,verifyRecurrences} from './oracles.mjs';
import {checkMidterm} from './midterm-oracles.mjs';
import Ajv2020 from 'ajv/dist/2020.js';
const read=async path=>JSON.parse(await readFile(path,'utf8'));
const manifest=await read('data/manifest.json'), inventory=await read('data/inventory.json');
const schemaCheck=new Ajv2020({allErrors:true}).compile(await read('data/question.schema.json'));
assert.equal(manifest.version,1);assert.equal(manifest.pillars.length,7);
const midtermId='utd-fall-midterm';
assert.equal(new Set(manifest.pillars.map(p=>p.id)).size,7);
assert.ok(manifest.pillars.some(p=>p.id===midtermId));
const ids=new Set(),questions=[],positions=[0,0,0,0];let checked=0;
for(const pillar of manifest.pillars){
  const expected=pillar.id===midtermId?400:100;
  assert.equal(pillar.blocks.length,expected/50);let count=0;
  for(const entry of pillar.blocks){
    assert.match(entry.path,/^data\/[a-z-]+\/block-0[1-8]\.json$/);
    const block=validateBlock(await read(entry.path));
    assert.ok(schemaCheck(block),`Schema failure ${entry.path}: ${JSON.stringify(schemaCheck.errors)}`);
    assert.equal(block.block_id,entry.id);assert.equal(block.pillar_id,pillar.id);assert.equal(block.questions.length,entry.count);assert.equal(entry.count,50);
    const blockPositions=[0,0,0,0];
    for(const q of block.questions){
      assert.ok(!ids.has(q.id),`Duplicate ID ${q.id}`);ids.add(q.id);questions.push(q);count++;
      positions[q.correct_index]++;blockPositions[q.correct_index]++;
      assert.ok(Array.isArray(q.source_notes)&&q.source_notes.length);
      const allText=[q.prompt,q.context,...q.options,...q.hints,q.explanation.correct_rationale,...q.explanation.incorrect_rationales.map(r=>r.rationale)].join(' ');
      assert.ok(!/\b(TODO|TBD|placeholder|lorem ipsum|sample question)\b|�|Ã|â€/.test(allText),`Placeholder or malformed Unicode ${q.id}`);
      for(const hint of q.hints){assert.ok(hint.length>=20);const answer=q.options[q.correct_index];if(answer.length>30)assert.ok(!hint.includes(answer),`Answer-revealing hint ${q.id}`);}
      if(q.has_exhibit){assert.ok(!q.exhibit_url.startsWith('http'));await access(q.exhibit_url);}
      if(pillar.id===midtermId){
        assert.ok(['intermediate','advanced'].includes(q.difficulty),q.id);
        assert.match(q.curriculum?.section||'',/^(1\.[1345678]|2\.[1-6]|3\.[1-3]|4\.[1-3])$/);
        assert.ok(q.curriculum.odd_exercises.length>0&&q.curriculum.odd_exercises.every(n=>Number.isInteger(n)&&n>0&&n%2===1),q.id);
      }
      if(q.verification?.kind==='midterm'?checkMidterm(q):checkQuestion(q))checked++;
    }
    assert.ok(blockPositions.every(n=>n===12||n===13),`Unbalanced key positions ${entry.id}`);
    const inv=inventory.pillars.find(p=>p.id===pillar.id).blocks.find(b=>b.id===entry.id);inv.validated=50;
  }
  assert.equal(count,expected);inventory.pillars.find(p=>p.id===pillar.id).validated=count;
}
assert.equal(questions.length,1000);assert.equal(manifest.total_questions,1000);
const signatures=new Map();
for(const q of questions){const signature=JSON.stringify([q.context,q.prompt]);assert.ok(!signatures.has(signature),`Duplicate item ${q.id} and ${signatures.get(signature)}`);signatures.set(signature,q.id);}
// Similar prompts and repeated option sets receive an explicit editorial report.
const tokens=q=>{
  const source=(q.context+' '+q.prompt).replace(/Induction coverage may vary by course section\.|Introductory recurrence solving and algorithm analysis may vary by course section\./g,'');
  const words=source.toLowerCase().match(/[\p{L}\p{N}]+|[¬∧∨→↔⊕+−=()]/gu)||[];
  return new Set(words.slice(0,-2).map((_,i)=>words.slice(i,i+3).join(' ')));
};
const tokenized=questions.map(tokens),similar=[],optionSets=new Map();
for(let i=0;i<questions.length;i++){
  const optionKey=JSON.stringify([...questions[i].options].sort());if(!optionSets.has(optionKey))optionSets.set(optionKey,[]);optionSets.get(optionKey).push(questions[i].id);
  for(let j=i+1;j<questions.length;j++){
    if(questions[i].id.split('-')[0]!==questions[j].id.split('-')[0])continue;
    const a=tokenized[i],b=tokenized[j],intersection=[...a].filter(x=>b.has(x)).length;
    const similarity=intersection/(a.size+b.size-intersection);
    if(similarity>=0.8)similar.push({ids:[questions[i].id,questions[j].id],similarity:Number(similarity.toFixed(3))});
  }
}
verifyRecurrences();inventory.validated_questions=questions.length;
await writeFile('data/inventory.json',JSON.stringify(inventory,null,2)+'\n');
const midterm=questions.filter(q=>q.id.startsWith(midtermId+'-'));
const report={questions:questions.length,blocks:manifest.pillars.reduce((n,p)=>n+p.blocks.length,0),pillars:manifest.pillars.length,independent_oracle_items:checked,midterm:{questions:midterm.length,intermediate:midterm.filter(q=>q.difficulty==='intermediate').length,advanced:midterm.filter(q=>q.difficulty==='advanced').length,independent_oracle_items:midterm.filter(q=>q.verification?.kind==='midterm').length},key_positions:positions,similar_context_prompt_pairs:similar,repeated_option_sets:[...optionSets.values()].filter(a=>a.length>1),editorial_note:'Related tasks share case contexts (four in the original pillars, five in the midterm pillar). Similarity and repeated option sets are inspection flags, not proof of duplication. Conceptual and proof explanations have author review, not independent human subject-matter review.'};
await writeFile('data/validation-report.json',JSON.stringify(report,null,2)+'\n');
console.log(`Validated ${report.questions} items / ${report.blocks} blocks / ${report.pillars} pillars; ${checked} oracle checks. Keys: ${positions}.`);
console.log(`Editorial flags: ${similar.length} similar case/prompt pairs; ${report.repeated_option_sets.length} reused option sets. See data/validation-report.json.`);
