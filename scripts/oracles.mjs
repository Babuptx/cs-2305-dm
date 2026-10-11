// Independent calculations: the generator uses Python; these checks use JS
// truth parsing, exhaustive enumeration, graph search, and recurrence unrolling.
import assert from 'node:assert/strict';
export function truthValues(expression) {
  const tokens = expression.match(/[pqr]|[()¬∧∨→↔⊕]/g);
  const precedence = {'↔':1,'→':2,'∨':3,'⊕':4,'∧':5};
  function evaluate(values) {
    let pos=0;
    function atom() {
      const t=tokens[pos++];
      if(t==='¬') return !atom();
      if(t==='(') {const v=expr(1);assert.equal(tokens[pos++],')');return v;}
      assert.ok(t in values);return values[t];
    }
    function expr(min) {
      let left=atom();
      while(precedence[tokens[pos]]>=min) {
        const op=tokens[pos++], right=expr(precedence[op]+(op==='→'?0:1));
        left=op==='∧'?left&&right:op==='∨'?left||right:op==='⊕'?left!==right:op==='→'?!left||right:left===right;
      }
      return left;
    }
    const result=expr(1);assert.equal(pos,tokens.length);return result;
  }
  return Array.from({length:8},(_,i)=>evaluate({p:!!(i&4),q:!!(i&2),r:!!(i&1)}));
}
function factorial(n) {let x=1;for(let i=2;i<=n;i++)x*=i;return x;}
function combinations(n,r) {if(r<0||r>n)return 0;let result=1;for(let i=1;i<=r;i++)result=result*(n-i+1)/i;return Math.round(result);}
export function countExpression(source) {
  const tokens=source.match(/\d+|\*\*|[()+\-*/ ,]|C|P|fact/g).filter(t=>t.trim()&&t!==' '); let pos=0;
  function primary() {
    const t=tokens[pos++];
    if(t==='('){const v=expression();assert.equal(tokens[pos++],')');return v;}
    if(['C','P','fact'].includes(t)){
      assert.equal(tokens[pos++],'(');const a=expression();let b;
      if(tokens[pos]===','){pos++;b=expression();}assert.equal(tokens[pos++],')');
      return t==='C'?combinations(a,b):t==='P'?factorial(a)/factorial(a-b):factorial(a);
    }
    assert.match(t,/^\d+$/);return Number(t);
  }
  function power(){const a=primary();if(tokens[pos]==='**'){pos++;return a**power();}return a;}
  function product(){let a=power();while(['*','/'].includes(tokens[pos])){const op=tokens[pos++],b=power();a=op==='*'?a*b:a/b;}return a;}
  function expression(){let a=product();while(['+','-'].includes(tokens[pos])){const op=tokens[pos++],b=product();a=op==='+'?a+b:a-b;}return a;}
  const result=expression();assert.equal(pos,tokens.length);return result;
}
const sameSet=(a,b)=>a.length===b.length&&a.every(x=>b.includes(x));
function adjacency(n,edges){const adj=Array.from({length:n},()=>[]);for(const[a,b]of edges){adj[a].push(b);adj[b].push(a);}return adj;}
function components(n,edges){const adj=adjacency(n,edges),seen=new Set(),groups=[];for(let start=0;start<n;start++){if(seen.has(start))continue;const group=[],todo=[start];while(todo.length){const v=todo.pop();if(seen.has(v))continue;seen.add(v);group.push(v);todo.push(...adj[v]);}groups.push(group);}return groups;}
function distances(n,edges,start){const adj=adjacency(n,edges),dist=Array(n).fill(Infinity),todo=[start];dist[start]=0;while(todo.length){const v=todo.shift();for(const w of adj[v])if(dist[w]===Infinity){dist[w]=dist[v]+1;todo.push(w);}}return dist;}
function graphQuery(v) {
  const{n,edges,query}=v,adj=adjacency(n,edges),groups=components(n,edges);
  if(query==='edges')return adj.reduce((s,x)=>s+x.length,0)/2;
  if(query==='components')return groups.length;
  if(query==='largest-component')return Math.max(...groups.map(x=>x.length));
  if(query==='degree-sum')return adj.reduce((s,x)=>s+x.length,0);
  if(query==='diameter')return Math.max(...Array.from({length:n},(_,i)=>distances(n,edges,i)).flat());
  if(query==='distance-0-last')return distances(n,edges,0)[n-1];
  if(query==='triangles'){let total=0;for(let a=0;a<n;a++)for(let b=a+1;b<n;b++)for(let c=b+1;c<n;c++)if(adj[a].includes(b)&&adj[a].includes(c)&&adj[b].includes(c))total++;return total;}
  if(query==='bridges')return edges.filter((_,i)=>components(n,edges.filter((_,j)=>i!==j)).length>groups.length).length;
  if(query==='girth')return Math.min(...edges.map(([a,b],i)=>distances(n,edges.filter((_,j)=>i!==j),a)[b]+1));
  if(query==='matching'){let best=0;for(let mask=0;mask<2**edges.length;mask++){const used=new Set();let valid=true,count=0;for(let i=0;i<edges.length;i++)if(mask&(1<<i)){const[a,b]=edges[i];if(used.has(a)||used.has(b)){valid=false;break;}used.add(a);used.add(b);count++;}if(valid)best=Math.max(best,count);}return best;}
  if(query==='vertex-cover'){let best=n;for(let mask=0;mask<2**n;mask++)if(edges.every(([a,b])=>(mask&(1<<a))||(mask&(1<<b))))best=Math.min(best,mask.toString(2).split('1').length-1);return best;}
  if(query==='spanning-trees'){let count=0;for(let mask=0;mask<2**edges.length;mask++){const selected=edges.filter((_,i)=>mask&(1<<i));if(selected.length===n-1&&components(n,selected).length===1)count++;}return count;}
  if(query==='chromatic'){for(let k=1;k<=n;k++){const colors=Array(n).fill(-1);function assign(i){if(i===n)return true;for(let color=0;color<k;color++)if(adj[i].every(j=>j>=i||colors[j]!==color)){colors[i]=color;if(assign(i+1))return true;}colors[i]=-1;return false;}if(assign(0))return k;}}
  throw Error(`Unknown graph query ${query}`);
}
const recurrenceKeys = [
 ['16','aₙ=4+3n','3','4+3(n−1)+3=4+3n'],
 ['96','bₙ=3·2ⁿ','2','Replace b₀=3 by b₀=6'],
 ['15','cₙ=2ⁿ−1','dₙ=cₙ+1','−1'],
 ['15','aₙ=n(n+1)/2','1','Σᵢ₌₁ⁿ i'],
 ['36','aₙ=n²','n²−(n−1)²=2n−1','Θ(n²)'],
 ['14','Σᵢ₌₁ⁿ i²','n(n+1)(2n+1)/6','Θ(n³)'],
 ['24','fₙ=n!','It is the identity for an empty product','n'],
 ['13','2','r²−r−1=0','The recurrence also uses n−2'],
 ['12','r²−2r−1=0','1+√2 and 1−√2','29'],
 ['5','aₙ=n','(r−1)²','A+Bn'],
 ['17','1 and 2','aₙ=1+2ⁿ','Θ(2ⁿ)'],
 ['−1','aₙ=(−1)ⁿ','2','No, its even and odd subsequences have different limits'],
 ['0','−1','aₙ=((−1)ⁿ−1)/2','Each consecutive odd/even pair sums to 0'],
 ['11','11','a₂ₖ=2+3k','a₂ₖ₊₁=5+3k'],
 ['−1','4','r²+1=0','i and −i'],
 ['256','aₙ=2^(2ⁿ)','The previous term is squared','bₙ=2bₙ₋₁'],
 ['1/4','aₙ=1/(n+1)','bₙ=bₙ₋₁+1','0'],
 ['7/8','aₙ=1−2^(−n)','1','eₙ=eₙ₋₁/2'],
 ['15','Nₕ=2^(h+1)−1','It counts the new root','2ʰ'],
 ['5','T(n)=log₂n','Every recursive argument remains an integer and reaches 1 exactly','Θ(log n)'],
 ['24','T(n)=n log₂n','n','Θ(n log n)'],
 ['15','T(n)=2n−1','n','Θ(n)'],
 ['32','T(n)=n² log₂n','n²','Θ(n² log n)'],
 ['10','n','The cost of each level is its current argument','Θ(n²)'],
 ['15','2ⁿ','2ⁿ−1','The base is a palindrome and each step mirrors equal palindrome halves around 1'],
];
export function verifyRecurrences() {
  const linear=(base,step,n)=>{const a=[...base];for(let i=a.length;i<=n;i++)a.push(step(a,i));return a;};
  const cases=[
    [[4],(a,i)=>a[i-1]+3,n=>4+3*n],[[3],(a,i)=>2*a[i-1],n=>3*2**n],
    [[0],(a,i)=>2*a[i-1]+1,n=>2**n-1],[[0],(a,i)=>a[i-1]+i,n=>n*(n+1)/2],
    [[0],(a,i)=>a[i-1]+2*i-1,n=>n*n],[[0],(a,i)=>a[i-1]+i*i,n=>n*(n+1)*(2*n+1)/6],
    [[1],(a,i)=>i*a[i-1],factorial],[[0,1],(a,i)=>a[i-1]+a[i-2],null],
    [[0,1],(a,i)=>2*a[i-1]+a[i-2],n=>((1+Math.SQRT2)**n-(1-Math.SQRT2)**n)/(2*Math.SQRT2)],
    [[0,1],(a,i)=>2*a[i-1]-a[i-2],n=>n],[[2,3],(a,i)=>3*a[i-1]-2*a[i-2],n=>1+2**n],
    [[1],(a,i)=>-a[i-1],n=>(-1)**n],[[0],(a,i)=>a[i-1]+(-1)**i,n=>((-1)**n-1)/2],
    [[2,5],(a,i)=>a[i-2]+3,n=>n%2?5+3*((n-1)/2):2+3*(n/2)],
    [[1,2],(a,i)=>-a[i-2],n=>[1,2,-1,-2][n%4]],
    [[2],(a,i)=>a[i-1]**2,n=>2**(2**n)],
    [[1],(a,i)=>a[i-1]/(1+a[i-1]),n=>1/(n+1)],
    [[0],(a,i)=>(a[i-1]+1)/2,n=>1-2**(-n)],
    [[1],(a,i)=>2*a[i-1]+1,n=>2**(n+1)-1],
  ];
  for(const[base,step,formula]of cases){const seq=linear(base,step,8);if(formula)for(let n=0;n<=8;n++)assert.ok(Math.abs(seq[n]-formula(n))<=Math.max(1,Math.abs(seq[n]))*1e-10);}
  assert.equal(linear([0,1],(a,i)=>a[i-1]+a[i-2],7)[7],13);
  for(const[mult,cost,base,formula]of [[1,()=>1,0,n=>Math.log2(n)],[2,n=>n,0,n=>n*Math.log2(n)],[2,()=>1,1,n=>2*n-1],[4,n=>n*n,0,n=>n*n*Math.log2(n)]]){
    const t=n=>n===1?base:mult*t(n/2)+cost(n);for(let n=1;n<=256;n*=2)assert.equal(t(n),formula(n));
  }
  let word='0';for(let n=0;n<8;n++){assert.equal(word,word.split('').reverse().join(''));assert.equal(word.length,2**(n+1)-1);assert.equal(word.split('0').length-1,2**n);assert.equal(word.split('1').length-1,2**n-1);word=word+'1'+word;}
}
export function checkQuestion(q) {
  const v=q.verification;if(!v)return false;
  const key=q.options[q.correct_index];
  let actual;
  if(v.kind==='dnf-equivalence'){assert.deepEqual(truthValues(key),truthValues(v.expression),q.id);return true;}
  if(v.kind==='arithmetic-case'){
    const gcd=(a,b)=>b?gcd(b,a%b):Math.abs(a);
    const residues=(m,fn)=>Array.from({length:m},(_,i)=>i).filter(fn);
    const divisors=n=>Array.from({length:n},(_,i)=>i+1).filter(d=>n%d===0);
    const mod=(a,m)=>((a%m)+m)%m;
    const keys=[
      [mod(-17,5),Math.floor(-17/5),'(4,5)','The remainder is outside 0≤r<6'],
      [gcd(84,30),'6=3·30−84',84*30/gcd(84,30),divisors(gcd(84,30)).length],
      [divisors(360).length,3,Math.max(...divisors(360).filter(n=>Number.isInteger(Math.sqrt(n)))),gcd(360,84)],
      [mod(19+25,7),mod(19*25,7),mod(19-25,7),-2],
      [residues(11,x=>mod(3*x,11)===1)[0],residues(11,x=>mod(3*x,11)===7)[0],'gcd(3,11)=1',residues(11,x=>mod(10*x,11)===1)[0]],
      ['x≡'+residues(8,x=>mod(2*x,8)===4).join(' or '),'2 has no inverse modulo 8',residues(8,x=>mod(2*x,8)===3).length,residues(8,x=>mod(4*x,8)===0).length],
      [mod(2**10,5),mod(3**4,5),mod(4**9,5),mod(5**20,5)],
      [residues(15,x=>x%3===2&&x%5===3)[0],15,23,'It fails the modulo 3 condition'],
      ['7 divides 0','It is false','a|bc implies a|b or a|c for arbitrary a','2|n'],
      [gcd(14,15),14*15/gcd(14,15),'(n+1)−n','It is even'],
      [divisors(91).find(x=>x>1&&x<91),'√91','2,3,5,7',divisors(91).length],
      [gcd(35,12),residues(12,x=>mod(35*x,12)===1)[0],'1=3·12−35','x≡y (mod 12)'],
    ];
    assert.equal(String(keys[v.case][v.query]).replaceAll('-','−'),key,q.id);return true;
  }
  if(['truth-column','truth-count','negated-truth-count'].includes(v.kind)){
    const bits=truthValues(v.expression);
    actual=v.kind==='truth-column'?bits.map(x=>x?'T':'F').join(''):bits.filter(x=>v.kind==='truth-count'?x:!x).length;
    assert.equal(actual,v.expected,q.id);assert.equal(String(actual),key,q.id);return true;
  }
  if(v.kind==='count-expression'){actual=countExpression(v.expression);assert.equal(actual,v.expected,q.id);assert.equal(String(actual),key,q.id);return true;}
  if(v.kind==='set-operation'){
    const union=[...new Set([...v.a,...v.b])];
    actual=v.operation==='A∪B'?union:v.operation==='A∩B'?v.a.filter(x=>v.b.includes(x)):v.operation==='A\\B'?v.a.filter(x=>!v.b.includes(x)):union.filter(x=>v.a.includes(x)!==v.b.includes(x));
    assert.ok(sameSet(actual,v.expected),q.id);return true;
  }
  if(v.kind==='map-classification'){
    const image=[...new Set(Object.values(v.mapping))],inj=image.length===v.domain.length,sur=sameSet(image,v.codomain);
    actual=inj&&sur?'Bijective':inj?'Injective but not surjective':sur?'Surjective but not injective':'Neither injective nor surjective';
    assert.equal(actual,key,q.id);return true;
  }
  if(v.kind==='map-image'||v.kind==='map-preimage'){actual=v.kind==='map-image'?[...new Set(Object.values(v.mapping))]:Object.keys(v.mapping).filter(x=>v.mapping[x]===v.target);assert.ok(sameSet(actual,v.expected),q.id);return true;}
  if(v.kind==='relation-property'){
    const has=(a,b)=>v.pairs.some(([x,y])=>x===a&&y===b),u=v.universe;
    actual=v.property==='reflexive'?u.every(a=>has(a,a)):v.property==='symmetric'?u.every(a=>u.every(b=>!has(a,b)||has(b,a))):v.property==='antisymmetric'?u.every(a=>u.every(b=>!has(a,b)||!has(b,a)||a===b)):u.every(a=>u.every(b=>u.every(c=>!has(a,b)||!has(b,c)||has(a,c))));
    assert.equal(actual,v.expected,q.id);assert.equal(key.startsWith('Yes:'),actual,q.id);return true;
  }
  if(v.kind==='relation-equivalence'||v.kind==='relation-classes'){
    const has=(a,b)=>v.pairs.some(([x,y])=>x===a&&y===b),u=v.universe;
    const equivalence=u.every(a=>has(a,a))&&u.every(a=>u.every(b=>!has(a,b)||has(b,a)))&&u.every(a=>u.every(b=>u.every(c=>!has(a,b)||!has(b,c)||has(a,c))));
    assert.ok(equivalence,q.id);
    if(v.kind==='relation-equivalence'){assert.ok(key.startsWith('Yes:'),q.id);return true;}
    actual=new Set(u.map(a=>JSON.stringify(u.filter(b=>has(a,b))))).size;
  }
  if(v.kind==='cartesian-count')actual=v.a.flatMap(a=>v.b.map(b=>[a,b])).length;
  if(v.kind==='power-set-count')actual=2**v.n;
  if(v.kind==='function-count')actual=v.m**v.n;
  if(v.kind==='power-product-count')actual=2**(v.n*v.m);
  if(v.kind==='venn-count')actual=v.query.includes('A∪B')?v.a+v.b-v.overlap:v.query.includes('A but not B')?v.a-v.overlap:v.query.includes('neither')?v.n-v.a-v.b+v.overlap:v.a+v.b-2*v.overlap;
  if(v.kind==='graph-query')actual=graphQuery(v);
  if(v.kind==='graph-euler'){
    const adj=adjacency(v.n,v.edges),odd=adj.filter(a=>a.length%2).length,active=components(v.n,v.edges).filter(g=>g.some(i=>adj[i].length)).length;
    actual=active===1&&odd===0?'A closed Euler trail exists':active===1&&odd===2?'An open Euler trail exists, but no closed one':'No trail uses every edge exactly once';
    assert.equal(actual,key,q.id);return true;
  }
  if(v.kind==='graph-bipartite'){
    actual=false;for(let mask=0;mask<2**v.n;mask++)if(v.edges.every(([a,b])=>!!(mask&(1<<a))!==!!(mask&(1<<b)))){actual=true;break;}
    assert.equal(actual,v.expected,q.id);assert.equal(key.startsWith('Yes:'),actual,q.id);return true;
  }
  if(v.kind==='recurrence-case'){assert.equal(key,recurrenceKeys[v.case][v.query],q.id);return true;}
  assert.notEqual(actual,undefined,`Unknown verification kind ${v.kind}`);
  assert.equal(actual,v.expected,q.id);assert.equal(String(actual),key,q.id);return true;
}
