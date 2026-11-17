#!/usr/bin/env python3
"""Export the nine prepared additions for the frozen E2E v1.4.1 validator.

Copies only the pinned wheel and nine exact four-column projections into the
frozen checkout's ignored task_prep_inputs folder. Existing outputs are refused.
"""

from reliability.task_prep.frozen_export import export

if __name__ == "__main__":
    export()
