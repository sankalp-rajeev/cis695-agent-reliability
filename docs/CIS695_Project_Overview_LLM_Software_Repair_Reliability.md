---
title: "CIS 695 Project Overview"
subtitle: "Reliable LLM Agents for Automated Software Repair"
author: "Sankalp Rajeev"
institution: "University of Michigan–Dearborn"
course: "CIS 695 — Master's Project"
advisor_candidate: "Dr. Foyzul Hassan"
semester: "Fall 2026"
status: "Advisor discussion draft"
version: "1.0"
---

# Reliable LLM Agents for Automated Software Repair

## High-Level Project Overview

**Student:** Sankalp Rajeev  
**Course:** CIS 695 — Master's Project  
**Advisor candidate:** Dr. Foyzul Hassan  
**Semester:** Fall 2026  
**Project window:** August 26 – December 10, 2026

---

# 1. One-Page Abstract

Large-language-model software agents can now inspect repositories, execute commands, modify source code, run tests, and submit patches for real software issues. Benchmarks such as SWE-bench have made this capability measurable by evaluating model-generated patches against real GitHub issues in reproducible repository environments. SWE-bench Verified contains 500 human-reviewed tasks selected to have clear issue descriptions, correct test patches, and sufficient information for a capable engineer or agent to solve them [1].

However, **producing a plausible patch is not the same as producing a trustworthy repair**.

A software-repair agent may believe it has solved an issue because a reproduction script or generated test passes, while the patch still fails hidden acceptance tests or breaks previously correct behavior. Recent research on repository-level LLM repair shows that test overfitting remains a real problem: patches can pass generated tests yet fail held-out golden or regression tests [8]. A separate 2026 study also found that simply encouraging agents to write more tests does not consistently improve final issue-resolution performance [9]. These findings suggest that “the agent ran a test” is not by itself a sufficient basis for trusting an autonomous repair.

This Master's Project will study the following question:

> **How reliably can an LLM software-repair agent decide that its own patch is correct, and can an independent execution-grounded verification layer reduce false-success decisions?**

The project will use a fixed software-repair agent to attempt a controlled subset of real repository-level bugs. For each task, the agent receives the issue description and buggy repository state, explores the codebase, edits source code, runs commands/tests, and submits a patch. The agent will also make an explicit final claim: **resolved** or **unresolved**.

The candidate patch will then be passed to an **independent verifier**. The verifier will not see the benchmark's gold patch, hidden acceptance tests, or hidden oracle labels. Instead, it will use evidence available in a realistic pre-merge setting, such as:

- patch integrity and scope checks;
- existing regression tests;
- repository-supported syntax, type, lint, or build checks;
- issue-derived reproduction tests generated independently from the issue and original code;
- execution traces and test outcomes.

The verifier will output **accept**, **flag**, or **reject**.

Only after both the repair agent and verifier have finished will the official benchmark harness evaluate the patch using the benchmark oracle. This creates three distinct signals:

1. **Agent belief:** does the repair agent think the issue is fixed?
2. **Verifier belief:** is there sufficient independent evidence to accept the patch?
3. **Oracle outcome:** does the patch actually satisfy the benchmark's authoritative tests?

The central outcome will be the **false-acceptance / false-success rate**: how often a patch is declared successful but fails authoritative evaluation. The project will also measure repair rate, verifier precision and recall, regression behavior, acceptance coverage, latency, token/API cost, and failure categories.

The primary benchmark is planned to be a controlled subset of **SWE-bench Verified**. A 10-task pilot will establish environment reliability, cost, and runtime before a final study size—approximately 50–75 tasks—is frozen. **BugsInPy** will be retained as a lower-complexity fallback if SWE-bench infrastructure becomes impractical [5].

The project will use a **pretrained model as-is**. Fine-tuning is deliberately excluded from the required scope because the research contribution is verification and reliability, not training a better coding model. One strong coding model and one fixed agent scaffold will be used for the main experiment; a second open-weight model may be added only as a stretch study.

The expected outcome is a reproducible framework and empirical analysis showing **when LLM software-repair agents can be trusted, when they are confidently wrong, and which independent verification signals are useful before accepting an autonomous patch**.

