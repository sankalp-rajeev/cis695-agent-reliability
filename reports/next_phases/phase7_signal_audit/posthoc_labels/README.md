Post-hoc, never used for any decision.

All input label and claim access occurred after the pushed signal-audit-labelfree tag. Original oracle labels were checked against the audited CSV original column; all normalized oracle/verifier/candidate digests match frozen candidates. The original records are mounted read-only at /original; host prefix is /home/sankalp/projects/cis695-agent-reliability. All 83 claims are RESOLVED. Precision and coverage use Wilson 95% intervals with z=1.959963984540054. No inference is made from an absent grader-gap entry. Label changes cannot change acceptance coverage because decisions were already frozen.

{
  "tasks": 83,
  "original_false_accepts": [
    "django__django-13212",
    "django__django-13297",
    "django__django-16667",
    "matplotlib__matplotlib-23299",
    "matplotlib__matplotlib-23476",
    "pylint-dev__pylint-4661",
    "pylint-dev__pylint-7277"
  ],
  "original_false_accepts_surviving": {
    "audited_default": [
      "django__django-13212",
      "django__django-16667",
      "matplotlib__matplotlib-23299",
      "matplotlib__matplotlib-23476",
      "pylint-dev__pylint-4661",
      "pylint-dev__pylint-7277"
    ],
    "CPU_2048": [
      "django__django-13212",
      "django__django-16667",
      "matplotlib__matplotlib-23299",
      "matplotlib__matplotlib-23476",
      "pylint-dev__pylint-4661"
    ]
  },
  "label_counts": {
    "original": {
      "incorrect": 14,
      "correct": 69
    },
    "audited_default": {
      "correct": 70,
      "incorrect": 13
    },
    "CPU_2048": {
      "correct": 72,
      "incorrect": 11
    }
  },
  "changed_labels": {
    "audited_default": 3,
    "CPU_2048": 5
  },
  "claim_statuses": {
    "RESOLVED": 83
  }
}
