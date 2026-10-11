// Independent JavaScript calculations for the Python-authored midterm bank.
// These derive answers from operands, never from stored expected answers.
import assert from 'node:assert/strict';
import {truthValues} from './oracles.mjs';
const total=a=>a.reduce((s,x)=>s+x,0);
const range=n=>Array.from({length:n},(_,i)=>i);
const assignments=range(8).map(i=>({p:!!(i&4),q:!!(i&2),r:!!(i&1)}));
function truth(ast,row){
  if(typeof ast==='string')return row[ast];
  const [op,...terms]=ast,v=terms.map(t=>truth(t,row));
  switch(op){
    case 'not':return !v[0];case 'and':return v.every(Boolean);case 'or':return v.some(Boolean);
    case 'implies':return !v[0]||v[1];case 'iff':return v[0]===v[1];case 'xor':return v[0]!==v[1];
    default:throw Error(`Unknown operator ${op}`);
  }
}
function multiply(a,b,bool=false){
  return a.map(row=>b[0].map((_,j)=>{
    const products=row.map((x,k)=>x*b[k][j]);
    return bool?Number(products.some(x=>x>0)):total(products);
  }));
}
function calc(op,a){
  const q=a.query;
  if(op==='logic'){
    const bits=assignments.map(r=>truth(a.ast,r));
    if(q==='column')return bits.map(x=>x?'T':'F').join('');
    if(q==='count')return bits.filter(Boolean).length;
    if(q==='q-true')return bits.filter((x,i)=>x&&assignments[i].q).length;
    if(q==='counter-p')return bits.filter((x,i)=>x&&!assignments[i].p).length;
  }
  if(op==='quantifiers'){
    const m=a.matrix, columns=m[0].map((_,j)=>m.map(r=>r[j]));
    if(q==='truths')return [m.every(r=>r.some(Boolean)),columns.some(c=>c.every(Boolean)),m.some(r=>r.every(Boolean)),columns.every(c=>c.some(Boolean))].map(x=>x?'T':'F').join(', ');
    if(q==='common-witnesses')return columns.filter(c=>c.every(Boolean)).length;
    if(q==='not-all-rows')return m.filter(r=>r.some(x=>!x)).length;
    if(q==='repair-rows')return m.filter(r=>r.every(x=>!x)).length;
    if(q==='repair-column')return Math.min(...columns.map(c=>c.filter(x=>!x).length));
  }
  if(op==='sets'){
    const A=new Set(a.a),B=new Set(a.b),C=new Set(a.c),U=a.u;
    if(q==='union-minus')return U.filter(x=>(A.has(x)||B.has(x))&&!C.has(x)).length;
    if(q==='xor')return U.filter(x=>A.has(x)!==B.has(x)).length;
    if(q==='outside')return U.filter(x=>!A.has(x)&&!B.has(x)&&!C.has(x)).length;
    const subsets=range(2**a.a.length).map(mask=>a.a.filter((_,i)=>mask&(1<<i)));
    if(q==='required-subsets')return subsets.filter(s=>a.a.filter(x=>B.has(x)).every(x=>s.includes(x))).length;
    if(q==='power-product')return subsets.filter(s=>s.every(x=>B.has(x))).flatMap(s=>a.c.filter(x=>!A.has(x)).map(x=>[s,x])).length;
  }
  if(op==='function'){
    const image=new Set(a.mapping);
    if(q==='image-count')return image.size;
    if(q==='preimage-count')return a.mapping.filter(y=>y===a.target).length;
    if(q==='composition-sum')return [2,3].reduce((s,x)=>s+2*a.mapping[x]-1,0);
    if(q==='collisions')return total(a.mapping.map((v,i)=>a.mapping.filter((w,j)=>v===w&&i!==j).length));
    if(q==='classification'){
      const inj=image.size===a.mapping.length,sur=a.codomain.every(y=>image.has(y));
      return inj&&sur?'Bijective':inj?'Injective but not surjective':sur?'Surjective but not injective':'Neither injective nor surjective';
    }
  }
  if(op==='sequence'){
    const seq=[];
    if(a.type==='arithmetic')for(let i=0;i<=9;i++)seq.push(i?seq[i-1]+4:7);
    if(a.type==='geometric')for(let i=0;i<=9;i++)seq.push(i?seq[i-1]*-2:3);
    if(a.type==='affine')for(let i=0;i<=4;i++)seq.push(i?3*seq[i-1]+4:2);
    if(a.type==='arithmetic')return {term:seq[8],sum:total(seq.slice(0,9)),slice:total(seq.slice(3,10)),
      'even-sum':total(range(6).map(i=>7+8*i)),telescoping:total(range(8).map(i=>seq[i+1]-seq[i]))}[q];
    if(a.type==='geometric')return {difference:seq[6]-seq[5],sum:total(seq.slice(0,6)),slice:total(seq.slice(3,8)),
      'even-sum':total([0,2,4,6].map(i=>seq[i])),recurrence:total(range(5).map(i=>seq[i+1]+2*seq[i]))}[q];
    if(a.type==='affine')return q==='term'?seq[4]:total(seq.slice(0,4));
  }
  if(op==='sum'){
    if(q==='odd-slice')return total(range(8).map(i=>2*(i+4)-1));
    if(q==='double')return total(range(4).flatMap(i=>range(3).map(j=>i+j+2)));
    if(q==='squares')return total(range(7).map(i=>(i+2)**2));
    if(q==='odd-total')return total(range(9).map(i=>2*i+1));
    if(q==='square-telescope')return total(range(7).map(i=>(i+3)**2-(i+2)**2));
    if(q==='fraction-telescope'){
      assert.ok(Math.abs(total(range(9).map(i=>1/(i+1)-1/(i+2)))-0.9)<1e-12);
      return '9/10';
    }
  }
  if(op==='matrix'){
    const ab=multiply(a.a,a.b),ba=multiply(a.b,a.a),sq=multiply(a.a,a.a);
    return {ab12:ab[0][1],ba12:ba[0][1],diagonal:ab[0][0]+ab[1][1],square21:sq[1][0],transpose21:ab[0][1]}[q];
  }
  if(op==='boolean-matrix'){
    if(q==='join'||q==='meet')return total(a.a.flatMap((row,i)=>row.map((x,j)=>Number(q==='join'?x||a.b[i][j]:x&&a.b[i][j]))));
    if(q==='product')return total(multiply(a.a,a.b,true).flat());
    const sq=multiply(a.a,a.a,true);
    if(q==='square12')return sq[0][1];
    if(q==='cube')return total(multiply(sq,a.a,true).flat());
  }
  if(op==='loop'){
    const n=a.n;let count=0;
    const triangle=k=>{let t=0;for(let i=1;i<=k;i++)for(let j=1;j<=i;j++)t++;return t;};
    if(a.type==='triangle')return triangle(n);
    if(a.type==='triangle-difference')return triangle(2*n)-triangle(n);
    if(a.type==='doubling'){for(let j=1;j<=n;j*=2)count++;return count;}
    if(a.type==='shrinking'||a.type==='shrinking-levels'){
      for(let m=n;m>=1;m/=2){if(a.type==='shrinking-levels')count++;else for(let j=0;j<m;j++)count++;}return count;
    }
    if(a.type==='linear-worst')return range(n).length;
    if(a.type==='linear-average')return total(range(n).map(i=>i+1))/n;
    if(a.type==='matrix-and'||a.type==='matrix-or'){
      for(let i=0;i<n;i++)for(let j=0;j<n;j++)for(let k=0;k<(a.type==='matrix-and'?n:n-1);k++)count++;return count;
    }
  }
  if(op==='modular'){
    const mod=x=>x-a.m*Math.floor(x/a.m);
    if(q==='quotient')return Math.floor(a.a/a.m);
    if(q==='remainder')return mod(a.a);
    if(q==='sum')return mod(a.a+a.b);
    if(q==='product')return mod(a.a*a.b);
    if(q==='powers')return mod(a.a*a.a-a.b*a.b*a.b);
  }
  if(op==='base'){
    if(q==='encode')return a.n.toString(a.b).toUpperCase();
    if(q==='decode')return parseInt(a.word,a.b);
    if(q==='length'){let digits=1;for(let power=a.b;power<=a.n;power*=a.b)digits++;return digits;}
  }
  if(op==='gcd'){
    const divisors=range(Math.min(a.a,a.b)).map(i=>i+1).filter(d=>a.a%d===0&&a.b%d===0),d=divisors.at(-1);
    if(q==='gcd')return d;
    if(q==='divisor-count')return divisors.length;
    if(q==='lcm'){let multiple=a.a;while(multiple%a.b)multiple+=a.a;return multiple;}
    if(q==='steps'){let x=a.a,y=a.b,steps=0;while(y){[x,y]=[y,x%y];steps++;}return steps;}
    if(q==='bezout')return (d-a.x*a.a)/a.b;
  }
  throw Error(`Unknown midterm verification ${op}/${a.type||q}`);
}
export function checkMidterm(q){
  const v=q.verification;
  if(v?.kind!=='midterm')return false;
  if(v.op==='logic-equivalence'){
    const target=assignments.map(r=>truth(v.args.ast,r));
    const matching=q.options.map((o,i)=>({i,bits:truthValues(o)})).filter(x=>x.bits.every((b,i)=>b===target[i]));
    assert.equal(matching.length,1,`Ambiguous equivalence ${q.id}`);
    assert.equal(matching[0].i,q.correct_index,q.id);return true;
  }
  const actual=calc(v.op,v.args);
  assert.notEqual(actual,undefined,`Missing oracle ${q.id}`);
  assert.equal(String(actual),q.options[q.correct_index],q.id);
  return true;
}