---

# 2. Why This Problem Matters

Software-engineering agents are rapidly moving from code completion toward autonomous repository-level work. They can:

- read issue reports;
- search large repositories;
- locate relevant files;
- reproduce failures;
- edit multiple source files;
- run tests and shell commands;
- submit patches.

SWE-bench formalized this setting around real GitHub issues and corresponding codebases [2]. The current ecosystem includes full agent frameworks, deliberately simple agents such as mini-SWE-agent, and more constrained systems such as Agentless [3][4].

The problem is no longer only:

> **Can an LLM generate a patch?**

A more important deployment question is:

> **When should a team trust and merge a patch produced by an autonomous agent?**

A production software team cannot use hidden benchmark tests every time a new issue appears. In real development, the true acceptance criteria may not yet exist. This means an autonomous repair system has to make decisions using incomplete evidence.

That creates a reliability problem.

---

# 3. What Already Exists

## 3.1 SWE-bench and execution-based evaluation

SWE-bench evaluates software-engineering systems on real GitHub issues. A task provides an issue description, repository, and base commit. A system produces a code patch. The benchmark then applies the patch and runs tests in a controlled environment [1][2].

Available SWE-bench variants include:

- **SWE-bench:** 2,294 instances;
- **SWE-bench Lite:** 300 instances;
- **SWE-bench Verified:** 500 human-validated instances;
- **SWE-bench Multimodal:** tasks that include visual/UI information;
- **SWE-bench Multilingual:** 300 tasks across 9 languages and 42 repositories [2].

SWE-bench Verified is the most appropriate starting point for this project because it reduces ambiguity in the benchmark itself.

## 3.2 Software-repair agents

**SWE-agent** demonstrated that an LLM equipped with a software-oriented agent-computer interface can navigate repositories and resolve issues.

**mini-SWE-agent** provides a much smaller agent loop and is designed explicitly for reproducible SWE-bench experiments. Its current documentation describes a minimal control flow, Docker/Singularity support, trajectory capture, and direct SWE-bench batch evaluation [3].

**Agentless** showed that a simpler localization → repair → patch-validation pipeline can compete strongly with complex agent systems, demonstrating that patch validation is already recognized as an important part of the problem [4].

## 3.3 Training data for software-engineering agents

**SWE-smith** provides a pipeline for generating software-engineering training tasks at scale. Its published dataset contains tens of thousands of tasks from over one hundred repositories and has been used to train open software-engineering models such as SWE-agent-LM-32B [6].

This makes model fine-tuning technically possible, but it does not mean fine-tuning is necessary for this project.

## 3.4 Harder and fresher benchmarks

**SWE-bench Pro** extends the benchmark toward longer-horizon enterprise-like tasks, with 1,865 problems from 41 repositories [7].

**SWE-rebench** addresses contamination and benchmark staleness by continuously collecting fresher repository-level tasks; its public dataset contains more than 21,000 interactive Python tasks [10].

These are important developments but add scope and infrastructure complexity. They are better suited as follow-up or stretch validation than as the required CIS 695 benchmark.

## 3.5 Test overfitting is already documented

A particularly relevant 2026 study evaluated test overfitting in repository-level LLM repair. It showed that patches which passed generated tests could still fail hidden acceptance/regression tests. In the reported setups, the overfitting rate among patches passing generated tests was 21.8% for one Claude-based setup and 33.0% for a GPT-4o-based setup before refinement [8].

The same work emphasized an important real-world constraint:

> hidden/golden acceptance tests are generally not available when an issue is still open.

Therefore, a realistic repair system needs surrogate evidence rather than access to the oracle.

A second 2026 empirical study analyzed test-writing behavior across multiple LLM agents and found that increasing or decreasing the amount of agent-written testing did not significantly alter final outcomes in its controlled experiments [9].

Together, these results motivate a project focused not on simply “adding more tests,” but on understanding **which independent evidence is actually useful for accepting or rejecting a repair**.

---

# 4. Research Gap

Existing work already gives us:

- strong coding models;
- autonomous agent loops;
- repository sandboxes;
- patch generation;
- internal test execution;
- benchmark-level authoritative evaluation;
- generated reproduction tests;
- candidate-selection and patch-validation techniques.

