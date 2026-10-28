"""Post-hoc policy-assessment arithmetic. Never supplies evidence to a verifier."""
from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from statistics import NormalDist

import numpy as np

BOOTSTRAP_SEED = 695
BOOTSTRAP_RESAMPLES = 10_000
DIFFERENCE_METRICS = ("precision", "recall", "f1", "accuracy", "coverage")


def ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def wilson(successes, trials, confidence=.95):
    if not 0 <= successes <= trials or trials < 0 or not 0 < confidence < 1:
        raise ValueError("invalid binomial counts or confidence")
    if trials == 0:
        return None, None
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    p = successes / trials
    scale = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / scale
    radius = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / scale
    return max(0., center - radius), min(1., center + radius)


@dataclass(frozen=True)
class Confusion:
    """Field order is TP, FP, FN, TN (acceptance is the predicted positive)."""
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def n(self):
        return self.tp + self.fp + self.fn + self.tn

    def metrics(self):
        p = ratio(self.tp, self.tp + self.fp)
        r = ratio(self.tp, self.tp + self.fn)
        specificity = ratio(self.tn, self.tn + self.fp)
        result = dict(n=self.n, accepted_right=self.tp, accepted_wrong=self.fp,
            precision=p, recall=r, f1=ratio(2 * self.tp, 2 * self.tp + self.fp + self.fn),
            accuracy=ratio(self.tp + self.tn, self.n), specificity=specificity,
            negative_predictive_value=ratio(self.tn, self.tn + self.fn),
            balanced_accuracy=(r + specificity) / 2 if r is not None and specificity is not None else None,
            false_acceptance_proportion=ratio(self.fp, self.tp + self.fp),
            coverage=ratio(self.tp + self.fp, self.n), wrong_patch_withholding_rate=specificity,
            correct_patch_acceptance_rate=r, false_positive_rate=ratio(self.fp, self.fp + self.tn),
            unsafe_detection_precision=ratio(self.tn, self.tn + self.fn),
            unsafe_detection_recall=specificity,
            unsafe_detection_f1=ratio(2 * self.tn, 2 * self.tn + self.fp + self.fn))
        for name, a, n in (("precision", self.tp, self.tp + self.fp), ("recall", self.tp, self.tp + self.fn),
                           ("false_acceptance_proportion", self.fp, self.tp + self.fp),
                           ("wrong_patch_withholding_rate", self.tn, self.tn + self.fp),
                           ("coverage", self.tp + self.fp, self.n)):
            result[name + "_wilson_low"], result[name + "_wilson_high"] = wilson(a, n)
        return result


def confusion(rows, policy):
    tp = fp = fn = tn = 0
    for row in rows:
        positive = row["oracle"] == "resolved"
        accepted = row[policy + "_decision"] == "ACCEPT"
        tp += accepted and positive
        fp += accepted and not positive
        fn += not accepted and positive
        tn += not accepted and not positive
    return Confusion(tp, fp, fn, tn)


def populations(rows):
    headline = [r for r in rows if r["stratum"] == "headline"]
    requests = [r for r in rows if r["stratum"] == "requests"]
    nonempty = lambda values: [r for r in values if r["oracle"] != "empty_patch"]
    return dict(HEADLINE_NONEMPTY_PRIMARY=nonempty(headline), REQUESTS_NONEMPTY=nonempty(requests),
        ALL_NONEMPTY=nonempty(rows), HEADLINE_INCLUDING_EMPTY_SENSITIVITY=headline,
        REQUESTS_ALL_SENSITIVITY=requests, ALL_100_INCLUDING_EMPTY_SENSITIVITY=list(rows),
        HEADLINE_EMPTY_STRUCTURAL=[r for r in headline if r["oracle"] == "empty_patch"],
        ALL_EMPTY_STRUCTURAL=[r for r in rows if r["oracle"] == "empty_patch"])


def transitions(rows):
    result = {}
    for row in rows:
        key = (row["baseline_decision"], row["full_decision"], row["oracle"])
        result[key] = result.get(key, 0) + 1
    return result


