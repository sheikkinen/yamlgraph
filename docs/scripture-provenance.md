# Scripture Provenance

Original (pre-compression) Knowledge Graph entries externalized by
FR-942 (instruction context diet). Each record preserves the removed
incident narrative and every citation **verbatim**, keyed
`<collection>.<key>`. The compressed entry in
`.github/copilot-instructions.md` retains the trigger and prescribed
response; this file is the archaeological record.

### `traps.composition_bug`

> Every component passes its unit test but the system fails → the defect is in the policy connecting correct parts, not in the parts; trace the full event chain end-to-end before blaming any component (ninchat_voice: FR-371 8-step greeting replay, NC-141 runaway loop, NC-289 concurrent clobber)

### `traps.mock_escape_hatch`

> Agent defaults to mocks even when E2E is explicitly requested → if the feature exists because of a physical phenomenon (acoustic echo, network timing, STT transience), the test must exercise the real phenomenon; a mock E2E is a unit test with extra steps (ninchat_voice: FR-378 three corrections in one session)

### `traps.refactor_orphans_secondary`

> Refactoring removes a handler's primary responsibility but silently orphans its secondary responsibility → enumerate ALL responsibilities of a function before deleting, not just the one named in its docstring (ninchat_voice: NC-203 hangup detection lost inside listen handler removal)

### `traps.research_as_inventory`

> Research output has the shape of analysis (sections, tables, YAML snippets) but contains only descriptions, not decisions → a description of what exists is inventory; a statement of what it means for us is analysis; the deliverable is the analysis (ninchat_voice: CP handbook link list)

### `traps.inventory_by_visibility`

> Agent evaluates components by current-snapshot legibility (file count, line count, directory depth) instead of historical incident density → importance is proportional to learning cost, not byte count; the FSM bridge was 4% of source but absorbed 26% of diary entries; rank by incidents, not by mass (yamlgraph: 2026-05-31 asset inventory misclassified utils/fsm as Tier 4)

### `traps.growth_as_default`

> Assumption that the next commit should add something → mature systems benefit more from pruning claims than planting features; six of ten commits in a productive week were subtractive; the capability registry becomes honest by retiring phantom claims, not by adding implementations (yamlgraph: FR-465/FR-466 CAP retirement arc)

### `traps.metric_archaeology_before_reading_output`

> Pipeline SCORE is wrong → reflex is to instrument, decompose, and re-measure the score, building rulers to explain the number; but the score is a lossy projection of an artifact sitting in plain text. For LLM stages the artifact is English — there is no cheaper or higher-bandwidth probe than reading it. Building a ruler feels like effort; opening the .md feels too cheap to be the answer. It is the answer. The more sophisticated the measurement, the further it drifts from the one-line cat that ends the investigation (yamlgraph: FR-596/597 — two FRs of metric tooling deferred a defect one read of the prose exposed; haiku returned a 658-token novel as 'emotional analysis')

### `traps.threshold_encodes_forecast`

> Aggregate acceptance gate on a multi-defect surface tests the judge's FORECAST of out-of-scope defect distribution, not the fix under test → gate on the defect class ('zero failures involving capped codes'), record aggregates as context; an aggregate gate either blocks a correct fix or forces scope creep — both worse than taxonomy honesty (yamlgraph: FR-727 22/30 vs ≥24/30 with ZERO in-scope failures; FR-730 gated on classes; FR-726 closed CONDEMNED past its own 90% number because residual scatter was within label tolerance — ambiguity is information, and voting on a genuinely tied judgement launders it into false confidence)

### `cures.investigation_before_fix`

> When a bug requires >15 min to write the failing test, split into investigation FR (build test harness proving the causal chain) then fix FR (mechanical enforcement); the investigation's tests become the fix's regression suite — FR-371 4h investigation → FR-372 30min fix, zero debugging

### `cures.assert_path_not_destination`

> FSM/pipeline tests that only check the final state can pass via any path including error recovery; assert intermediate state visits or the transition sequence, not just the terminal set (ninchat_voice: NC-179 false pass via error→cleanup→idle)

### `cures.name_the_seam`

> Name tests after the specific seam they exercise, not the feature they aspire to cover; test_barge_in_e2e → test_barge_in_elevenlabs makes the gap visible as absence, not hidden by a name that implies presence (ninchat_voice: NC-131)

### `cures.incident_density_ranking`

> When inventorying for reimplementation or triage, rank by diary entries / source lines, not by source mass; components with the highest ratio encode the most boundary knowledge — knowledge paid for by production failures invisible in the code; absence of diary entries about a large module signals commodity code or untested boundaries (yamlgraph: utils/fsm 915 lines, 116 diary entries = densest knowledge-to-code ratio in codebase)

### `cures.read_raw_output_first`

