# Phase 4 follow-up: G3 diagnosis

This is a read-only investigation of the 122 `GOLD_LINE_IN_GENERATOR` findings in the sealed pilot run `runs/study_v4_pilot` (seal `ff2fe8d5…`). Nothing in `src/`, `configs/`, the prompts or the sealed run was changed. Gold-patch lines are identified only by sha256 (the first 12 hex characters in the tables below; the full values are in `runs/study_v1_5/v4_pilot_audit.log`), their length and their finding location. No line text appears in this report.

## Conclusion

All 122 findings are written by the model. They cover 20 distinct gold lines in 7 of the 10 tasks. The other three tasks (`django__django-16667`, `pytest-dev__pytest-5809` and `astropy__astropy-13398`) have none.

- **Where each line first appears.** In each of its conversations, every line first appears in an assistant message's `reasoning_content`, the DeepSeek generator's own reasoning. No line appears in a tool output or user message before the model wrote it.
- **The four tool-output findings.** All four are in `django__django-16631` pass 2. They come from the model reading back `/tmp/testbed_fixed`, a copy of the repository that the model itself had edited with the fix.
- **Environment.** None of the 20 lines exists anywhere in its task's image filesystem. No pilot image has a commit, tag or ref beyond the base commit's history.
- **Audit.** The audit is correct. Five sampled findings were re-checked independently and none is a false positive. A looser check with all whitespace removed found no near-copies among the 20 lines.
- **What the model did with the lines.** In three tasks the model put its candidate fix into scratch files under `/tmp`, or ran it in memory, to confirm that its tests pass on fixed code. No line was written into a `v4_repro/` test or into an existing repository file. No line is in any frozen kept test.

So G3 failed because the generator writes out, in its reasoning and in scratch checks, the same lines as the gold fix. The cause is not an environment leak and not an audit false positive. This data cannot tell whether the model derived those lines from the issue and the source or recalled them.

## Classification per task

The prompt's category B is split into B-test (written into a `v4_repro/` test) and B-source (written into a repository file). **No finding fits either.** Every line is model-written, but it stayed in the model's reasoning or went into scratch files outside the repository. So the table also gives the B sub-type that does apply.

| Task | Findings | Distinct lines | Class | B sub-type |
|---|---:|---:|---|---|
| matplotlib__matplotlib-25479 | 4 | 1 | B | reasoning only |
| django__django-13807 | 35 | 5 | B | reasoning, a `/tmp` scratch file and an in-memory run |
| django__django-15572 | 9 | 2 | B | reasoning only |
| django__django-16667 | 0 | 0 | none | – |
| pytest-dev__pytest-5809 | 0 | 0 | none | – |
| django__django-12965 | 3 | 1 | B | reasoning only |
| django__django-16631 | 58 | 7 | B | reasoning, `/tmp` scratch files and the `/tmp/testbed_fixed` copy; 4 tool-output hits are read-backs of that copy |
| django__django-11095 | 11 | 3 | B | reasoning and a `/tmp` scratch file |
| astropy__astropy-13398 | 0 | 0 | none | – |
| sympy__sympy-13480 | 2 | 1 | B | reasoning only |

There are no A (environment leak) findings and no C (audit false positive) findings.

## 1. Findings grouped by task, conversation, role and message index

My independent re-scan of the three per-conversation trajectories reproduced all 122 audit entries, matching each one by task, conversation, message index and sha256. Every finding is in an assistant message (118) or a tool output (4). None is in a system or user message. Each assistant hit is in the message's `reasoning_content` or in its tool-call arguments, with a copy in the message's `extra` field. Four are in `content`.

### Findings per task and role

