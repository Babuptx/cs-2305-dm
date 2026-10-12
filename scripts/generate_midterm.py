"""Original, slide-scoped midterm practice. Source PDFs are never build inputs.

Run after generate_bank.py, or alone to update only pillar 7. Related odd
exercise numbers are study pointers, not claims that questions reproduce them.
"""
from pathlib import Path
from fractions import Fraction
import itertools
import json
import math
import random

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'utd-fall-midterm'
TITLE = 'Fall Semester Midterm Practice'
BANK = []
BLOCKS = []
CURRENT = {}

def block(title):
    if BLOCKS:
        assert len(BANK) == len(BLOCKS)*50, (BLOCKS[-1], len(BANK))
    BLOCKS.append(title)

def case(topic, section, odd, context, objective, hint):
    assert all(n % 2 for n in odd)
    CURRENT.update(topic=topic, section=section, odd=odd, context=context,
                   objective=objective, hint=hint)

def add(prompt, answer, wrong, reason, advanced=False, verify=None, hint=None):
    i = len(BANK)
    choices = [(str(answer), '')] + [(str(a), why) for a, why in wrong]
    assert len(choices) == 4 and len({a for a, _ in choices}) == 4, (prompt, choices)
    keys = [0,1,2,3]*12 + ([0,1] if (i//50)%2 == 0 else [2,3])
    random.Random(230500+i//50).shuffle(keys)
    key = keys[i%50]
    correct = choices.pop(0)
    random.Random(i+2026).shuffle(choices)
    choices.insert(key, correct)
    q = dict(id=f'{SLUG}-{i+1:03}', topic=CURRENT['topic'],
             difficulty='advanced' if advanced else 'intermediate',
             question_type='single_choice', prompt=prompt, context=CURRENT['context'],
             options=[x[0] for x in choices], correct_index=key,
             hints=[hint or CURRENT['hint'], 'State the domain and all hypotheses explicitly. Work out the result before comparing the four choices.'],
             explanation=dict(learning_objective=CURRENT['objective'], correct_rationale=reason,
                              incorrect_rationales=[dict(option_index=j,rationale=why) for j,(_,why) in enumerate(choices) if j!=key]),
             source_notes=[f'Original slide-aligned practice. Related study: Rosen, uploaded eighth edition, §{CURRENT["section"]}, odd exercises '+', '.join(map(str,CURRENT['odd']))+'. These are study pointers; this item is not a reproduced textbook exercise.'],
             curriculum=dict(section=CURRENT['section'], odd_exercises=CURRENT['odd'], workshop=CURRENT['topic']),
             has_exhibit=False, exhibit_url='')
    if verify:
        q['verification'] = dict(kind='midterm', **verify)
    BANK.append(q)

def num(prompt, value, reason, op, args, advanced=False, alternatives=None):
    candidates=[]
    for n in (alternatives or [])+[value+1,value-1,value+2,value*2,0,1,2,3,4]:
        if n!=value and n not in candidates:
            candidates.append(n)
        if len(candidates)==3: break
    add(prompt, value, [(n,f'{n} does not satisfy the stated computation. {reason}') for n in candidates],
        reason,advanced,dict(op=op,args=args))

def choices(prompt, answer, others, reason, advanced=False, verify=None):
    """Use only when the derivation explicitly distinguishes every alternative."""
    add(prompt, answer, [(x,f'This alternative fails the required condition. {reason}') for x in others],reason,advanced,verify)

def fmtset(a):
    return '{'+', '.join(map(str,sorted(set(a))))+'}' if a else '∅'

def boolean(ast, row):
    if isinstance(ast,str): return row[ast]
    op,*terms=ast
    v=[boolean(t,row) for t in terms]
    return {'not':lambda:not v[0], 'and':lambda:all(v),'or':lambda:any(v),
            'implies':lambda:not v[0] or v[1], 'iff':lambda:v[0]==v[1],
            'xor':lambda:v[0]!=v[1]}[op]()

def formula(ast):
    if isinstance(ast,str): return ast
    op,*ts=ast
    return '¬'+formula(ts[0]) if op=='not' else '('+{'and':' ∧ ','or':' ∨ ','implies':' → ','iff':' ↔ ','xor':' ⊕ '}[op].join(map(formula,ts))+')'

def logic():
    block('Logic, equivalence & consistency')
    formulas=[
        ['and',['implies','p','q'],['implies','q','r'],['not','r']],
        ['iff',['implies','p','q'],['or','r','p']],
        ['xor',['and','p','q'],['or','q','r']],
        ['and',['or','p','q'],['or',['not','q'],'r'],['or',['not','r'],['not','p']]],
        ['implies',['xor','p','r'],['and','q',['not','r']]],
        ['iff',['not',['and','p','q']],['xor','q','r']],
        ['or',['and','p',['not','r']],['and',['not','p'],'q'],['and','q','r']],
        ['and',['iff','p',['not','q']],['implies','r','p']],
        ['implies',['and',['implies','p','q'],['implies','r',['not','q']]],['not',['and','p','r']]],
        ['and',['or','p','r'],['implies','p','q'],['implies','r',['not','q']]]
    ]
    rows=[dict(zip('pqr',bs)) for bs in itertools.product([False,True],repeat=3)]
    for k,ast in enumerate(formulas):
        f=formula(ast); vals=[boolean(ast,r) for r in rows]; bits=''.join('T' if v else 'F' for v in vals)
        case(f'Logic workshop {k+1}', '1.3', [9,11,33,35], f'Let F = {f}. Variables p, q, r are propositions; → is material implication and ⊕ is exclusive OR.',
             'Distinguish equivalence, satisfiability, implication, and conditional model counts.',
             'An implication is false only for a true antecedent and a false consequent. Evaluate inner connectives first.')
        reason=f'In row order FFF, FFT, FTF, FTT, TFF, TFT, TTF, TTT, F has outputs {bits}.'
        wrong=[bits[:j]+('F' if bits[j]=='T' else 'T')+bits[j+1:] for j in [0,3,6]]
        CURRENT.update(section='1.1',odd=[33,35,39])
        choices('Which truth-table output column represents F in row order FFF, FFT, FTF, FTT, TFF, TFT, TTF, TTT?',bits,wrong,reason,verify=dict(op='logic',args=dict(ast=ast,query='column')))
        num('How many assignments satisfy all of F?',sum(vals),reason+f' Count the T entries: {sum(vals)}.', 'logic',dict(ast=ast,query='count'),alternatives=[8-sum(vals),8,0,4])
        CURRENT.update(section='1.3',odd=[9,11,33,35])
        true_rows=[r for r,v in zip(rows,vals) if v and r['q']]
        num('If q is known to be true, how many assignments to p and r still satisfy F?',len(true_rows),
            reason+' Keep only the rows FTF, FTT, TTF, TTT, then count their true outputs.', 'logic',dict(ast=ast,query='q-true'))
        count=sum(v and not r['p'] for r,v in zip(rows,vals))
        num('How many counterexamples does the proposed inference “F, therefore p” have?',count,
            reason+' A counterexample must make the whole premise F true and p false; a false premise is not a counterexample.', 'logic',dict(ast=ast,query='counter-p'),True)
        # Negation equivalence is checked against every option, not just the key.
        target=['not',ast]
        candidates=[ast,['and','p',['not','p']],['or','p',['not','p']],['not','p'],'q',['xor','p','r']]
        target_bits=[boolean(target,r) for r in rows]
        distinct=[]
        for other in candidates:
            b=[boolean(other,r) for r in rows]
            if b!=target_bits and formula(other) not in distinct:
                distinct.append(formula(other))
            if len(distinct)==3:break
        # Deliberate algebraic equivalent written as an implication to false.
        equiv=['implies',ast,['and','p',['not','p']]]
        choices('Which expression is equivalent to ¬F for every assignment?',formula(equiv),distinct,
                'The consequent p ∧ ¬p is always false. F → false is true exactly when F is false. Compare full truth tables; matching one row is insufficient.',True,
                dict(op='logic-equivalence',args=dict(ast=target)))

def quantifiers():
    block('Quantifiers & rules of inference')
    matrices=[[[1,0,0],[0,1,0],[0,0,1]],[[1,0,1],[1,1,0],[1,0,0]],[[1,1,1],[0,0,0],[1,0,1]],[[0,1,0],[0,1,1],[1,0,0]],[[1,1,0],[1,0,1],[0,1,1]]]
    forms=['∀x ∃y P(x,y)','∃y ∀x P(x,y)','∃x ∀y P(x,y)','∀y ∃x P(x,y)']
    for i,m in enumerate(matrices):
        case(f'Quantifier models {i+1}','1.5',[3,27,31,45],
             'Both domains are D = {1, 2, 3}. P(x,y) is true at the 1 entries of this table (rows x, columns y):\n'+'\n'.join(' '.join(map(str,r)) for r in m),
             'Track witness dependence, quantifier order, and counterexamples on a finite domain.',
             'For ∀x∃y inspect every row; for ∃y∀x find one column that works in every row.')
        truths=[all(any(r) for r in m),any(all(m[x][y] for x in range(3)) for y in range(3)),any(all(r) for r in m),all(any(m[x][y] for x in range(3)) for y in range(3))]
        key=', '.join('T' if t else 'F' for t in truths)
        others=[', '.join('T' if t else 'F' for t in [*truths[:j],not truths[j],*truths[j+1:]]) for j in range(3)]
        choices('In order, what are the truth values of '+ '; '.join(forms)+'?',key,others,
                'The four tests are: no empty row; an all-1 column; an all-1 row; no empty column. Applying these tests gives '+key+'.',verify=dict(op='quantifiers',args=dict(matrix=m,query='truths')))
        witnesses=[y+1 for y in range(3) if all(m[x][y] for x in range(3))]
        num('How many values of y witness ∀x P(x,y)?',len(witnesses),'A witness y needs an all-1 column. The qualifying columns are '+fmtset(witnesses)+'.','quantifiers',dict(matrix=m,query='common-witnesses'))
        counter=[x+1 for x,r in enumerate(m) if not all(r)]
        num('For how many x is the negation ¬∀y P(x,y) true?',len(counter),'Negate ∀y to ∃y¬. Count rows containing at least one 0: '+fmtset(counter)+'.','quantifiers',dict(matrix=m,query='not-all-rows'))
        missing=sum(not any(r) for r in m)
        num('What is the minimum number of 0 entries that must become 1 to make ∀x∃y P(x,y) true?',missing,
            f'Each empty row requires one new witness, and a change cannot repair two different rows. There are {missing} empty rows, so this lower bound is achievable.', 'quantifiers',dict(matrix=m,query='repair-rows'),True)
        cost=min(sum(not m[x][y] for x in range(3)) for y in range(3))
        num('What is the minimum number of 0 entries that must become 1 to make ∃y∀x P(x,y) true?',cost,
            'Choose a single column and fill every zero in it. Column costs are '+str([sum(not m[x][y] for x in range(3)) for y in range(3)])+f'; their minimum is {cost}.','quantifiers',dict(matrix=m,query='repair-column'),True)
    # Five argument workshops, each with distinct reasoning obligations.
    conceptual_quantifiers()
    more_quantifiers()

def rows(data):
    for row in data:
        prompt,key,wrong,reason,*advanced=row
        choices(prompt,key,wrong,reason,bool(advanced and advanced[0]))

def conceptual_quantifiers():
    case('Quantifier order in systems','1.5',[11,15,17,31], 'D is a nonempty set of devices and K a nonempty set of keys. A(d,k) means device d accepts key k.',
         'Translate nested statements and negate them without changing witness scope.', 'Distinguish a common key from keys that may depend on the device.')
    rows([
      ('Translate “Every device rejects at least one key.”','∀d ∃k ¬A(d,k)',['∃k ∀d ¬A(d,k)','∀d ∀k ¬A(d,k)','∃d ∀k A(d,k)'],'For each device a rejected key must exist; that key may vary with d. A common rejected key or rejection of all keys is stronger.'),
      ('Negate “Some key is accepted by every device.”','∀k ∃d ¬A(d,k)',['∃k ∀d ¬A(d,k)','∀d ∃k A(d,k)','∃d ∀k ¬A(d,k)'],'Negating ∃k∀d A flips both quantifiers and negates A. Each key has a rejecting device, possibly a different device.'),
      ('Which condition is sufficient for ∀d∃k A(d,k)?','∃k∀d A(d,k)',['∃d∃k A(d,k)','∀k∃d A(d,k)','∃d∀k A(d,k)'],'A universally accepted key supplies a witness for every device. The other options may leave a device accepting nothing.'),
      ('Which two-device, two-key acceptance pattern shows ∀d∃k A does not imply ∃k∀d A?','Each device accepts only its own distinct key.',['Both devices accept both keys.','Both devices accept only the first key.','Neither device accepts any key.'],'The diagonal pattern gives each row a 1 but no column all 1. The first two have a common key; the last fails the premise.',True),
      ('How can ∀d∃!k A(d,k) hold while some key is accepted by multiple devices?','Each device accepts exactly one key, and those keys need not be distinct.',['Unique existence forces different devices to use different keys.','Unique existence requires every key to be accepted.','The statement requires a single key accepted by every device.'],'Uniqueness is inside the scope for each d. It controls each row, not collisions between rows, unused columns, or a shared universal key.',True)
    ])

def proofs():
    block('Proof construction & diagnosis')
    case('Parity through algebra','1.7',[1,3,5,19], 'Let a and b be odd integers. Write a=2u+1 and b=2v+1 with u,v∈Z.',
         'Turn parity hypotheses into integer factorizations and identify invalid converses.', 'An even expression must be twice an integer; an odd expression must be twice an integer plus one.')
    rows([
      ('Which identity proves ab is odd?','ab=2(2uv+u+v)+1',['ab=2(uv+u+v)+1','ab=2(2uv+u+v)','ab=2(u+v)+1'],'Expansion gives 4uv+2u+2v+1. The quantity 2uv+u+v is an integer, so the displayed correct identity is of the form 2k+1.'),
      ('Which factorization proves a²+b² is even?','a²+b²=2(2u²+2u+2v²+2v+1)',['a²+b²=2(u²+v²)+1','a²+b²=2(u+v)','a²+b²=4(u²+v²)+1'],'Expand each odd square to 4u²+4u+1 and 4v²+4v+1. Their sum is twice the indicated integer.'),
      ('Which statement about a+b is justified?','It is even, but it need not be divisible by 4.',['It is always divisible by 4.','It is always odd.','It is never divisible by 4.'],'a+b=2(u+v+1). For a=b=1 the sum is 2; for a=1,b=3 it is 4. These also distinguish “always” from “never.”'),
      ('Drop the oddness assumptions. If a+b is even, what follows for integers a,b?','They have the same parity.',['They are both even.','They are both odd.','They have different parity.'],'Modulo 2, a+b≡0 implies a≡b. Both even and both odd pairs work; mixed parity does not.',True),
      ('Why is “ab is even, therefore both a and b are even” invalid?','a=2,b=3 is a counterexample.',['a=2,b=4 is a counterexample.','a=1,b=3 is a counterexample.','a=0,b=0 is a counterexample.'],'The pair (2,3) has even product but not two even factors. The other pairs either satisfy the conclusion or fail the premise.',True)
    ])
    case('Rational and irrational closure','1.7',[9,11,13,15], 'Let t be irrational and r a nonzero rational number. Rational numbers are ratios of integers with a nonzero denominator.',
         'Use closure of rationals in contradiction proofs and keep nonzero assumptions.', 'If an alleged rational expression lets you solve for an irrational number using rational operations, seek a contradiction.')
    rows([
      ('Which assumption starts a contradiction proof that t+r is irrational?','Assume t+r is rational.',['Assume t is rational.','Assume r is irrational.','Assume t+r is irrational.'],'Assume the negation of the conclusion while preserving the hypotheses. Then t=(t+r)−r would be rational by closure under subtraction.'),
      ('Which step proves rt cannot be rational?','If rt=s∈Q, then t=s/r∈Q because r≠0.',['If rt=s∈Q, then t=s−r.','Every product of two irrationals is irrational.','Multiplication always preserves irrationality, even by zero.'],'Divide by the nonzero rational r; closure gives the contradiction. Zero would destroy the conclusion, and the displayed subtraction is not algebraically equivalent.'),
      ('Which pair refutes “the product of two irrational numbers is irrational”?','√5 and √5',['√5 and 2','2 and 3','0 and √5'],'Both √5 factors are irrational, but their product is 5. Each other pair includes a rational factor and therefore fails the hypothesis.'),
      ('Why is 1/t irrational?','If 1/t were nonzero rational, taking its reciprocal would make t rational.',['Every nonzero real is irrational.','The reciprocal of every rational is irrational.','Because t might equal zero.'],'Irrational t is nonzero. A nonzero rational has a rational reciprocal, contradicting the hypothesis on t.',True),
      ('For irrational t>0, why is √t irrational?','A rational √t would have rational square t.',['The square of every irrational is irrational.','Every positive number has an irrational square root.','A rational square root would be negative.'],'Rationals are closed under multiplication, so squaring a rational √t contradicts irrationality of t. The other universal claims are false.',True)
    ])
    case('A lowest-terms contradiction','1.7',[9,15,19], 'Consider a proof that √7 is irrational. Assume √7=a/b in lowest terms, a,b∈Z and b≠0. Use the fact that prime 7 dividing a² implies 7 divides a.',
         'Connect lowest terms, prime divisibility, and the actual contradiction.', 'The contradiction must violate coprimality, not just show that a squared expression is divisible.')
    rows([
      ('What equation follows after squaring?','a²=7b²',['a=7b','7a²=b²','a²=49b²'],'Squaring √7=a/b gives 7=a²/b², hence a²=7b².'),
      ('After setting a=7k, what relation follows?','b²=7k²',['b²=k²','b²=49k²','b=7k²'],'Substitute a=7k into a²=7b²: 49k²=7b²; divide by 7.'),
      ('What is the contradiction at the end?','7 divides both a and b although gcd(a,b)=1.',['a and b are integers.','b is nonzero.','a² and b² are nonnegative.'],'The prime-divides-square fact yields 7|b as well as 7|a. This contradicts the chosen lowest-terms representation.'),
      ('Why may the rational representation be chosen in lowest terms?','Every rational ratio can be reduced by the gcd of numerator and denominator.',['Every ratio of integers already has gcd 1.','Irrational numbers have lowest-terms fractions.','A fraction can be reduced only when its denominator is prime.'],'If the rationality assumption is true, a reduced representation exists. Reducing does not assume the theorem or restrict rational numbers.',True),
      ('Why does the same argument not establish that √9 is irrational?','9|a² does not force 9|a; a=3 disproves that step.',['Squaring equal quantities is invalid.','No integer has a square divisible by 9.','The denominator of a rational number cannot be 1.'],'The prime-divides-square inference used with 7 cannot be replaced by 9. In fact √9=3/1 is rational.',True)
    ])
    case('Contraposition and residues','1.7',[17,19], 'For integer n consider the claim: if n² is divisible by 3, then n is divisible by 3.',
         'Build a contrapositive by exhausting residue cases and distinguish converse from inverse.', 'If 3 does not divide n, write n as 3k+1 or 3k+2.')
    rows([
      ('What is the contrapositive?','If 3 does not divide n, then 3 does not divide n².',['If 3 divides n, then 3 divides n².','If 3 does not divide n², then 3 does not divide n.','If 3 divides n², then 3 does not divide n.'],'For P→Q the contrapositive is ¬Q→¬P, with P meaning 3|n² and Q meaning 3|n.'),
      ('Which cases exhaust integers not divisible by 3?','n=3k+1 or n=3k+2, k∈Z',['n=3k only','n=3k+1 only','n=2k or n=2k+1 only'],'The division algorithm gives residues 0,1,2; exclude 0. Parity is exhaustive for integers but does not itself identify nonmultiples of 3.'),
      ('What remainder does n² have when n=3k+2?','1 modulo 3',['0 modulo 3','2 modulo 3','4 modulo 3 as a canonical remainder'],'(3k+2)²=9k²+12k+4=3(3k²+4k+1)+1. The canonical remainder is 1.'),
      ('What completes the proof after both nonzero residue cases give square remainder 1?','The contrapositive is true, so the original implication is true.',['The converse alone proves the original.','A single example proves all integers.','The original was assumed, so it is proved.'],'Exhausting both possible residues proves the contrapositive for every eligible integer; logical equivalence then proves the claim.',True),
      ('Replacing 3 by 4 makes the original claim false. Which n is a counterexample?','n=2',['n=3','n=4','n=5'],'4 divides 2² but not 2. For 3 and 5 the premise fails; 4 satisfies the conclusion.',True)
    ])
    case('Existence versus uniqueness','1.8',[13,15,17], 'Let c be any fixed real number. Consider the equation 5x+2=c with unknown x∈R.',
         'Separate construction of a solution from proof that no other solution exists.', 'First supply a witness; then start with two arbitrary solutions and compare them.')
    rows([
      ('Which witness proves existence?','x=(c−2)/5',['x=(c+2)/5','x=5c−2','x=c/5'],'Substitution gives 5((c−2)/5)+2=c. The other expressions do not solve the equation for arbitrary c.'),
      ('What is the appropriate uniqueness setup?','Assume u and v both solve 5x+2=c.',['Assume only the proposed solution works.','Choose one numerical c and inspect its solution.','Assume no solution exists.'],'To prove at most one solution, compare arbitrary solutions u,v; do not assume the desired uniqueness.'),
      ('Which step forces u=v?','Subtracting 5u+2=5v+2 gives 5(u−v)=0; divide by 5.',['Subtracting gives u+v=0.','The existence of u excludes v.','Both are real, so they are equal.'],'The nonzero coefficient 5 allows cancellation. Being real or merely existing does not establish equality.'),
      ('If the unknown must be an integer and c=4, what changes?','There is no integer solution, although the real solution is unique.',['There are two integer solutions.','x=0 is an integer solution.','Uniqueness over R guarantees existence over Z.'],'The unique real candidate is 2/5, not an integer. Restricting the domain can remove existence.',True),
      ('For ax+2=c over R, which condition guarantees exactly one solution for every c?','a≠0',['a=0','c=2 only, with arbitrary a','a and c have the same sign'],'For a≠0 solve x=(c−2)/a uniquely. If a=0 then c=2 gives every real as a solution, and c≠2 gives none.',True)
    ])
    case('Exhaustive cases and inequalities','1.8',[5,7,9,23], 'Let x,y∈R. Consider max(x,y)+min(x,y)=x+y and |x+y|≤|x|+|y|.',
         'Choose exhaustive cases, use symmetry properly, and locate equality conditions.', 'A proof by cases must cover equality as well as both strict orderings.')
    rows([
      ('Which split suffices for the max/min identity?','x≥y and x<y',['x>y and x<y','x>0 and y>0','x=y only'],'The split x≥y or x<y is exhaustive and determines both min and max. Strict inequalities alone omit x=y.'),
      ('In the case x≥y, what is max(x,y)−min(x,y)?','x−y',['y−x','x+y','2x'],'When x≥y, max=x and min=y, so their difference is x−y.'),
      ('Which calculation refutes the claimed identity |x+y|=|x|+|y| for all real x,y?','x=3,y=−3 gives 0≠6.',['x=3,y=3 gives 6=6.','x=0,y=3 gives 3=3.','x=−3,y=−3 gives 6=6.'],'Opposite nonzero signs can cause cancellation. The other pairs give equality and therefore are not counterexamples.'),
      ('Why may one assume x≥y without loss of generality for the max/min SUM identity?','Interchanging x and y leaves both sides unchanged.',['All real pairs satisfy x≥y.','The case x<y is impossible.','An inequality assumption is always free to add.'],'The expression is symmetric, so exchanging labels converts the omitted case into the proved one. WLOG needs that symmetry.',True),
      ('When does |x+y|=|x|+|y| hold for real x,y?','When xy≥0, including zero values.',['Only when x=y.','Exactly when xy<0.','For every real pair.'],'Same-sign terms or a zero give equality. Opposite nonzero signs give |x+y| strictly smaller than |x|+|y|.',True)
    ])
    case('Counterexamples and quantifier burden','1.7',[11,17], 'Evaluate universal assertions about real numbers using counterexamples and direct algebra.',
         'Refute universal claims with hypotheses satisfied and explain why tested examples do not prove them.', 'A counterexample must make the hypothesis true and the claimed conclusion false.')
    rows([
      ('Which pair refutes “If x²=y², then x=y”?','x=−4,y=4',['x=4,y=4','x=2,y=3','x=0,y=0'],'The first pair has equal squares but unequal entries. The second and fourth satisfy the conclusion, while the third fails the hypothesis.'),
      ('Which added hypothesis makes x²=y² ⇒ x=y valid?','x,y≥0',['x,y≠0','x and y are integers','x,y≤4'],'Equal squares imply x=y or x=−y. Nonnegativity eliminates distinct opposites; the other restrictions still allow −4 and 4.'),
      ('Which pair refutes “If x+y>0, then x>0 and y>0”?','x=−2,y=5',['x=2,y=5','x=−2,y=−5','x=0,y=0'],'The sum 3 is positive but x is not. Other options either satisfy the conclusion or fail the premise.'),
      ('What weaker conclusion is always valid when x+y>0?','x>0 or y>0',['x>0 and y>0','xy>0','x=y'],'If both x and y were ≤0 then their sum would be ≤0. Therefore at least one is positive; both need not be.',True),
      ('Why do 1,000 successful numerical tests not prove a claim over all real pairs?','They leave untested cases in an infinite domain.',['Universal claims cannot be proved.','Testing any example invalidates a proof.','A claim becomes true after enough tests.'],'Finite testing can suggest a claim or find a counterexample, but universal proof requires an argument covering every allowed pair.',True)
    ])
    case('Constructive difference of squares','1.7',[7], 'Let n=2k+1 be any odd integer, with k∈Z. Seek integers u,v such that n=u²−v².',
         'Construct witnesses algebraically and use residues to identify limitations.', 'Use u²−v²=(u−v)(u+v), and try two consecutive integers.')
    rows([
      ('Which construction works for every such n?','u=k+1, v=k',['u=k, v=k+1','u=2k+1, v=0','u=k+2, v=k'],'(k+1)²−k²=2k+1=n. Reversing the pair gives −n; the other constructions do not work for all k.'),
      ('For n=−9, which consecutive-integer witnesses follow from that construction?','u=−4,v=−5',['u=5,v=4','u=−5,v=−4','u=−9,v=0'],'k=(−9−1)/2=−5. Then u=−4,v=−5 and 16−25=−9.'),
      ('Which kind of existence proof is this?','Constructive, because formulas give actual integer witnesses.',['Nonconstructive, because n varies.','Inductive, because k is an integer.','Circular, because it uses algebra.'],'The explicit u and v are a construction valid for each n. A variable parameter does not turn it into a nonconstructive or inductive proof.'),
      ('Which integer cannot be a difference of two integer squares?','14',['15','16','−9'],'A square is 0 or 1 modulo 4, so their difference cannot be 2 modulo 4. The alternatives are 4²−1², 4²−0², and (−4)²−(−5)².',True),
      ('Which factorization constructs every multiple 4m as a difference of squares?','4m=(m+1)²−(m−1)²',['4m=(m+1)²−m²','4m=m²−(m−1)²','4m=(2m)²'],'Expansion gives m²+2m+1−(m²−2m+1)=4m for all integers m. The other expressions are 2m+1, 2m−1, and 4m².',True)
    ])
    case('Constructing composite runs','1.8',[11,13], 'Let N=7!. Examine the six consecutive integers N+2, N+3, …, N+7.',
         'Construct simultaneous witnesses and distinguish composite from merely divisible.', 'Each small integer in the displayed range divides the factorial and its own offset.')
    rows([
      ('Why does 5 divide N+5?','5 divides both 7! and 5, so it divides their sum.',['5 divides every sum of positive integers.','7! is prime.','N+5 ends in 5 for every possible factorial N.'],'The sum property of divisibility applies: 5|7! and 5|5 imply 5|(7!+5). A general decimal-ending claim is unnecessary and false for small factorials.'),
      ('What extra fact shows N+5 is composite, not just divisible by 5?','1<5<N+5',['N+5 is positive only.','5 is odd only.','Every multiple of 5 is composite, including 5.'],'A proper divisor strictly between 1 and the number proves compositeness. The prime number 5 itself is a multiple of 5.'),
      ('How many consecutive composites are established by this displayed construction?','6',['5','7','5040'],'The offsets 2 through 7 contain 7−2+1=6 integers, each with its own proper divisor.'),
      ('Which construction proves arbitrarily long finite runs of composites?','For length L≥1, use (L+1)!+j for j=2,…,L+1.',['Use L!+1 only.','Claim every integer after L! is composite.','Use the first L prime numbers.'],'There are L consecutive offsets; each j divides the factorial and its offset and lies strictly between 1 and the constructed number.',True),
      ('What does this construction NOT establish?','That only finitely many primes exist.',['That a run of six composites exists.','That gaps between consecutive primes are unbounded.','That there are arbitrarily long finite composite runs.'],'Arbitrarily long gaps can coexist with infinitely many primes. The construction gives finite composite intervals of every requested length, not an eventually prime-free tail.',True)
    ])
    case('Proof errors and logical structure','1.8',[17,19,21], 'A valid proof must justify every step using the hypotheses and already established results.',
         'Recognize circularity, unsafe cancellation, vacuity, and incomplete biconditionals.', 'Check denominators, the direction of implication, and whether a supposedly arbitrary object was specially selected.')
    rows([
      ('Assuming a=b, a purported proof cancels a−b. What is wrong?','It divides by zero.',['Equality cannot be multiplied.','Variables cannot denote equal numbers.','Every cancellation is invalid.'],'The hypothesis implies a−b=0. Dividing by that factor is undefined; cancellation requires a nonzero factor.'),
      ('To prove P iff Q, what is required?','Prove P→Q and Q→P.',['Prove only P→Q.','Prove only ¬Q→¬P.','Give one case in which both hold.'],'A biconditional needs both directions. ¬Q→¬P is equivalent to the first direction and adds no converse.'),
      ('If a conditional has a false hypothesis for every object in a specified domain, how is it true?','Vacuously; there is no counterexample with a true hypothesis.',['Its conclusion has been proved for every object.','It must be false because the hypothesis is false.','It is true only when the domain is empty.'],'Material implication is false only when its hypothesis is true and its conclusion false. Vacuity can occur in a nonempty domain.'),
      ('Which proof plan is circular for a previously unproved theorem T?','Use T itself as an essential justification for T.',['Assume ¬T and derive a contradiction from established facts.','Prove an equivalent claim independently.','Prove all exhaustive cases using established facts.'],'Using T as a premise presupposes the result. Contradiction, independent equivalence, and exhaustive cases are valid methods.',True),
      ('Which statement correctly distinguishes a disproof from an incomplete proof?','A valid counterexample disproves a universal claim; a gap in one argument alone does not.',['Any failed proof proves the claim false.','A true claim admits no flawed attempted proof.','A counterexample may ignore the hypotheses.'],'An argument may fail even when its conclusion is true. To disprove the universal statement, exhibit an allowed instance with a false conclusion.',True)
    ])
def sets_functions():
    block('Sets, power sets & functions')
    samples=[([1,2,4,7],[2,3,4,8],[1,4,5,8]),([0,2,3,5,8],[1,3,5,7],[0,1,5,6,8]),([1,3,5,7,9],[2,3,5,8],[3,4,7,8,9])]
    for k,(aa,bb,cc) in enumerate(samples):
        a,b,c=map(set,(aa,bb,cc)); u=set(range(10))
        case(f'Finite-set synthesis {k+1}','2.2',[3,27,29,41],f'U={fmtset(u)}, A={fmtset(a)}, B={fmtset(b)}, C={fmtset(c)}. Complements are relative to U.',
             'Combine set operations, complements, power sets, and exact membership conditions.', 'Translate each set operation into its membership condition before counting.')
        operations=[('How many elements are in (A∪B)∖C?',len((a|b)-c),'union-minus',fmtset((a|b)-c),False),
                    ('How many elements belong to exactly one of A and B?',len(a^b),'xor',fmtset(a^b),False),
                    ('What is |U∖(A∪B∪C)|?',len(u-(a|b|c)),'outside',fmtset(u-(a|b|c)),False),
                    ('What is |𝒫(A∩B) × (C∖A)|?',2**len(a&b)*len(c-a),'power-product',f'2^{len(a&b)} × {len(c-a)}',True),
                    ('How many subsets S of A satisfy A∩B ⊆ S?',2**len(a-b),'required-subsets',f'The {len(a&b)} required elements are fixed; the {len(a-b)} remaining elements are optional, giving 2^{len(a-b)}',True)]
        for prompt,value,query,detail,adv in operations:
            num(prompt,value,f'The relevant calculation is {detail}. The resulting cardinality is {value}.','sets',dict(a=aa,b=bb,c=cc,u=sorted(u),query=query),adv)
    case('Elements versus subsets','2.1',[11,13,21,23,25], 'Let A={∅,{∅}}. The symbols ∈ and ⊆ have different meanings, and 𝒫 denotes the power set.',
         'Distinguish an object, a singleton containing it, and a collection of subsets.', 'List the elements of A first, then form all subsets as separate objects.')
    rows([
      ('How many elements does 𝒫(A) have?','4',['0','2','3'],'A has two distinct elements, ∅ and {∅}. Its power set has 2²=4 elements.'),
      ('Which is an element of 𝒫(A)?','{{∅}}',['{{{∅}}}','{1}','{∅,1}'],'{{∅}} is the singleton whose element {∅} belongs to A, so it is a subset of A. The other choices contain objects not in A.'),
      ('Which statement is false?','{{∅}}∈A',['∅∈A','{∅}∈A','{{∅}}⊆A'],'The elements of A are exactly ∅ and {∅}; {{∅}} is neither. But its only element {∅} lies in A, making it a subset.'),
      ('What is |𝒫(𝒫(A))|?','16',['4','8','256'],'First |A|=2, then |𝒫(A)|=4, then |𝒫(𝒫(A))|=2⁴=16. Apply exponentiation once at each power-set level.',True),
      ('If B={∅}, what is |A×B|?','2',['0','1','4'],'B is not empty: it has one element. The pairs are (∅,∅) and ({∅},∅), so |A×B|=2·1.',True)
    ])
    case('Set identities by membership','2.2',[15,17,19,25,37], 'A,B,C are arbitrary subsets of a fixed universe U; Aᶜ means U∖A.',
         'Use membership logic to prove identities and detect invalid cancellation.', 'Union behaves like OR, intersection like AND, and complement like negation.')
    rows([
      ('Which expression equals A∖(B∩C)?','(A∖B)∪(A∖C)',['(A∖B)∩(A∖C)','(B∖A)∪(C∖A)','A∩B∩C'],'Membership is A∧¬(B∧C)=A∧(¬B∨¬C), which distributes to (A∧¬B)∨(A∧¬C).'),
      ('Which condition is equivalent to A⊆B?','A∩Bᶜ=∅',['A∪B=U','A∩B=∅','B⊆A'],'There must be no element of A outside B. The other conditions express covering the universe, disjointness, or the reversed inclusion.'),
      ('Which identity is always true?','(A∪B)∩(A∪C)=A∪(B∩C)',['A∖B=B∖A','A∪B=A∩B','A×B=B×A'],'The first is distributivity. Differences are directional, unions differ from intersections, and ordered Cartesian pairs need not commute.'),
      ('Why does A∪B=A∪C not imply B=C?','A can hide differences between B and C.',['Union is not associative.','Set equality is not symmetric.','The implication fails only for infinite sets.'],'For A={1}, B=∅, C={1}, both unions are {1}, but B≠C. This finite counterexample also identifies the invalid cancellation.',True),
      ('If both A∪B=A∪C and A∩B=A∩C hold, what follows?','B=C',['B and C must be disjoint.','A must be empty.','No relation between B and C follows.'],'For any x, if x∈A compare the intersections; if x∉A compare the unions. In each case x∈B iff x∈C, proving equality.',True)
    ])
    for k,(mapping,codomain,target) in enumerate([([2,0,3,1],[0,1,2,3],1),([1,1,3,4],[0,1,2,3,4],1),([0,1,2,1],[0,1,2],1)]):
        domain=list(range(len(mapping))); image=set(mapping)
        case(f'Function table {k+1}','2.3',[5,11,13,31,33],f'f:D→B, D={fmtset(domain)}, B={fmtset(codomain)}. The outputs f(0),f(1),f(2),f(3) are '+str(mapping)+'. Define g:B→Z by g(y)=2y−1.',
             'Read image and preimage sets, classify maps, and compose in the correct order.', 'Compare distinct outputs with the entire codomain; composition applies the rightmost function first.')
        num('What is |f(D)|?',len(image),f'The distinct outputs are {fmtset(image)}; repeated outputs count once.','function',dict(mapping=mapping,query='image-count'))
        pre=[x for x in domain if mapping[x]==target]
        num(f'What is |f⁻¹({{{target}}})|?',len(pre),f'The preimage is {fmtset(pre)}. A preimage set is defined even when f has no inverse function.','function',dict(mapping=mapping,target=target,query='preimage-count'))
        inj=len(image)==len(domain);sur=image==set(codomain)
        names=['Bijective','Injective but not surjective','Surjective but not injective','Neither injective nor surjective']
        key=names[0] if inj and sur else names[1] if inj else names[2] if sur else names[3]
        choices('How is f classified with the stated codomain?',key,[s for s in names if s!=key],
                f'There are {len(domain)} inputs and {len(image)} distinct outputs, so injectivity is {inj}. The image is {fmtset(image)}, while the codomain is {fmtset(codomain)}, so surjectivity is {sur}.',verify=dict(op='function',args=dict(mapping=mapping,codomain=codomain,query='classification')))
        num('What is (g∘f)(2)+(g∘f)(3)?',2*mapping[2]-1+2*mapping[3]-1,
            f'First apply f: outputs {mapping[2]} and {mapping[3]}. Apply g to each and add (2·{mapping[2]}−1)+(2·{mapping[3]}−1).','function',dict(mapping=mapping,query='composition-sum'),True)
        count=sum(mapping[a]==mapping[b] for a in domain for b in domain if a!=b)
        num('How many ordered pairs (a,b) with a≠b have f(a)=f(b)?',count,
            'Group inputs by output. A group of size t contributes t(t−1) ordered distinct-input pairs. Here the group sizes are '+str([mapping.count(y) for y in sorted(image)])+f', giving {count}.','function',dict(mapping=mapping,query='collisions'),True)
    case('Domain and codomain matter','2.3',[11,13,23,29,71], 'Consider f(x)=x² and h(x)=3x−2 with domains and codomains specified in each question.',
         'Prove function classifications using collisions, missing values, and algebraic inverses.', 'A formula alone does not determine whether a function is onto; inspect its codomain.')
    rows([
      ('How is f:R→R classified?','Neither injective nor surjective',['Bijective','Injective but not surjective','Surjective but not injective'],'Inputs 1 and −1 collide, and negative real outputs are unattained.'),
      ('Which restriction makes x² a bijection?','[0,∞)→[0,∞)',['R→R','Z→Z','R→[0,∞)'],'On nonnegative reals, squares are strictly increasing and every nonnegative y has unique preimage √y. Allowing both signs loses injectivity.'),
      ('What is the inverse of h:R→R?','h⁻¹(y)=(y+2)/3',['h⁻¹(y)=(y−2)/3','h⁻¹(y)=3y+2','h⁻¹(y)=1/(3y−2)'],'Solving y=3x−2 gives x=(y+2)/3. An inverse function reverses a map; it is not a reciprocal.'),
      ('Why is h:Z→Z not surjective?','Only integers congruent to 1 modulo 3 occur.',['Two distinct integer inputs collide.','The output is sometimes noninteger.','Every integer is an output.'],'3x−2≡1 mod 3. For example 0 has no integer preimage, although the map is injective because its slope is nonzero.',True),
      ('If g∘f is injective, which conclusion always follows?','f is injective.',['g is injective on its entire domain.','f is surjective.','g is surjective.'],'If f(a)=f(b), applying g gives equal composite outputs, hence a=b. The composite only tests g on the image of f, not its full domain.',True)
    ])
    case('Floors, ceilings and preimages','2.3',[9,31,45,53], 'Let f:R→Z be f(x)=⌊x⌋. By definition, ⌊x⌋ is the unique integer n with n≤x<n+1.',
         'Apply boundary inequalities accurately for negative inputs and preimage intervals.', 'Floor rounds downward, not toward zero; the right endpoint of a floor interval is excluded.')
    rows([
      ('What is f(−7/3)?','−3',['−2','2','3'],'−3≤−7/3<−2, so the floor is −3.'),
      ('What is f⁻¹({−2})?','[−2,−1)',['(−2,−1]','[−3,−2)','{−2}'],'Exactly the reals −2≤x<−1 have floor −2. The preimage is an interval, not only the integer itself.'),
      ('What is f⁻¹({1,2})?','[1,3)',['[1,2]','(1,3]','{1,2}'],'Combine [1,2) and [2,3), retaining 1 and excluding 3.'),
      ('Which identity holds for every real x?','⌊−x⌋=−⌈x⌉',['⌊−x⌋=−⌊x⌋','⌊x⌋=⌈x⌉','⌊2x⌋=2⌊x⌋'],'Negation reverses inequalities and exchanges floor with ceiling. For x=1.7, the other proposed identities already fail.',True),
      ('For integer n, which identity is valid for all real x?','⌊x+n⌋=⌊x⌋+n',['⌊x+n⌋=⌊x⌋·n','⌊nx⌋=n⌊x⌋','⌈x⌉=⌊x⌋+1'],'If k≤x<k+1, adding integer n gives k+n≤x+n<k+n+1. Scaling does not preserve floors in this way, and floor equals ceiling at integers.',True)
    ])

def sequences_countability():
    block('Sequences, sums & countability')
    case('Arithmetic sequence with indexing','2.4',[1,3,17,29,35,39], 'Let a₀=7 and aₙ=aₙ₋₁+4 for integers n≥1.',
         'Unroll a first-order recurrence and handle inclusive summation limits.', 'Count the increments from index zero, and count both endpoints in a finite sum.')
    for prompt,val,query,why,adv in [
      ('What is a₈?',39,'term','Eight increments give 7+8·4=39.',False),
      ('What is Σ from k=0 to 8 of aₖ?',207,'sum','There are 9 terms with first 7 and last 39. Their sum is 9(7+39)/2=207.',False),
      ('What is Σ from k=3 to 9 of aₖ?',217,'slice','There are 7 terms from 19 to 43; sum 7(19+43)/2=217.',False),
      ('What is Σ from j=0 to 5 of a₂ⱼ?',162,'even-sum','The even-indexed terms are 7,15,23,31,39,47. Their sum is 6(7+47)/2=162.',True),
      ('What is Σ from k=1 to 8 of (aₖ−aₖ₋₁)?',32,'telescoping','All interior terms cancel, leaving a₈−a₀=39−7=32. Equivalently sum eight increments of 4.',True)]:
        num(prompt,val,why,'sequence',dict(type='arithmetic',query=query),adv)
    case('Alternating geometric sequence','2.4',[1,3,17,29,31], 'Let bₙ=3(−2)ⁿ for n≥0.',
         'Track signs and use finite geometric sums with shifted limits.', 'Keep the ratio negative and use (1−r^(N+1))/(1−r) for indices zero through N.')
    for prompt,val,query,why,adv in [
      ('What is b₆−b₅?',288,'difference','b₆=192 and b₅=−96; subtraction gives 288.',False),
      ('What is Σ from k=0 to 5 of bₖ?',-63,'sum','3(1−(−2)⁶)/(1−(−2))=1−64=−63.',False),
      ('What is Σ from k=3 to 7 of bₖ?',-264,'slice','The sum through 7 is 1−256=−255; through 2 it is 1−(−8)=9. Subtract: −264.',False),
      ('What is Σ from j=0 to 3 of b₂ⱼ?',255,'even-sum','Even-indexed terms have ratio 4: 3+12+48+192=255.',True),
      ('What is Σ from k=0 to 4 of (bₖ₊₁+2bₖ)?',0,'recurrence','Each summand is zero because bₖ₊₁=−2bₖ, so the entire sum is zero.',True)]:
        num(prompt,val,why,'sequence',dict(type='geometric',query=query),adv)
    case('Unrolling an affine recurrence','2.4',[9,13,15,17], 'Let c₀=2 and cₙ=3cₙ₋₁+4 for n≥1. Only elementary iteration and substitution are needed.',
         'Shift a recurrence to a geometric sequence and verify an explicit rule.', 'Look for a constant shift that makes the nonhomogeneous addition disappear.')
    num('What is c₄?',322,'The successive values are c₁=10, c₂=34, c₃=106, c₄=322.','sequence',dict(type='affine',query='term'))
    num('What is c₀+c₁+c₂+c₃?',152,'The first four values are 2,10,34,106; their sum is 152.','sequence',dict(type='affine',query='sum'))
    rows([
      ('Which transformation gives dₙ=3dₙ₋₁?','dₙ=cₙ+2',['dₙ=cₙ−2','dₙ=cₙ+4','dₙ=cₙ/3'],'cₙ+2=3cₙ₋₁+6=3(cₙ₋₁+2). The required shift solves 4+s=3s, giving s=2.'),
      ('Which explicit formula satisfies the initial value and recurrence?','cₙ=4·3ⁿ−2',['cₙ=2·3ⁿ+4','cₙ=6n+2','cₙ=4·3ⁿ+2'],'The shifted sequence starts d₀=4 and multiplies by 3, so cₙ=dₙ−2=4·3ⁿ−2. Substitution checks both the base and the step.',True),
      ('Why does merely checking the formula at n=0 and n=1 not prove it for every n?','Other formulas can agree at those two indices but fail the recurrence later.',['A recurrence cannot be checked algebraically.','Initial conditions never matter.','Two matching terms always determine any sequence.'],'The proposed rule must satisfy cₙ=3cₙ₋₁+4 at a general index as well as the initial condition; two numerical matches alone are insufficient.',True)
    ])
    case('Index shifts and double sums','2.4',[29,33,39,41], 'All sums below have integer indices and include both endpoints. An empty sum is zero.',
         'Evaluate nested sums and preserve summands when shifting an index.', 'Write a few terms at both ends before applying a closed summation formula.')
    num('What is Σ from k=4 to 11 of (2k−1)?',112,'There are 8 odd terms, first 7 and last 21; 8(7+21)/2=112.','sum',dict(query='odd-slice'))
    num('What is Σ from i=1 to 4 of Σ from j=1 to 3 of (i+j)?',54,'Each inner sum is 3i+6. Sum over i to get 3·10+4·6=54.','sum',dict(query='double'))
    num('What is Σ from k=0 to 6 of (k+2)²?',203,'The squares are 2² through 8². The sum of 1² through 8² is 204; subtract 1 to get 203.','sum',dict(query='squares'))
    rows([
      ('After setting j=k−3, which sum equals Σ from k=3 to n of (k+1), for n≥3?','Σ from j=0 to n−3 of (j+4)',['Σ from j=0 to n−3 of (j+1)','Σ from j=3 to n of (j+4)','Σ from j=0 to n of (j+4)'],'The new limits are 0 and n−3, while k+1 becomes j+4. Shift both bounds and the summand.',True),
      ('For n≥1, which formula equals Σ from i=1 to n of Σ from j=1 to i of 1?','n(n+1)/2',['n²','n(n−1)/2','2n'],'For a fixed i the inner sum is i, not n. Summing 1+2+…+n gives n(n+1)/2; the dependent upper bound matters.',True)
    ])
    case('Telescoping and finite differences','2.4',[15,17,35,37], 'Let s₀=0 and sₙ=sₙ₋₁+(2n−1) for n≥1. Also consider sums of differences f(k+1)−f(k).',
         'Recognize telescoping cancellation and verify a sequence formula by its difference.', 'Pair each positive interior term with its negative copy; only endpoints remain.')
    num('What is s₉?',81,'The first nine positive odd numbers sum to 9²=81; successive values 0,1,4,9,… agree with sₙ=n².','sum',dict(query='odd-total'))
    num('What is Σ from k=2 to 8 of ((k+1)²−k²)?',77,'Cancellation leaves 9²−2²=81−4=77.','sum',dict(query='square-telescope'))
    choices('What is Σ from k=1 to 9 of (1/k−1/(k+1))?','9/10',['1/10','1','9'],
            'Write 1−1/2+1/2−1/3+…+1/9−1/10. The result is 1−1/10=9/10.',verify=dict(op='sum',args=dict(query='fraction-telescope')))
    rows([
      ('Which identity verifies the transition for sₙ=n²?','n²−(n−1)²=2n−1',['n²−(n−1)²=2n+1','n²−(n−1)²=n','n²=(n−1)²+1'],'Expand the left side to n²−n²+2n−1. Together with s₀=0, it verifies the proposed formula against the recurrence.',True),
      ('For n≥m≥1, what is Σ from k=m to n of 1/[k(k+1)]?','1/m−1/(n+1)',['1/(m+1)−1/n','1/m−1/n','(n−m+1)/(n(n+1))'],'Decompose 1/[k(k+1)]=1/k−1/(k+1). Interior fractions cancel, leaving exactly the lower and shifted upper endpoints.',True)
    ])
    cardinality()

def cardinality():
    case('Bijections and infinite subsets','2.5',[1,3,13,19], 'N={0,1,2,…}, Z⁺={1,2,3,…}. “Countable” includes finite sets as well as countably infinite sets.',
         'Build bijections and avoid extending finite-cardinality intuitions to infinite sets.', 'Show both that every target has a preimage and that no two inputs collide.')
    rows([
      ('Which is a bijection Z⁺→{integers greater than 20}?','f(n)=n+20',['f(n)=20n','f(n)=n+19','f(n)=n²+20'],'Subtracting 20 gives a unique positive-integer preimage for every target. The alternatives miss targets or include 20.'),
      ('Why does the proper inclusion 2Z⊊Z not imply |2Z|<|Z|?','n↦2n is a bijection Z→2Z.',['The inclusion is actually equality.','2Z is finite.','Every subset has its parent’s cardinality.'],'The explicit bijection proves equal cardinality despite proper inclusion. This behavior is possible for infinite sets, not all subsets.'),
      ('Which classification applies to Z∖{−10,…,10}?','Countably infinite',['Finite','Uncountable','Empty'],'It is an infinite subset of countable Z, and deleting finitely many integers leaves infinitely many integers.'),
      ('Which fact suffices to show an infinite set S is countably infinite?','There is an injection S→N.',['There is an injection N→S only.','S contains a copy of N only.','S is a subset of R only.'],'An injection into N shows S is at most countable; the stated infinitude excludes the finite case. An injection from N only gives a lower bound.',True),
      ('What does Schröder–Bernstein allow one to conclude from injections A→B and B→A?','A and B admit a bijection.',['The two injections are inverses.','A and B are equal as sets.','Both sets are finite.'],'Injections in both directions establish equality of cardinalities, even for infinite or different sets. They need not be mutual inverses.',True)
    ])
    case('Rationals and finite descriptions','2.5',[1,3,25,37], 'A finite binary string has finitely many symbols. An infinite binary sequence has one bit at every positive integer index.',
         'Separate a countable union of finite descriptions from an uncountable set of infinite sequences.', 'List finite objects by length, but do not treat an infinite sequence as a finite-length object.')
    rows([
      ('How is the set of all finite binary strings classified?','Countably infinite',['Finite','Uncountable','The same finite size as {0,1}'],'List by increasing length, then lexicographically within each finite length. This gives an enumeration with infinitely many strings.'),
      ('Why is Q countable even though each interval contains infinitely many rationals?','Rational numbers can be encoded by reduced integer numerator/positive denominator pairs.',['Every dense set is countable.','Every rational has a finite decimal expansion.','Q contains only finitely many negative numbers.'],'Integer pairs can be enumerated diagonally; choosing a reduced fraction gives a unique encoding. Density and decimal termination are separate issues.'),
      ('Which set is uncountable?','All infinite binary sequences',['All finite binary strings','All ordered pairs of integers','All positive rational numbers'],'Diagonalization constructs a binary sequence different from the nth listed sequence at position n. The other three sets admit enumerations.'),
      ('Why does listing real numbers by the length of their decimal representations fail?','Most real numbers do not have a finite decimal representation.',['Decimal digits form an uncountable alphabet.','Finite strings cannot be enumerated.','Every real has exactly two decimal representations.'],'Length-by-length enumeration covers only finite descriptions, not arbitrary infinite expansions. The digit alphabet is finite, and only certain reals have two standard expansions.',True),
      ('What follows about finite programs over a finite alphabet?','There are countably many such programs.',['There are uncountably many finite programs.','There are only finitely many possible lengths.','Every function N→{0,1} is computable by a finite program.'],'Programs form a subset of countably many finite strings. Boolean-valued functions on N correspond to uncountably many infinite bit sequences, so finite programs cannot compute all of them.',True)
    ])
    case('Cantor diagonal construction','2.5',[3,35], 'Suppose infinite binary sequences are listed as s₁,s₂,…, with sᵢ(j) the jth bit of sequence i. Define d(i)=1−sᵢ(i).',
         'Explain the exact contradiction in a diagonal argument and avoid digit-expansion ambiguity.', 'Compare the constructed sequence with the ith listed sequence at coordinate i.')
    rows([
      ('Why is d different from s₆?','They differ at position 6.',['They have different lengths.','d must contain only ones.','s₆ is finite.'],'The definition gives d(6)=1−s₆(6), the opposite bit. Both sequences still have infinite length.'),
      ('What makes d a legitimate binary sequence?','Every value 1−sᵢ(i) is either 0 or 1.',['d is eventually zero by definition.','d has finitely many terms.','d already has a position in the assumed list.'],'Complementing a bit produces a bit, so d satisfies the object definition independently of the completeness of the alleged list.'),
      ('What assumption is contradicted?','The list includes every infinite binary sequence.',['Binary digits exist.','Every sequence has a first bit.','The integers are countable.'],'d is an infinite binary sequence omitted from the list. The contradiction concerns exhaustive enumeration.'),
      ('For decimal diagonalization, why can choosing only replacement digits 4 and 5 help?','It avoids ambiguity from a terminating expansion versus an infinite tail of 9s.',['4 and 5 are the only real decimal digits.','It makes the constructed real rational.','It ensures every digit is different from every digit in the list.'],'Choose 4 unless the diagonal digit is 4, otherwise 5. The new number differs at each diagonal coordinate and has no alternative tail-of-9 representation.',True),
      ('Why does this diagonal method not prove finite binary strings uncountable?','The constructed diagonal object can have infinite length and thus lie outside the finite-string set.',['Finite strings have no digits.','The natural numbers cannot index finite strings.','Every diagonal object is finite.'],'A contradiction requires the omitted object to belong to the set allegedly enumerated. An infinite sequence is not a finite string.',True)
    ])
    case('Countable and uncountable set operations','2.5',[9,11,15,17], 'Let U be uncountable and C countable. A set may be finite, countably infinite, or uncountable.',
         'Use closure of countable unions and build examples for unconstrained intersections and differences.', 'If two countable pieces covered an uncountable set, their union would yield a contradiction.')
    rows([
      ('What must be true of U∖C?','It is uncountable.',['It is finite.','It is countably infinite.','It is empty.'],'If U∖C were countable, then U=(U∖C)∪(U∩C) would be a union of two countable sets, contradicting uncountability.'),
      ('What must be true of U∩C?','It is countable, possibly finite or empty.',['It is uncountable.','It is necessarily infinite.','It equals C.'],'The intersection is a subset of countable C, so it is countable; U need not contain all or any of C.'),
      ('Which two uncountable sets have empty intersection?','(0,1) and (2,3)',['R and Q','R and Z','(0,2) and (1,3)'],'Both intervals are uncountable and disjoint. Q and Z are not uncountable, and the last intervals overlap.'),
      ('Can the difference of two uncountable sets be countably infinite?','Yes: R∖(R∖Z)=Z.',['No: it must be uncountable.','No: it must be empty.','Yes: R∖Q is countably infinite.'],'Both R and R∖Z are uncountable, and their difference is exactly countably infinite Z. R∖Q is instead uncountable.',True),
      ('Why are irrational numbers uncountable?','Otherwise their union with countable Q would make R countable.',['Every irrational has a finite decimal expansion.','Removing any subset from R preserves its cardinality.','There are more irrational symbols than rational symbols.'],'R is the union of its rational and irrational parts. A union of two countable sets is countable, contradicting the uncountability of R.',True)
    ])
    case('Hilbert hotel and paired indices','2.5',[5,7,19,21], 'A hotel has rooms 1,2,3,… and every room is occupied. Guests and arrivals are indexed by positive integers.',
         'Construct injective reassignment plans and enumerate products of countable sets.', 'A valid reassignment must avoid collisions and reserve enough rooms for every arrival.')
    rows([
      ('How can 12 new guests be accommodated without evicting anyone?','Move old guest n to n+12; use rooms 1 through 12 for arrivals.',['Move old guest n to n−12 for every n.','Put all arrivals into room 1.','Keep every old guest fixed and choose an already occupied room.'],'The shift is injective, preserves positive room numbers, and leaves exactly the first twelve rooms free.'),
      ('How can countably many new guests be accommodated?','Move old guest n to 2n; put new guest k in 2k−1.',['Move old guest n to n+1 and place all new guests in room 1.','Use only room 1 for every old guest.','Assign old and new guest n both to 2n.'],'Even and odd positive integers partition the rooms, and each mapping is injective.'),
      ('Why is Z⁺×Z⁺ countable?','List pairs by increasing sum of coordinates, then within each finite diagonal.',['It is a finite set.','Multiplying two infinite cardinalities always gives uncountability.','List all pairs with first coordinate 1 before ever proceeding to 2.'],'Each diagonal i+j=s is finite and every pair belongs to one. Finishing an infinite first row before moving on never reaches later rows.'),
      ('What is wrong with moving guest n to ⌊n/2⌋?','It creates collisions and can assign room 0.',['It is injective but not onto.','It only fails because infinitely many rooms exist.','Every guest keeps the same room.'],'Guests 2 and 3 both go to room 1, while guest 1 goes to nonexistent room 0. A reassignment needs distinct valid rooms.',True),
      ('Why can a countable union of countable sets be enumerated in this setting?','Index elements by a pair (set index, within-set index) and traverse diagonally, skipping repetitions.',['Every union contains only finitely many elements.','Every set must have exactly the same elements.','List one infinite set completely before starting the next.'],'The double indexing reduces enumeration to countable pairs. Skipping repeats avoids listing the same element twice; exhausting one infinite row sequentially is ineffective.',True)
    ])

def matmul(a,b,boolean_product=False):
    return [[int(any(a[i][k] and b[k][j] for k in range(len(b)))) if boolean_product else sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]

def matrices_algorithms():
    block('Matrices & algorithm reasoning')
    for k,(a,b) in enumerate([([[2,1],[-1,3]],[[0,4],[2,-1]]),([[1,-2],[3,0]],[[2,1],[-1,4]]),([[0,3],[2,1]],[[1,-1],[4,2]])]):
        ab=matmul(a,b);ba=matmul(b,a);a2=matmul(a,a)
        case(f'Matrix multiplication {k+1}','2.6',[3,11,13,17],f'Matrices are written as lists of rows. A={a}; B={b}. Indices start at 1. Products in this workshop are ordinary arithmetic products.',
             'Apply row-column multiplication, distinguish AB from BA, and reverse order when transposing a product.', 'For entry (i,j), take row i from the left matrix and column j from the right matrix.')
        for prompt,val,query,reason,adv in [
          ('What is entry (1,2) of AB?',ab[0][1],'ab12',f'Row 1 of A dotted with column 2 of B gives {a[0][0]}·{b[0][1]}+{a[0][1]}·{b[1][1]}={ab[0][1]}.',False),
          ('What is entry (1,2) of BA?',ba[0][1],'ba12',f'Reverse the roles: {b[0][0]}·{a[0][1]}+{b[0][1]}·{a[1][1]}={ba[0][1]}. Matrix multiplication need not commute.',False),
          ('What is the sum of diagonal entries of AB?',ab[0][0]+ab[1][1],'diagonal',f'AB={ab}; add entries (1,1) and (2,2), obtaining {ab[0][0]}+{ab[1][1]}.',False),
          ('What is entry (2,1) of A²?',a2[1][0],'square21',f'A² means AA, not entrywise squaring. Entry (2,1) is {a[1][0]}·{a[0][0]}+{a[1][1]}·{a[1][0]}={a2[1][0]}.',True),
          ('What is entry (2,1) of BᵀAᵀ?',ab[0][1],'transpose21',f'BᵀAᵀ=(AB)ᵀ, so its (2,1) entry is the (1,2) entry of AB, namely {ab[0][1]}. Transposition reverses product order.',True)]:
            num(prompt,val,reason,'matrix',dict(a=a,b=b,query=query),adv)
    for k,(a,b) in enumerate([([[1,0,1],[0,1,0],[1,1,0]],[[0,1,0],[1,0,1],[0,0,1]]),([[0,1,0],[1,0,1],[0,0,1]],[[1,0,1],[0,1,1],[1,0,0]])]):
        ab=matmul(a,b,True);a2=matmul(a,a,True);a3=matmul(a2,a,True)
        case(f'Boolean matrices {k+1}','2.6',[27,29,31,35],f'A={a}; B={b}, with each inner list a row. Join ∨ and meet ∧ act entrywise. Boolean product ⊙ uses AND for multiplication and OR for addition. Indices start at 1.',
             'Compute joins, meets and Boolean powers without substituting ordinary addition.', 'A Boolean-product entry is 1 if at least one corresponding pair of factors is both 1.')
        join=sum(a[i][j] or b[i][j] for i in range(3) for j in range(3));meet=sum(a[i][j] and b[i][j] for i in range(3) for j in range(3))
        for prompt,val,query,why,adv in [
          ('How many 1 entries does A∨B have?',join,'join',f'Apply OR in each of the nine positions and count once per position; there are {join} ones.',False),
          ('How many 1 entries does A∧B have?',meet,'meet',f'Only positions where both entries are 1 survive; there are {meet} such positions.',False),
          ('How many 1 entries does A⊙B have?',sum(map(sum,ab)),'product',f'The Boolean product is {ab}; count its 1 entries, not the number of successful intermediate witnesses.',False),
          ('What is entry (1,2) of A⊙A?',a2[0][1],'square12',f'The Boolean square is {a2}. Its first-row, second-column entry is {a2[0][1]}.',True),
          ('How many 1 entries does (A⊙A)⊙A have?',sum(map(sum,a3)),'cube',f'First A⊙A={a2}; then Boolean-multiply by A to obtain {a3}. Count the ones in that matrix.',True)]:
            num(prompt,val,why,'boolean-matrix',dict(a=a,b=b,query=query),adv,alternatives=[0,1,2,3,4,5,6,7,8,9])
    case('Tracing binary search','3.1',[13,27], 'Search the increasing list [2,5,8,12,17,23,31,44,58] for 23. Use 1-based indices, low=1, high=9. At each step mid=⌊(low+high)/2⌋; compare the target with a[mid], stop if equal, otherwise discard mid and the impossible half.',
         'Trace an explicitly specified search and state its invariant and precondition.', 'Track low, high, and mid; the retained interval must still contain every possible target location.')
    rows([
      ('Which indices are examined in order?','5, 7, 6',['5, 6','4, 6','5, 3, 4'],'First mid=5 gives 17<23, so low=6. Next mid=7 gives 31>23, so high=6. Then mid=6 finds 23.'),
      ('After the first iteration, which interval remains?','[6,9]',['[1,4]','[5,9]','[1,9]'],'The middle value 17 is smaller than 23, so indices 1 through 5 can be discarded. Low becomes mid+1=6.'),
      ('What precondition justifies discarding half the list?','The list is sorted in increasing order.',['The list length is odd.','All values are positive.','The target is at the original midpoint.'],'Sorted order ensures every value on the discarded side is too small or too large. Odd length and positivity are not required.'),
      ('Which invariant supports correctness?','If the target occurs, its index remains in [low,high] until found.',['The target is always exactly at mid.','Every discarded value equals the target.','The interval length stays constant.'],'The comparison and sorted order preserve all feasible target positions in the retained interval. Its length decreases, rather than staying constant.',True),
      ('Which change can cause a nonterminating unsuccessful search?','Using low=mid instead of mid+1 when a[mid]<target.',['Using high=mid−1 when a[mid]>target.','Stopping immediately on equality.','Stopping when low>high.'],'With a one-element interval below the target, low=mid makes no progress. Discarding mid strictly shrinks the interval.',True)
    ])
    case('Bubble-sort passes','3.1',[37,41], 'Bubble sort [6,1,5,2,4] in ascending order. A pass compares adjacent pairs left to right, swapping when the left entry is larger. Pass 1 visits pairs (1,2),(2,3),(3,4),(4,5); each later pass omits the sorted suffix.',
         'Trace adjacent exchanges and identify the invariant of a completed pass.', 'A left-to-right pass pushes the largest remaining element to the right boundary.')
    rows([
      ('What is the list after the first full pass?','[1,5,2,4,6]',['[1,2,4,5,6]','[1,6,2,4,5]','[6,1,2,4,5]'],'The 6 swaps with 1,5,2,4 successively, producing [1,5,2,4,6]. One pass does not necessarily sort the entire list.'),
      ('How many swaps occur in the first pass?','4',['1','3','5'],'The initial maximum 6 moves across all four neighboring elements, requiring four swaps.'),
      ('What is the list after the second pass?','[1,2,4,5,6]',['[1,5,2,4,6]','[2,1,4,5,6]','[1,2,5,4,6]'],'Within the first four entries, 1≤5, then 5 swaps with 2 and 4, leaving 5 in position 4.'),
      ('Without early termination, how many adjacent comparisons do all passes use for n=5?','10',['5','9','20'],'The passes make 4+3+2+1=10 comparisons. Comparisons and swaps are different counts.',True),
      ('Why may the final entry be excluded after the first pass?','It is a maximum of the original list and already in a valid final position.',['It is necessarily a minimum.','Every entry is now sorted.','Bubble sort never compares the final entry.'],'The pass compares and carries the running maximum to the last position; remaining work is confined to the prefix.',True)
    ])
    case('Insertion-sort reasoning','3.1',[41,47,53], 'Insertion sort processes [7,3,6,2,5] left to right. To insert a key, shift larger entries in the sorted prefix one place right, then place the key. Count only comparisons of prefix values with the key, not index-bound checks.',
         'Trace a growing sorted prefix and distinguish data movement from key comparisons.', 'The prefix is sorted before each insertion; the untouched suffix need not be sorted.')
    rows([
      ('What is the list immediately after inserting the third original element, 6?','[3,6,7,2,5]',['[2,3,5,6,7]','[3,7,6,2,5]','[6,3,7,2,5]'],'First insert 3 before 7, obtaining [3,7,6,2,5]; then shift 7 and put 6 between 3 and 7.'),
      ('How many prefix elements shift when key 2 is inserted?','3',['1','2','4'],'The sorted prefix [3,6,7] has all three values larger than 2, so each shifts right.'),
      ('When 5 is inserted into [2,3,6,7], how many key comparisons occur?','3',['2','4','5'],'Compare 7>5 and 6>5 (shift both), then 3>5 is false (stop). The failed stopping comparison still counts.'),
      ('Which invariant explains correctness?','Before each insertion, the processed prefix is sorted and contains precisely the processed original elements.',['The entire list is sorted after each comparison.','The suffix always contains the smallest values.','Every insertion shifts every previous value.'],'Inserting the next key into the correct location preserves sortedness and membership of the enlarged prefix.',True),
      ('With distinct increasing input of length n, how many key comparisons are required?','n−1',['0','n(n−1)/2','n²'],'Each of the n−1 insertions performs one failed comparison with its immediate predecessor and shifts nothing. This is a best-case linear count.',True)
    ])
    case('Greedy choices versus optimality','3.1',[57,59], 'Unlimited coins of values 1,4,6 are available. The greedy rule repeatedly takes the largest coin not exceeding the remainder. The objective is the fewest coins.',
         'Trace a greedy rule and disprove its optimality with a valid feasible improvement.', 'A locally largest coin need not minimize the total number of later coins.')
    rows([
      ('What does greedy choose for amount 8?','6,1,1',['4,4','6,4','1,1,1,1,1,1,1,1'],'Greedy first takes 6, leaving 2; only 1 fits, twice. The pair 4,4 is optimal but is not the greedy trace.'),
      ('What is the minimum number of coins for amount 8?','2',['1','3','8'],'Two 4-coins suffice. One coin cannot, since 8 is not an available denomination; hence two is optimal.'),
      ('What does the amount-8 example establish?','This greedy rule is not optimal for every amount in this coin system.',['Greedy algorithms never solve any problem optimally.','No algorithm can make amount 8.','The amount-8 greedy answer is infeasible.'],'The greedy answer is feasible but uses three coins instead of two. One counterexample refutes universal optimality for this system, not every greedy algorithm.'),
      ('What is the greedy decomposition of 12 and its optimal coin count?','6+6; optimal count 2',['6+4+1+1; optimal count 4','4+4+4; optimal count 3','6+6; optimal count 3'],'Greedy takes two 6s. Since the largest coin is 6, one coin cannot total 12, proving optimality in this instance.',True),
      ('Why does the presence of a 1-coin ensure this rule terminates for a nonnegative integer amount?','Each chosen coin decreases the nonnegative remainder, and any positive remainder admits a coin.',['It proves the fewest-coin property.','It makes every choice unique across all algorithms.','It lets the remainder increase indefinitely.'],'A strictly decreasing nonnegative integer cannot decrease forever; the 1-coin prevents getting stuck above zero. Termination does not establish optimality.',True)
    ])
    case('Algorithm specification and correctness','3.1',[1,3,7,9], 'An algorithm must solve its stated problem for every allowed input and terminate. Input assumptions and counted operations are part of the specification.',
         'Distinguish termination, correctness, invariants, and counterexamples to an implementation.', 'Try empty inputs, negative values, repeated values, and boundary indices against the stated domain.')
    rows([
      ('To find the maximum of a nonempty list of arbitrary integers, why can initializing max=0 be wrong?','An all-negative list would incorrectly return 0.',['Zero is not an integer.','All maxima are positive.','The list must be sorted first.'],'On [−5,−2], no value exceeds 0, so the algorithm returns a value not in the list. Initialize with the first element instead.'),
      ('Which invariant fits a correct maximum scan initialized from the first element?','After processing i entries, max equals the maximum of those i entries.',['max is always the last value read.','The entire list becomes sorted.','max decreases at every step.'],'Updating max when a larger entry appears maintains exactly the maximum of the processed prefix.'),
      ('A loop starts n=1 and repeatedly sets n=2n while n>0 over mathematical integers. What fails?','Termination',['The multiplication operation is undefined.','Input is missing.','n becomes zero after finitely many steps.'],'The values 1,2,4,8,… remain positive. Under mathematical integer arithmetic there is no overflow to end the loop.'),
      ('Why is a finite test suite not by itself a correctness proof for all integer lists?','Unseen allowed inputs may expose errors; a general invariant or argument is needed.',['Testing is never useful.','All integer lists are finite in number.','Any tested algorithm must be correct.'],'The input domain contains arbitrarily many lists. Testing can find errors, while a proof accounts for all allowed inputs.',True),
      ('How many symmetric character pairs need checking to recognize a palindrome of length n?','⌊n/2⌋',['n²','2n','n−1 for every n'],'Compare positions i and n+1−i until the middle. Each pair covers two positions, and an odd middle character matches itself automatically.',True)
    ])

def complexity():
    block('Growth rates & operation counts')
    case('Polynomial bounds with witnesses','3.2',[3,7,9,29], 'For real x≥1, let f(x)=4x³+7x²+2. Big-O uses positive C and a threshold k: |f(x)|≤C|g(x)| for all x>k.',
         'Give valid upper and lower bounds, and distinguish a valid bound from a tight one.', 'For x≥1, each lower power is at most the leading power; a lower bound comes from the leading positive term.')
    rows([
      ('Which witnesses establish f(x)∈O(x³)?','C=13, k=1',['C=4, k=1','C=1, k=1','C=0, k=1'],'For x≥1, 7x²≤7x³ and 2≤2x³, so f(x)≤13x³. C=4 fails because both lower terms are positive; the smaller constants also fail.'),
      ('Which lower bound holds for all x≥1?','f(x)≥4x³',['f(x)≥14x³','f(x)≥x⁴','f(x)≥2ˣ'],'The lower-order terms are nonnegative, so f≥4x³. The constant 14 already fails near x=1; x⁴ and 2ˣ eventually outgrow f.'),
      ('What is the tight asymptotic class of f?','Θ(x³)',['Θ(x²)','Θ(x⁴)','Θ(2ˣ)'],'Combining 4x³≤f(x)≤13x³ for x≥1 gives matching cubic lower and upper bounds.'),
      ('Why is f not O(x²)?','f(x)/x²≥4x grows without bound.',['Its value exceeds x² at one input.','It has four terms.','Big-O never applies to polynomials.'],'No fixed constant C can bound the unbounded ratio for all sufficiently large x. One isolated comparison would not suffice.',True),
      ('Which statement about O(x⁴) is correct?','f∈O(x⁴), but this is a looser upper bound than Θ(x³).',['f∉O(x⁴) because its degree is 3.','f∈Θ(x⁴).','O(x⁴) means exactly x⁴ operations at every input.'],'For x≥1, x³≤x⁴, so the cubic upper bound implies a quartic one. Big-O is an upper-bound relation, not necessarily a tight estimate.',True)
    ])
    case('Rational functions and dominant terms','3.2',[5,7,25,29], 'For real x≥1, let f(x)=(2x⁴+3x)/(5x²+1). The denominator is positive.',
         'Bound numerator and denominator in the correct directions to prove a tight order.', 'For a quotient lower bound, bound the numerator below and denominator above; reverse those directions for an upper bound.')
    rows([
      ('Which bound is valid for the denominator on x≥1?','5x²≤5x²+1≤6x²',['5x²+1≤5x²','5x²+1≥6x² for all x≥1','5x²+1=x²'],'Since 1≤x², adding it to 5x² produces at most 6x² and at least 5x².'),
      ('Which lower bound follows?','f(x)≥x²/3',['f(x)≥3x²','f(x)≥x⁴','f(x)≥2ˣ'],'Use numerator≥2x⁴ and denominator≤6x² to obtain f≥(2x⁴)/(6x²)=x²/3.'),
      ('Which upper bound follows for x≥1?','f(x)≤x²',['f(x)≤1','f(x)≤x','f(x)≤x²/4'],'Because 3x≤3x⁴, the numerator≤5x⁴; denominator≥5x². Hence f≤x². The other bounds fail for large x.'),
      ('What is the tight growth rate?','Θ(x²)',['Θ(x)','Θ(x⁴)','Θ(1)'],'The two-sided bounds x²/3≤f(x)≤x² establish quadratic growth without cancellation of unequal polynomial terms.',True),
      ('Why is “drop the denominator because it is smaller than the numerator” invalid?','A growing denominator changes the growth rate; here its quadratic growth reduces degree four to degree two.',['Dividing polynomials always gives a constant.','Only constant functions have denominators.','Big-O forbids rational functions.'],'Dominance is assessed within sums; a division must retain the denominator’s growth. Here x⁴/x² is x², not x⁴.',True)
    ])
    case('Comparing exponential and logarithmic growth','3.2',[13,19,21], 'All logarithms have a fixed base greater than 1. The variable n tends through positive integers to infinity.',
         'Compare growth classes while distinguishing exponent changes from constant multipliers.', 'Rewrite exponent shifts as constant factors and exponent scaling as a change of base.')
    rows([
      ('How does 2^(n+5) compare with 2ⁿ?','It is Θ(2ⁿ) because it equals 32·2ⁿ.',['It is Θ(n·2ⁿ).','It is Θ(4ⁿ).','It is O(n⁵).'],'Adding a fixed constant to the exponent multiplies by a fixed constant, which does not change Θ.'),
      ('Why is 2^(2n) not O(2ⁿ)?','The ratio 2^(2n)/2ⁿ=2ⁿ is unbounded.',['Both functions have base 2, so they are equal.','The ratio is the constant 2.','It has a larger value at n=1 only.'],'Scaling the exponent yields 4ⁿ. The exponentially growing ratio prevents any fixed Big-O constant.'),
      ('Which order is increasing asymptotically?','(log n)³, √n, n log n, n², 1.2ⁿ',['√n, (log n)³, n², n log n, 1.2ⁿ','1.2ⁿ, n², n log n, √n, (log n)³','(log n)³, √n, 1.2ⁿ, n log n, n²'],'Fixed powers of log grow slower than positive powers of n; n log n is between n and n²; any fixed exponential base greater than 1 eventually beats polynomials.'),
      ('Why are log₂n and log₁₀n in the same Θ class?','Change of base multiplies by the fixed positive constant log₂10.',['They are equal for every n.','All logarithms are constant.','The logarithm base can grow arbitrarily with n without changing Θ.'],'log₂n=(log₂10)·log₁₀n. This argument requires fixed bases; the base cannot silently depend on n.',True),
      ('Which relation between n! and 2ⁿ is correct?','2ⁿ∈O(n!), but n!∉O(2ⁿ).',['n!∈Θ(2ⁿ).','n!∈O(n²).','2ⁿ∉O(n!).'],'For n≥4, at least roughly n/2 factors of n! are at least n/2; their product eventually dominates 2ⁿ by an unbounded factor. Factorials outgrow fixed-base exponentials.',True)
    ])
    case('Checking witness thresholds','3.2',[1,3,9], 'Let f(x)=5x²+8 on real x>0. A proposed proof claims C=6 and k=2 witness f(x)∈O(x²).',
         'Check a claimed inequality over its full domain and repair a defective threshold.', 'Reduce 5x²+8≤6x² to its simplest inequality and inspect values just above the threshold.')
    rows([
      ('What inequality must hold for these proposed witnesses?','8≤x² for every real x>2',['8≤x for every real x>2','5x²≤8','x≤2'],'Subtract 5x² from both sides. The definition requires all real inputs above k, not just integers or a few examples.'),
      ('Which x refutes this specific witness pair?','x=5/2',['x=3','x=4','x=10'],'At 2.5>2, x²=6.25<8. At 3,4,10 the required inequality holds.'),
      ('Which change repairs the proof while keeping C=6?','Use k=3.',['Use k=1.','Use k=0.','Keep k=2 and ignore nonintegers.'],'For x>3, x²>9>8. Ignoring nonintegers changes the stated domain and is not a repair of this real-domain proof.'),
      ('What if the domain were positive integers instead?','C=6,k=2 would work because integer x>2 implies x≥3.',['The same pair still fails at x=2.5 in that domain.','Big-O is undefined on integers.','A threshold must itself be an input.'],'The counterexample 2.5 is excluded. Every allowed integer beyond 2 meets x²≥9>8, illustrating why domains matter.',True),
      ('Does failure of one witness pair disprove f∈O(x²)?','No; a different positive constant and threshold may work.',['Yes; every possible witness pair must work.','Yes; Big-O forbids lower-order terms.','No; every function is O(x²).'],'Big-O asserts existence of suitable witnesses. C=6,k=3 repairs this pair, and C=13,k=1 is another valid choice.',True)
    ])
    case('Combining bounds carefully','3.2',[17,25,31,39,43,45,47], 'Functions below are eventually nonnegative unless otherwise stated. O is an upper bound; Ω is a lower bound; Θ requires both.',
         'Compose valid asymptotic bounds without inventing lower bounds or ignoring cancellation.', 'An upper bound alone does not imply a matching lower bound, and subtraction can cancel leading terms.')
    rows([
      ('If f∈O(n²) and g∈O(n³), which is guaranteed?','f+g∈O(n³)',['f+g∈Θ(n³)','f+g∈Ω(n³)','f+g∈O(n)'],'The sum is at most a constant times n²+n³, hence O(n³). Either function could be small, so a cubic lower bound is not guaranteed.'),
      ('If f∈Θ(n²) and g∈Θ(n³), both eventually positive, what is fg?','Θ(n⁵)',['Θ(n⁶)','Θ(n³)','Θ(n²)'],'Multiply positive lower bounds and positive upper bounds: constant multiples of n²·n³=n⁵ sandwich the product.'),
      ('Which condition is equivalent to f∈Θ(g)?','f∈O(g) and f∈Ω(g)',['f∈O(g) or f∈Ω(g)','f∈O(g) only','f∈Ω(g) only'],'A tight asymptotic bound needs both directions of eventual constant-factor control.'),
      ('If f=n³+n and g=n³, what is f−g?','Θ(n)',['Θ(n³)','Θ(n⁶)','Θ(1)'],'The cubic terms cancel exactly, leaving n. Applying a maximum-degree heuristic blindly to subtraction would miss this.',True),
      ('Why does f∈O(g) and g∉O(f) alone not define little-o for arbitrary oscillating positive functions?','It need not force f(n)/g(n)→0.',['Every Big-O relation is automatically little-o.','Little-o allows a ratio tending to 1.','Positive functions cannot oscillate.'],'For even n let f(n)=n, for odd n let f(n)=1, and let g(n)=n. Then f∈O(g), g∉O(f), but f/g equals 1 on even n and does not tend to 0.',True)
    ])
    case('Triangular nested loops','3.3',[1,3,9], 'For integer n≥1, execute:\nfor i=1,…,n:\n  for j=1,…,i:\n    tick()\nCount only calls to tick, not loop-control operations.',
         'Sum dependent loop bounds and prove matching asymptotic bounds.', 'The inner loop length changes with i; add the lengths instead of assuming n iterations every time.')
    num('How many tick calls occur when n=12?',78,'The count is 1+2+…+12=12·13/2=78.','loop',dict(type='triangle',n=12))
    num('How many additional tick calls occur when n changes from 12 to 24?',222,'T(24)−T(12)=24·25/2−78=300−78=222.','loop',dict(type='triangle-difference',n=12))
    rows([
      ('What is the exact count T(n)?','n(n+1)/2',['n²','n(n−1)/2','n+1'],'There are i calls at outer index i, so T=Σᵢ₌₁ⁿi=n(n+1)/2.'),
      ('Which argument establishes T(n)∈Θ(n²)?','n²/2≤n(n+1)/2≤n² for n≥1.',['T(n)≤n² alone establishes Θ.','T(12)=78 alone establishes Θ.','Every nested loop is Θ(n²) regardless of its bounds.'],'The displayed two-sided inequalities give positive quadratic lower and upper constants. An upper bound alone gives only Big-O.',True),
      ('If the inner loop changes to j=i,…,n, what happens to the total?','It is unchanged: the lengths become n,n−1,…,1.',['It doubles exactly.','It becomes n.','It becomes n².'],'The lengths reverse order but still sum to n(n+1)/2. Endpoints are inclusive.',True)
    ])
    case('Doubling-loop boundaries','3.3',[1,3], 'For integer n≥1, set j=1 and repeat tick(); j=2j while j≤n. Count only calls to tick.',
         'Handle logarithmic loop boundaries and powers-of-two off-by-one errors.', 'The visited values are 1,2,4,… up to the largest power of two not exceeding n.')
    num('How many tick calls occur for n=64?',7,'Visited values are 1,2,4,8,16,32,64: seven calls.','loop',dict(type='doubling',n=64))
    num('How many tick calls occur for n=63?',6,'The largest visited power is 32, so there are six calls; 64 exceeds the limit.','loop',dict(type='doubling',n=63))
    rows([
      ('What is the exact call count for n≥1?','⌊log₂n⌋+1',['⌈log₂n⌉','n','2⌊log₂n⌋'],'Visited exponents are 0 through ⌊log₂n⌋ inclusive; there is one call per exponent.'),
      ('If j starts at 0 instead, what occurs for n≥1?','The loop never terminates because doubling keeps j=0.',['It makes one fewer call.','It still takes Θ(log n) calls.','It skips the loop entirely.'],'The condition 0≤n stays true and j=2·0 remains 0. The positive initialization is essential to progress.',True),
      ('If the loop is run once for each i=1,…,n with j reset to 1, what is the total asymptotic count?','Θ(n log n)',['Θ(log n)','Θ(n²)','Θ(n)'],'Each of n independent outer iterations performs ⌊log₂n⌋+1 calls. Multiplying these gives Θ(n log n) as n grows.',True)
    ])
    case('Geometrically shrinking work','3.3',[1,3,9], 'Let n=2ᵏ, k≥0. Set m=n. While m≥1, execute tick exactly m times, then set m=m/2. Count only tick calls.',
         'Distinguish logarithmic depth from the sum of varying work at each level.', 'List the work at successive levels: n,n/2,n/4,…,1.')
    num('How many tick calls occur when n=32?',63,'The work is 32+16+8+4+2+1=63.','loop',dict(type='shrinking',n=32))
    num('How many outer iterations occur when n=32?',6,'The outer m values are 32,16,8,4,2,1. After the sixth iteration m=1/2 and the condition fails.','loop',dict(type='shrinking-levels',n=32))
    rows([
      ('What is the exact total for power-of-two n?','2n−1',['n log₂n','log₂n+1','n²'],'The finite geometric series n+n/2+…+1 equals 2n−1.'),
      ('Why is the total Θ(n), even though the outer loop has Θ(log n) iterations?','The inner work shrinks geometrically instead of remaining n at each level.',['Every logarithmic-depth loop is linear.','Only the final level counts.','Nested loops cannot be logarithmic.'],'Summing the actual level costs yields 2n−1. Multiplying n by the number of levels gives a valid loose upper bound, not a tight count.',True),
      ('If every level instead executes exactly n tick calls, what is the total?','n(log₂n+1)',['2n−1','n+log₂n','log₂n+1'],'There are log₂n+1 levels, each now with fixed cost n, so multiplication is appropriate for this changed program.',True)
    ])
    case('Search cost and averages','3.3',[5,7,23,25], 'Linear search checks positions 1 through n in order, stopping at the first match. Count one equality comparison per checked item. For average successful search, assume distinct items and each target position equally likely.',
         'Keep best, worst, and average costs distinct and state the probability assumption.', 'A target at position i uses exactly i equality tests under this counting model.')
    num('For n=15, what is the worst-case number of equality tests?',15,'The target may be last or absent, requiring all fifteen entries to be checked.','loop',dict(type='linear-worst',n=15))
    num('For n=15, what is the expected successful-search count under the stated distribution?',8,'Average positions 1 through 15: (1+…+15)/15=16/2=8.','loop',dict(type='linear-average',n=15))
    rows([
      ('What is the best-case count for a nonempty list?','1',['0','n','⌊log₂n⌋'],'A match at the first entry succeeds after one equality test. The model still requires that test.'),
      ('If target positions are not uniformly distributed, what is the expected successful count?','Σ from i=1 to n of i·Pr(target at i)',['Always (n+1)/2 regardless of probabilities.','Always n.','The maximum probability alone.'],'Expected cost is the probability-weighted sum of per-position costs. The familiar midpoint average assumes uniform probabilities.',True),
      ('Why is it wrong to call every O(n) search algorithm “worst-case exactly n comparisons”?','O(n) permits different constants and smaller growth, and must be tied to a specified cost model.',['O(n) is always an average-case statement.','Big-O counts only memory.','Any search requires n comparisons even on sorted data.'],'Big-O is an asymptotic upper bound, not an exact count or an automatic worst-case label. Binary search on sorted data has a smaller worst-case order.',True)
    ])
    case('Matrix algorithm operation accounting','3.3',[9,11], 'To multiply two n×n zero-one matrices, compute each Boolean output as n AND terms joined by n−1 OR operations. Do not short-circuit, and count only these AND and OR operations.',
         'Derive exact counts from an explicitly specified implementation and distinguish them from asymptotic growth.', 'Count operations per output entry, then multiply by the n² entries.')
    num('How many AND operations are used when n=4?',64,'There are 4² output entries and 4 ANDs per entry, giving 16·4=64.','loop',dict(type='matrix-and',n=4))
    num('How many OR operations are used when n=4?',48,'There are 4² entries and 4−1=3 ORs per entry, giving 16·3=48.','loop',dict(type='matrix-or',n=4))
    rows([
      ('What is the exact combined count?','2n³−n²',['2n³','n²','n³−n²'],'Each output uses n+(n−1)=2n−1 operations. Multiply by n² to get 2n³−n². Initializing an accumulator and OR-ing n times would be a different implementation.'),
      ('What is the tight asymptotic cost?','Θ(n³)',['Θ(n²)','Θ(n log n)','Θ(2ⁿ)'],'For n≥1, n³≤2n³−n²≤2n³, giving matching cubic bounds.',True),
      ('For an m×k matrix times a k×r matrix using the same model, what is the exact combined count?','mr(2k−1)',['mkr−mr','mk(2r−1)','2mkr always, with no lower-order correction'],'There are mr output entries, each requiring k ANDs and k−1 ORs. The shared dimension k determines work per entry.',True)
    ])

def base_repr(n,b):
    digits='0123456789ABCDEF'
    if n==0:return '0'
    out=''
    while n:
        n,r=divmod(n,b);out=digits[r]+out
    return out

def extended_gcd(a,b):
    if b==0:return a,1,0
    d,x,y=extended_gcd(b,a%b)
    return d,y,x-(a//b)*y

def number_theory():
    block('Divisibility, bases, primes & GCDs')
    for k,(a,m,b) in enumerate([(-137,12,29),(-221,17,43)]):
        q,r=divmod(a,m)
        case(f'Negative division and congruence {k+1}','4.1',[13,17,27,29,39],f'Let a={a}, b={b}, and modulus m={m}. Canonical remainders satisfy 0≤r<m; div uses the floor quotient.',
             'Apply the division algorithm to negative integers and preserve residues under arithmetic.', 'Choose q so that a=mq+r with a nonnegative remainder smaller than m.')
        specs=[('What is a div m?',q,'quotient',f'{a}={m}·({q})+{r}, with 0≤{r}<{m}. Truncation toward zero would give a negative remainder.',False),
               ('What is a mod m?',r,'remainder',f'From {a}={m}·({q})+{r}, the canonical remainder is {r}.',False),
               ('What is (a+b) mod m?',(a+b)%m,'sum',f'Reduce each term: ({r}+{b%m}) mod {m}={(a+b)%m}.',False),
               ('What is ab mod m?',a*b%m,'product',f'Multiply reduced residues: ({r}·{b%m}) mod {m}={a*b%m}.',True),
               ('What is (a²−b³) mod m?',(a*a-b**3)%m,'powers',f'Use residues first: ({r}²−{b%m}³) mod {m}={(a*a-b**3)%m}. Reduce the final difference to the canonical interval.',True)]
        for prompt,val,query,why,adv in specs:num(prompt,val,why,'modular',dict(a=a,b=b,m=m,query=query),adv)
    for k,(n,b) in enumerate([(365,2),(746,16)]):
        case(f'Integer representation {k+1}','4.2',[1,3,5,7,11,13,21,37],f'Use bases 2, 8, and 16 as indicated. In hexadecimal, A=10,…,F=15. The decimal integer N is {n}. All representations are unsigned.',
             'Convert bases by place value and repeated division, and reason about representation length.', 'Repeated-division remainders are read in reverse order; a base-b digit must be between 0 and b−1.')
        encoded=base_repr(n,b)
        choices(f'What is the base-{b} representation of N?',encoded,[base_repr(n+1,b),base_repr(n-1,b),base_repr(2*n,b)],
                f'Place values are powers of {b}. The representation {encoded} evaluates to {n}; its digits arise from successive division remainders read last to first.',verify=dict(op='base',args=dict(n=n,b=b,query='encode')))
        word=base_repr(n+53,b)
        num(f'What decimal integer is represented by ({word}) in base {b}?',n+53,
            f'Sum each digit times its positional power of {b}. The total is {n+53}.','base',dict(word=word,b=b,query='decode'))
        octal=base_repr(n,8)
        choices('What is the octal representation of N?',octal,[base_repr(n+8,8),base_repr(n-8,8),base_repr(n+1,8)],
                f'Repeated division by 8 gives {octal}. Alternatively group a binary representation in threes from the right.',verify=dict(op='base',args=dict(n=n,b=8,query='encode')))
        binarysum=base_repr(n+29,2)
        choices('What is the binary representation of N+29 (where 29 is decimal)?',binarysum,[base_repr(n+28,2),base_repr(n+30,2),base_repr(n*29,2)],
                f'The sum is {n+29} in decimal. Converting this sum or adding the two binary expansions with carries gives {binarysum}.',True,dict(op='base',args=dict(n=n+29,b=2,query='encode')))
        length=len(base_repr(n*n,b))
        num(f'How many base-{b} digits are needed to represent N² without leading zeros?',length,
            f'N²={n*n}. Since {b}^{length-1}≤{n*n}<{b}^{length}, exactly {length} digits are required.','base',dict(n=n*n,b=b,query='length'),True)
    for k,(a,b) in enumerate([(252,198),(414,180)]):
        d,x,y=extended_gcd(a,b);lcm=a*b//d;divs=[i for i in range(1,d+1) if d%i==0]
        remainders=[];v,w=a,b
        while w:
            remainders.append((v,w,v//w,v%w));v,w=w,v%w
        case(f'Euclidean algorithm {k+1}','4.3',[25,27,29,33,35,39],f'Let a={a} and b={b}. Count the final Euclidean division producing remainder 0 as one division.',
             'Connect Euclidean remainders, common divisors, least common multiples, and Bézout coefficients.', 'The last nonzero remainder is the gcd; each Euclidean step preserves the common divisors.')
        trace='; '.join(f'{v}={q}·{w}+{r}' for v,w,q,r in remainders)
        num('What is gcd(a,b)?',d,trace+f'. The last nonzero remainder is {d}.','gcd',dict(a=a,b=b,query='gcd'))
        num('What is lcm(a,b)?',lcm,f'For positive a,b, lcm=ab/gcd={a}·{b}/{d}={lcm}.','gcd',dict(a=a,b=b,query='lcm'))
        num('How many positive common divisors do a and b have?',len(divs),f'They are exactly the positive divisors of gcd={d}: {fmtset(divs)}.','gcd',dict(a=a,b=b,query='divisor-count'))
        num('How many Euclidean divisions are performed?',len(remainders),trace+f'. This is {len(remainders)} divisions including the final zero remainder.','gcd',dict(a=a,b=b,query='steps'),True)
        num(f'If gcd(a,b)=({x})a+tb, what is integer t?',y,f'Solve {d}=({x})·{a}+t·{b}, giving t=({d}−({x})·{a})/{b}={y}. Substitution verifies the Bézout identity.','gcd',dict(a=a,b=b,x=x,query='bezout'),True)
    case('Divisibility implications and counterexamples','4.1',[3,5,7,9,11,43], 'Unless a statement says otherwise, a,b,c are integers and every divisor in a|b is nonzero.',
         'Prove divisibility statements by integer witnesses and refute unsafe product cancellation.', 'Write b=ak for a divisibility hypothesis; keep track of which factors are known to divide which terms.')
    rows([
      ('If a|b and a|c, why does a|(5b−2c)?','Write b=au,c=av; then 5b−2c=a(5u−2v).',['Because divisibility applies to all real linear combinations.','Because b=c.','Because a must be prime.'],'The coefficient 5u−2v is an integer. Integer linear combinations preserve divisibility; arbitrary real coefficients do not.'),
      ('Which example refutes a|bc ⇒ a|b or a|c for general positive integers?','a=6,b=2,c=3',['a=2,b=4,c=5','a=3,b=6,c=9','a=5,b=10,c=2'],'6 divides 2·3, but divides neither 2 nor 3. In the other examples at least one factor is divisible by a.'),
      ('If nonzero a|b and b|a, what must hold?','|a|=|b|',['a=b always','a=−b always','a and b are both prime'],'Write b=ak and a=bℓ. Then kℓ=1, so k=ℓ=1 or k=ℓ=−1. Thus b=a or b=−a.'),
      ('Why is n²≡1 (mod 3) when 3 does not divide integer n?','The remaining residues are 1 and 2, whose squares are both 1 modulo 3.',['All integers square to 1 modulo 3.','n must be prime.','Only positive n have a remainder.'],'The residue cases 0,1,2 cover every integer including negatives. Excluding 0 leaves two cases, both with square residue 1.',True),
      ('Which cancellation is valid from ac≡bc (mod m), m≥2?','Conclude a≡b (mod m) if gcd(c,m)=1.',['Cancel c for every integer c.','Cancel only when c is prime, regardless of m.','Conclude a=b as ordinary integers.'],'Coprimality ensures m|c(a−b) implies m|(a−b). Without it, e.g. 2·1≡2·4 mod 6 but 1≢4 mod 6. Congruence also need not mean integer equality.',True)
    ])
    case('Prime testing and factorization','4.3',[1,3,5,7,9,19], 'A prime is an integer greater than 1 whose only positive divisors are 1 and itself. A composite is an integer greater than 1 that is not prime.',
         'Use the square-root divisor bound and factorization without misclassifying 0 or 1.', 'If n=ab is composite, at least one factor is at most √n, and that factor has a prime divisor.')
    rows([
      ('Which statement about 1 is correct?','It is neither prime nor composite.',['It is prime because it divides itself.','It is composite because it is not prime.','It has two distinct positive divisors.'],'Both prime and composite classifications require n>1. The number 1 has just one positive divisor.'),
      ('Which prime trial divisors suffice to test 131 for primality?','2,3,5,7,11',['2,3,5,7 only','Every integer up to 131 is required','13 and 17 only'],'√131 is between 11 and 12. Test all primes up to 11; none divides 131, so it is prime.'),
      ('What is the prime factorization of 1176?','2³·3·7²',['2²·3²·7²','2³·3·7','2³·3²·7'],'Divide by 8 to obtain 147=3·49. Thus 1176=8·3·49; the other products do not equal 1176.'),
      ('If p is prime and p|ab, what follows?','p|a or p|b',['p divides both factors.','p=a or p=b necessarily.','Both a and b must be prime.'],'Euclid’s lemma gives divisibility of at least one factor. If p∤a, gcd(p,a)=1 and a Bézout identity forces p|b.',True),
      ('Why is 2^15−1 composite without evaluating it?','2^15−1=(2⁵−1)(2¹⁰+2⁵+1), with both factors greater than 1.',['Every odd number is composite.','Every power of 2 minus 1 is prime.','15 is odd, so 2^15−1 is even.'],'Use t³−1=(t−1)(t²+t+1) with t=2⁵. A nontrivial factorization proves compositeness.',True)
    ])
    case('Coprimality versus pairwise coprimality','4.3',[15,17,25,27,31], 'Consider the positive integers 6,10,15. Pairwise relatively prime means every pair has gcd 1; gcd of an entire list is a different condition.',
         'Distinguish pairwise coprimality from having no common divisor of the entire list.', 'Compute all pair gcds separately; one global gcd does not control every pair.')
    rows([
      ('What is gcd(6,10,15)?','1',['2','3','5'],'gcd(6,10)=2 and gcd(2,15)=1. No prime divides all three.'),
      ('Are 6,10,15 pairwise relatively prime?','No: the pair gcds are 2,3,5.',['Yes, because their overall gcd is 1.','Yes, because all three are distinct.','No, because their overall gcd is 30.'],'gcd(6,10)=2, gcd(6,15)=3, and gcd(10,15)=5. Pairwise coprimality requires each to be 1.'),
      ('What is lcm(6,10,15)?','30',['60','900','1'],'The prime factorizations use 2,3,5 with maximum exponent one each, so the lcm is 2·3·5=30.'),
      ('What added condition is necessary when saying “two primes are relatively prime”?','The two primes must be distinct.',['Both primes must be odd.','Both primes must exceed 100.','One prime must divide the other.'],'A prime p has gcd(p,p)=p, not 1. Distinct primes share no prime divisor; 2 is allowed.',True),
      ('If gcd(a,b)=1 and gcd(a,c)=1, why is gcd(a,bc)=1?','Any prime common divisor of a and bc would divide b or c, contradicting one of the coprimality assumptions.',['Because b and c must also be relatively prime.','Because bc must be prime.','Because a must equal 1.'],'Apply Euclid’s lemma to any alleged common prime divisor. The assumptions do not require b,c to be coprime to one another.',True)
    ])
    case('Bézout identities and preserved gcds','4.3',[29,31,33,39], 'Integers a,b are not both zero. Bézout’s theorem states gcd(a,b)=sa+tb for some integers s,t. The gcd is taken positive.',
         'Use linear combinations to prove coprimality and understand Euclidean invariance.', 'Every common divisor divides every integer linear combination, including a displayed combination equal to 1.')
    rows([
      ('What follows from 1=5a−2b with integers a,b?','gcd(a,b)=1',['a=1 and b=2 necessarily','a and b must both be prime','lcm(a,b)=1'],'Every common positive divisor divides the right side and hence 1. This proves coprimality without requiring either input to be prime.'),
      ('Why is gcd(a,b)=gcd(b,a−3b)?','The two pairs have exactly the same common divisors.',['Subtracting always leaves the value of each integer unchanged.','a−3b must be positive.','Both gcds are automatically 1.'],'A common divisor of a,b divides a−3b; conversely a common divisor of b,a−3b divides (a−3b)+3b=a.'),
      ('What is gcd(−42,0)?','42',['−42','0','1'],'Positive common divisors of −42 and 0 are the positive divisors of 42, since every nonzero integer divides 0. The greatest is 42.'),
      ('For nonzero integers a,b, what is the sign-correct gcd–lcm identity when lcm is positive?','gcd(a,b)·lcm(a,b)=|ab|',['gcd(a,b)·lcm(a,b)=ab even when ab<0','gcd(a,b)+lcm(a,b)=|ab|','gcd(a,b)=lcm(a,b) always'],'Both gcd and lcm are positive, so their product equals the absolute product. Prime-exponent minima and maxima add to the two original exponents.',True),
      ('If a≡b (mod m), why is gcd(a,m)=gcd(b,m)?','a=b+km, so a,m and b,m have exactly the same common divisors.',['Congruent integers must be equal.','Every residue is coprime to m.','m must be prime for the claim to hold.'],'Adding an integer multiple of one input to the other preserves common divisors, exactly as in the Euclidean step. The modulus need not be prime.',True)
    ])

def write_midterm():
    assert len(BANK)==400 and len(BLOCKS)==8
    directory=ROOT/'data'/SLUG
    directory.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'data/inventory.json').read_text(encoding='utf-8'))
    entry=dict(id=SLUG,title=TITLE,course_dependent=False,description='400 slide-scoped questions, with related odd-numbered Rosen exercise pointers and worked reasoning.',blocks=[])
    inv=dict(id=SLUG,planned=400,generated=400,validated=0,blocks=[])
    for i,title in enumerate(BLOCKS):
        bid=f'{SLUG}-block-{i+1:02}'
        file=directory/f'block-{i+1:02}.json'
        data=dict(schema_version=1,block_id=bid,pillar_id=SLUG,block_title=f'{TITLE} · {title}',questions=BANK[i*50:(i+1)*50])
        file.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        entry['blocks'].append(dict(id=bid,title=f'{i+1}. {title}',path=file.relative_to(ROOT).as_posix(),count=50))
        inv['blocks'].append(dict(id=bid,planned=50,generated=50,validated=0))
    for data,new in [(manifest,entry),(inventory,inv)]:
        data['pillars']=[p for p in data['pillars'] if p['id']!=SLUG]+[new]
    manifest['total_questions']=sum(b['count'] for p in manifest['pillars'] for b in p['blocks'])
    inventory['requested_questions']=inventory['generated_questions']=manifest['total_questions']
    inventory['validated_questions']=sum(p['validated'] for p in inventory['pillars'])
    for filename,data in [('manifest.json',manifest),('inventory.json',inventory)]:
        (ROOT/'data'/filename).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    coverage=dict(title=TITLE,questions=400,blocks=8,intermediate=sum(q['difficulty']=='intermediate' for q in BANK),advanced=sum(q['difficulty']=='advanced' for q in BANK),
                  source_policy='Original questions matched to classroom subject matter; related odd exercise pointers refer to the locally supplied Rosen eighth edition. Source PDFs and extracted text are excluded from version control and deployment.',
                  scope='Propositional logic, quantifiers, inference and elementary proofs; sets, functions, sequences, sums, countability and matrices; algorithms and growth; divisibility, integer representations, primes and gcds. No induction unit, advanced recurrence solving, graph theory or later counting unit.',
                  sections={section:sum(q['curriculum']['section']==section for q in BANK) for section in sorted({q['curriculum']['section'] for q in BANK})})
    (directory/'coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Generated 400 midterm questions: {coverage["intermediate"]} intermediate, {coverage["advanced"]} advanced, eight blocks. Total bank: {manifest["total_questions"]}.')

def build():
    BANK.clear();BLOCKS.clear()
    for builder in [logic,quantifiers,proofs,sets_functions,sequences_countability,matrices_algorithms,complexity,number_theory]:builder()
    write_midterm()

def more_quantifiers():
    case('Arithmetic quantifier domains','1.4',[13,15,21,37], 'Compare domains Z (integers), Z⁺ (positive integers), and R (real numbers).',
         'Use witnesses and counterexamples to distinguish domain-dependent truth.', 'Try boundary values such as zero and a smallest positive integer before generalizing.')
    rows([
      ('Over Z, what establishes ∀x∃y (x+y=7)?','For each x, choose y=7−x.',['Choose x=0 and y=7 only.','Choose y=7 for every x.','Choose y=x for every x.'],'The dependent witness 7−x is an integer and works for every integer x. One example does not prove a universal claim.'),
      ('Why is ∀x∃y (x+y=7) false over Z⁺?','At x=7, the only possible y is 0, outside Z⁺.',['There are infinitely many x.','At x=1, y=6 is positive.','An existential witness must be independent of x.'],'The universal claim fails at x=7. Infinitude is not an obstruction, and ∀x∃y permits dependence.'),
      ('Over R, which claim is true?','∀x∃y (y>x)',['∃y∀x (y>x)','∀x∀y (y>x)','∃x∀y (y>x)'],'For any x take y=x+1. No single real exceeds all reals; equal values also refute the universal pair claim.'),
      ('Over R, which is the negation of ∀x≠0 ∃y (xy=1)?','∃x (x≠0 ∧ ∀y (xy≠1))',['∀x (x=0 ∨ ∃y (xy≠1))','∃x∀y (xy=1)','∀x≠0 ∀y (xy≠1)'],'Write the restriction as ∀x(x≠0 → ∃y xy=1). Negate the implication and both quantifiers. The counterexample must satisfy x≠0.',True),
      ('Which statement holds over R but fails over Z?','∀x∃y (2y=x)',['∀x∃y (y=x+1)','∀x (x²≥0)','∃x (x²=4)'],'In R take y=x/2. In Z the input x=1 has no integer half. The other three are true in both domains.',True)
    ])
    case('Chaining quantified inference','1.6',[5,9,13,15], 'All audited services are logged. No logged service is anonymous. Some service is audited. The domain is all services.',
         'Apply instantiation, modus ponens, and existential generalization with a consistent witness.', 'Keep the same witness when applying universal premises to an existentially chosen object.')
    rows([
      ('Which conclusion follows?','Some service is logged and not anonymous.',['All services are audited.','Some audited service is anonymous.','No service is logged.'],'Choose an audited witness a. Universal premises give logged(a) and not anonymous(a), then existentially generalize.'),
      ('Which formula translates the second premise?','∀x(L(x) → ¬N(x))',['∀x(¬L(x) → N(x))','∃x(L(x) ∧ ¬N(x))','∀x(N(x) → L(x))'],'“No logged service is anonymous” excludes L∧N for every x. An existential statement is weaker, and the other implications reverse or change the condition.'),
      ('After selecting an audited witness a, how is L(a) inferred?','Universal instantiation followed by modus ponens.',['Existential generalization alone.','Affirming the consequent.','Universal generalization from one witness.'],'Instantiate A(x)→L(x) at a, then combine with A(a). No inference from a single witness to all services is justified.'),
      ('Remove the existential premise. What can still be concluded?','Every audited service is not anonymous.',['An audited service exists.','Some logged service exists.','Every service is audited.'],'The implication A→¬N follows by chaining regardless of whether audited services exist. Universal statements alone need not supply a witness.',True),
      ('Which proposed extra inference is invalid?','A service is logged, therefore it is audited.',['A service is audited, therefore it is logged.','A service is anonymous, therefore it is not logged.','A service is audited, therefore it is not anonymous.'],'The invalid converse affirms the consequent of A→L. A logged service may be unaudited. The other implications follow directly or by contraposition.',True)
    ])
    case('Resolution and invalid converses','1.6',[3,9,11], 'Premises: p∨q, p→r, q→s, and ¬r. All premises are assumed true.',
         'Combine rules of inference and distinguish a conclusion from an unsupported converse.', 'Use modus tollens before disjunctive syllogism, and do not infer the antecedent from a consequent.')
    rows([
      ('What follows first from p→r and ¬r?','¬p',['p','r','¬q'],'Modus tollens derives ¬p. It says nothing directly about q.'),
      ('What follows from p∨q and the result ¬p?','q',['¬q','p∧q','¬p∧¬q'],'Disjunctive syllogism leaves q true when p is false.'),
      ('Which assignment satisfies every premise?','p=F, q=T, r=F, s=T',['p=T, q=F, r=F, s=T','p=F, q=F, r=F, s=T','p=F, q=T, r=F, s=F'],'¬r forces r false; p→r forces p false; p∨q forces q true; q→s forces s true.'),
      ('Which added premise makes this system inconsistent?','¬s',['¬p','q','s∨r'],'The original premises entail s, so adding ¬s is contradictory. Each other option is true in the satisfying assignment.',True),
      ('What clause results by resolution from ¬p∨r and p∨q?','q∨r',['q∧r','¬q∨r','p∨r'],'Resolve the complementary literals p and ¬p; retain q and r. Resolution gives a disjunction, not two separately established facts.',True)
    ])
    case('Witness discipline and proof scope','1.6',[13,15,17], 'P and Q are predicates on a nonempty domain. No relationship between their truth sets is assumed.',
         'Diagnose invalid witness reuse and restricted universal generalization.', 'Two existential statements may be witnessed by different objects.')
    rows([
      ('From ∃xP(x) and ∃xQ(x), what always follows?','∃x∃y (P(x)∧Q(y))',['∃x(P(x)∧Q(x))','∀x(P(x)∨Q(x))','∀xP(x)'],'Name separate witnesses a and b. The first conclusion preserves that distinction; a common witness need not exist.'),
      ('Which two-element model refutes ∃xP(x)∧∃xQ(x) ⇒ ∃x(P(x)∧Q(x))?','P holds only at 1; Q holds only at 2.',['P and Q both hold only at 1.','P holds nowhere; Q holds only at 2.','P and Q both hold everywhere.'],'The disjoint nonempty truth sets satisfy both premises but have empty intersection. The other models either satisfy the conclusion or fail a premise.'),
      ('Which operation is always valid?','From ∀xP(x), infer P(a) for a domain element a.',['From P(a), infer ∀xP(x) for an arbitrary named a.','From ∃xP(x), infer P(a) for every preselected a.','From ∃xP(x), infer uniqueness of its witness.'],'Universal instantiation applies to any element. Existence alone does not identify a preselected element or assert uniqueness.'),
      ('Why can an existentially chosen witness not automatically be universally generalized?','It may have special properties not shared by an arbitrary domain element.',['Universal generalization is never valid.','Existential witnesses must always be unique.','The domain must be infinite for generalization.'],'A witness was selected because it satisfies a property. Universal generalization needs an arbitrary element without such a restrictive assumption.',True),
      ('Which implication is valid even when P and Q have disjoint truth sets?','∀x(P(x)∧Q(x)) → (∀xP(x)∧∀xQ(x))',['(∃xP(x)∧∃xQ(x)) → ∃x(P(x)∧Q(x))','∀x(P(x)∨Q(x)) → (∀xP(x)∨∀xQ(x))','∃x(P(x)→Q(x)) → (∃xP(x)→∀xQ(x))'],'Universal quantification distributes over conjunction: instantiate at any element and simplify each conjunct. Existential conjunction and universal disjunction do not distribute in the proposed reverse directions.',True)
    ])

if __name__=='__main__':
    build()