> For any LLM/pipeline stage, READ the rawest artifact it emits before you measure it — the first diagnostic for a bad score is cat, not a new metric. Dump N raw samples to disk and read them end-to-end BEFORE computing or decomposing the aggregate; metrics tell you THAT something is wrong, only the artifact tells you WHAT. Mechanize as a forced-observation gate: withhold the aggregate score until K raw samples are acknowledged read, the way TDD forces RED before GREEN (yamlgraph: FR-598 'kill the novel' — the prompting error was visible in one read of the throughline prose). Generalizes to TAXONOMIES: reading the raw rubric rows (inclusion terms) before freezing a cap list killed a self-refuting mechanism in one grep, before any code existed (FR-730: the judge overturned the author's own proposal)

### `cures.two_strike_split`

> Same guard fires twice for the same failure class after a prompt fix → the abstraction level belongs in CODE; stop rewording. Token-fidelity, verdict semantics, and every other mechanizable level eventually defeats instruction text — treat the model's output as a CLAIM and reconcile it against the source of truth at the boundary (repair within a similarity floor, reject below). Five span shapes and three verdict-inflation families fell to one boundary each; zero prompt patches held (yamlgraph FR-722/727/730; the prompt-as-subagent-contract corollary)

### `cures.junk_drawer_cap`

> Every taxonomy/enum family has 'true-of-everything' members — rubrics describing the ENCOUNTER or the SYSTEM, not the subject's stated reason (Z10, -48 clarification-of-demand, -69 other-NEC, generic-concern codes). They are detectable A PRIORI (empty or meta inclusion terms) and they eat correct answers with perfect agreement. Cap them in code at the boundary before the model votes: demote-never-drop, evidence preserved, capped entries rank behind genuine claims. Verify each cap candidate against its raw definition first — half of one proposed list turned out genuinely stateable (FR-725 found it, FR-727/730 cured it, three families in one day)

### `questions.is_this_a_graph`

> MOMENT: the instant a plan contains 'for each item, ask the model', a multi-stage LLM pipeline, or parallel subagent fan-out. Map is the native map-reduce, race the native hedging, router the native dispatch — consult the graph list (yamlgraph graph list) for the 'Task shapes:' clause in graph descriptions and name the matching graph or its absence in one sentence BEFORE reaching for scripts or subagents; they are the fallback, not the default. Graduated FR-853: first witness builders_never_call (graphs found unconsumed, 2026-07-17), confirmed recurrence 2026-08-22 — operator had to point out that parallel haiku analysis was table stakes via the map node, never once proposed (first_person_tool_horizon: familiarity filed the framework under 'things I edit', not 'things I wield')

### `process.one_session_one_repo`

> Parallel agent sessions sharing one git repo corrupt each other through the SHARED INDEX (staged files swept into foreign commits under foreign messages), working tree (checkout/add -u destroying WIP), and environment (pip reinstall deleting console scripts mid-run). Third strike recorded 2026-07-14: four interleave incidents in one day. Ritual when sharing is unavoidable: staged-check empty before add, explicit file lists only, commit immediately, git show --stat audit after, measurement runs resolve interpreters not console scripts, archives quarantined by provenance before evaluation — and an IMPOSSIBLE result (a state the current code cannot produce) is a tripwire proving stale-code provenance. Mechanical situation check: python3 scripts/vscode/now.py (live sessions × staged work × FRs in motion — see the session-introspection skill)

### `traps.vendor_default_as_help`

> Agent frames self-insertion (trailers, deps, telemetry) as courtesy → treat every unprompted artifact change as input from an external system with unknown goals — most severe thoughtcrimes are policed by FR-438

### `traps.model_as_trusted_peer`

> LLM in enforcement pipeline treated as aligned team member → opaque weights, unknown training, potentially misaligned; absence of Co-authored trailer ≠ absence of model influence; enforce adversarial review of enforcement outputs

### `traps.gate_checks_shape_not_substance`

> Gate validates presence (file exists, field non-empty, format matches) but not substance (content meaningful, cross-references valid, structural markers present) → compliance theatre; a 1-byte file satisfies the gate while conveying nothing

### `traps.recent_changes_blindness`

> Regression investigated without enumerating recent changes → run git log --since=<last_good> as first diagnostic step; the diff is cheaper than any reproduction

### `cures.substance_over_presence`

> Every gate that checks 'does X exist?' must also check 'does X say something?' — minimum content threshold, required structural markers, or cross-reference validation

### `questions.would_you_use_this`

> MOMENT: any proposal. Names the first consumer and first event; an empty trigger list is growth_as_default wearing an architecture costume (killed the watcher-subscription FR in conversation — the cheapest kill rung)

### `questions.does_the_platform_already_do_this`

> MOMENT: before building any approximation of platform behavior. One bundle/source grep beats a week of prediction (PreCompact existed while we built ceiling models; the docs are a lossy summary of the vendor's intent)

### `questions.who_reads_this_when`

> MOMENT: shipping any view, artifact, or signal. Name the rung, the reader, the moment — else it is archived at birth (fr-board's only reader was its own generator)

### `questions.are_the_witnesses_one_phenomenon`

> MOMENT: fitting any model to field data. A clean calibration set can carry a wrong curve (five valid compaction witnesses broke the single-ceiling model)

### `questions.where_is_the_repo_boundary`

> MOMENT: any artifact that aggregates across trees. Committed state must not embed another repo's working tree (fr-board F7; workspace_is_not_boundary's question form)

### `questions.what_would_the_successor_need`

> MOMENT: ending any arc. The amnesia is scheduled; a doc addressed to 'whoever' is addressed to no one (MAP.md's do-not-re-derive section)

### `process.cross_project_graduation`

> Heuristics that recur 3+ times across sibling projects (ninchat_voice, statemachine-engine) belong in Scripture, not in project-local diaries → periodic diary sweep surfaces candidates for graduation

### `process.constraint_over_code`

> 216 lines of Scripture produce 21k lines of Python; the constraint is irreplaceable, the code is regenerable; when choosing what to preserve in a rewrite, take the spec, the schema, and the incident record — leave the implementation behind