| Task | Findings | System | User | Assistant | Tool output | Distinct lines |
|---|---:|---:|---:|---:|---:|---:|
| matplotlib__matplotlib-25479 | 4 | 0 | 0 | 4 | 0 | 1 |
| django__django-13807 | 35 | 0 | 0 | 35 | 0 | 5 |
| django__django-15572 | 9 | 0 | 0 | 9 | 0 | 2 |
| django__django-16667 | 0 | 0 | 0 | 0 | 0 | 0 |
| pytest-dev__pytest-5809 | 0 | 0 | 0 | 0 | 0 | 0 |
| django__django-12965 | 3 | 0 | 0 | 3 | 0 | 1 |
| django__django-16631 | 58 | 0 | 0 | 54 | 4 | 7 |
| django__django-11095 | 11 | 0 | 0 | 11 | 0 | 3 |
| astropy__astropy-13398 | 0 | 0 | 0 | 0 | 0 | 0 |
| sympy__sympy-13480 | 2 | 0 | 0 | 2 | 0 | 1 |
| **Total** | **122** | 0 | 0 | 118 | 4 | **20** |

### Findings by conversation, role and message index

Each line is listed by the first 12 characters of its sha256 (full hashes are in the audit log), and `×n` means the message held n distinct gold lines.

| Task | Conversation | Role | Message index | Lines | Findings |
|---|---|---|---:|---|---:|
| matplotlib__matplotlib-25479 | requirements | assistant | 27 | 6ad76b440300 | 1 |
| matplotlib__matplotlib-25479 | requirements | assistant | 41 | 6ad76b440300 | 1 |
| matplotlib__matplotlib-25479 | pass 1 | assistant | 9 | 6ad76b440300 | 1 |
| matplotlib__matplotlib-25479 | pass 1 | assistant | 45 | 6ad76b440300 | 1 |
| django__django-13807 | requirements | assistant | 10 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | requirements | assistant | 28 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | pass 1 | assistant | 13 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | pass 1 | assistant | 41 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | pass 1 | assistant | 43 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | pass 2 | assistant | 11 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-13807 | pass 2 | assistant | 21 | 1161a2f78bc4, 2f0f881b3d5f, 61a456bcc97d, f36faa926c6f, fd4fd516a22b | 5 |
| django__django-15572 | requirements | assistant | 15 | 9d67f6ccf8ec | 1 |
| django__django-15572 | requirements | assistant | 23 | 9d67f6ccf8ec | 1 |
| django__django-15572 | requirements | assistant | 27 | 9d67f6ccf8ec | 1 |
| django__django-15572 | requirements | assistant | 37 | 9d67f6ccf8ec | 1 |
| django__django-15572 | requirements | assistant | 43 | 170153a38c07, 9d67f6ccf8ec | 2 |
| django__django-15572 | pass 2 | assistant | 29 | 9d67f6ccf8ec | 1 |
| django__django-15572 | pass 2 | assistant | 31 | 170153a38c07, 9d67f6ccf8ec | 2 |
| django__django-12965 | requirements | assistant | 31 | d29ad35aa789 | 1 |
| django__django-12965 | pass 1 | assistant | 25 | d29ad35aa789 | 1 |
| django__django-12965 | pass 2 | assistant | 50 | d29ad35aa789 | 1 |
| django__django-16631 | requirements | assistant | 13 | 0dc0958e6fe8, 443191891a2a, 6d17202e8a18, 9eef1b49ce45, bd5c41a51e9f, f77491b986b8 | 6 |
| django__django-16631 | requirements | assistant | 22 | 0dc0958e6fe8, 443191891a2a, 6d17202e8a18, 9eef1b49ce45, bd5c41a51e9f, f77491b986b8 | 6 |
| django__django-16631 | requirements | assistant | 44 | 6d17202e8a18, f77491b986b8 | 2 |
| django__django-16631 | requirements | assistant | 50 | 0dc0958e6fe8, 443191891a2a, 6d17202e8a18, 9eef1b49ce45, bd5c41a51e9f, f77491b986b8 | 6 |
| django__django-16631 | requirements | assistant | 54 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45 | 3 |
| django__django-16631 | pass 1 | assistant | 15 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f, f77491b986b8 | 5 |
| django__django-16631 | pass 1 | assistant | 21 | 0dc0958e6fe8, 9eef1b49ce45, f77491b986b8 | 3 |
| django__django-16631 | pass 1 | assistant | 27 | 0dc0958e6fe8, 443191891a2a, 6d17202e8a18, 75887edd0fe3, 9eef1b49ce45, bd5c41a51e9f, f77491b986b8 | 7 |
| django__django-16631 | pass 1 | assistant | 39 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f | 4 |
| django__django-16631 | pass 1 | assistant | 41 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f | 4 |
| django__django-16631 | pass 2 | assistant | 15 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f | 4 |
| django__django-16631 | pass 2 | assistant | 35 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f | 4 |
| django__django-16631 | pass 2 | tool output | 44 | 0dc0958e6fe8, 443191891a2a, 9eef1b49ce45, bd5c41a51e9f | 4 |
| django__django-11095 | requirements | assistant | 10 | 0c3735e44e69, a19742d4e0b1, fe427d17ffcc | 3 |
| django__django-11095 | requirements | assistant | 15 | 0c3735e44e69 | 1 |
| django__django-11095 | pass 1 | assistant | 11 | 0c3735e44e69 | 1 |
| django__django-11095 | pass 1 | assistant | 13 | 0c3735e44e69, a19742d4e0b1 | 2 |
| django__django-11095 | pass 1 | assistant | 19 | a19742d4e0b1 | 1 |
| django__django-11095 | pass 2 | assistant | 17 | 0c3735e44e69, a19742d4e0b1, fe427d17ffcc | 3 |
| sympy__sympy-13480 | requirements | assistant | 13 | a66c51369635 | 1 |
| sympy__sympy-13480 | requirements | assistant | 17 | a66c51369635 | 1 |


