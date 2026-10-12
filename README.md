# CS 2305 Discrete Mathematics for Computing I

An original supplementary practice lab for computer science students. Static HTML/CSS/JavaScript with separate UTF-8 JSON banks, worked reasoning, and explanations for every distractor. No runtime dependencies or account required.

**Independent supplementary practice.** The first six pillars provide general course practice; their induction, advanced graph examples, and recurrence-solving topics may vary by section. Pillar 7 is scoped to the supplied fall-semester classroom materials and matching textbook content. This AI-assisted bank has automated checks and author review, but no independent human subject-matter review. Report suspected errors before relying on an item.

Live site: https://Babuptx.github.io/cs-2305-dm/

## Inventory

| Pillar | Scope | Blocks | Questions |
| --- | --- | --- | --- |
| Logic and mathematical reasoning | Boolean operations, truth tables, minterms, negation, quantifiers, witness dependence | 2 × 50 | 100 |
| Proof techniques | Direct proof, contraposition, contradiction, counterexamples, induction, strong induction, uniqueness, invariants | 2 × 50 | 100 |
| Sets, relations, and functions | Set operations, Venn regions, Cartesian products, power sets, relation properties, function classifications and inverses | 2 × 50 | 100 |
| Counting and combinatorics | Product/sum rules, permutations, combinations, inclusion–exclusion, stars and bars, pigeonhole principle | 2 × 50 | 100 |
| Graph theory and number theory | Paths, connectivity, degree sums, Euler trails, bipartiteness, divisibility, gcd, modular arithmetic | 2 × 50 | 100 |
| Recurrence relations | Recursive definitions, unrolling, closed forms, characteristic roots, nonlinear transformations, introductory algorithm analysis | 2 × 50 | 100 |
| Fall Semester Midterm Practice | Slide-scoped logic/proofs, sets/functions, sequences/countability/matrices, algorithms/complexity, and number theory through GCDs | 8 × 50 | 400 |
| **Total** | | **20 blocks** | **1,000** |

The original six pillars each have 25 case workshops with four tasks per case. Pillar 7 has 80 workshops with five tasks each: 240 intermediate and 160 advanced items. Related items share context while testing different reasoning obligations. Difficulty labels are author judgments, not empirically calibrated exam scores.

## Fall Semester Midterm Practice

The uploaded classroom materials govern topic selection; the supplied Rosen eighth-edition textbook supplies related exercises by subject. The mapping covers §§1.1, 1.3–1.8, 2.1–2.6, 3.1–3.3, and 4.1–4.3. Odd-exercise numbers shown after answer reveal are **related study pointers**, not claims that the original practice item reproduces the exercise or predicts the professor's exam. Refer to the book for its exact wording. No instructor endorsement is claimed.

The eight blocks are logic/equivalence; quantifiers/inference; proof construction; sets/functions; sequences/sums/countability; matrices/algorithms; growth/operation counts; and number theory. Elementary recurrences belong to the sequence material, but this pillar does not import the other pillars' induction, advanced recurrence solving, graph theory, or later counting units. `data/utd-fall-midterm/coverage.json` records the distribution.

Working reference now offers the existing **All-course essentials** and a separate scrollable **Fall Semester Midterm Reference** collection with topic navigation. The latter corrects mathematical conditions in the supplied cheat sheet, including prime/composite definitions, signed GCD identities, positive asymptotic constants, little-o, fixed-width representations, and operation-count assumptions. Additional sheet topics are labeled separately. This full reference is not formatted as a permitted one-page exam aid.

All supplied PDFs and extracted analysis stay under ignored `/refer/`. The build copies only `index.html`, `styles.css`, `js/`, and `data/`; no local course source material is deployed.

## Run locally

With Node.js 22 or newer installed:

```powershell
Set-Location -LiteralPath 'C:\Users\crpan\OneDrive\Documents\GitHub\gitview\cs-2305-dm'
npm start
```

Open http://127.0.0.1:8080. Use HTTP; directly opening `index.html` cannot fetch the JSON banks. The server binds only to the local computer; set `PORT` to change its port.

On the original Windows workstation, portable Node was prepared outside the repository:

```powershell
$quizNode = (Get-ChildItem -LiteralPath "$env:LOCALAPPDATA\CodexQuizTools" -Filter node.exe -Recurse | Select-Object -First 1).FullName
& $quizNode scripts/serve.mjs
# Install development dependencies once before content validation:
& (Join-Path (Split-Path $quizNode) 'npm.cmd') ci
& $quizNode scripts/validate.mjs
& $quizNode --test tests/engine.test.mjs
```

## Workflow and scoring

The fifth dropdown opens **Fall Semester Midterm Flashcards**: 40 original concept cards spanning the 19 midterm sections. Recall the front-side prompt, then click/tap the card or use Enter/Space to reveal an explanation, worked example, and takeaway. Previous/Next, arrow keys, and Shuffle deck support review. The viewer scrolls on small screens, preserves quiz progress, and leaves any active quiz timer running. Flashcards are separate from scored question totals.