The remaining practical gap is:

> **What should an autonomous repair system believe before the hidden oracle is known?**

A benchmark can tell us *after the fact* whether a patch was correct. A real deployed agent must decide *before the fact* whether the patch is trustworthy enough to propose, merge, or escalate for review.

This project therefore treats **repair acceptance** as a separate research problem.

---

# 5. Project Problem Statement

An LLM repair agent receives:

- an issue description;
- a buggy repository state;
- access to shell/tools;
- visible repository tests.

It produces:

- a candidate patch;
- an execution trajectory;
- a final claim that the issue is resolved or unresolved.

The project investigates whether that final claim is reliable.

Formally, for each task we compare:

```text
Agent claim      ∈ {resolved, unresolved}
Verifier decision ∈ {accept, flag, reject}
Oracle outcome    ∈ {resolved, unresolved}
```

The key undesirable case is:

```text
Agent says RESOLVED
        or
Verifier says ACCEPT
        ↓
Official benchmark says UNRESOLVED
```

This is a **false success / false acceptance**.

---

# 6. Core Research Questions

## RQ1 — Agent reliability

**How often does a software-repair agent declare success when the authoritative benchmark later shows the patch is incorrect?**

## RQ2 — Verification value

**Can independent execution-grounded verification reduce the false-acceptance rate?**

## RQ3 — Verification composition

**Which verification signals contribute most: regression tests, issue-derived reproduction tests, static checks, or patch-risk checks?**

## RQ4 — Reliability–coverage trade-off

**Does stronger verification improve trustworthiness only by rejecting too many actually-correct patches?**

## RQ5 — Failure modes

**What kinds of software issues and agent behaviors produce false confidence?**

---

# 7. What Kinds of Software Tasks Will We Solve?

The project is not limited to one-line syntax bugs.

Repository-level issue benchmarks contain realistic engineering problems such as:

## 7.1 Logic and semantic bugs

The code executes, but the behavior is wrong for an edge case.

Examples:

- Boolean logic implements “exactly one” when the specification requires parity.
- A mathematical simplification misses a valid algebraic reduction.
- A function returns the wrong result for a boundary condition.

## 7.2 Framework and API behavior

A framework feature behaves incorrectly in a particular context.

Examples:

- an enumeration class is accidentally treated as callable by a template engine;
- a foreign-key validation path uses the wrong manager;
- two filtered relations unexpectedly collapse into one SQL join.

## 7.3 Database / ORM bugs

The application generates incorrect SQL or database-specific behavior.

Examples:

- combined `OR` and `AND` constraints generate malformed schema SQL on certain databases;
- query ordering fails after combining querysets;
- timezone conversion is reversed in database functions.

## 7.4 Numerical and scientific-computing bugs

A mathematical or scientific library handles an edge case incorrectly.

Examples:

- modular arithmetic fails to simplify an expression that should reduce;
- a number-theory function omits a valid modular root;
- plotting limits behave incorrectly under logarithmic scaling.

## 7.5 State-management and UI/library behavior

A library preserves the wrong internal state after an operation.

Examples:

- clearing a plotting axis re-enables labels that should remain hidden;
- style configuration affects the wrong visual element;
- registered objects are not retrieved consistently through a high-level API.

## 7.6 Platform and process bugs

Behavior differs by operating system, process launch mode, or runtime configuration.

Examples:

- an auto-reloader fails to preserve Python interpreter options;
- file-locking code interprets a successful OS call as failure;
- subprocess state is not propagated correctly.

---

# 8. Real Benchmark Examples

The following are real SWE-bench Verified task types; descriptions are summarized rather than copied verbatim.

## Example A — SymPy modular arithmetic

**Task:** `sympy__sympy-15599`

A modular arithmetic expression involving a multiplied imaginary term is not simplified as expected. The repair requires understanding SymPy's `Mod` simplification logic rather than simply changing an output string [11].

**Why useful for this project:**  
A narrow generated test may validate one example while missing related symbolic edge cases.

## Example B — Django enumeration types in templates

**Task:** `django__django-12304`

Django enumeration/choice classes cannot be referenced naturally in templates because the template engine treats the class as a callable and attempts to invoke it [12].