## 2. Commands behind the tool-output findings

All four tool-output findings are in one message, `django__django-16631` pass 2 #44. It was produced by the command below, which is shown up to its first 300 characters. That command contains no gold line.

| Message | Lines | Command |
|---|---|---|
| pass 2 #44 | bd5c41a51e9f, 0dc0958e6fe8, 9eef1b49ce45, 443191891a2a | `sed -n '190,225p' /tmp/testbed_fixed/django/contrib/auth/__init__.py && sed -n '125,165p' /tmp/testbed_fixed/django/contrib/auth/base_user.py && cd /tmp/testbed_fixed && PYTHONPATH=/tmp/testbed_fixed python - <<'PY' from pathlib import Path p=Path('v4_repro/test_repro_R4.py') text=p.read_text() …` |

`/tmp/testbed_fixed` was built by the model's own tool call at pass 2 #35. That call copies `/testbed/django` to `/tmp`, then writes the model's candidate fix into the copy. The four lines first appear in that conversation at pass 2 #15, in the assistant's reasoning. The tool output therefore shows the model its own edit, not anything from the environment.

## 3. Assistant findings: copied from the environment, or written by the model?

For each of the 118 assistant findings, I checked every earlier tool and user message in the same conversation.

- **Copied from the environment:** 0. No line appeared in an earlier tool or user message of the same conversation.
- **Written by the model:** 118. In each conversation, every one of the 20 lines first appears in an assistant message's `reasoning_content`.

Of the 118, 90 are in reasoning text only. The other 28 are also in tool-call arguments: the model put the line into a command, as section 9 describes.

## 4. Git history in the pilot images

Each image was checked in a throwaway container, run with `--rm --network none --read-only --pull=never` on its pinned image id, using `git -c safe.directory=* --no-optional-locks` inside `/testbed`. Nothing was written.

| Task | `rev-list --all --count` | `rev-list HEAD --count` | Tags | Refs | Commits on refs that are not ancestors of HEAD | Reflog entries | Stash entries |
|---|---:|---:|---:|---:|---:|---:|---:|
| matplotlib__matplotlib-25479 | 47,024 | 47,024 | 112 | 113 | 0 | 1 | 0 |
| django__django-13807 | 29,076 | 29,076 | 8 | 9 | 0 | 1 | 0 |
| django__django-15572 | 30,636 | 30,636 | 8 | 9 | 0 | 1 | 0 |
| django__django-16667 | 31,572 | 31,572 | 8 | 9 | 0 | 1 | 0 |
| pytest-dev__pytest-5809 | 10,438 | 10,438 | 124 | 125 | 0 | 1 | 0 |
| django__django-12965 | 28,363 | 28,363 | 8 | 9 | 0 | 1 | 0 |
| django__django-16631 | 31,546 | 31,546 | 8 | 9 | 0 | 1 | 0 |
| django__django-11095 | 26,840 | 26,840 | 8 | 9 | 0 | 1 | 0 |
| astropy__astropy-13398 | 33,660 | 33,660 | 17 | 18 | 0 | 1 | 0 |
| sympy__sympy-13480 | 29,902 | 29,902 | 55 | 56 | 0 | 1 | 0 |