Select a pillar/block, study or exam mode, and an optional 30/50/75/90-minute limit. Answer/change selections, flag questions, and use the block map or Previous/Next. Left/Right keys navigate when focus is outside an interactive control. Shuffle preserves responses by stable question ID. A 50-question block is a practice grouping, not a claim about the real exam's question count.

Study mode offers two hints and deliberate answer reveal. Revealing locks the selected response. Hints do not reduce scores. An unanswered reveal stays unanswered and scores zero. Exam mode withholds hints, keys, explanations, and source notes from its display until submission. Finish asks for confirmation; timer expiry submits once. Review shows score, correct/incorrect/unanswered counts, elapsed time, the correct option, your response, and every rationale.

Versioned, validated browser storage holds the latest session, cumulative attempts, and theme. Resume restores order, responses, flags, hints, locks, and the original deadline. Timed blocks use wall-clock time even while closed. Completed resumes are not counted again. Repeated attempts contribute to aggregate totals, rather than being treated as unique question mastery. Reset asks before clearing progress. Storage failures leave the current quiz usable but may prevent persistence. No names or sensitive information are collected.

Static JSON keys are downloadable. This is educational practice, not a secure examination platform.

## Validation

```powershell
npm ci
npm run validate
npm test
npx playwright install chromium
# Keep npm start running in another terminal:
npm run test:browser
npm run build
```

Validation checks inventory totals, IDs, runtime schema, manifest paths, key indexes, exact distractor-index coverage, UTF-8 text, placeholders, local exhibits, hints, duplicate items, similar prompts, repeated option sets, and balanced answer positions. `data/question.schema.json` documents the interchange schema; runtime validation adds cross-field constraints such as indexes bounded by choices. `data/inventory.json` records planned/generated/validated counts; `data/validation-report.json` records the actual results.

Independent JavaScript oracles check computed answers using truth parsing, arithmetic, finite set/graph computations, sequences, matrices, loop simulations, modular arithmetic, and base conversions. Python generation and JavaScript checking use separate implementations. The report gives current checked-item counts; conceptual proofs are author-reviewed rather than machine-proved. The midterm tests deliberately corrupt each computational answer key and verify that the independent checker rejects it. Similarity flags remain available for editorial inspection: distinct objectives can share a case, and reused numerical option sets need not indicate repeated questions.

Engine tests cover locks, ID-based shuffle grading, exam display restrictions, exactly-once grading, timer switching/expiry, resume, malformed persistence, fetch races/errors, and unavailable storage. Playwright exercises both modes, all twenty blocks, hints, flags, review, shuffle, saved preferences/progress, reset, expired-session recovery, the 90-minute option, reference collection switching and scrolling, keyboard dismissal, source notes, malformed banks, fetch failures, and desktop/mobile layout. Screenshots go to ignored `test-results/`.

## Structure and adding content

```text
index.html / styles.css         Learner interface
js/app.js                      DOM rendering and controls
js/engine.js                   State, grading, timers, persistence
js/flashcards.js               Flashcard loading, validation, and viewer
data/flashcards/utd-midterm.json Midterm concepts and worked examples
data/manifest.json             Runtime pillar and block inventory
data/<pillar>/block-01.json     Question banks
data/question.schema.json      Block/item schema
scripts/generate_bank.py       Reproducible authored workshops
scripts/oracles.mjs             Independent calculations
scripts/validate.mjs            Content checks and report
tests/                         Engine/browser tests
.github/workflows/pages.yml     Validation and Pages deployment
```

Each question supplies a stable ID, topic, difficulty, prompt/context, choices, zero-based key, hints, learning objective, correct rationale, one rationale per distractor, source notes, and exhibit metadata. Optional `verification` powers automated checking and is never displayed to learners. Exhibits should use local paths and meaningful alt text.

Add schema-compatible JSON with unique IDs, then register its path, ID, title, and count in the manifest. The engine follows the manifest; the release validator currently requires seven pillars, twenty blocks, and 1,000 questions. Edit authored case definitions and independent checks before regenerating. `python scripts/generate_bank.py` rebuilds all seven pillars; `python scripts/generate_midterm.py` updates only Pillar 7 and the combined inventory. Regeneration replaces generated banks: preserve manual corrections in the generator first.

## Deployment, corrections, and source policy

Develop on `sandbox`, validate, and merge normally into `main`. The workflow checks both branches and deploys only `main`. `npm run build` copies the site/content to `dist/`, excluding Git metadata and development tooling. Relative asset paths support `/cs-2305-dm/` hosting.

Pages settings should be **Settings → Pages → Build and deployment → Source → GitHub Actions**. If necessary, enable that source, then run **Actions → Validate and deploy quiz → Run workflow** on `main`. Official action versions follow [GitHub's Pages workflow guide](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

For a correction, open an issue containing the question ID, disputed statement, derivation/counterexample, and a credible reference where helpful. Do not upload proprietary exams or paid-bank material. No textbook passages or third-party image assets are copied. Further reading: [MIT Mathematics for Computer Science](https://ocw.mit.edu/courses/6-042j-mathematics-for-computer-science-spring-2015/). This is general reference material, not an endorsement or a claim that MIT reviewed these original items.

No license was selected by the owner, so none is added. Dependencies retain their own licenses.
