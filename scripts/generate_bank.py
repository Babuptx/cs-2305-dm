"""Reproducible original case workshops; four different tasks per case.
Each case has a stable topic/objective, not randomized number substitutions.
The generated JSON is the runtime source of truth. No network or dependencies.
"""
import itertools, json, math, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = {}
PILLARS = [
    ('logic', 'Logic and mathematical reasoning'),
    ('proofs', 'Proof techniques'),
    ('sets', 'Sets, relations, and functions'),
    ('counting', 'Counting and combinatorics'),
    ('graphs-number', 'Graph theory and number theory'),
    ('recurrences', 'Recurrence relations'),
]

def add(pillar, topic, prompt, correct, wrong, rationale, hint, objective=None, context='', verification=None):
    """wrong is a list of (option, specific misconception explanation)."""
    qs = BANK.setdefault(pillar, [])
    index = len(qs)
    assert len(wrong) == 3, (pillar, prompt)
    choices = [(str(correct), None)] + [(str(a), b) for a, b in wrong]
    assert len({a for a, _ in choices}) == 4, (prompt, choices)
    # Equal total key-position distribution; order is seeded separately per block.
    positions = [(v+2)%4 if index//50 % 2 else v for v in KEY_POSITIONS]
    random.Random(f'{pillar}-block-{index//50}').shuffle(positions)
    key = positions[index % 50]
    random.Random(f'{pillar}-{index}').shuffle(choices[1:])
    answer = choices.pop(0)
    random.Random(f'{pillar}-{index}').shuffle(choices)
    choices.insert(key, answer)
    q = dict(id=f'{pillar}-{index+1:03}', topic=topic,
             difficulty='foundational' if index < 32 else 'intermediate' if index < 76 else 'advanced',
             question_type='single_choice', prompt=prompt, context=context,
             options=[a for a, _ in choices], correct_index=key,
             hints=[hint, 'Write down the relevant definition, then test each proposed answer against every condition in this question.'],
             explanation=dict(learning_objective=objective or f'Apply {topic.lower()} with explicit justification.',
                              correct_rationale=rationale,
                              incorrect_rationales=[dict(option_index=i, rationale=b) for i, (_, b) in enumerate(choices) if i != key]),
             source_notes=['Original practice item. Rationale derived from the stated definitions; no claim of external expert review.'],
             has_exhibit=False, exhibit_url='')
    if verification is not None:
        q['verification'] = verification
    second_hints = {
      'logic': 'Track witness dependence in quantified statements; compare entire truth tables rather than a single row in propositional statements.',
      'proofs': 'Check that each claimed step uses only hypotheses already established. For induction, distinguish the assumed case from the case being proved.',
      'sets': 'Test set membership element by element. For a relation or function, look for a missing pair, collision, or unattained output.',
      'counting': 'Count disjoint alternatives by addition and independent successive choices by multiplication. A complement may simplify an at-least-one condition.',
      'graphs-number': 'Check graph claims against the full edge list. Check arithmetic claims by substituting the proposed quotient, residue, divisor, or inverse.',
      'recurrences': 'A pattern must satisfy every initial value and the recurrence itself. Substitute the candidate at a general index to check the transition.',
    }
    q['hints'][1] = second_hints[pillar]
    qs.append(q)

KEY_POSITIONS = ([0, 1, 2, 3] * 12) + [0, 1]
random.Random(2305).shuffle(KEY_POSITIONS)

def numeric(pillar, topic, prompt, value, rationale, hint, alternatives=None, verification=None, context=''):
    values = []
    bound = 8 if verification and verification.get('kind') in ['truth-count','negated-truth-count'] else None
    for v in (alternatives or []) + [value+1, value-1, value+2, value+3, value*2+1,0,1,2,3,4,5,6,7,8]:
        if bound is not None and v > bound: continue
        if v != value and v not in values and v >= 0:
            values.append(v)
        if len(values) == 3: break
    add(pillar, topic, prompt, value,
        [(v, f'The proposed result {v} fails the required computation: {rationale}') for v in values],
        rationale, hint, verification=verification, context=context)

def boolean_options(correct, candidates):
    return [(x, why) for x, why in candidates if x != correct][:3]

def logic():
    # Distinct Boolean structures, rather than relabeled instances of one formula.
    formulas = [
        ('p ∧ (q ∨ r)', lambda p,q,r:p and (q or r)),
        ('p ∨ (q ∧ r)', lambda p,q,r:p or (q and r)),
        ('(p → q) ∧ r', lambda p,q,r:(not p or q) and r),
        ('p → (q ∧ r)', lambda p,q,r:not p or (q and r)),
        ('(p ∧ q) → r', lambda p,q,r:not (p and q) or r),
        ('p ↔ (q ∨ r)', lambda p,q,r:p == (q or r)),
        ('p ⊕ (q ∧ r)', lambda p,q,r:p != (q and r)),
        ('(p ↔ q) ∨ r', lambda p,q,r:(p == q) or r),
        ('(p ⊕ q) ∧ ¬r', lambda p,q,r:(p != q) and not r),
        ('(p → q) ∧ (q → r)', lambda p,q,r:(not p or q) and (not q or r)),
        ('(p ∨ q) ∧ (¬p ∨ r)', lambda p,q,r:(p or q) and (not p or r)),
        ('(p ∧ q) ∨ (¬p ∧ r)', lambda p,q,r:(p and q) or (not p and r)),
        ('¬(p ↔ q) ∨ ¬r', lambda p,q,r:p != q or not r),
        ('(p → r) ↔ (q → r)', lambda p,q,r:(not p or r) == (not q or r)),
        ('(p ∨ q) ↔ r', lambda p,q,r:(p or q) == r),
        ('p ⊕ q ⊕ r', lambda p,q,r:p != q != r),
        ('¬p ∧ (q → r)', lambda p,q,r:not p and (not q or r)),
        ('(p ↔ q) ∧ (q ↔ r)', lambda p,q,r:p == q and q == r),
        ('(p ∧ ¬q) ∨ (q ∧ ¬r)', lambda p,q,r:(p and not q) or (q and not r)),
        ('((p → q) ∧ p) → q', lambda p,q,r:not ((not p or q) and p) or q),
    ]
    # Python chained comparison is not associative XOR; use an explicit parity rule.
    formulas[15] = ('p ⊕ q ⊕ r', lambda p,q,r:bool((int(p)+int(q)+int(r))%2))
    vals = list(itertools.product([False, True], repeat=3))
    def row(v): return '(' + ', '.join('T' if x else 'F' for x in v) + ')'
    for i, (expr, fn) in enumerate(formulas):
        bits = [bool(fn(*v)) for v in vals]
        ctx = 'p, q, r are propositions. → is material implication; ↔ is equivalence; ⊕ is exclusive OR. For parity XOR, associate left to right.'
        vector = ''.join('T' if b else 'F' for b in bits)
        variants = [vector[:j] + ('F' if vector[j]=='T' else 'T') + vector[j+1:] for j in [0,3,7]]
        trace = '; '.join(f'{row(v)}: {"T" if b else "F"}' for v,b in zip(vals,bits))
        add('logic','Truth-table evaluation',f'For F = {expr}, which output column follows the input order FFF, FFT, FTF, FTT, TFF, TFT, TTF, TTT?',vector,
            [(v,f'This column changes a required row. The actual evaluation is {trace}.') for v in variants],
            f'Evaluate the connectives from the innermost parentheses. In order: {trace}. Thus the column is {vector}.',
            'For each row, evaluate parentheses first. An implication is false only when its antecedent is true and its consequent is false.',context=ctx,
            verification={'kind':'truth-column','expression':expr,'expected':vector})
        count = sum(bits)
        numeric('logic','Satisfying valuations',f'How many assignments to p, q, r satisfy {expr}?', count,
                f'There are 2³ = 8 assignments. The output column is {vector}; exactly {count} positions are T.',
                'List the eight assignments systematically; count only rows in which the entire formula is true.', alternatives=[8-count,8,4,0],context=ctx,
                verification={'kind':'truth-count','expression':expr,'expected':count})
        # Distinguish logical equivalence from matching a single example.
        term = lambda v: '('+' ∧ '.join(name if b else '¬'+name for name,b in zip('pqr',v))+')'
        dnf = ' ∨ '.join(term(v) for v,b in zip(vals,bits) if b) or 'False'
        false_dnf = ' ∨ '.join(term(v) for v,b in zip(vals,bits) if not b) or 'False'
        add('logic','Canonical disjunctive form',f'Which sum of minterms is equivalent to {expr}?',dnf,
            [(false_dnf,'These minterms describe the false rows, so this is the negation of the formula.'),
             ('p ∧ ¬p','This contradiction is always false, but the given formula has a true row.'),
             ('p ∧ q ∧ r' if dnf != '(p ∧ q ∧ r)' else 'p ∧ q ∧ ¬r','This single minterm does not describe the full set of satisfying assignments.')],
            f'A minterm fixes all three truth values. Include precisely the true rows {vector}: {dnf}. Each included term is true on one row and no others.',
            'A canonical disjunctive form includes one conjunction per true row, using a negated variable for a false input.',context=ctx,
            verification={'kind':'dnf-equivalence','expression':expr})
        numeric('logic','Negation and model counting',f'How many assignments make ¬({expr}) true?',8-count,
                f'Negation reverses every output of {vector}. Of eight assignments, {count} satisfy the original, so 8 − {count} = {8-count} satisfy its negation.',
                'The truth sets of a proposition and its negation partition all assignments.',alternatives=[count,8,0,4],context=ctx,
                verification={'kind':'negated-truth-count','expression':expr,'expected':8-count})
    # Quantifier workshops: each probes translation, negation, witness, and scope.
    workshops = [
      ('Every process has a resource it can access.', '∀p ∃r A(p,r)', '∃p ∀r ¬A(p,r)',
       'A resource may depend on the process.', 'Choose a resource for each process separately.',
       '∃r ∀p A(p,r)', 'One resource works for every process; this is stronger.',
       '∃p ∃r A(p,r)', 'One successful access does not cover all processes.'),
      ('Some resource is accessible to every process.', '∃r ∀p A(p,r)', '∀r ∃p ¬A(p,r)',
       'One resource must work for all processes.', 'Choose the resource before considering arbitrary processes.',
       '∀p ∃r A(p,r)', 'Individual resources for processes need not be a common resource.',
       '∀p ∀r A(p,r)', 'Universal access to every resource is stronger than required.'),
      ('No process accesses every resource.', '∀p ∃r ¬A(p,r)', '∃p ∀r A(p,r)',
       'Each process misses at least one resource.', 'For an arbitrary process, identify a resource it cannot access.',
       '∃r ∀p ¬A(p,r)', 'A universally inaccessible resource is stronger than individual misses.',
       '∀p ∀r ¬A(p,r)', 'No access at all is stronger than missing one resource.'),
      ('Every process accesses every resource.', '∀p ∀r A(p,r)', '∃p ∃r ¬A(p,r)',
       'All process–resource pairs must succeed.', 'Take an arbitrary process and an arbitrary resource.',
       '∃p ∀r A(p,r)', 'A single process is insufficient.',
       '∀p ∃r A(p,r)', 'Only one accessible resource per process is insufficient.'),
      ('At least one process accesses at least one resource.', '∃p ∃r A(p,r)', '∀p ∀r ¬A(p,r)',
       'A single successful pair suffices.', 'Produce one process–resource pair with access.',
       '∀p ∃r A(p,r)', 'This requires coverage for all processes.',
       '∃p ∀r A(p,r)', 'This requires one process with all resources.'),
    ]
    for statement, formula, neg, scope, strategy, w1, r1, w2, r2 in workshops:
        context = 'The process domain and resource domain are nonempty. A(p,r) means process p can access resource r.'
        add('logic','Quantifier translation',f'Translate: “{statement}”',formula,[(w1,r1),(w2,r2),(neg,'This formula expresses the negation of the requested statement.')],
            f'{statement} {scope} The required quantifier order is {formula}.', 'Identify whether the statement requires all objects or a witness in each domain.',context=context)
        wrong_negs = [formula, f'¬({neg})', w1]
        # formula and ¬neg are equivalent but distinct strings; all are wrong for negation.
        if w1 in wrong_negs[:2]: wrong_negs[2] = w2
        add('logic','Negating quantified claims',f'Which formula is the negation of {formula}?',neg,
            [(x,'Negate every quantifier and the final predicate. This proposed formula does not perform those changes in the required scope.') for x in wrong_negs],
            f'Use ¬∀ = ∃¬ and ¬∃ = ∀¬, keeping quantifier order. The result is {neg}.', 'Move the negation inward one quantifier at a time.',context=context)
        add('logic','Witness dependence',f'What does the quantifier order in {formula} require?',scope,
            [('All quantified objects must be identical.','Distinct domains and quantification do not require identical objects.'),
             ('The order can always be reversed.','An existential choice inside a universal may depend on it; reversing their order changes that dependence.'),
             ('The statement describes exactly one successful access.','Existential quantifiers assert at least one, and universal quantifiers cover the domain; neither asserts exactly one.')],
            f'Interpret the quantifiers from left to right. {scope} This is the dependence encoded by {formula}.', 'Check whether an existential choice is inside or outside a universal quantifier.',context=context)
        add('logic','Constructing quantified proofs',f'Which proof plan correctly establishes {formula}?',strategy,
            [('Choose objects without establishing their access relation.','Picking objects alone does not prove A or ¬A for them, so the required predicate remains unproved.'),
             ('Assume the target statement and restate it.','This is circular reasoning; no witnesses or universal conditions are justified.'),
             ('Check only the first object in each domain.','An arbitrary enumeration position gives no information about the other objects or required witnesses.')],
            f'The plan follows the quantifier order: {strategy} Justify A or ¬A for the specified objects.', 'Universal claims need an arbitrary object; existential claims need a justified witness.',context=context)

def proof_workshop(topic, statement, questions):
    assert len(questions) == 4
    for prompt, correct, wrong, reason, hint in questions:
        add('proofs',topic,prompt,correct,wrong,reason,hint,context=f'Proof workshop: {statement} Induction coverage may vary by course section.')

def proofs():
    # Four different reasoning obligations for each theorem, including boundary checks.
    proof_workshop('Parity: direct proof','The sum of two odd integers is even.',[
      ('Which representation correctly starts a direct proof?','a = 2u+1, b = 2v+1 with u,v integers', [('a = 2u, b = 2v','These represent even, not odd integers.'),('a = u+1, b = v+1','Adding one to an arbitrary integer does not specify parity.'),('a = 2u+1, b = 2v','The second integer is even.')], 'By the definition of oddness, each odd integer has the form 2k+1 for an integer k.', 'Start from the definition of an odd integer.'),
      ('Which calculation proves the conclusion?','a+b = 2(u+v+1)', [('a+b = 2(u+v)+1','The two +1 terms add to 2, not 1.'),('a+b = 2uv+2','Addition of a and b does not produce a product uv.'),('a+b = u+v+2','The coefficients of u and v have been lost.')], 'Add (2u+1)+(2v+1)=2u+2v+2=2(u+v+1). The quantity inside parentheses is an integer.', 'Expand the sum before factoring out 2.'),
      ('Why does the factorization complete the proof?','u+v+1 is an integer', [('u+v+1 must be positive','Negative even integers are also even.'),('u+v+1 must be odd','An even number is twice any integer, regardless of its parity.'),('u and v must be equal','The argument works for different u and v.')], 'Even means equal to twice an integer. Closure of integers under addition gives the required integer witness.', 'Which property of the factor is in the definition of evenness?'),
      ('Which extension is false?','The sum of three odd integers is even', [('The sum of four odd integers is even','Pair the integers; each pair sums to an even integer.'),('The sum of an odd and an even integer is odd','2u+1+2v=2(u+v)+1.'),('The sum of two even integers is even','2u+2v=2(u+v).')], 'Three odd integers sum to 2(u+v+w+1)+1, which is odd; 1+1+1=3 is a counterexample.', 'Track the number of +1 terms modulo 2.')])
    proof_workshop('Parity: contraposition','If n² is even, then n is even.',[
      ('Which statement is the contrapositive?','If n is odd, then n² is odd', [('If n is even, then n² is even','This is the converse, not the contrapositive.'),('If n² is odd, then n is odd','This is the inverse of the original implication.'),('If n is odd, then n² is even','The consequent was not negated correctly.')], 'For P→Q, the contrapositive is ¬Q→¬P. Here ¬Q means n is odd and ¬P means n² is odd.', 'Reverse the implication and negate both parts.'),
      ('For n=2k+1, which expansion is correct?','n² = 2(2k²+2k)+1', [('n² = 4k²+1','The cross term 4k is missing.'),('n² = 2k²+2k+1','Squaring 2k produces 4k².'),('n² = 2(k²+k)','The constant term has vanished, falsely suggesting an even square.')], '(2k+1)²=4k²+4k+1=2(2k²+2k)+1.', 'Include the cross term when squaring a sum.'),
      ('Which fact is needed to infer oddness from that expansion?','2k²+2k is an integer', [('k must be nonnegative','Oddness is defined for all integers.'),('k² must be odd','The proof does not require that.'),('n must be prime','Primality has no role here.')], 'The expression is 2m+1 with integer m=2k²+2k, exactly the definition of oddness.', 'Check the integer witness in 2m+1.'),
      ('Which proposed analogous implication fails?','If n² is divisible by 4, then n is divisible by 4', [('If n² is odd, then n is odd','An even n would have an even square.'),('If n is even, then n² is divisible by 4','n=2k gives n²=4k².'),('If n² is even, then n is even','This is the theorem established by contraposition.')], 'n=2 has square 4 divisible by 4, but 2 is not divisible by 4.', 'Look for the smallest integer satisfying the hypothesis but not the conclusion.')])
    # The remaining cases are authored tables of theorem-specific obligations.
    records = [
    ('Divisibility transitivity','If a|b and b|c, then a|c (a,b,c integers).',
     [('Which witnesses express the hypotheses?','b=ak and c=bℓ for integers k,ℓ','b=a+k and c=b+ℓ','a=bk and b=cℓ','k and ℓ may be arbitrary real numbers','Divisibility uses integer multiplicative witnesses; its direction is b=ak, c=bℓ.'),
      ('Which substitution proves a|c?','c=a(kℓ)','c=a(k+ℓ)','c=(a+k)ℓ','c=a+kℓ','Substitute b=ak into c=bℓ to get c=a(kℓ).'),
      ('Why is kℓ an acceptable witness?','Integers are closed under multiplication','The product is always positive','The product is always prime','The product must equal 1','k and ℓ are integers, so kℓ is an integer; its sign is irrelevant.'),
      ('Which converse implication is false?','a|c and b|c imply a|b','a|b and b|c imply a|c','a|b implies a|2b','a|b and a|c imply a|(b+c)','Take a=2, b=3, c=6: both divide c, but 2 does not divide 3.')]),
    ('Linear combinations','If d|a and d|b, then d|(3a−2b).',
     [('Which premise is essential?','Both multiplicative witnesses are integers','a and b must be positive','d must be prime','a and b must be equal','Divisibility requires a=du and b=dv for integers u and v.'),
      ('Which factorization gives the witness?','3a−2b=d(3u−2v)','3a−2b=d(3u+2v)','3a−2b=3du−2v','3a−2b=d(u−v)','Substituting a=du and b=dv gives 3du−2dv=d(3u−2v).'),
      ('What closes the direct argument?','3u−2v is an integer','3u−2v is necessarily positive','u/v is an integer','d is a common multiple','Integer linear combinations remain integers, giving the required witness.'),
      ('Which coefficient change invalidates this general integer-witness argument?','Replace 3 by 1/2','Replace 3 by −3','Replace −2 by 0','Replace −2 by 7','With d=2,a=2,b=0, (1/2)a=1 is not divisible by 2. Integer coefficients are essential.')]),
    ('Rational closure','The sum of two rational numbers is rational.',
     [('Which representations satisfy the definition?','a/b and c/d with integers a,b,c,d and b,d≠0','a/b with arbitrary real a,b and b≠0','a/0 and c/d','a and c must both be prime','Rational numbers are quotients of integers with nonzero denominator.'),
      ('Which common-denominator expression is correct?','(ad+bc)/(bd)','(a+c)/(b+d)','(ac)/(bd)','(ab+cd)/(bd)','a/b+c/d=ad/(bd)+bc/(bd)=(ad+bc)/(bd).'),
      ('Which denominator fact must be checked?','bd≠0','bd must be 1','b+d≠0','bd must be prime','A product of two nonzero integers is nonzero, so the quotient is defined.'),
      ('Which related universal claim has a counterexample?','The sum of two irrational numbers is irrational','The sum of two rationals is rational','The product of two rationals is rational','The negative of a rational is rational','√2 and −√2 are irrational but their sum is 0, rational.')]),
    ('Irrationality contradiction','√2 is irrational.',
     [('What assumption starts a contradiction proof?','√2=a/b in lowest terms, with positive integers a,b','√2 is already irrational','a and b are both even in lowest terms','a/b need not be rational','Assume rationality and reduce the fraction so gcd(a,b)=1.'),
      ('Which equation follows by squaring?','a²=2b²','a=2b','a²=b²/2','2a²=b²','Squaring √2=a/b gives 2=a²/b², hence a²=2b².'),
      ('After a=2k is substituted, what follows?','b²=2k², so b is even','b is odd because a is even','a and b are necessarily equal','b²=4k²','4k²=2b² implies b²=2k². An even square has an even integer root.'),
      ('What is the actual contradiction?','a and b share factor 2 despite being in lowest terms','An even integer cannot be squared','2 cannot be rational','a² and b² cannot both be positive','The parity deductions force both a and b even, contradicting gcd(a,b)=1.')]),
    ('Euclid: primes','There are infinitely many primes.',
     [('Which temporary assumption is appropriate?','All primes are a finite list p₁,…,pₖ','There are no integers','Every integer is prime','There is a largest integer','Negate infinitude by supposing a complete finite list of primes.'),
      ('Which constructed integer is useful?','N=p₁p₂⋯pₖ+1','N=p₁+p₂+⋯+pₖ','N=p₁p₂⋯pₖ','N=1','The product plus one has remainder 1 upon division by each listed prime.'),
      ('Which claim about N is actually justified?','No listed prime divides N','N is always prime','N is always even','N is always a perfect square','For each pᵢ, the product is 0 modulo pᵢ, so N is 1 modulo pᵢ. N need not itself be prime.'),
      ('How is the contradiction obtained even if N is composite?','A prime divisor of N is absent from the list','Composite numbers have no prime divisors','N must be on the list as an integer','Subtract 1 from N and stop','Since N>1, it has a prime divisor; no listed prime divides N, contradicting completeness of the list.')]),
    ('Counterexample discipline','Evaluate the claim: every odd integer is prime.',
     [('Which integer is a counterexample?','9','2','3','−2','9 is odd and composite: 9=3·3. The other candidates either are not odd or are prime.'),
      ('Which logical condition must a counterexample meet?','The hypothesis is true and the conclusion is false','Both hypothesis and conclusion are false','The conclusion is true','The hypothesis is false','To refute P→Q, exhibit P∧¬Q.'),
      ('What does checking 3,5,7 establish?','Only those three instances satisfy the claim','The universal claim is proved','All odd integers are prime','The claim is false','Finitely many successful tests do not prove an unbounded universal statement.'),
      ('Which corrected implication is true?','Every prime greater than 2 is odd','Every odd integer greater than 2 is prime','Every composite integer is even','Every prime is odd','An even integer greater than 2 has divisor 2 and is not prime; 2 is the sole even prime.')]),
    ('Induction: triangular sum','For n≥1, 1+⋯+n=n(n+1)/2.',
     [('What is the base case n=1?','1=1·2/2','0=1·2/2','1=1·1/2','2=1·2/2','At n=1 the sum is 1 and the formula is 1·2/2=1.'),
      ('Which induction hypothesis is correct?','1+⋯+k=k(k+1)/2 for a fixed k≥1','The formula holds for all n by assumption','1+⋯+(k+1)=(k+1)(k+2)/2 by assumption','The sum equals k²','Assume the claim at k, not at the target k+1 or for every n.'),
      ('Which algebra proves the next case?','k(k+1)/2+(k+1)=(k+1)(k+2)/2','k(k+1)/2+1=(k+1)(k+2)/2','k(k+1)/2+k=(k+1)(k+2)/2','k(k+1)/2=(k+1)(k+2)/2','Append the new term k+1, factor k+1, and combine k/2+1=(k+2)/2.'),
      ('Why does a verified step without a base case fail?','It gives no starting true instance','The algebra becomes invalid','Induction needs every case checked separately','The integers are finite','A chain of implications P(k)→P(k+1) needs an initial P(1) to establish subsequent cases.')]),
    ('Induction: odd sum','For n≥1, 1+3+⋯+(2n−1)=n².',
     [('Which term is appended at the induction step?','2k+1','2k−1','k+1','2k+2','The (k+1)st odd number is 2(k+1)−1=2k+1.'),
      ('Which expression uses the hypothesis?','k²+(2k+1)','(k+1)²+(2k+1)','k²+(2k−1)','k²+1','Replace the sum of the first k odd numbers by k², then add the new odd term.'),
      ('Which identity finishes the step?','k²+2k+1=(k+1)²','k²+2k−1=(k+1)²','k²+1=(k+1)²','2k²+1=(k+1)²','Expand (k+1)²=k²+2k+1 to identify the target.'),
      ('What is the base-case equality?','1=1²','1+3=1²','0=1²','3=1²','At n=1 there is exactly one summand, 1, equal to 1².')]),
    ('Induction: powers','For n≥0, Σᵢ₌₀ⁿ 2ⁱ=2ⁿ⁺¹−1.',
     [('Which base case matches n≥0?','1=2¹−1','0=2⁰−1','2=2¹−1','1=2⁰−1','At n=0 the sole term is 2⁰=1 and the proposed right side is 2−1=1.'),
      ('What is added when moving from k to k+1?','2ᵏ⁺¹','2ᵏ','k+1','2ᵏ⁺²','The new index is k+1, so the new term is 2^(k+1).'),
      ('Which calculation completes the step?','(2ᵏ⁺¹−1)+2ᵏ⁺¹=2ᵏ⁺²−1','(2ᵏ⁺¹−1)+2ᵏ=2ᵏ⁺²−1','2ᵏ⁺¹−1=2ᵏ⁺²−1','2ᵏ⁺¹+1=2ᵏ⁺²−1','Two copies of 2^(k+1) equal 2^(k+2); preserve the −1.'),
      ('If the formula were stated only for n≥1, which base case would suffice?','n=1','n=0 alone without a step from 0','n=−1','No base case','For a claim starting at 1, prove P(1) and the transition for every k≥1.')]),
    ('Induction: inequality','For n≥1, 2ⁿ≥n+1.',
     [('Which step follows from 2ᵏ≥k+1?','2ᵏ⁺¹≥2k+2','2ᵏ⁺¹≥k','2ᵏ⁺¹=k+2','2ᵏ⁺¹≤2k+2','Multiply both sides by positive 2, preserving the inequality.'),
      ('Which comparison is needed next?','2k+2≥k+2 for k≥0','2k+2≤k+2 for k≥1','k+1≥2k+2','2k+2=k+2 for all k','Subtracting k+2 leaves k≥0, so the lower bound implies the next target.'),
      ('What is the target at k+1?','2ᵏ⁺¹≥k+2','2ᵏ≥k+2','2ᵏ⁺¹≥k+1 only','2ᵏ⁺²≥k+1','Replace n by k+1 in 2^n≥n+1.'),
      ('Which careless inference is invalid?','A lower bound implies equality','Multiplication by positive 2 preserves ≥','k≥1 implies k≥0','2¹≥2','Knowing x≥y does not imply x=y; the theorem is an inequality, not an identity.')]),
    ('Induction: factorial bound','For n≥4, n!>2ⁿ.',
     [('Which valid base case begins the proof?','4!=24>16=2⁴','3!=6>8=2³','2!=2>4=2²','1!=1>2=2¹','The bound first holds at 4 among these cases.'),
      ('What factor connects consecutive factorials?','(k+1)!=(k+1)k!','(k+1)!=k!+1','(k+1)!=2k!','(k+1)!=kk!','The factorial definition appends multiplication by k+1.'),
      ('Why does the induction hypothesis imply the next inequality?','k+1>2, so (k+1)2ᵏ>2ᵏ⁺¹','k+1=2 for k≥4','Factorials add instead of multiply','2ᵏ⁺¹=2ᵏ+1','For k≥4, k+1≥5>2. Multiply k!>2^k by k+1 and compare to 2·2^k.'),
      ('Why is replacing n≥4 by n≥1 wrong?','The statement fails at n=1,2,3','The induction step always fails','4! is not defined','2ⁿ is never positive','The proposed stronger statement includes 1!≤2, 2!≤4, and 3!≤8.')]),
    ('Strong induction: factorization','Every integer n≥2 is a product of primes.',
     [('What is the smallest base case?','2 is prime','1 is prime','0 is prime','−1 is prime','2 itself is a one-factor product of primes.'),
      ('Which hypothesis is suited to composite n?','All integers m with 2≤m<n have prime factorizations','Only n−1 has a factorization','n already has a factorization','All real numbers are prime','For n=ab, both factors a,b lie below n but need not equal n−1.'),
      ('What must be shown for n=ab composite?','2≤a,b<n','a=1','b=n','a and b are already prime','A nontrivial factorization of a positive composite n uses factors at least 2 and strictly less than n.'),
      ('How are the two smaller factorizations used?','Concatenate their prime factors to obtain n','Add their prime factors','Subtract one factorization from the other','Discard all repeated prime factors','If a=∏pᵢ and b=∏qⱼ, then ab is the product of both lists, including multiplicities.')]),
    ('Strong induction: stamps','Every amount n≥12 can be made with 4-unit and 5-unit stamps.',
     [('Which consecutive base cases support adding 4?','12,13,14,15','12 only','12 and 16 only','0 and 1','Every residue class modulo 4 needs a starting reachable amount: 12=3·4, 13=2·4+5, 14=4+2·5, 15=3·5.'),
      ('For n≥16, which smaller amount is used?','n−4','n−5 only for n=16','n/4','n+4','n−4≥12 and n−4<n, so the strong hypothesis covers it.'),
      ('What operation constructs n from the smaller amount?','Add one 4-unit stamp','Add one 1-unit stamp','Multiply the stamp count by n','Remove one 5-unit stamp','A representation of n−4 plus one 4-unit stamp totals n.'),
      ('Which attempted earlier starting point is disproved?','Every n≥11 is representable','Every n≥12 is representable','16 is representable','13 is representable','11 cannot equal 4a+5b for nonnegative integers: b=0,1,2 leaves 11,6,1, none divisible by 4.')]),
    ('Well-ordering','Every nonempty subset of nonnegative integers has a least element.',
     [('Which set satisfies the theorem’s domain?','{7,11,20}','All negative integers','Positive real numbers','The empty set','{7,11,20} is a nonempty subset of nonnegative integers; the other sets lack the required domain or nonemptiness.'),
      ('Why is nonemptiness necessary?','An empty set has no element to be least','The empty set has infinitely many least elements','Every empty set has least element 0','Nonemptiness is never required','A least element must belong to the set, impossible if there are no elements.'),
      ('Why does the analogous claim for positive real numbers fail?','For every x>0, x/2 is smaller and still positive','All positive real numbers are integers','The number 1 is least','0 belongs to the positive reals','No positive real is least because halving gives a smaller positive real.'),
      ('What role does a least counterexample play in an induction-style proof?','All earlier permitted cases are true','All later cases are false','The least case is automatically true','The counterexample must be 0','Minimality rules out earlier counterexamples; use their truth to contradict failure at the least one.')]),
    ('Uniqueness','An additive identity is unique.',
     [('How should a uniqueness proof begin?','Assume e and f are both additive identities','Assume no identity exists','Assume e≠f and stop','Check only one identity','To prove at most one, take two candidates satisfying the defining property and show equality.'),
      ('Which equality follows using both identity properties?','e=e+f=f','e+f=0 without definitions','e=f+1','e+f=e−f','Since f is an identity, e+f=e; since e is an identity, e+f=f. Therefore e=f.'),
      ('What is proved by showing any two candidates equal?','At most one identity exists','An identity necessarily exists','Every element is an identity','There are exactly two identities','Uniqueness alone proves at most one; existence is a separate obligation.'),
      ('What extra fact yields existence and uniqueness for integers?','0 is an additive identity','1 is an additive identity','Every integer is prime','Addition lacks closure','Verify n+0=0+n=n; combined with at-most-one, this proves exactly one identity.')]),
    ('Existence: constructive proof','There exists an integer n with n²−n=6.',
     [('Which witness proves existence?','n=3','n=2','n=1','n=0','3²−3=9−3=6, so 3 is an explicit witness.'),
      ('What additional integer is also a witness?','n=−2','n=−3','n=−1','n=4','(−2)²−(−2)=4+2=6.'),
      ('Which factorization describes all solutions?','(n−3)(n+2)=0','(n−2)(n+3)=0','(n−3)(n−2)=0','(n+3)(n+2)=0','n²−n−6 factors as (n−3)(n+2).'),
      ('Which conclusion is not justified?','There is exactly one integer solution','There is at least one integer solution','There are two integer solutions','3 is a solution','The roots 3 and −2 show that uniqueness is false.')]),
    ('Cases: absolute values','For real x, |x|≥x.',
     [('Which cases exhaust the domain?','x≥0 and x<0','x>0 and x<0','x=1 and x=−1','x is an integer or prime','The first partition includes zero and all real signs; the second misses zero.'),
      ('What is |x| in the nonnegative case?','x','−x always','x²','1','By definition, |x|=x when x≥0, giving equality.'),
      ('What establishes the negative case?','−x>x when x<0','−x<x when x<0','|x|=x<0','x²=x','If x<0, then −x>0>x, and |x|=−x.'),
      ('When is equality attained?','Exactly when x≥0','Exactly when x<0','Only when x=1','For no real x','For x≥0, |x|=x; for x<0, |x|=−x>x.')]),
    ('Proof errors: cancellation','Inspect a supposed proof that 1=2 from a=b≠0.',
     [('Why is dividing a²−ab by a−b invalid?','a−b=0 under the premise','a and b are positive','Multiplication is invalid','Squaring is always invalid','Since a=b, the cancelled factor a−b equals zero, and division by zero is undefined.'),
      ('Which step remains valid before cancellation?','a²−b²=ab−b²','(a+b)=b after division','2=1','a−b is nonzero','Multiplying a=b by a and subtracting b² gives the equality; only subsequent zero cancellation fails.'),
      ('Under which condition is cancelling a factor c valid over the reals?','c≠0','c=0','c is arbitrary without restriction','c must equal 1','If c≠0, its multiplicative inverse exists; dividing by c preserves equality.'),
      ('What lesson generalizes to proof construction?','Check every operation’s preconditions','Equalities can never be factored','Contradictions prove every calculation valid','A numeric example proves all identities','Domain restrictions such as nonzero denominators are part of a valid argument, not optional details.')]),
    ('Proof errors: induction','The false claim says every finite group of horses has one color.',
     [('Where does the overlapping-subsets induction fail?','The step from one horse to two','The base case with one horse','Every step from three onward','The meaning of a finite set','Two one-horse subsets have no shared horse, so their colors cannot be linked.'),
      ('What is needed to link the colors of two subsets?','A common horse in both subsets','Only equal subset sizes','Distinct horses in both','An empty intersection','A shared element provides a color that both uniform subsets must have.'),
      ('Why does checking the base case not rescue the proof?','Every required induction step must also be valid','A true base implies all claims','The base must be false','The theorem can ignore size two','A chain breaks at the first invalid transition, even with a true starting case.'),
      ('Which observation disproves the universal claim?','Two horses can have different colors','One horse has one color','A three-horse set has three elements','A finite set can be empty','An instance of two differently colored horses satisfies the domain but violates the conclusion.')]),
    ('Contrapositive versus converse','If an integer is divisible by 6, it is divisible by 3.',
     [('Which implication is equivalent to the claim?','If 3 does not divide n, then 6 does not divide n','If 3 divides n, then 6 divides n','If 6 does not divide n, then 3 does not divide n','If 6 divides n, then 3 does not divide n','Only the contrapositive is logically equivalent to an implication.'),
      ('Which integer refutes the converse?','3','6','12','18','3 is divisible by 3 but not by 6.'),
      ('Which integer witness proves the direct claim?','n=6k=3(2k)','n=3k=6k','n=6+k','n=3(2+k)','If n=6k with integer k, then 2k is an integer witness for divisibility by 3.'),
      ('What changes the implication into a biconditional?','Require both divisibility by 2 and divisibility by 3','Only require divisibility by 3','Require n to be odd','Require n to be nonzero','Since 2 and 3 are coprime, n is divisible by 6 iff it is divisible by both 2 and 3.')]),
    ('Proof of a set identity','A∩(B∪C)=(A∩B)∪(A∩C).',
     [('Which proof method directly establishes equality?','Show both inclusions using arbitrary elements','Show only one inclusion','Count elements without assumptions','Check only empty sets','Two sets are equal iff each is a subset of the other.'),
      ('Which membership statement matches the left side?','x∈A and (x∈B or x∈C)','x∈A or (x∈B and x∈C)','x∈A and x∈B and x∈C','x∈B or x∈C only','Intersection means and; union means or, with parentheses preserving scope.'),
      ('Which logical equivalence drives the proof?','p∧(q∨r) ≡ (p∧q)∨(p∧r)','p∧(q∨r) ≡ p∨q∨r','p∧(q∨r) ≡ p∧q∧r','p∧(q∨r) ≡ ¬p','Distributivity of conjunction over disjunction translates exactly to the set identity.'),
      ('Why does checking one finite example not prove the identity?','The claim ranges over arbitrary sets','Finite sets cannot satisfy it','The identity is false','Examples never provide insight','An example illustrates the identity, but elementwise equivalence covers all possible sets.')]),
    ('Invariant reasoning','Starting at 0, each move adds or subtracts 2.',
     [('Which property is invariant?','The current value is even','The current value is positive','The current value increases','The current value is prime','0 is even, and adding or subtracting 2 preserves evenness.'),
      ('Which target is unreachable?','7','−4','0','10','Every reached value is even, whereas 7 is odd; the other values can be reached with repeated moves.'),
      ('What inductive step proves preservation?','2k±2=2(k±1)','2k±2 is always positive','2k+2=2k+1','Every reached value is odd','An even state has form 2k; either move produces another integer multiple of 2.'),
      ('What is the distinction between necessary and sufficient conditions here?','Evenness is necessary and, for these moves, sufficient','Every invariant is always sufficient','Oddness is sufficient','A necessary condition guarantees reachability in all systems','The invariant rules out odd targets. Separately, k positive or negative moves reach every even integer 2k.')]),
    ('Pigeonhole proof','Among 6 integers, two have the same remainder modulo 5.',
     [('What are the boxes in the pigeonhole argument?','The five remainder classes 0,1,2,3,4','The six input integers','Only the class of even integers','All real numbers','Each integer is assigned to exactly one of five remainders modulo 5.'),
      ('Which count forces a collision?','6 objects in 5 boxes','5 objects in 6 boxes','5 objects in 5 boxes','1 object in 5 boxes','If every box held at most one integer, five boxes could hold only five integers.'),
      ('What follows for the two integers a,b?','5 divides a−b','5 divides a+b always','a=b always','Both integers are divisible by 5','Equal remainders imply a≡b mod 5, equivalent to 5|(a−b).'),
      ('Why can the claim fail with only 5 integers?','0,1,2,3,4 have distinct remainders','All five must be equal','There are only four remainder classes','Five integers cannot be distinct','The explicit set 0 through 4 uses each remainder once, so no collision is forced.')]),
    ]
    for topic, statement, rows in records:
        questions = []
        for prompt, answer, a,b,c, reason in rows:
            wrong = [(x, f'This does not satisfy the stated proof obligation. {reason}') for x in [a,b,c]]
            questions.append((prompt,answer,wrong,reason,'Separate the hypothesis, the exact target, and the definition or theorem that connects them.'))
        proof_workshop(topic,statement,questions)
    assert len(BANK['proofs']) == 100, len(BANK['proofs'])

def setstr(s):
    return '{' + ', '.join(map(str, sorted(s))) + '}' if s else '∅'

def set_answer(topic, prompt, correct, candidates, reason, hint, context='', verification=None):
    key = setstr(correct)
    wrong = []
    for s in candidates:
        option = setstr(s)
        if option != key and option not in [x for x,_ in wrong]:
            wrong.append((option, f'This set has different membership from the required result. {reason}'))
        if len(wrong) == 3: break
    assert len(wrong) == 3, (prompt, wrong)
    add('sets',topic,prompt,key,wrong,reason,hint,context=context,verification=verification)

def sets():
    finite = [
      ('Predicate-defined sets',set(range(1,9)),{2,4,6,8},{2,3,5,7},'U={1,…,8}; A consists of even elements and B of primes.'),
      ('Binary-word sets',{'00','01','10','11'},{'10','11'},{'01','11'},'U is the set of two-bit words; A has leading bit 1, B has trailing bit 1.'),
      ('Nested membership',{'∅','{1}','{2}','{1,2}'},{'∅','{1}'},{'{1}','{1,2}'},'U={∅,{1},{2},{1,2}}; A={∅,{1}}, B={{1},{1,2}}. Each displayed element of U is itself a set.'),
      ('Finite interval sets',set(range(-3,4)),{-2,-1,0,1,2},{0,1,2,3},'U={−3,…,3}; A={x∈U: |x|≤2}; B={x∈U: x≥0}.'),
    ]
    for topic,u,a,b,context in finite:
        for name, result, desc in [
            ('A∪B',a|b,'A union contains elements in either set.'),
            ('A∩B',a&b,'An intersection contains only elements shared by both sets.'),
            ('A\\B',a-b,'A difference retains elements of A that are absent from B.'),
            ('A△B',(a-b)|(b-a),'A symmetric difference contains elements in exactly one of the sets.')]:
            reason=f'{desc} From A={setstr(a)} and B={setstr(b)}, the result is {setstr(result)}.'
            extra=[a|b,a&b,a-b,b-a,u-a,u-b,u,set(),a,b]
            set_answer(topic,f'What is {name} in this universe?',result,extra,reason,'Translate the operation into a condition on one arbitrary element.',context,
                       verification={'kind':'set-operation','operation':name,'a':sorted(a),'b':sorted(b),'expected':sorted(result)})
    maps = [
      ('A finite bijection',['a','b','c'],[1,2,3],{'a':2,'b':3,'c':1}),
      ('An injection with unused codomain',['a','b'],[1,2,3],{'a':1,'b':3}),
      ('A surjection with a collision',['a','b','c'],[1,2],{'a':1,'b':2,'c':1}),
      ('A map that is neither',['a','b','c'],[1,2,3],{'a':1,'b':1,'c':2}),
      ('The empty-domain function',[],[1,2],{}),
    ]
    for topic,domain,codomain,mapping in maps:
        ctx=f'Domain A={setstr(domain)}; codomain B={setstr(codomain)}; f is specified by {mapping or "the empty table"}.'
        inj = len(set(mapping.values())) == len(domain)
        sur = set(mapping.values()) == set(codomain)
        classification = 'Bijective' if inj and sur else 'Injective but not surjective' if inj else 'Surjective but not injective' if sur else 'Neither injective nor surjective'
        choices=['Bijective','Injective but not surjective','Surjective but not injective','Neither injective nor surjective']
        reason=f'The outputs are {setstr(mapping.values())}. Distinct inputs have distinct outputs: {inj}. Every codomain element is attained: {sur}. Thus f is {classification.lower()}.'
        add('sets',topic,'Which classification fits f?',classification,[(x,f'This classification conflicts with the table. {reason}') for x in choices if x!=classification],reason,
            'Check collisions and unused codomain elements separately.',context=ctx,
            verification={'kind':'map-classification','domain':domain,'codomain':codomain,'mapping':mapping,'expected':classification})
        image=set(mapping.values())
        set_answer('Images','What is f(A), the image of the entire domain?',image,[set(codomain),set(),{codomain[0]},{codomain[-1]},{99}],
            f'The image is precisely the outputs in the table, {setstr(image)}. It need not equal the codomain.', 'Collect actual outputs, not all permitted outputs.',ctx,
            {'kind':'map-image','mapping':mapping,'expected':sorted(image)})
        y=codomain[0]; pre={x for x in domain if mapping[x]==y}
        set_answer('Preimages',f'What is f⁻¹({{{y}}})? Here f⁻¹ denotes a preimage, not an assumed inverse function.',pre,
            [set(domain),set(),{domain[0]} if domain else {'a'}, {domain[-1]} if domain else {'b'}, {'a','b'}, {'z'}],
            f'Collect exactly the inputs whose output is {y}: {setstr(pre)}. A preimage is defined even when f is not bijective.',
            'Read the table backward for this specific output.',ctx,
            {'kind':'map-preimage','mapping':mapping,'target':y,'expected':sorted(pre)})
        inverse='Yes: f is bijective' if inj and sur else 'No: f is not bijective'
        add('sets','Inverse existence','Does f have a two-sided inverse B→A?',inverse,
            [('Yes: every function has a two-sided inverse','An inverse on the whole codomain requires both existence and uniqueness of each preimage.'),
             ('Yes: injectivity alone is sufficient','Injectivity gives uniqueness but does not guarantee a preimage for every codomain element.'),
             ('Yes: surjectivity alone is sufficient','Surjectivity gives existence but collisions can prevent a two-sided inverse.')],
            f'A two-sided inverse exists exactly for bijections. Here the classification is {classification.lower()}, so {inverse.lower()}.',
            'An inverse must assign exactly one input to every codomain output.',context=ctx)
    rels=[
      ('Equality relation',list(range(3)),lambda x,y:x==y),
      ('Strict order',list(range(3)),lambda x,y:x<y),
      ('Non-strict order',list(range(3)),lambda x,y:x<=y),
      ('Same parity',list(range(4)),lambda x,y:x%2==y%2),
      ('Adjacency on a three-vertex path',list(range(3)),lambda x,y:abs(x-y)==1),
    ]
    for topic,u,fn in rels:
        pairs=[(a,b) for a in u for b in u if fn(a,b)]
        ctx=f'U={setstr(u)}; R={pairs}. Ordered pairs specify the entire relation.'
        props=[
          ('reflexive',all(fn(x,x) for x in u),'Every (x,x) must be present.'),
          ('symmetric',all(not fn(x,y) or fn(y,x) for x in u for y in u),'Every pair must have its reversed pair.'),
          ('transitive',all(not(fn(x,y) and fn(y,z)) or fn(x,z) for x in u for y in u for z in u),'Every two-step chain must have its shortcut.'),
          ('antisymmetric',all(not(fn(x,y) and fn(y,x)) or x==y for x in u for y in u),'Two-way pairs between distinct elements are forbidden.'),
        ]
        for prop,value,definition in props:
            if prop == 'antisymmetric' and topic == 'Equality relation':
                add('sets','Equivalence relations','Is this equality relation an equivalence relation?',
                    'Yes: it is reflexive, symmetric, and transitive',
                    [('No: equivalence requires nonreflexivity','Equivalence requires reflexivity, not its failure.'),
                     ('No: antisymmetry forbids equivalence','Equality is both antisymmetric and an equivalence relation; the properties are compatible.'),
                     ('Yes: finiteness alone makes it an equivalence relation','Finiteness does not imply the three required properties.')],
                    'Every (x,x) occurs; reversing an equality preserves it; and x=y,y=z imply x=z. These are exactly reflexivity, symmetry, and transitivity.',
                    'An equivalence relation must satisfy three separate properties.',context=ctx,
                    verification={'kind':'relation-equivalence','universe':u,'pairs':pairs,'expected':True})
                continue
            if prop == 'antisymmetric' and topic == 'Same parity':
                numeric('sets','Equivalence classes','How many equivalence classes does this same-parity relation have?',2,
                    'The classes are {0,2} and {1,3}. Each element is related exactly to the elements of its own parity, so these two disjoint classes partition U.',
                    'Group elements that are related to each other; count the resulting disjoint groups.',alternatives=[4,1,3],context=ctx,
                    verification={'kind':'relation-classes','universe':u,'pairs':pairs,'expected':2})
                continue
            if prop=='reflexive':
                witness=next((f'({x},{x}) is missing' for x in u if not fn(x,x)), 'all diagonal pairs occur')
            elif prop=='symmetric':
                witness=next((f'({x},{y}) occurs but ({y},{x}) does not' for x in u for y in u if fn(x,y) and not fn(y,x)), 'every pair has its reverse')
            elif prop=='transitive':
                witness=next((f'({x},{y}) and ({y},{z}) occur, but ({x},{z}) is missing' for x in u for y in u for z in u if fn(x,y) and fn(y,z) and not fn(x,z)), 'every two-step chain has its shortcut')
            else:
                witness=next((f'{x}≠{y} but both directions occur' for x in u for y in u if x!=y and fn(x,y) and fn(y,x)), 'no distinct elements have pairs in both directions')
            answer=f'{"Yes" if value else "No"}: {witness}'
            add('sets',f'{topic}: {prop}',f'Is R {prop}?',answer,
                [('Yes: every finite relation has this property','Finiteness alone implies none of the four standard relation properties.'),
                 ('No: nonempty relations never have this property','Nonemptiness is not an obstruction to this property.'),
                 ('It cannot be determined from the full pair list','The complete finite relation is given, so its defining property can be checked.')],
                f'{definition} In this pair list, {witness}. Therefore the answer is {"yes" if value else "no"}.',
                f'Use the definition: {definition}',context=ctx,
                verification={'kind':'relation-property','universe':u,'pairs':pairs,'property':prop,'expected':value})
    # Cartesian products and function counting: different objects and definitions.
    product_cases=[
      ({1,2},{'a','b','c'},'A={1,2}, B={a,b,c}'),
      (set(),{1,2},'A=∅, B={1,2}'),
      ({'x'},{'y'},'A={x}, B={y}, with x≠y'),
      ({'∅','{0}'},{0,1},'A={∅,{0}}, B={0,1}; the two elements of A are sets'),
    ]
    for a,b,ctx in product_cases:
        n,m=len(a),len(b)
        numeric('sets','Cartesian-product cardinality','How many ordered pairs belong to A×B?',n*m,
            f'Choose one of {n} first coordinates and one of {m} second coordinates: {n}·{m}={n*m}.',
            'A pair requires one element from each factor.',alternatives=[n+m,n**m,m**n],context=ctx,
            verification={'kind':'cartesian-count','a':list(a),'b':list(b),'expected':n*m})
        numeric('sets','Power-set cardinality','How many subsets does A have?',2**n,
            f'Each of {n} elements is either included or omitted independently, giving 2^{n}={2**n}. The empty set is one subset.',
            'For each element, decide in or out.',alternatives=[n,n*n,2*n],context=ctx,
            verification={'kind':'power-set-count','n':n,'expected':2**n})
        numeric('sets','Counting functions','How many functions A→B exist?',m**n,
            f'For each of {n} inputs choose one of {m} outputs, giving {m}^{n}={m**n}. With no inputs there is one empty function.',
            'Choices are made once per domain element, and outputs may repeat.',alternatives=[n*m,n**m,n+m],context=ctx,
            verification={'kind':'function-count','n':n,'m':m,'expected':m**n})
        numeric('sets','Power set of a product','How many subsets of A×B exist?',2**(n*m),
            f'A×B has {n*m} ordered pairs, so its power set has 2^{n*m}={2**(n*m)} elements.',
            'First count pairs, then count subsets of the resulting set.',alternatives=[2**n*2**m,n*m,2**n+2**m],context=ctx,
            verification={'kind':'power-product-count','n':n,'m':m,'expected':2**(n*m)})
    regions=[
      (40,22,17,9,'A student survey has 40 respondents, 22 studying logic, 17 studying graphs, and 9 studying both.'),
      (32,12,15,0,'There are 32 files: 12 are executable, 15 are images, and none is both.'),
      (25,8,16,8,'Among 25 devices, 8 are in A and 16 are in B; all 8 devices of A are also in B.'),
    ]
    for total,a,b,overlap,ctx in regions:
        for label,val,reason in [
          ('How many are in A∪B?',a+b-overlap,f'Inclusion–exclusion: {a}+{b}−{overlap}={a+b-overlap}.'),
          ('How many are in A but not B?',a-overlap,f'Subtract the shared region from A: {a}−{overlap}={a-overlap}.'),
          ('How many are in neither A nor B?',total-a-b+overlap,f'The union has {a+b-overlap}; subtract it from {total} to get {total-a-b+overlap}.'),
          ('How many are in exactly one of A,B?',a+b-2*overlap,f'The two exclusive regions total ({a}−{overlap})+({b}−{overlap})={a+b-2*overlap}.'),
        ]:
            numeric('sets','Venn-region reasoning',label,val,reason,'Sketch four disjoint regions: A only, B only, both, and neither.',context=ctx,
                verification={'kind':'venn-count','n':total,'a':a,'b':b,'overlap':overlap,'query':label,'expected':val})
    infinite=[
      ('Integer translation','f:ℤ→ℤ, f(n)=n+3',
       [('Is f injective?','Yes, a+3=b+3 implies a=b','No, all inputs collide','Only for positive inputs','Only for even inputs','Subtract 3 from equal outputs; arbitrary integers a,b must be equal.'),
        ('Is f surjective?','Yes, y has preimage y−3','No, 0 is unattained','No, negative outputs are unattained','Only odd outputs are attained','For any integer y, y−3 is an integer and f(y−3)=y.'),
        ('What is the inverse function?','f⁻¹(y)=y−3','f⁻¹(y)=y+3','f⁻¹(y)=3−y','f⁻¹(y)=y/3','Solving y=n+3 gives n=y−3; both compositions return the original input.'),
        ('What is f⁻¹({0,1}) as a set?','{−3,−2}','{3,4}','{0,1}','∅','The equations n+3=0 and n+3=1 give n=−3 and n=−2.')]),
      ('Integer doubling','f:ℤ→ℤ, f(n)=2n',
       [('Is f injective?','Yes, 2a=2b implies a=b','No, 1 and 2 collide','Only on nonnegative inputs','Only on odd inputs','Division by the nonzero integer 2 in the integer equality yields a=b.'),
        ('What is the image?','All even integers','All integers','All odd integers','Only positive even integers','Every output is 2n, hence even; conversely every even integer is 2n for an integer n.'),
        ('Why is f not onto ℤ?','1 has no integer preimage','0 has no preimage','−2 has no preimage','2 has two preimages','2n=1 requires n=1/2, outside the integer domain.'),
        ('Which codomain change makes f bijective?','Use the even integers as codomain','Use only the odd integers','Keep ℤ and remove 0 from the domain','Use positive integers without changing the domain','Restrict the codomain to the image; injectivity remains and every even output has a unique preimage.')]),
      ('Squaring across domains','g:ℝ→ℝ, g(x)=x²',
       [('Why is g not injective?','g(1)=g(−1)','g(0)=0','g(2)=4','Every square is nonnegative','Distinct inputs 1 and −1 have equal output, directly violating injectivity.'),
        ('Why is g not onto ℝ?','−1 is not a square of a real number','0 is not a square','1 has no preimage','4 has two preimages','A real square is nonnegative, so negative codomain elements are unattained.'),
        ('Which domain and codomain make squaring bijective?','[0,∞)→[0,∞)','ℝ→ℝ','ℝ→[0,∞)','[0,∞)→ℝ','On nonnegative reals squaring is strictly increasing, and every nonnegative y has unique preimage √y.'),
        ('What is g⁻¹({4}) as a preimage set on ℝ?','{−2,2}','{2}','{−4,4}','{16}','Solve x²=4: both x=2 and x=−2 are allowed in the real domain.')]),
    ]
    for topic,ctx,rows in infinite:
        for prompt,key,a,b,c,reason in rows:
            add('sets',topic,prompt,key,[(x,f'This conflicts with the specified domain or function. {reason}') for x in [a,b,c]],reason,
                'Check the domain, codomain, and equation for a preimage before drawing a conclusion.',context=ctx)
    empties=[
      ('Which statement is true?','∅⊆{∅}','∅∈∅','{∅}=∅','{∅}⊆∅','Every element of ∅ belongs to {∅}, vacuously; the singleton {∅} has one element while ∅ has none.'),
      ('What is |{∅}|?','1','0','2','Infinite','The outer set contains exactly one element, namely the empty set.'),
      ('What is the power set of ∅?','{∅}','∅','{{∅}}','{0}','The only subset of ∅ is ∅ itself, so P(∅) is its singleton.'),
      ('Which function cannot exist?','A function {0}→∅','A function ∅→{0}','A function ∅→∅','A function {0}→{0}','The input 0 would need an output in an empty codomain, impossible. An empty domain has the empty function.')]
    for prompt,key,a,b,c,reason in empties:
        add('sets','Empty sets and vacuous truth',prompt,key,[(x,f'Keep membership separate from inclusion and count the outer set’s elements. {reason}') for x in [a,b,c]],reason,
            'An element of a set and a subset of a set are different notions.')
    assert len(BANK['sets']) == 100, len(BANK['sets'])

def counting():
    # 25 genuinely different counting scenarios, each with four distinct constraints.
    # An expression is independently re-evaluated by the JavaScript validator.
    cases=[
      ('Bit strings','Consider binary strings of length 8.',[
       ('How many strings are possible?','2**8','Each of eight ordered positions has two independent choices.'),
       ('How many have exactly three 1s?','C(8,3)','Choose the three positions occupied by 1; all remaining bits are fixed.'),
       ('How many have at least one 1?','2**8-1','Subtract the sole all-zero string from all binary strings.'),
       ('How many are palindromes?','2**4','The first four bits determine the mirrored last four bits.')]),
      ('Digit codes','A code has four digits from 0 through 9; leading zeros are allowed.',[
       ('How many unrestricted codes exist?','10**4','Each of four ordered positions has ten choices.'),
       ('How many codes have no repeated digit?','P(10,4)','Choose four distinct digits in order: 10·9·8·7.'),
       ('How many end in an even digit?','10**3*5','The last digit has five even choices; each earlier digit has ten choices.'),
       ('How many contain exactly one zero?','4*9**3','Choose the zero’s position, then fill the other three positions with nonzero digits.')]),
      ('Ordered roles','Seven distinct volunteers can hold president, secretary, and treasurer roles.',[
       ('How many assignments use three different people?','P(7,3)','Roles are distinct: choose president, then secretary, then treasurer without repetition.'),
       ('How many assignments have Ada as president?','P(6,2)','The president is fixed; assign two different people from the other six to the other roles.'),
       ('How many assignments exclude Ada entirely?','P(6,3)','Assign three distinct roles using only six eligible people.'),
       ('How many assignments include Ada in some role?','P(7,3)-P(6,3)','Subtract assignments avoiding Ada from all assignments.')]),
      ('Unordered committees','A three-person committee is chosen from five engineers and four designers, all distinct.',[
       ('How many committees are possible?','C(9,3)','A committee has no role order, so choose three from nine.'),
       ('How many have exactly two engineers?','C(5,2)*C(4,1)','Choose two engineers and one designer independently.'),
       ('How many have at least one designer?','C(9,3)-C(5,3)','Subtract the all-engineer committees.'),
       ('How many have members of both categories?','C(9,3)-C(5,3)-C(4,3)','Subtract the disjoint all-engineer and all-designer cases.')]),
      ('Distinct-book arrangements','Five distinct mathematics books and three distinct computing books are placed on a shelf.',[
       ('How many unrestricted arrangements exist?','fact(8)','Arrange all eight distinct books in a linear order.'),
       ('How many keep all three computing books consecutive?','fact(6)*fact(3)','Treat the computing books as one block among six units, then arrange within the block.'),
       ('How many put all mathematics books before all computing books?','fact(5)*fact(3)','Category order is fixed; permute independently within each category.'),
       ('How many keep both categories as separate consecutive blocks?','2*fact(5)*fact(3)','Choose which category block comes first, then permute books within both blocks.')]),
      ('Circular seating','Six distinct people sit around an unmarked circular table. Rotations coincide; reflections differ.',[
       ('How many circular arrangements exist?','fact(5)','Fix one person to remove rotational symmetry, then arrange the other five.'),
       ('How many have Ada and Ben adjacent?','2*fact(4)','Treat them as a block: five circular units give 4! arrangements, with two internal orders.'),
       ('How many have Ada and Ben nonadjacent?','fact(5)-2*fact(4)','Subtract adjacent arrangements from all circular arrangements.'),
       ('With six marked seats instead, how many seatings exist?','fact(6)','Marked seats distinguish rotations, so all six people are ordered into seats.')]),
      ('Repeated letters','Arrange all letters of BANANA, treating identical copies as indistinguishable.',[
       ('How many distinct arrangements exist?','fact(6)/(fact(3)*fact(2))','There are three A copies, two N copies, and one B. Divide 6! by 3!2!.'),
       ('How many arrangements begin with B?','fact(5)/(fact(3)*fact(2))','Fix B; arrange three A copies and two N copies.'),
       ('How many arrangements end with A?','fact(5)/(fact(2)*fact(2))','Fix one A at the end, leaving two A, two N, and one B.'),
       ('How many keep the three A copies consecutive?','fact(4)/fact(2)','Treat AAA as one unit with B,N,N; divide 4! by 2! for the identical Ns.')]),
      ('Stars and bars','Distribute nine identical tokens among four labeled containers.',[
       ('How many distributions allow empty containers?','C(12,3)','Nonnegative solutions x₁+⋯+x₄=9 are counted by C(9+4−1,4−1).'),
       ('How many distributions put at least one in each container?','C(8,3)','Give one to each first; distribute the remaining five nonnegatively: C(8,3).'),
       ('How many distributions leave container 1 empty?','C(11,2)','Distribute nine among the remaining three labeled containers.'),
       ('How many distributions put at least two in container 1?','C(10,3)','Reserve two in the first container, then distribute the remaining seven among all four.')]),
      ('Bounded allocations','Choose nonnegative integer x,y,z with x+y+z=7.',[
       ('How many triples exist?','C(9,2)','Stars and bars gives C(7+3−1,3−1).'),
       ('How many have x≤3?','C(9,2)-C(5,2)','Subtract x≥4 cases; set x′=x−4 and distribute the remaining three.'),
       ('How many have x=3?','5','Then y+z=4, with y=0,1,2,3,4 and a determined z.'),
       ('How many have x≤3 and y≤3?','C(9,2)-2*C(5,2)','Subtract x≥4 and y≥4. Their intersection is empty because x+y would be at least 8.')]),
      ('Grid routes','A shortest route goes from (0,0) to (4,3) using only right and up moves.',[
       ('How many shortest routes exist?','C(7,3)','Choose positions of three up moves among seven moves.'),
       ('How many pass through (2,1)?','C(3,1)*C(4,2)','Multiply routes to (2,1) by routes from there to (4,3).'),
       ('How many avoid (2,1)?','C(7,3)-C(3,1)*C(4,2)','Subtract the routes through the forbidden point.'),
       ('How many begin with an up move?','C(6,2)','Fix the first up move; choose positions of the remaining two ups among six moves.')]),
      ('Inclusion–exclusion: divisibility','Consider integers from 1 through 60.',[
       ('How many are divisible by 3?','20','The list 3,6,…,60 contains 60/3 terms.'),
       ('How many are divisible by 3 or 5?','20+12-4','Add counts for 3 and 5, subtract the four multiples of lcm(3,5)=15.'),
       ('How many are divisible by neither 3 nor 5?','60-(20+12-4)','Subtract the union count from the universe size.'),
       ('How many are divisible by exactly one of 3 and 5?','20+12-2*4','Subtract the overlap twice so each common multiple is excluded from both exclusive regions.')]),
      ('Three-set overlap','In a group of 30, |A|=14, |B|=12, |C|=10, pair intersections have sizes 5,4,3, and |A∩B∩C|=2.',[
       ('How many are in A∪B∪C?','14+12+10-5-4-3+2','Three-set inclusion–exclusion adds single counts, subtracts pair counts, and adds the triple back.'),
       ('How many are in none of the three sets?','30-(14+12+10-5-4-3+2)','Subtract the union size from 30.'),
       ('How many are in exactly two of the sets?','5+4+3-3*2','Each triple-member appears in three pair intersections but should not count as exactly two.'),
       ('How many are in A only?','14-5-4+2','Remove A∩B and A∩C from A, then restore the twice-removed triple intersection.')]),
      ('Subset constraints','The set S has eight elements, including distinct elements a and b.',[
       ('How many subsets contain a?','2**7','Fix inclusion of a; each other element is free.'),
       ('How many subsets contain both a and b?','2**6','Fix two inclusions; the remaining six elements are free.'),
       ('How many subsets contain exactly one of a,b?','2*2**6','Choose which distinguished element appears, then freely choose the other six.'),
       ('How many four-element subsets contain a but not b?','C(6,3)','Include a, exclude b, and choose three from the other six.')]),
      ('Combinations with repetition','An order chooses five scoops from three flavors; scoop order is irrelevant.',[
       ('How many flavor-count orders exist?','C(7,2)','Nonnegative flavor counts sum to five, giving C(5+3−1,3−1).'),
       ('How many orders use all three flavors?','C(4,2)','Reserve one scoop of each, then distribute the remaining two.'),
       ('How many orders use exactly one flavor?','3','Choose the sole flavor; all five scoops then have it.'),
       ('How many orders use exactly two flavors?','C(3,2)*4','Choose two flavors; positive counts summing to five have four possibilities.')]),
      ('Pigeonhole thresholds','Objects are assigned to five labeled boxes.',[
       ('What minimum number guarantees some box has at least three objects?','11','Ten objects could place two in every box; the eleventh forces a third.'),
       ('What minimum number guarantees a shared box?','6','Five objects could occupy distinct boxes; one additional object forces a collision.'),
       ('With 17 objects, what occupancy is guaranteed in some box?','4','The maximum occupancy is at least ceil(17/5)=4.'),
       ('How many assignments of four distinct objects to boxes exist?','5**4','Each distinct object independently selects one of five boxes.')]),
      ('Surjection counting','Map a four-element labeled domain onto a three-element labeled codomain.',[
       ('How many unrestricted functions exist?','3**4','Each of four inputs has three output choices.'),
       ('How many onto functions exist?','3**4-3*2**4+3','Exclude functions missing each codomain value; restore overlaps missing two values.'),
       ('How many functions are constant?','3','Choose the sole output used by all four inputs.'),
       ('How many functions use exactly two outputs?','C(3,2)*(2**4-2)','Choose two outputs and exclude the two constant maps on those two values.')]),
      ('Injective assignments','Map a three-element labeled domain into a five-element labeled codomain.',[
       ('How many unrestricted functions exist?','5**3','Each of three inputs independently chooses an output.'),
       ('How many injections exist?','P(5,3)','Distinct inputs need distinct outputs: 5·4·3.'),
       ('How many functions fail injectivity?','5**3-P(5,3)','Subtract injections from all functions.'),
       ('How many injections send one specified input to one specified output?','P(4,2)','The specified pair is fixed; choose two distinct remaining outputs for the other inputs.')]),
      ('Anagrams with exclusions','Arrange the four distinct letters A,B,C,D in a line.',[
       ('How many arrangements exist?','fact(4)','All letters are distinct, giving 4! permutations.'),
       ('How many avoid A in the first position?','fact(4)-fact(3)','Subtract arrangements with first letter fixed as A.'),
       ('How many avoid A first and D last?','fact(4)-2*fact(3)+fact(2)','Inclusion–exclusion subtracts each forbidden endpoint, restoring cases with both.'),
       ('How many have A before B?','fact(4)/2','Swapping A and B pairs each arrangement with one having the opposite relative order.')]),
      ('Binary parity','Consider binary strings of length 6.',[
       ('How many have even parity?','2**5','The first five bits determine the sixth for even parity.'),
       ('How many have exactly two 1s?','C(6,2)','Choose two positions for 1s.'),
       ('How many have at most two 1s?','C(6,0)+C(6,1)+C(6,2)','Add the disjoint weights 0,1,2.'),
       ('How many have a 1 at each endpoint?','2**4','Fix first and last bits; four interior bits are free.')]),
      ('Alternating categories','Four distinct women and four distinct men stand in a line; the categories only constrain alternation.',[
       ('How many alternating arrangements exist?','2*fact(4)*fact(4)','Choose the starting category, then permute each group in its four positions.'),
       ('How many alternating arrangements start with a woman?','fact(4)*fact(4)','Category positions are fixed; only within-category permutations remain.'),
       ('How many alternating arrangements have Ada, a woman, first?','fact(3)*fact(4)','Fix Ada first, arrange the other women and all men.'),
       ('How many unrestricted lineups exist?','fact(8)','Without alternation, any permutation of eight distinct people is allowed.')]),
      ('Nonadjacent selections','Select three positions from the seven positions of a line.',[
       ('How many selections are possible without restrictions?','C(7,3)','Choose three unordered positions from seven.'),
       ('How many selections have no adjacent chosen positions?','C(5,3)','For sorted positions i₁<i₂<i₃ with gaps at least two, subtract 0,1,2 to obtain a three-subset of five positions.'),
       ('How many selections include both endpoints?','5','Fix positions 1 and 7, then select one of five interior positions.'),
       ('How many nonadjacent selections include both endpoints?','3','With endpoints selected, the remaining position can be 3,4,5; positions 2 and 6 are adjacent to an endpoint.')]),
      ('Binomial expansion','Consider the expansion (x+2)⁶.',[
       ('What is the coefficient of x⁴?','C(6,4)*2**2','Choose the four factors supplying x; the other two supply 2.'),
       ('What is the constant term?','2**6','Choose 2 from every factor.'),
       ('What is the sum of all coefficients?','3**6','Set x=1; the sum is (1+2)^6.'),
       ('What is the coefficient of x⁵?','C(6,5)*2','Choose five x factors and one factor supplying 2.')]),
      ('Labeled teams','Split eight distinct people into a red team of three and a blue team of five.',[
       ('How many team assignments exist?','C(8,3)','Choose the red team; the rest form blue automatically.'),
       ('How many assignments put Ada on red?','C(7,2)','Fix Ada on red and choose two more from seven.'),
       ('How many assignments put Ada and Ben on different teams?','2*C(6,2)','Choose which one is on red, then choose two red teammates from the other six.'),
       ('How many assignments also choose one red captain?','C(8,3)*3','Choose the red team, then choose one of its three members as captain.')]),
      ('Simple-graph enumeration','A simple undirected graph has five fixed labeled vertices; loops are forbidden.',[
       ('How many potential edges are there?','C(5,2)','Each edge is an unordered pair of distinct vertices.'),
       ('How many such graphs exist?','2**C(5,2)','Each of ten potential edges is independently present or absent.'),
       ('How many such graphs have exactly four edges?','C(C(5,2),4)','Choose four from the ten potential edges.'),
       ('How many such graphs have a specified vertex isolated?','2**C(4,2)','Remove all four incident edge choices; the other four vertices have six freely selectable edges.')]),
      ('Partitions and pairings','There are six distinct labeled items.',[
       ('How many ways split them into two unlabeled groups of three?','C(6,3)/2','Choosing one triple counts each split twice, once for either group.'),
       ('How many ways partition them into three unordered pairs?','fact(6)/(2**3*fact(3))','Divide 6! by two orientations per pair and by the 3! orderings of pairs.'),
       ('How many ways choose one unordered pair?','C(6,2)','Choose two items without order.'),
       ('How many ways select an ordered list of three distinct items?','P(6,3)','Order matters and repetition is prohibited, so use 6·5·4.')]),
    ]
    def C(n,r): return math.comb(n,r)
    def P(n,r): return math.perm(n,r)
    for topic,ctx,rows in cases:
        for prompt,expr,reason in rows:
            value=eval(expr,{'__builtins__':{}},dict(C=C,P=P,fact=math.factorial))
            assert value == int(value)
            candidate_exprs=[expr.replace('C(', 'P('),expr.replace('P(', 'C('),expr.replace('fact(', '('),expr.replace('**','*'),
                             re.sub(r'\*\*(\d+)',lambda m:'**'+str(max(0,int(m[1])-1)),expr),
                             re.sub(r'\*\*(\d+)',lambda m:'**'+str(int(m[1])+1),expr)]
            alternatives=[]
            for candidate in candidate_exprs:
                try:
                    v=eval(candidate,{'__builtins__':{}},dict(C=C,P=P,fact=math.factorial))
                    if v>=0 and v==int(v) and int(v)!=int(value): alternatives.append(int(v))
                except (ValueError,ZeroDivisionError): pass
            numeric('counting',topic,prompt,int(value),f'{reason} Therefore {expr} = {int(value)}.',
                'Decide what is ordered, what is distinguishable, and which restrictions can be counted directly or by a complement.',context=ctx,
                verification={'kind':'count-expression','expression':expr,'expected':int(value)},alternatives=alternatives)
    assert len(BANK['counting']) == 100

def graph_info(n,edges):
    adj=[set() for _ in range(n)]
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    components=[]; unseen=set(range(n))
    while unseen:
        seen=set(); todo=[min(unseen)]
        while todo:
            v=todo.pop()
            if v in seen: continue
            seen.add(v);todo.extend(adj[v]-seen)
        unseen-=seen; components.append(sorted(seen))
    colors={}; conflict=None
    for start in range(n):
        if start in colors: continue
        colors[start]=0; todo=[start]
        while todo:
            v=todo.pop(0)
            for w in sorted(adj[v]):
                if w not in colors: colors[w]=1-colors[v]; todo.append(w)
                elif colors[w]==colors[v]: conflict=(v,w)
    return adj,components,colors,conflict

def graphs_number():
    graphs=[
      ('Path P₅',5,[(0,1),(1,2),(2,3),(3,4)],'What is the diameter (maximum shortest-path distance)?',4,'The endpoints 0 and 4 are four edges apart, and no pair is farther.','diameter'),
      ('Cycle C₄',4,[(0,1),(1,2),(2,3),(3,0)],'How many spanning trees does this cycle have?',4,'Delete any one of the four edges. Each deletion gives a different spanning tree.','spanning-trees'),
      ('Cycle C₅',5,[(0,1),(1,2),(2,3),(3,4),(4,0)],'What is its chromatic number?',3,'An odd cycle cannot be two-colored. Three colors suffice by alternating two on a path and using a third for the final vertex.','chromatic'),
      ('Complete graph K₄',4,list(itertools.combinations(range(4),2)),'How many triangles does it contain?',4,'Every three-vertex subset is a triangle, so C(4,3)=4.','triangles'),
      ('Complete bipartite K₂,₃',5,[(a,b) for a in [0,1] for b in [2,3,4]],'What is the maximum matching size?',2,'A matching uses at most two vertices on the smaller side. Edges (0,2),(1,3) attain size two.','matching'),
      ('Star K₁,₄',5,[(0,i) for i in range(1,5)],'What is the minimum vertex-cover size?',1,'The center 0 meets every edge, and at least one vertex is needed because edges exist.','vertex-cover'),
      ('Triangle plus separate edge',5,[(0,1),(1,2),(2,0),(3,4)],'How many connected components are there?',2,'Vertices {0,1,2} form one component; {3,4} form another.','components'),
      ('Three-edge matching',6,[(0,1),(2,3),(4,5)],'How many vertices are in the largest connected component?',2,'Every component consists of exactly one edge and its two endpoints.','largest-component'),
      ('Diamond: K₄ minus one edge',4,[(0,1),(0,2),(0,3),(1,2),(2,3)],'What is the sum of all vertex degrees?',10,'The degrees are 3,2,3,2; their sum is 10, equal to twice the five edges.','degree-sum'),
      ('Wheel with a five-cycle rim',6,[(i,(i+1)%5) for i in range(5)]+[(5,i) for i in range(5)],'What is the chromatic number?',4,'The odd rim requires three colors; the hub is adjacent to every rim vertex and needs a fourth.','chromatic'),
      ('Cube graph',8,[(a,b) for a in range(8) for b in range(a+1,8) if (a^b).bit_count()==1],'What is the shortest-path distance from vertex 0 to vertex 7?',3,'The binary labels 000 and 111 differ in three bits. Each edge changes one bit, and changing those three bits gives a three-edge path.','distance-0-last'),
      ('Two triangles joined by a bridge',6,[(0,1),(1,2),(2,0),(3,4),(4,5),(5,3),(2,3)],'How many bridges (edges whose deletion increases the component count) exist?',1,'Only (2,3) links the triangles. Edges inside a triangle have an alternate two-edge route.','bridges'),
      ('Petersen graph',10,[(i,(i+1)%5) for i in range(5)]+[(i,i+5) for i in range(5)]+[(5+i,5+(i+2)%5) for i in range(5)],'What is the girth (length of a shortest cycle)?',5,'The outer rim is a 5-cycle. From the edge list, adjacent vertices have no common neighbor, ruling out triangles. No two vertices have two common neighbors, ruling out 4-cycles. Thus the shortest cycle has length 5.','girth'),
    ]
    for topic,n,edges,prompt,value,reason,query in graphs:
        adj,components,colors,conflict=graph_info(n,edges)
        ctx=f'{topic}. A finite simple undirected graph has vertices 0,…,{n-1} and exactly these edges: '+', '.join(f'({a},{b})' for a,b in edges)+'.'
        degrees=[len(a) for a in adj]
        numeric('graphs-number','Handshaking lemma',f'How many edges does this graph have, using its degree sum?',len(edges),
            f'The vertex degrees in label order are {degrees}, summing to {sum(degrees)}. Each undirected edge contributes twice, so |E|={sum(degrees)}/2={len(edges)}.',
            'Compute each vertex degree and divide the total by two.',context=ctx,
            verification={'kind':'graph-query','n':n,'edges':edges,'query':'edges','expected':len(edges)})
        numeric('graphs-number',topic,prompt,value,reason,'Use the displayed edges to test the defining property; names alone are not a substitute for the graph.',context=ctx,
            verification={'kind':'graph-query','n':n,'edges':edges,'query':query,'expected':value})
        odd=[i for i,d in enumerate(degrees) if d%2]
        active_components=[c for c in components if any(degrees[v] for v in c)]
        euler='A closed Euler trail exists' if len(active_components)==1 and not odd else 'An open Euler trail exists, but no closed one' if len(active_components)==1 and len(odd)==2 else 'No trail uses every edge exactly once'
        choices=['A closed Euler trail exists','An open Euler trail exists, but no closed one','No trail uses every edge exactly once','Every simple graph automatically has a closed Euler trail']
        reason=f'The odd-degree vertices are {odd}; the edge-containing component count is {len(active_components)}. An Euler trail requires edge connectivity and zero or two odd vertices. Zero gives a closed trail; two gives an open one. Thus: {euler.lower()}.'
        add('graphs-number','Euler trails','Which statement about traversing every edge exactly once is correct?',euler,[(x,f'The Euler conditions rule out this statement. {reason}') for x in choices if x!=euler],reason,
            'Check connectivity among vertices incident to edges, then count odd degrees.',context=ctx,
            verification={'kind':'graph-euler','n':n,'edges':edges,'expected':euler})
        bip=conflict is None
        if bip:
            sides=[[v for v in range(n) if colors[v]==i] for i in [0,1]]
            key=f'Yes: a valid partition is {sides[0]} and {sides[1]}'
            reason=f'Color the vertices in two classes {sides[0]} and {sides[1]}. Every displayed edge crosses the partition, so the graph is bipartite.'
        else:
            key='No: it contains an odd cycle'
            reason=f'Two-color propagation produces the same color at endpoints {conflict} of an edge. Equivalently, an odd cycle obstructs bipartiteness. The graph therefore is not bipartite.'
        add('graphs-number','Bipartite graphs','Is this graph bipartite?',key,
            [('Yes: any graph with an even number of edges is bipartite','Edge-count parity does not imply a two-coloring.'),
             ('No: only disconnected graphs are bipartite','Connected graphs such as paths can be bipartite.'),
             ('It depends on the order in which vertices are labeled','Bipartiteness is invariant under relabeling.')],reason,
            'Try alternating two colors along edges; a same-color edge witnesses a conflict.',context=ctx,
            verification={'kind':'graph-bipartite','n':n,'edges':edges,'expected':bip})
    arithmetic=[
      ('Euclidean division','Use the convention a=mq+r with 0≤r<m and m>0.',[
       ('What is the remainder when −17 is divided by 5?','3','−17=5(−4)+3; the remainder is required to be nonnegative.'),
       ('What is the quotient when −17 is divided by 5?','−4','The remainder 3 gives quotient −4, because −17=−20+3.'),
       ('Which pair (q,r) represents 29 divided by 6?','(4,5)','29=6·4+5, with 0≤5<6.'),
       ('Why is (q,r)=(5,−1) invalid for 29 divided by 6?','The remainder is outside 0≤r<6','It satisfies the equation but uses a negative remainder, violating the division convention.')]),
      ('Greatest common divisors','Consider a=84 and b=30.',[
       ('What is gcd(84,30)?','6','84=2·30+24; 30=24+6; 24=4·6, so the last nonzero remainder is 6.'),
       ('Which Bézout identity is valid?','6=3·30−84','3·30−84=90−84=6.'),
       ('What is lcm(84,30)?','420','For positive integers, gcd·lcm=ab. Thus lcm=84·30/6=420.'),
       ('How many positive common divisors do 84 and 30 have?','4','Common divisors are divisors of gcd 6: 1,2,3,6.')]),
      ('Prime factorization','Let N=2³·3²·5=360.',[
       ('How many positive divisors does N have?','24','Choose exponents 0..3 for 2, 0..2 for 3, and 0..1 for 5: 4·3·2=24.'),
       ('How many distinct prime divisors does N have?','3','The distinct prime factors are 2,3,5.'),
       ('Which is the largest square divisor of N?','36','Use the largest even exponent for each prime: 2²·3²=36.'),
       ('What is gcd(N,84)?','12','84=2²·3·7. Take the smaller exponents of common primes: 2²·3=12.')]),
      ('Modular operations','Use least nonnegative residues modulo 7.',[
       ('What is (19+25) mod 7?','2','19+25=44=6·7+2.'),
       ('What is (19·25) mod 7?','6','19≡5 and 25≡4, so their product is 20≡6.'),
       ('What is (19−25) mod 7?','1','−6=−7+1, giving least nonnegative residue 1.'),
       ('Which integer is congruent to 19 modulo 7?','−2','19−(−2)=21 is divisible by 7.')]),
      ('Modular inverses','Work modulo 11.',[
       ('What is the multiplicative inverse of 3?','4','3·4=12≡1 modulo 11.'),
       ('Solve 3x≡7 (mod 11), using 0≤x<11.','6','Multiply by inverse 4: x≡28≡6.'),
       ('Why does 3 have an inverse modulo 11?','gcd(3,11)=1','An integer has an inverse modulo m exactly when it is coprime to m.'),
       ('What is the inverse of 10 modulo 11?','10','10≡−1, and (−1)²≡1, so it is its own inverse.')]),
      ('Noninvertible congruences','Work modulo 8.',[
       ('Which residues solve 2x≡4 (mod 8)?','x≡2 or 6','The congruence reduces to x≡2 modulo 4, yielding two residues modulo 8.'),
       ('Why can 2x≡2y (mod 8) not imply x≡y (mod 8)?','2 has no inverse modulo 8','gcd(2,8)=2; x=0,y=4 have equal doubled residues but different residues.'),
       ('How many residues solve 2x≡3 (mod 8)?','0','The left side is even modulo 8; the right side is odd. Equivalently gcd(2,8) does not divide 3.'),
       ('How many residues solve 4x≡0 (mod 8)?','4','x must be even: 0,2,4,6 are the four solutions.')]),
      ('Modular powers','Use arithmetic modulo 5.',[
       ('What is 2¹⁰ mod 5?','4','Powers of 2 cycle 2,4,3,1 with period four; 10≡2 mod 4, so the residue is 4.'),
       ('What is 3⁴ mod 5?','1','3²≡4, so 3⁴≡4²=16≡1.'),
       ('What is 4⁹ mod 5?','4','4≡−1 and an odd power of −1 is −1≡4.'),
       ('What is 5²⁰ mod 5?','0','Any positive power of 5 is divisible by 5; coprime-base exponent reductions do not apply.')]),
      ('Chinese remainder reasoning','Solve simultaneous congruences x≡2 (mod 3), x≡3 (mod 5).',[
       ('What is the least nonnegative solution?','8','Candidates congruent to 3 modulo 5 are 3,8,13; only 8 is 2 modulo 3.'),
       ('What is the period of all solutions?','15','The moduli 3 and 5 are coprime, so solutions form one residue class modulo their product 15.'),
       ('Which solution follows immediately after 8?','23','All solutions are 8+15k; the next is 23.'),
       ('Why is x=3 not a solution?','It fails the modulo 3 condition','3≡0 modulo 3, whereas the required residue is 2.')]),
      ('Divisibility boundaries','All variables below are integers; divisibility means b=ak for an integer k.',[
       ('Which statement is true?','7 divides 0','0=7·0 supplies an integer witness.'),
       ('Which statement about 0 dividing 5 is correct?','It is false','5=0·k has no integer solution.'),
       ('Which implication is false?','a|bc implies a|b or a|c for arbitrary a','For a=6,b=2,c=3, 6 divides bc but divides neither factor. The prime-divisor version needs a prime a.'),
       ('If 4|n, what must also hold?','2|n','Writing n=4k=2(2k) gives an integer witness for 2|n.')]),
      ('Coprime integers','Consider consecutive integers n and n+1.',[
       ('What is gcd(n,n+1) for integer n?','1','Any common divisor divides (n+1)−n=1, so the positive gcd is 1.'),
       ('For n=14, what is lcm(14,15)?','210','They are coprime, so lcm is their product 14·15.'),
       ('Which Bézout expression equals 1?','(n+1)−n','Use coefficients 1 and −1 to obtain 1 from the consecutive integers.'),
       ('What is always true of n(n+1)?','It is even','One of two consecutive integers is even, so their product is even.')]),
      ('Primality tests','Consider the positive integer 91.',[
       ('Which proper factor proves 91 composite?','7','91=7·13, with both factors greater than 1.'),
       ('To test primality by trial division, which upper bound suffices?','√91','If 91 had a factorization with both factors above √91, the product would exceed 91.'),
       ('Which prime divisors need testing at or below √91?','2,3,5,7','√91 is between 9 and 10; these are exactly the primes no greater than it.'),
       ('How many positive divisors does 91 have?','4','91=7·13 has divisors 1,7,13,91, or (1+1)(1+1)=4 by exponents.')]),
      ('Gcd and cancellation','Consider gcd(35,12) and congruences modulo 12.',[
       ('What is gcd(35,12)?','1','35=2·12+11 and 12=11+1, so the last nonzero remainder is 1.'),
       ('What is the inverse of 35 modulo 12?','11','35≡11≡−1 mod 12, and 11²≡1.'),
       ('Which identity gives a Bézout witness for gcd=1?','1=3·12−35','36−35=1; integer coefficients establish coprimality.'),
       ('If 35x≡35y (mod 12), what follows?','x≡y (mod 12)','35 is invertible modulo 12; multiplying by its inverse permits cancellation.')]),
    ]
    # Distractors are selected from context-sensitive arithmetic misconceptions.
    distractors={
      '3':['2','4','5'], '−4':['−3','3','4'], '(4,5)':['(5,−1)','(3,11)','(4,6)'],
      '6':['2','3','12'], '4':['2','3','5'], '420':['2520','114','210'],
      '24':['6','12','36'], '36':['18','60','90'], '12':['6','24','84'],
      '2':['0','1','3'], '1':['0','2','7'], '−2':['−1','0','2'], '10':['1','9','0'],
      'x≡2 or 6':['x≡2 only','x≡4 only','x≡1 or 5'], '0':['1','2','8'],
      '8':['3','13','2'], '15':['8','5','3'], '23':['18','13','16'],
      '210':['29','105','420'], '7':['2','3','5'], '√91':['91²','91/2','log₂91'],
      '2,3,5,7':['2,3,5','2,3,5,7,11','1,2,3,5,7'], '11':['1','5','7'],
    }
    generic=[
      'This follows without any hypotheses',
      'The claim depends only on whether the integer is positive',
      'Division or cancellation is always allowed, including by zero',
    ]
    distractors.update({
      'The remainder is outside 0≤r<6':['The equation 29=6q+r fails','The quotient must always be positive','The remainder must be greater than the divisor'],
      '6=3·30−84':['6=84−2·30','6=84+30','6=2·84−5·30'],
      'gcd(3,11)=1':['3 is smaller than 11','Every nonzero residue is invertible for every modulus','3 divides 11'],
      '2 has no inverse modulo 8':['2 is larger than the modulus','Every even residue is zero','Congruences never allow cancellation'],
      'It fails the modulo 3 condition':['It fails the modulo 5 condition','It satisfies both conditions but is too small','It is excluded because solutions must be prime'],
      '7 divides 0':['0 divides 7','7 divides 1','7 divides every integer'],
      'It is false':['It is true because 0 is even','It is true with witness 5','It is true because every integer divides 0'],
      'a|bc implies a|b or a|c for arbitrary a':['a|b and b|c imply a|c','a|b implies a|2b','a|b and a|c imply a|(b+c)'],
      '2|n':['8|n','n is odd','3|n'],
      '(n+1)−n':['(n+1)+n','n(n+1)','(n+1)−2n'],
      'It is even':['It is odd','It is always prime','It is always divisible by 4'],
      '1=3·12−35':['1=35−2·12','1=35+12','1=2·35−6·12'],
      'x≡y (mod 12)':['x=y as integers','x≡−y (mod 12)','x and y must both be even'],
    })
    for case_index,(topic,ctx,rows) in enumerate(arithmetic):
        for row_index,(prompt,key,reason) in enumerate(rows):
            options=distractors[key]
            add('graphs-number',topic,prompt,key,[(x,f'This proposed result fails the stated definition or arithmetic. {reason}') for x in options],reason,
                'Use integer witnesses, remainders, or the Euclidean algorithm; check any proposed solution by substitution.',context=ctx,
                verification={'kind':'arithmetic-case','case':case_index,'query':row_index})
    assert len(BANK['graphs-number']) == 100

def recurrences():
    # Cases span arithmetic, geometric, affine, polynomial, alternating, delayed,
    # nonlinear, and divide-and-conquer recurrences. Each has four distinct tasks.
    cases=[
      ('Arithmetic sequence','a₀=4; aₙ=aₙ₋₁+3 for n≥1.',[
       ('What is a₄?','16','Four increments of 3 give 4+4·3=16.'),
       ('Which closed form holds for n≥0?','aₙ=4+3n','Unrolling adds 3 exactly n times to the initial value 4.'),
       ('What is aₙ−aₙ₋₁?','3','The defining recurrence says the difference is the constant 3.'),
       ('Which equality verifies the induction step for the closed form?','4+3(n−1)+3=4+3n','Substitute the formula for a_(n−1) and add 3.')]),
      ('Geometric sequence','b₀=3; bₙ=2bₙ₋₁ for n≥1.',[
       ('What is b₅?','96','Five doublings give 3·2⁵=96.'),
       ('Which closed form is correct?','bₙ=3·2ⁿ','Each recurrence application contributes a factor of 2.'),
       ('What is bₙ/bₙ₋₁?','2','All terms are positive, so division is defined and the recurrence gives ratio 2.'),
       ('Which change to the base term doubles every term?','Replace b₀=3 by b₀=6','The homogeneous recurrence scales all future terms by the same factor as its initial value.')]),
      ('Affine recurrence','c₀=0; cₙ=2cₙ₋₁+1 for n≥1.',[
       ('What is c₄?','15','The terms are 0,1,3,7,15.'),
       ('Which closed form is correct?','cₙ=2ⁿ−1','Substituting gives 2(2^(n−1)−1)+1=2^n−1, and c₀=0.'),
       ('Which shifted variable yields a homogeneous recurrence?','dₙ=cₙ+1','Then dₙ=2(cₙ₋₁+1)=2dₙ₋₁.'),
       ('Which constant value is a fixed point of x↦2x+1?','−1','Solve x=2x+1, giving x=−1; shifting away from this fixed point explains d=c+1.')]),
      ('Triangular accumulation','a₀=0; aₙ=aₙ₋₁+n for n≥1.',[
       ('What is a₅?','15','Accumulate 1+2+3+4+5=15.'),
       ('Which closed form is correct?','aₙ=n(n+1)/2','The recurrence is the sum of the first n positive integers.'),
       ('What is the second finite difference aₙ−2aₙ₋₁+aₙ₋₂ for n≥2?','1','First differences are n and n−1; subtract to get 1.'),
       ('Which summation is obtained by unrolling?','Σᵢ₌₁ⁿ i','At each step from 1 through n add that step’s index, starting from zero.')]),
      ('Odd-number accumulation','a₀=0; aₙ=aₙ₋₁+(2n−1) for n≥1.',[
       ('What is a₆?','36','The first six odd numbers sum to 6²=36.'),
       ('Which closed form is correct?','aₙ=n²','n²−(n−1)²=2n−1, matching the recurrence and zero base.'),
       ('Which difference verifies the formula?','n²−(n−1)²=2n−1','Expand the square to obtain the recurrence’s increment.'),
       ('What is the growth order?','Θ(n²)','The exact formula n² has quadratic growth.')]),
      ('Square accumulation','s₀=0; sₙ=sₙ₋₁+n² for n≥1.',[
       ('What is s₃?','14','1²+2²+3²=1+4+9=14.'),
       ('Which expression represents sₙ by unrolling?','Σᵢ₌₁ⁿ i²','Each step adds the square of its index.'),
       ('Which closed form is correct?','n(n+1)(2n+1)/6','This sum-of-squares formula has zero base and consecutive difference n².'),
       ('What is the growth order?','Θ(n³)','The leading term of the closed form is n³/3.')]),
      ('Factorial recurrence','f₀=1; fₙ=n fₙ₋₁ for n≥1.',[
       ('What is f₄?','24','Multiply 1·2·3·4=24.'),
       ('Which closed form is correct?','fₙ=n!','The definition of factorial gives n!=n(n−1)! with 0!=1.'),
       ('Why is the base f₀=1 important?','It is the identity for an empty product','Unrolling to n=0 leaves no factors; the empty product equals 1.'),
       ('For n≥1, what is fₙ/fₙ₋₁?','n','Every preceding factorial is nonzero; divide the recurrence by f_(n−1).')]),
      ('Fibonacci recurrence','F₀=0,F₁=1; Fₙ=Fₙ₋₁+Fₙ₋₂ for n≥2.',[
       ('What is F₇?','13','The sequence is 0,1,1,2,3,5,8,13.'),
       ('How many initial values are needed?','2','The second-order recurrence references two previous indices.'),
       ('What is the characteristic equation?','r²−r−1=0','Substitute r^n=r^(n−1)+r^(n−2) and divide by r^(n−2).'),
       ('Why is ordinary one-case substitution at n−1 insufficient for an induction proof?','The recurrence also uses n−2','To evaluate F_n through the recurrence, the proof must know formulas at both prior indices; use two bases and a suitable hypothesis.')]),
      ('Pell-style recurrence','p₀=0,p₁=1; pₙ=2pₙ₋₁+pₙ₋₂ for n≥2.',[
       ('What is p₄?','12','Terms are 0,1,2,5,12.'),
       ('What is the characteristic equation?','r²−2r−1=0','Substitute r^n=2r^(n−1)+r^(n−2).'),
       ('What are its characteristic roots?','1+√2 and 1−√2','The quadratic formula gives [2±√8]/2=1±√2.'),
       ('Which term follows 12?','29','p₅=2p₄+p₃=2·12+5=29.')]),
      ('Repeated characteristic root','a₀=0,a₁=1; aₙ=2aₙ₋₁−aₙ₋₂ for n≥2.',[
       ('What is a₅?','5','The initial difference is 1 and the recurrence preserves that difference, so terms are 0,1,2,3,4,5.'),
       ('Which closed form is correct?','aₙ=n','Substituting 2(n−1)−(n−2)=n verifies the recurrence and the two bases.'),
       ('Which characteristic polynomial is correct?','(r−1)²','r²−2r+1 factors as (r−1)².'),
       ('Which general solution form accommodates the repeated root?','A+Bn','A root 1 of multiplicity two gives (A+Bn)1^n; two initial conditions determine A,B.')]),
      ('Distinct characteristic roots','a₀=2,a₁=3; aₙ=3aₙ₋₁−2aₙ₋₂ for n≥2.',[
       ('What is a₄?','17','The terms are 2,3,5,9,17.'),
       ('Which characteristic roots occur?','1 and 2','r²−3r+2=(r−1)(r−2).'),
       ('Which closed form satisfies the bases?','aₙ=1+2ⁿ','At n=0 and 1 it gives 2 and 3; each root’s power satisfies the recurrence.'),
       ('What is its growth order?','Θ(2ⁿ)','The constant term 1 is dominated by 2^n.')]),
      ('Alternating signs','a₀=1; aₙ=−aₙ₋₁ for n≥1.',[
       ('What is a₇?','−1','Each step changes the sign; an odd index has value −1.'),
       ('Which closed form is correct?','aₙ=(−1)ⁿ','A factor −1 is introduced at each of n steps.'),
       ('What is the smallest positive period?','2','The values repeat 1,−1 with period two, not one.'),
       ('Does this sequence converge over the reals?','No, its even and odd subsequences have different limits','Even indices are 1 and odd indices are −1, so no single limit exists.')]),
      ('Alternating increments','a₀=0; aₙ=aₙ₋₁+(−1)ⁿ for n≥1.',[
       ('What is a₄?','0','The increments −1,+1,−1,+1 cancel.'),
       ('What is a₅?','−1','After a₄=0, the fifth increment is −1.'),
       ('Which closed form is correct?','aₙ=((−1)ⁿ−1)/2','It is 0 at even indices and −1 at odd indices, matching the accumulated alternating increments.'),
       ('Why does pairwise grouping simplify the sum?','Each consecutive odd/even pair sums to 0','The increments at indices 2j−1 and 2j are −1 and +1.')]),
      ('Parity-separated recurrence','a₀=2,a₁=5; aₙ=aₙ₋₂+3 for n≥2.',[
       ('What is a₆?','11','Even indices are 2,5,8,11 at indices 0,2,4,6.'),
       ('What is a₅?','11','Odd indices are 5,8,11 at indices 1,3,5.'),
       ('Which formula gives even indices?','a₂ₖ=2+3k','The even subsequence begins at 2 and advances by 3 each two-index step.'),
       ('Which formula gives odd indices?','a₂ₖ₊₁=5+3k','The odd subsequence begins at 5 and advances independently by 3.')]),
      ('Period-four recurrence','a₀=1,a₁=2; aₙ=−aₙ₋₂ for n≥2.',[
       ('What is a₆?','−1','The cycle is 1,2,−1,−2; index 6 has residue 2 modulo 4.'),
       ('What is the smallest positive period?','4','The four distinct values repeat after four indices.'),
       ('What is the characteristic equation?','r²+1=0','Substitute r^n=−r^(n−2), yielding r²=−1.'),
       ('Which pair of roots occurs over the complex numbers?','i and −i','Both square to −1; no real roots solve r²+1=0.')]),
      ('Nonlinear squaring','a₀=2; aₙ=(aₙ₋₁)² for n≥1.',[
       ('What is a₃?','256','Terms are 2,4,16,256.'),
       ('Which closed form is correct?','aₙ=2^(2ⁿ)','Each squaring doubles the exponent, beginning with exponent 1.'),
       ('Why is this not a linear recurrence in aₙ?','The previous term is squared','Linearity permits constant coefficients on previous terms, not powers of those terms.'),
       ('If bₙ=log₂aₙ, what recurrence follows?','bₙ=2bₙ₋₁','log₂(a²)=2log₂a converts squaring into doubling; b₀=1.')]),
      ('Reciprocal accumulation','a₀=1; aₙ=aₙ₋₁/(1+aₙ₋₁) for n≥1.',[
       ('What is a₃?','1/4','Terms are 1,1/2,1/3,1/4.'),
       ('Which closed form is correct?','aₙ=1/(n+1)','Substitution gives [1/n]/[1+1/n]=1/(n+1), with a₀=1.'),
       ('Which transformed recurrence holds for bₙ=1/aₙ?','bₙ=bₙ₋₁+1','Invert the defining equation: 1/aₙ=1/aₙ₋₁+1.'),
       ('What is the limit as n→∞?','0','The closed form 1/(n+1) tends to zero.')]),
      ('Contracting affine recurrence','a₀=0; aₙ=(aₙ₋₁+1)/2 for n≥1.',[
       ('What is a₃?','7/8','Terms are 0,1/2,3/4,7/8.'),
       ('Which closed form is correct?','aₙ=1−2^(−n)','The deviation from fixed point 1 is halved at each step.'),
       ('What is the fixed point?','1','Solve L=(L+1)/2 to get L=1.'),
       ('What recurrence holds for eₙ=1−aₙ?','eₙ=eₙ₋₁/2','Subtract the recurrence from 1: 1−(a+1)/2=(1−a)/2.')]),
      ('Binary-tree node count','N₀=1; Nₕ=2Nₕ₋₁+1 for h≥1 models a full binary tree of height h.',[
       ('What is N₃?','15','Counts are 1,3,7,15, including the root and both subtrees.'),
       ('Which closed form counts all nodes?','Nₕ=2^(h+1)−1','Each level j has 2^j nodes, so sum levels 0 through h.'),
       ('Why is the recurrence’s constant term 1?','It counts the new root','Two child subtrees supply 2N_(h−1); the root adds one node.'),
       ('How many leaves are at height h?','2ʰ','Each level doubles its predecessor, starting with one node at level zero.')]),
      ('Binary search steps','T(1)=0; T(n)=T(n/2)+1 for powers of two n≥2.',[
       ('What is T(32)?','5','32→16→8→4→2→1 uses five halvings.'),
       ('Which exact formula holds on this domain?','T(n)=log₂n','After k halvings n/2^k=1, so k=log₂n.'),
       ('Why specify powers of two?','Every recursive argument remains an integer and reaches 1 exactly','Without the restriction, n/2 may not be an integer and floor/ceiling rules would be needed.'),
       ('What is the growth order?','Θ(log n)','One unit of work is added per halving, giving logarithmic depth.')]),
      ('Merge-style work','T(1)=0; T(n)=2T(n/2)+n for powers of two n≥2.',[
       ('What is T(8)?','24','T(2)=2,T(4)=8,T(8)=2·8+8=24.'),
       ('Which exact formula is correct?','T(n)=n log₂n','There are log₂n internal recursion levels, each contributing total work n.'),
       ('What is the total work at each internal recursion level?','n','At level j there are 2^j subproblems of size n/2^j, totaling n work.'),
       ('What is the growth order?','Θ(n log n)','The exact solution n log₂n gives linear work across logarithmically many levels.')]),
      ('Two half-size subproblems','T(1)=1; T(n)=2T(n/2)+1 for powers of two n≥2.',[
       ('What is T(8)?','15','T(2)=3,T(4)=7,T(8)=15.'),
       ('Which exact formula is correct?','T(n)=2n−1','Substitute 2(2(n/2)−1)+1=2n−1; the base n=1 gives 1.'),
       ('How many leaves are in the recursion tree?','n','Each leaf has size 1 and halving partitions n into n singleton leaves.'),
       ('What is the growth order?','Θ(n)','The solution 2n−1 is linear.')]),
      ('Quadratic divide and conquer','T(1)=0; T(n)=4T(n/2)+n² for powers of two n≥2.',[
       ('What is T(4)?','32','T(2)=4 and T(4)=4·4+16=32.'),
       ('Which exact formula is correct?','T(n)=n² log₂n','Each internal level has 4^j nodes of size n/2^j; total level cost is n².'),
       ('What is the internal level cost?','n²','4^j(n/2^j)²=n².'),
       ('What is the growth order?','Θ(n² log n)','There are log₂n internal levels, each costing n².')]),
      ('Recursive summation algorithm','T(0)=0; T(n)=T(n−1)+n for n≥1.',[
       ('What is T(4)?','10','T(4)=1+2+3+4=10.'),
       ('How many recursive reductions reach the base?','n','Each step reduces the argument by one, from n to 0.'),
       ('Why is linear recursion depth not enough to infer linear total work?','The cost of each level is its current argument','Costs are n,n−1,…,1 rather than a constant per level.'),
       ('What is the growth order?','Θ(n²)','The sum n(n+1)/2 has quadratic leading term.')]),
      ('Recursive string construction','s₀ is the one-character word 0; sₙ=sₙ₋₁ 1 sₙ₋₁ by concatenation.',[
       ('What is |s₃|?','15','Lengths satisfy L₀=1,Lₙ=2Lₙ₋₁+1, giving 1,3,7,15.'),
       ('How many copies of 0 occur in sₙ?','2ⁿ','Each recursion doubles all prior zeros and introduces no new zero; start with one.'),
       ('How many copies of 1 occur in sₙ?','2ⁿ−1','The count satisfies O₀=0,Oₙ=2Oₙ₋₁+1, giving 2^n−1.'),
       ('Why is every sₙ a palindrome?','The base is a palindrome and each step mirrors equal palindrome halves around 1','Inductively, reversing s_(n−1)1s_(n−1) returns the same word because each half equals its reverse.')]),
    ]
    pools={
      '16':['13','19','12'], '96':['48','32','192'], '15':['14','16','8'], '3':['2','4','1'],
      '−1':['1','0','−2'], '36':['30','42','12'], '1':['0','2','−1'], '14':['9','12','15'],
      '24':['16','20','120'], '13':['8','21','12'], '2':['1','3','0'], '12':['10','14','7'],
      '29':['24','27','34'], '5':['4','6','8'], '17':['16','18','9'], '4':['2','3','8'],
      '0':['1','−1','2'], '11':['8','14','10'], '256':['64','128','512'], '1/4':['1/3','1/8','1/5'],
      '7/8':['3/4','1/8','15/16'], '32':['16','24','64'], '10':['8','12','16'],
      'Θ(n²)':['Θ(n)','Θ(log n)','Θ(2ⁿ)'], 'Θ(n³)':['Θ(n²)','Θ(n)','Θ(n⁴)'],
      'Θ(2ⁿ)':['Θ(n)','Θ(n²)','Θ(log n)'], 'Θ(log n)':['Θ(n)','Θ(n log n)','Θ(1)'],
      'Θ(n log n)':['Θ(n)','Θ(log n)','Θ(n²)'], 'Θ(n)':['Θ(log n)','Θ(n²)','Θ(2ⁿ)'],
      'Θ(n² log n)':['Θ(n²)','Θ(n log n)','Θ(n³)'], 'n':['n−1','2n','n²'], 'n²':['n','2n','n² log₂n'],
      '2ⁿ':['n','2n','2ⁿ−1'], '2ʰ':['h','2h','2ʰ−1'], '2ⁿ−1':['2ⁿ','n','n²'],
    }
    # Formula distractors target index offsets, confusing addition/multiplication,
    # dropping forcing terms, and ignoring initial values.
    formula_pools={
      'aₙ=4+3n':['aₙ=4·3ⁿ','aₙ=3n','aₙ=4+3(n−1)'],
      'bₙ=3·2ⁿ':['bₙ=3+2n','bₙ=2ⁿ','bₙ=3·2ⁿ⁻¹'],
      'cₙ=2ⁿ−1':['cₙ=2ⁿ','cₙ=n','cₙ=2n−1'],
      'dₙ=cₙ+1':['dₙ=cₙ−1','dₙ=2cₙ','dₙ=cₙ²'],
      'aₙ=n(n+1)/2':['aₙ=n²','aₙ=n(n−1)/2','aₙ=2ⁿ'],
      'aₙ=n²':['aₙ=n(n+1)/2','aₙ=2n−1','aₙ=2ⁿ'],
      'Σᵢ₌₁ⁿ i':['Σᵢ₌₁ⁿ i²','n+n','2ⁿ'],
      'Σᵢ₌₁ⁿ i²':['(Σᵢ₌₁ⁿ i)²','Σᵢ₌₁ⁿ i','n²'],
      'n(n+1)(2n+1)/6':['n(n+1)/2','n²','n³'],
      'fₙ=n!':['fₙ=n²','fₙ=2ⁿ','fₙ=n'],
      'r²−r−1=0':['r²+r+1=0','r−2=0','r²−1=0'],
      'r²−2r−1=0':['r²−r−1=0','r²+2r+1=0','r²−2=0'],
      '1+√2 and 1−√2':['2 and −1','1 and 2','√2 and −√2'],
      '(r−1)²':['(r+1)²','r²−1','r−2'],
      'A+Bn':['A·2ⁿ+B','A+B·(−1)ⁿ','A·n²+B'],
      '1 and 2':['−1 and −2','1 and 3','2 and 3'],
      'aₙ=n':['aₙ=n²','aₙ=2ⁿ','aₙ=1'],
      'aₙ=1+2ⁿ':['aₙ=2ⁿ','aₙ=2+3n','aₙ=3ⁿ'],
      'aₙ=(−1)ⁿ':['aₙ=1','aₙ=−n','aₙ=(−2)ⁿ'],
      'aₙ=((−1)ⁿ−1)/2':['aₙ=(−1)ⁿ','aₙ=n','aₙ=−n'],
      'a₂ₖ=2+3k':['a₂ₖ=2+6k','a₂ₖ=5+3k','a₂ₖ=2·3ᵏ'],
      'a₂ₖ₊₁=5+3k':['a₂ₖ₊₁=2+3k','a₂ₖ₊₁=5+6k','a₂ₖ₊₁=5·3ᵏ'],
      'r²+1=0':['r²−1=0','r+1=0','r²−2r+1=0'],
      'i and −i':['1 and −1','2 and −2','0 and 1'],
      'aₙ=2^(2ⁿ)':['aₙ=2ⁿ','aₙ=2n','aₙ=2^(n²)'],
      'bₙ=2bₙ₋₁':['bₙ=bₙ₋₁+2','bₙ=(bₙ₋₁)²','bₙ=bₙ₋₁/2'],
      'aₙ=1/(n+1)':['aₙ=1/2ⁿ','aₙ=1/n','aₙ=n+1'],
      'bₙ=bₙ₋₁+1':['bₙ=2bₙ₋₁','bₙ=bₙ₋₁−1','bₙ=(bₙ₋₁)²'],
      'aₙ=1−2^(−n)':['aₙ=2^(−n)','aₙ=1+2^(−n)','aₙ=n/2'],
      'eₙ=eₙ₋₁/2':['eₙ=2eₙ₋₁','eₙ=eₙ₋₁+1','eₙ=eₙ₋₁−1'],
      'Nₕ=2^(h+1)−1':['Nₕ=2ʰ','Nₕ=2h+1','Nₕ=2^(h+1)'],
      'T(n)=log₂n':['T(n)=n','T(n)=n/2','T(n)=2ⁿ'],
      'T(n)=n log₂n':['T(n)=n','T(n)=log₂n','T(n)=n²'],
      'T(n)=2n−1':['T(n)=n−1','T(n)=2ⁿ−1','T(n)=n²'],
      'T(n)=n² log₂n':['T(n)=n²','T(n)=n log₂n','T(n)=n³'],
      '4+3(n−1)+3=4+3n':['4+3(n−1)+1=4+3n','4+3(n−1)=4+3n','4·3ⁿ=4+3n'],
      'Replace b₀=3 by b₀=6':['Replace multiplier 2 by 4 but keep b₀=3','Replace b₀=3 by b₀=4','Add 2 to each step but keep b₀=3'],
      'n²−(n−1)²=2n−1':['n²−(n−1)²=2n+1','n²−(n−1)²=n','n²−(n−1)²=1'],
      'It is the identity for an empty product':['It is the identity for addition','All recurrences require base 1','Choosing 0 would leave positive factorials unchanged'],
      'The recurrence also uses n−2':['The recurrence has no base cases','Induction cannot prove sequences','The previous term must always be zero'],
      'No, its even and odd subsequences have different limits':['Yes, the limit is 0 because the values cancel','Yes, the limit is 1 because a₀=1','Yes, the limit is −1 because a₁=−1'],
      'Each consecutive odd/even pair sums to 0':['Every increment equals 0','Every pair sums to 2','The increments are all positive'],
      'The previous term is squared':['Its initial term is 2','It contains only one prior term','It uses integer indices'],
      'It counts the new root':['It counts a new leaf in each old subtree','It counts both child subtrees','It corrects for two duplicate roots already counted'],
      'Every recursive argument remains an integer and reaches 1 exactly':['Only powers of two have logarithms','The cost per step is zero for other integers','The recurrence has no base case for powers of two'],
      'The cost of each level is its current argument':['Every level always costs one unit','Depth and work are always equal','The base case contributes all work'],
      'The base is a palindrome and each step mirrors equal palindrome halves around 1':['Any word repeated twice is automatically a palindrome','Inserting 1 anywhere makes a palindrome','Equal lengths of two arbitrary halves ensure a palindrome'],
    }
    for case_index,(topic,ctx,rows) in enumerate(cases):
        ctx+=' Introductory recurrence solving and algorithm analysis may vary by course section.'
        for row_index,(prompt,key,reason) in enumerate(rows):
            options=pools.get(key,formula_pools.get(key))
            assert options is not None, key
            add('recurrences',topic,prompt,key,[(x,f'This does not match the recurrence, its initial values, or the requested reasoning. {reason}') for x in options],reason,
                'Compute a few initial terms, then check a proposed rule at the base indices and in the recurrence.',context=ctx,
                verification={'kind':'recurrence-case','case':case_index,'query':row_index})
    assert len(BANK['recurrences']) == 100

def write_bank():
    manifest=dict(version=1,title='CS 2305 Discrete Mathematics for Computing I',total_questions=600,pillars=[])
    inventory=dict(version=1,requested_questions=600,generated_questions=0,validated_questions=0,pillars=[])
    for slug,title in PILLARS:
        qs=BANK[slug]; assert len(qs)==100
        directory=ROOT/'data'/slug; directory.mkdir(parents=True,exist_ok=True)
        entry=dict(id=slug,title=title,course_dependent=slug in ['proofs','recurrences'],blocks=[])
        inv=dict(id=slug,planned=100,generated=100,validated=0,blocks=[])
        for index in range(2):
            block_id=f'{slug}-block-{index+1:02}'
            block=dict(schema_version=1,block_id=block_id,pillar_id=slug,block_title=f'{title} · Block {index+1}',questions=qs[index*50:(index+1)*50])
            file=directory/f'block-{index+1:02}.json'
            file.write_text(json.dumps(block,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            entry['blocks'].append(dict(id=block_id,title=f'Block {index+1}',path=file.relative_to(ROOT).as_posix(),count=50))
            inv['blocks'].append(dict(id=block_id,planned=50,generated=50,validated=0))
        manifest['pillars'].append(entry);inventory['pillars'].append(inv)
    inventory['generated_questions']=600
    (ROOT/'data'/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'data'/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')
    print('Generated 600 original workshop questions in twelve 50-question blocks.')

if __name__ == '__main__':
    for builder in [logic,proofs,sets,counting,graphs_number,recurrences]: builder()
    write_bank()

    # Regeneration retains the seventh pillar in the complete inventory.
    from generate_midterm import build as build_midterm
    build_midterm()