In every image, every commit reachable from a ref is an ancestor of HEAD. Unreachable objects (`git fsck --unreachable`) were not checked.

The pilot images were also searched for other files carrying a gold line. For each of the 7 tasks with findings, a throwaway container with the same flags walked the whole filesystem. It skipped `/proc`, `/sys`, `/dev`, `/run`, `/tmp`, binary files and files over 5 MB, normalized each file's whitespace, and checked whether any of that task's gold lines was a substring. The lines reached the container on stdin, and only hashes and paths came back. **No line was found in any file.**

| Task | Files scanned | Files containing a gold line |
|---|---:|---:|
| matplotlib__matplotlib-25479 | 144,500 | 0 |
| django__django-13807 | 33,211 | 0 |
| django__django-15572 | 36,047 | 0 |
| django__django-12965 | 33,063 | 0 |
| django__django-16631 | 36,186 | 0 |
| django__django-11095 | 32,785 | 0 |
| sympy__sympy-13480 | 29,816 | 0 |

## 5. Search terms in the generator trajectories

The counts below are matches in the commands the generator ran: the `command` argument of each tool call, across all three conversations. Matches in the raw trajectory text are higher, because that text also holds the prompts, a copy of each command in `extra`, and command outputs. Those raw counts are in the investigation's scratch output and were not used here.

| Task | git log | git show | --all | git tag | reflog | rev-list | pip download | pip show | site-packages | find / | curl | wget |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| matplotlib__matplotlib-25479 | 17 | 5 | 10 | 1 | 3 | 0 | 1 | 0 | 2 | 11 | 4 | 0 |
| django__django-13807 | 4 | 0 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| django__django-15572 | 4 | 1 | 2 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 0 |
| django__django-16667 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| pytest-dev__pytest-5809 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| django__django-12965 | 8 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 1 | 0 |
| django__django-16631 | 8 | 3 | 4 | 0 | 1 | 0 | 0 | 0 | 0 | 2 | 0 | 0 |
| django__django-11095 | 3 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| astropy__astropy-13398 | 9 | 1 | 6 | 2 | 3 | 0 | 1 | 0 | 1 | 5 | 1 | 0 |
| sympy__sympy-13480 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

The generator did look through git history, ran `find /`, and ran `pip download` and `curl` with the network off. Section 4 shows that none of those sources holds a gold line. The task with the most such searches, matplotlib, has 1 distinct gold line, and that line first appears in reasoning.

## 6. Audit check on five findings

The check was reimplemented without the audit's own `gold_candidate_lines`. The archive was hash-checked against the registry first, and every member file was compared. Each cell gives the result with whitespace collapsed to single spaces, then with all whitespace removed.

| Finding | Line sha256 (12) | Length | In issue | Equal to or inside a `-` line | Archive files containing it |
|---|---|---:|---|---|---|
| matplotlib__matplotlib-25479 requirements #27 | 6ad76b440300 | 29 | no / no | no / no | 0 / 0 of 4,535 |
| django__django-13807 requirements #10 | 1161a2f78bc4 | 33 | no / no | no / no | 0 / 0 of 6,423 |
| django__django-15572 requirements #15 | 9d67f6ccf8ec | 70 | no / no | no / no | 0 / 0 of 6,618 |
| django__django-16631 requirements #13 | 6d17202e8a18 | 29 | no / no | no / no | 0 / 0 of 6,652 |
| django__django-11095 requirements #10 | 0c3735e44e69 | 36 | no / no | no / no | 0 / 0 of 6,067 |

None of the five is an audit false positive.

## 7–9. Distinct lines, the looser check, and where each line was written

