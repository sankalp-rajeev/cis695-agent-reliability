"""The v1.4 decision rule with only its version changed."""

from dataclasses import dataclass

from reliability.verifier.policy_v1_4 import FullPolicyV14


@dataclass(frozen=True, slots=True)
class FullPolicyV141(FullPolicyV14):
    version: str = 'v1.4.1-full'