def exact_mcnemar(baseline_only_correct, full_only_correct):
    """Two-sided conditional binomial McNemar, conditional on discordant pairs."""
    n = baseline_only_correct + full_only_correct
    k = min(baseline_only_correct, full_only_correct)
    if n == 0:
        return 1.
    return min(1., 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def enrichment_exact(total, total_wrong, stopped, stopped_wrong):
    """One-sided hypergeometric P(X >= observed); overlapping base rate is conditioned on."""
    if not (0 <= total_wrong <= total and 0 <= stopped <= total and
            0 <= stopped_wrong <= min(total_wrong, stopped) and stopped - stopped_wrong <= total - total_wrong):
        raise ValueError("inconsistent finite-population counts")
    denominator = math.comb(total, stopped)
    lower = max(stopped_wrong, stopped - (total - total_wrong))
    return sum(math.comb(total_wrong, k) * math.comb(total - total_wrong, stopped - k)
               for k in range(lower, min(total_wrong, stopped) + 1)) / denominator


def paired_exact(rows):
    stopped = [r for r in rows if r["baseline_decision"] == "ACCEPT" and r["full_decision"] != "ACCEPT"]
    added = [r for r in rows if r["baseline_decision"] != "ACCEPT" and r["full_decision"] == "ACCEPT"]
    base = [r for r in rows if r["baseline_decision"] == "ACCEPT"]
    wrong = lambda values: sum(r["oracle"] != "resolved" for r in values)
    b = c = 0
    accept_pairs = {"both_accept": 0, "baseline_only_accept": 0, "full_only_accept": 0, "neither_accept": 0}
    correctness_pairs = {"both_correct": 0, "baseline_only_correct": 0, "full_only_correct": 0, "neither_correct": 0}
    for row in rows:
        ba, fa = row["baseline_decision"] == "ACCEPT", row["full_decision"] == "ACCEPT"
        truth = row["oracle"] == "resolved"
        accept_key = "both_accept" if ba and fa else "baseline_only_accept" if ba else "full_only_accept" if fa else "neither_accept"
        accept_pairs[accept_key] += 1
        bc, fc = ba == truth, fa == truth
        correct_key = "both_correct" if bc and fc else "baseline_only_correct" if bc else "full_only_correct" if fc else "neither_correct"
        correctness_pairs[correct_key] += 1
        b += bc and not fc
        c += fc and not bc
    return dict(stopped_count=len(stopped), stopped_wrong=wrong(stopped), stopped_right=len(stopped) - wrong(stopped),
        added_accept_count=len(added), baseline_accepted_count=len(base), baseline_accepted_wrong=wrong(base),
        stopped_wrong_share=ratio(wrong(stopped), len(stopped)), baseline_accepted_wrong_share=ratio(wrong(base), len(base)),
        stopped_wrong_share_wilson=wilson(wrong(stopped), len(stopped)),
        enrichment_exact_one_sided_p=enrichment_exact(len(base), wrong(base), len(stopped), wrong(stopped)),
        accept_disagreement_table=accept_pairs, correctness_disagreement_table=correctness_pairs,
        correctness_mcnemar_exact_two_sided_p=exact_mcnemar(b, c),
        stopped_ids=[r["instance_id"] for r in stopped])


def _array_metrics(truth, accepted):
    tp = np.sum(accepted & truth, axis=1)
    fp = np.sum(accepted & ~truth, axis=1)
    fn = np.sum(~accepted & truth, axis=1)
    tn = np.sum(~accepted & ~truth, axis=1)
    def divide(a, b):
        result = np.full(a.shape, np.nan, dtype=float)
        return np.divide(a, b, out=result, where=b != 0)
    return dict(precision=divide(tp, tp + fp), recall=divide(tp, tp + fn),
                f1=divide(2 * tp, 2 * tp + fp + fn), accuracy=(tp + tn) / truth.shape[1],
                coverage=(tp + fp) / truth.shape[1])


def _interval(values):
    available = values[np.isfinite(values)]
    low, high = np.quantile(available, [.025, .975], method="linear") if len(available) else (None, None)
    return dict(low=float(low) if low is not None else None, high=float(high) if high is not None else None,
                valid_resamples=len(available), undefined_resamples=len(values) - len(available))


def paired_bootstrap(rows, seed=BOOTSTRAP_SEED, resamples=BOOTSTRAP_RESAMPLES):
    if not rows or resamples < 1:
        raise ValueError("bootstrap needs patches and resamples")
    n = len(rows)
    rng = np.random.Generator(np.random.PCG64(seed))
    indices = rng.integers(0, n, size=(resamples, n), dtype=np.int64)
    truth = np.array([r["oracle"] == "resolved" for r in rows])[indices]
    draws = {}
    for policy in ("baseline", "full"):
        predicted = np.array([r[policy + "_decision"] == "ACCEPT" for r in rows])[indices]
        draws[policy] = _array_metrics(truth, predicted)
    differences = {m: draws["full"][m] - draws["baseline"][m] for m in DIFFERENCE_METRICS}
    points = {p: confusion(rows, p).metrics() for p in ("baseline", "full")}
    result = dict(seed=seed, resamples=resamples, n=n, generator="numpy.PCG64", numpy_version=np.__version__,
        unit="patch; same sampled row indices for truth and both policies", method="percentile 95%, linear quantiles",
        resample_indices_sha256=hashlib.sha256(indices.astype('<i8').tobytes()).hexdigest(),
        differences={m: dict(point=points["full"][m] - points["baseline"][m]
                             if points["full"][m] is not None and points["baseline"][m] is not None else None,
                             **_interval(differences[m])) for m in DIFFERENCE_METRICS},
        policy_f1={p: dict(point=points[p]["f1"], **_interval(draws[p]["f1"])) for p in ("baseline", "full")})
    replicates = [dict(resample=i + 1,
        **{m + "_full_minus_baseline": float(differences[m][i]) if np.isfinite(differences[m][i]) else None for m in DIFFERENCE_METRICS},
        baseline_f1=float(draws['baseline']['f1'][i]) if np.isfinite(draws['baseline']['f1'][i]) else None,
        full_f1=float(draws['full']['f1'][i]) if np.isfinite(draws['full']['f1'][i]) else None) for i in range(resamples)]
    return result, replicates