**Why useful:**  
The patch is small, but correctness depends on framework semantics and avoiding regressions for other callable objects.

## Example C — Django CheckConstraint SQL

**Task:** `django__django-11299`

A particular combination of logical conditions in a database check constraint generates incorrect SQL on SQLite and Oracle [13].

**Why useful:**  
A repair might pass tests on one backend while remaining invalid on another, making regression and environment-aware verification important.

## Example D — Matplotlib tick-label styling

**Task:** `matplotlib__matplotlib-25287`

A scientific plotting configuration changes tick-label color, but the offset/exponent text derives its color from a different configuration property [14].

**Why useful:**  
The patch can look obviously correct while still affecting related styling behaviors elsewhere.

These tasks illustrate why repository-level repair is not equivalent to generating a standalone function.

---

# 9. Proposed Solution at a High Level

The system will have **two independent stages**.

## Stage 1 — Repair agent

The repair agent receives the issue and repository.

It can:

1. search files;
2. inspect relevant code;
3. run commands;
4. reproduce the problem;
5. modify source files;
6. run tests;
7. submit a patch;
8. declare `RESOLVED` or `UNRESOLVED`.

## Stage 2 — Independent verifier

The verifier receives:

- the original issue;
- original repository;
- frozen candidate patch.

It does **not** receive:

- the gold patch;
- benchmark acceptance-test patch;
- hidden oracle result.

The verifier checks:

- does the patch apply cleanly?
- did the agent alter inappropriate files/tests?
- do relevant existing tests still pass?
- do broader regression tests pass?
- do repository-provided static/type/build checks pass?
- can an independently generated issue-specific reproduction test distinguish buggy from patched behavior?
- are there high-risk patch characteristics?

The verifier returns:

```text
ACCEPT
FLAG FOR REVIEW
REJECT
```

## Stage 3 — Oracle evaluation

Only afterward is the patch submitted to the official benchmark evaluation.

That oracle result is used for **research evaluation**, not for verification.

---

# 10. Critical Experimental Rule: No Oracle Leakage

The benchmark contains information that exists only because the real bug was later fixed.

The repair agent and verifier must not see:

- gold patch;
- gold test patch;
- hidden `FAIL_TO_PASS` acceptance tests;
- final resolved/unresolved label.

Otherwise, the experiment would not represent real issue resolution.

The hidden benchmark oracle is used **only after decisions are frozen**.

This separation is central to the scientific validity of the project.

---

# 11. What We Are Trying to Achieve

The project is successful if it can answer:

1. **How frequently is the agent confidently wrong?**
2. **Can we detect some of these wrong patches before the oracle does?**
3. **What evidence is actually useful?**
4. **What does verification cost in time and compute?**
5. **Which failures remain impossible to detect with the proposed signals?**

The project does **not** need to produce a new state-of-the-art SWE-bench score.

A useful result could be:

> “The verifier reduced false acceptance substantially but reduced automation coverage.”

Another useful result could be:

> “Regression/static checks catch regressions but do little for semantic incompleteness; issue-derived tests help in some categories but can themselves overfit.”

A negative result is still a valid research result if the experiment is controlled.

---

# 12. Scope

## Required scope

- one agent scaffold;
- one primary pretrained coding model;
- one primary benchmark;
- 10-task engineering pilot;
- approximately 50–75 final tasks, finalized after pilot;
- one frozen agent configuration;
- one independent verifier;
- official external evaluation;
- quantitative reliability analysis;
- qualitative failure analysis.

## Optional/stretch scope

- second open-weight model;
- fresh tasks from SWE-rebench;
- generated-test ablation;
- one verification-feedback retry;
- integration of verifier concepts into Nexus.

---

# 13. What We Will Not Do

The project will not:

- train a foundation model;
- fine-tune the required primary model;
- benchmark ten different LLMs;
- build an IDE product;
- compete for the SWE-bench leaderboard;
- expose gold tests to the verifier;
- let the verifier secretly become a second repair agent;
- use proprietary internship code;
- rebuild Nexus as the capstone.

These exclusions protect the 3-credit semester scope.

---

# 14. Relationship to Nexus