- **Step 7:** 122 findings and 20 distinct lines. The per-task counts are in section 1. The table below gives the number of messages each line appears in.
- **Step 8:** with all whitespace removed, 0 of the 20 lines match the issue, a `-` line or any base-archive file. The exact check missed no near-copies.
- **Step 9:** no line went into (a) a `v4_repro/` file or (b) an existing repository file. 10 lines are (c), in reasoning text only. The other 10 are in reasoning and also in scratch work outside the repository. That work is one or more of: `/tmp/check_with_expected_fix.py`, `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`, `/tmp/verify_fixed.py`, the edited copy `/tmp/testbed_fixed/django/contrib/auth/{__init__,base_user}.py`, and an in-memory `python -` run in `/testbed`. All of those wrote no repository file. None of the 20 lines is in a frozen test under `verification/v4/tests/`.

### Distinct lines (steps 7, 8 and 9)

The loose columns compare each line with all whitespace removed against the issue, the patch's `-` lines and the files of the base archive. The "written to" column comes from the targets of the commands that contain the line.

| Task | Line sha256 (12) | Length | Messages | Conversations | Loose: issue | Loose: `-` lines | Loose: archive files | First seen | Written to | In a frozen test |
|---|---|---:|---:|---|---|---|---:|---|---|---|
| django__django-11095 | 0c3735e44e69 | 36 | 5 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-11095 | a19742d4e0b1 | 51 | 4 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/check_with_expected_fix.py` | no |
| django__django-11095 | fe427d17ffcc | 41 | 2 | requirements, pass 2 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-12965 | d29ad35aa789 | 34 | 3 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-13807 | 1161a2f78bc4 | 33 | 7 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`; an inline `python -` run in /testbed that writes no file | no |
| django__django-13807 | 2f0f881b3d5f | 45 | 7 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`; an inline `python -` run in /testbed that writes no file | no |
| django__django-13807 | 61a456bcc97d | 63 | 7 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`; an inline `python -` run in /testbed that writes no file | no |
| django__django-13807 | f36faa926c6f | 33 | 7 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`; an inline `python -` run in /testbed that writes no file | no |
| django__django-13807 | fd4fd516a22b | 32 | 7 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/run_fixed.py`, `/tmp/test_r1_fixed.py`; an inline `python -` run in /testbed that writes no file | no |
| django__django-15572 | 170153a38c07 | 46 | 2 | requirements, pass 2 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-15572 | 9d67f6ccf8ec | 70 | 7 | requirements, pass 2 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-16631 | 0dc0958e6fe8 | 41 | 12 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/testbed_fixed/django/contrib/auth/__init__.py`, `/tmp/testbed_fixed/django/contrib/auth/base_user.py`, `/tmp/verify_fixed.py` | no |
| django__django-16631 | 443191891a2a | 46 | 11 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/testbed_fixed/django/contrib/auth/__init__.py`, `/tmp/testbed_fixed/django/contrib/auth/base_user.py`, `/tmp/verify_fixed.py` | no |
| django__django-16631 | 6d17202e8a18 | 29 | 5 | requirements, pass 1 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-16631 | 75887edd0fe3 | 46 | 1 | pass 1 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| django__django-16631 | 9eef1b49ce45 | 53 | 12 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/testbed_fixed/django/contrib/auth/__init__.py`, `/tmp/testbed_fixed/django/contrib/auth/base_user.py`, `/tmp/verify_fixed.py` | no |
| django__django-16631 | bd5c41a51e9f | 36 | 10 | requirements, pass 1, pass 2 | no | no | 0 | assistant `reasoning_content` | a scratch file outside the repository: `/tmp/testbed_fixed/django/contrib/auth/__init__.py`, `/tmp/testbed_fixed/django/contrib/auth/base_user.py`, `/tmp/verify_fixed.py` | no |
| django__django-16631 | f77491b986b8 | 31 | 7 | requirements, pass 1 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| matplotlib__matplotlib-25479 | 6ad76b440300 | 29 | 4 | requirements, pass 1 | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
| sympy__sympy-13480 | a66c51369635 | 30 | 2 | requirements | no | no | 0 | assistant `reasoning_content` | (c) only in reasoning text | no |
