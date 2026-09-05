# The reader who knows nothing

*Draft — LinkedIn article. Author: Sami Heikkinen. Status: draft; run through `scripts/outsider.sh --input` once (2026-09-05 13:07Z): 6 unclear, 4 of them the quoted jargon example, 2 mine — glossed.*

---

Most of my ideas arrive at five in the morning and are about five words long.

"Census the capability files." "Retire the ledger." "Investigate the framework defect." I type them to an AI agent and go make coffee. What happens next is a pipeline I have spent a year building: the agent writes a plan, a second model judges the plan and freezes its scope, the agent implements against that frozen scope with tests first, a third model reviews the pull request against the plan. About an hour of automation passes. I have usually forgotten the spark by then — there are three or four others churning.

Then the pull request lands in front of me, and I cannot read it.

Not "it is wrong". It is usually right. I cannot *read* it. "Extend CAP journey census with enum-leak demotion and junk-drawer cap per FR-990 R-3." Every word is a real thing in the repository. Every word was coined this week, by an agent, for another agent. The description was written by the only entity that had the context, for the only other entity that had it, and I — the person who is supposed to decide whether it merges — am the outsider.

## The rule that had no enforcer

The repository already had a rule about this. It said: *name your reader.* Write for the person who reads this next, not for yourself. Agents read that rule at the start of every session. It changed nothing, and yesterday I finally understood why: every reader in the loop already knew the vocabulary. The planner knew it, the judge knew it, the reviewer had the whole codebase open. A rule with no reader who can *fail* is decoration.

So we built a reader who provably knows nothing.

## What the outsider is

It is a small script. It takes one thing — the title and body of a pull request — and hands it to a language model that runs from a temporary directory *outside* the repository, so it cannot load the project's instructions, cannot open a file, cannot call a tool. It has to read the description the way a stranger would. It answers in four fixed sections:

1. What this change does, in my own words — hedges stated inline ("the text does not say who this is for").
2. Could I decide whether to merge from the description alone? Yes or no, with one sentence.
3. Words and references I could not understand — each one quoted, each with the question it raised.
4. What a merge decision would still need.

Then a piece of ordinary code — not the model — derives the verdict: two or fewer unclear terms and no hedge in section one, or it is a NO. The report is posted as a comment on the pull request. It is advice. It gates nothing. It runs once per PR.

## What it found

On the pull request that built it, the informed reviewer — a model given everything — found six real defects: a cleanup routine that deleted another run's lock, a record written before the thing it recorded had happened, a parser that accepted too much. The outsider, given only the description, found six different things: terms that meant nothing without the codebase, decisions described but not justified, how to run it. **Zero overlap.** The two readers sit at opposite ends of the knowledge axis, and each is blind to what the other sees.

On my own follow-up — a write-up of an experiment I had been staring at for two hours — it listed five terms it could not understand and nine things a decision would need. All fair. I had written "plan §13" as if the world knew which plan, and which section.

On a plan to delete a file, it raised something no one in the loop had written down: the record we were moving into GitHub comments can be edited or deleted. The plan now says so. That was the first time the outsider found a hole in the *plan*, not just in the prose.

## What the day taught

**Two adversaries, one who knows nothing.** A single review, however good, has one vantage point. Pair it with a reader whose only qualification is ignorance and the union of findings is much larger than either.

**Models flicker; put the rule in code.** The same text, read twice by the same model two minutes apart, got "five unclear terms" and then "zero". That is not a defect to fix in the prompt; it is the nature of the instrument. So the verdict is computed in code, the result is advisory, and we run it once per PR — you do not take five readings from a nagger and keep the kind one.

**The tests ran the script and never noticed it could not be run.** Thirty-six tests passed. The first human to type the command got "permission denied" — the file had been committed without its executable bit, and every test had invoked it via `bash`, which never asks. A test that supplies the interpreter witnesses the text, not the command.

**Don't make every run write to a shared file.** Version one appended a line to a committed ledger on every run, so we could count how many PRs it had read. Five merge conflicts in one day, all on that one line. The fix — a plan judged today, the repository's number for it is FR-1004 — is to delete the ledger and let the posted comment *be* the record, with the provenance — which commit, which model, a fingerprint of the text read — inside it. And while writing this article I checked the replacement count query: GitHub's search said thirty PRs; the actual number of comments is seven. The count has to come from the comments themselves. The plan gets one more revision.

**It cannot see quotation marks.** I ran this article through it before posting. It flagged six terms. Four of them were the jargon I quoted in the second paragraph *as an example of jargon*. Of course it did — it does not know what a quotation is, only what it cannot understand. The other two were mine, and are now glossed.

## The bridge between two kinds of forgetting

I forget the spark within the hour. The agent has no memory at all past the session. The pull request description is the only bridge between us — and it was being written in a language neither of us would speak tomorrow. The outsider stands on that bridge and asks, politely, what every word means.

It is about two hundred lines of shell and Python on top of YAMLGraph, the YAML-first pipeline framework I have been building in the open. Today it runs on `gpt-5.6-sol` through the GitHub Copilot command line, takes about a minute per pull request, and costs a few cents. A stand-alone version that needs only `pip install yamlgraph`, the GitHub CLI and one API key is being packaged now. The repository, the plans, the judgements and the diary entries that produced all of this are public:

https://github.com/sheikkinen/yamlgraph

If your team's pull requests are written by agents for agents, try giving them one reader who knows nothing.

#AgenticAI #AIEngineering #SoftwareEngineering #CodeReview