The student's existing **Nexus** project already demonstrates an engineering loop:

```text
Observe
→ Diagnose
→ Patch
→ Evaluate
```

Nexus answers:

> **Can an autonomous LLMOps system detect a failure, propose remediation, and re-evaluate it?**

The Master's Project asks the research question Nexus does not answer:

> **When should such a system trust its own remediation?**

Therefore, the capstone is not a duplicate of Nexus.

It converts the engineering idea into a controlled research study with:

- real public software bugs;
- independent ground truth;
- formal reliability metrics;
- verifier ablations;
- failure analysis;
- reproducible evaluation.

Long-term, the resulting verifier could become a reliability layer inside Nexus, but that integration is not required for CIS 695.

---

# 15. Expected Deliverables

1. Formal project proposal and literature review.
2. Reproducible benchmark subset.
3. Fixed repair-agent pipeline.
4. Independent verification pipeline.
5. Structured trajectories and patch records.
6. Official oracle results.
7. Reliability metrics and statistical analysis.
8. Verification ablation study.
9. Failure taxonomy and representative case studies.
10. Final CIS 695 report.
11. Final presentation.
12. Reproducible repository, subject to model/API and benchmark licences.

---

# 16. Success Metrics

The primary metric is **false-acceptance rate**:

> Of the patches we believed were safe to accept, how many were actually wrong?

It must be paired with **acceptance coverage**:

> What percentage of patches did we accept?

This prevents a trivial verifier from appearing “perfect” by rejecting everything.

Secondary metrics:

- authoritative issue-resolution rate;
- verifier precision;
- verifier recall;
- false-rejection rate;
- regression rate;
- cost per task;
- latency per task;
- patch size;
- failure categories.

---

# 17. Why This Is an Appropriate Master's Project

The project combines:

- artificial intelligence;
- LLM agents;
- empirical software engineering;
- automated program repair;
- testing and verification;
- reproducible experimentation;
- statistical analysis;
- software-system design.

It is sufficiently technical to demonstrate graduate-level independent work while remaining controllable within a single semester because the project deliberately reuses established agent frameworks and public benchmarks instead of training a new model.

---

# 18. References / Research Basis

[1] SWE-bench Verified — human-validated 500-task subset.  
https://www.swebench.com/verified.html

[2] SWE-bench FAQ / dataset overview and evaluation process.  
https://www.swebench.com/SWE-bench/faq/

[3] mini-SWE-agent documentation — minimal agent and SWE-bench runner.  
https://mini-swe-agent.com/latest/

[4] Xia et al., *Agentless: Demystifying LLM-based Software Engineering Agents*, 2024.  
https://arxiv.org/abs/2407.01489

[5] BugsInPy — reproducible real Python bugs and test infrastructure.  
https://github.com/soarsmu/BugsInPy

[6] Yang et al., *SWE-smith: Scaling Data for Software Engineering Agents*, NeurIPS 2025.  
https://arxiv.org/abs/2504.21798

[7] Deng et al., *SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?*, 2025.  
https://arxiv.org/abs/2509.16941

[8] Ahmed et al., *Investigating Test Overfitting on SWE-bench / Is the Cure Still Worse Than the Disease?*, FSE 2026.  
https://arxiv.org/abs/2511.16858

[9] Chen et al., *Rethinking the Value of Agent-Generated Tests for LLM-Based Software Engineering Agents*, 2026.  
https://arxiv.org/abs/2602.07900

[10] Badertdinov et al., *SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents*, 2025.  
https://arxiv.org/abs/2505.20411

[11] SWE-bench Verified task: `sympy__sympy-15599`.  
https://www.tbench.ai/registry/swebench-verified/head/sympy__sympy-15599

[12] SWE-bench Verified task: `django__django-12304`.  
https://www.tbench.ai/registry/swebench-verified/head/django__django-12304

[13] SWE-bench Verified task: `django__django-11299`.  
https://www.tbench.ai/registry/swebench-verified/head/django__django-11299

[14] SWE-bench Verified task: `matplotlib__matplotlib-25287`.  
https://www.tbench.ai/registry/swebench-verified/head/matplotlib__matplotlib-25287
