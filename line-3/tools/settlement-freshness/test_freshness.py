"""Historical real-chain replay and labelled rejection mutations; no network."""
import copy
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

import freshness as f

FOLDER = Path("line-3/tools/settlement-freshness")


def inputs():
    sample = f.w.load_workspace_json(FOLDER / "live-evidence.json")
    policy = f.w.load_workspace_json(FOLDER / "observed-policy.json")
    time_args = f.w.load_workspace_json(FOLDER / "trial.json")["timeArguments"]
    return sample, policy, time_args


class FreshnessTests(unittest.TestCase):
    def evaluate(self, sample=None, policy=None, **overrides):
        original, expected, time_args = inputs()
        time_args.update(overrides)
        return f.evaluate(sample if sample is not None else original,
                          policy if policy is not None else expected, **time_args)

    def test_actual_zto_observation_at_trial_time(self):
        sample, policy, time_args = inputs()
        before = copy.deepcopy((sample, policy, time_args))
        result = f.evaluate(sample, policy, **time_args)
        self.assertTrue(result["accepted"])
        self.assertEqual(result["anchors"]["head"]["ageSeconds"], 8)
        self.assertEqual(result["anchors"]["finalized"]["ageSeconds"], 896)
        self.assertEqual(result["payment"]["transferEvidence"]["netRaw"], "166357571280020680094504")
        self.assertEqual((sample, policy, time_args), before)

    def test_old_settled_payment_is_compatible_with_fresh_head(self):
        result = self.evaluate()
        self.assertTrue(result["payment"]["finalized"])
        self.assertLess(result["payment"]["inclusion"]["number"], result["anchors"]["finalized"]["number"])
        self.assertTrue(result["accepted"])

    def test_stale_evidence_fails_despite_accepted_payment(self):
        result = self.evaluate(as_of=inputs()[2]["as_of"] + 1201)
        self.assertFalse(result["accepted"])
        self.assertTrue(result["payment"]["accepted"])
        self.assertEqual(result["alerts"], ["head_too_old", "finalized_too_old"])
        self.assertEqual(f.exit_code(result), 1)

    def test_independent_head_and_finalized_age_limits(self):
        self.assertEqual(self.evaluate(max_head_age=7)["alerts"], ["head_too_old"])
        self.assertEqual(self.evaluate(max_finalized_age=895)["alerts"], ["finalized_too_old"])
        self.assertTrue(self.evaluate(max_head_age=8, max_finalized_age=896)["accepted"])

    def test_future_skew_boundary(self):
        timestamp = self.evaluate()["anchors"]["head"]["timestampUnix"]
        self.assertTrue(self.evaluate(as_of=timestamp-30, future_skew=30)["accepted"])
        self.assertEqual(self.evaluate(as_of=timestamp-31, future_skew=30)["alerts"], ["head_in_future"])
        self.assertEqual(self.evaluate(as_of=timestamp-1, future_skew=0)["alerts"], ["head_in_future"])

    def test_saved_evidence_cannot_choose_the_clock(self):
        sample, _, _ = inputs()
        sample["asOfUnix"] = inputs()[2]["as_of"]
        with self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_older_timestamp_free_transcript_refused(self):
        sample = f.w.load_workspace_json("line-3/tools/payment-recheck/current-evidence.json")
        with self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_every_timestamp_required_and_strict(self):
        for value in (None, True, 1.5, "0x00", "0x-1", hex(f.TIME_MAX+1)):
            sample, _, _ = inputs()
            sample["reads"][1]["result"]["timestamp"] = value
            with self.subTest(value=value), self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_timestamp_change_on_same_hash_refused(self):
        sample, _, _ = inputs()
        read = next(x for x in reversed(sample["reads"]) if x["method"] == "eth_getBlockByNumber")
        read["result"]["timestamp"] = hex(int(read["result"]["timestamp"],16)+1)
        with self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_inconsistent_time_order_refused(self):
        sample, _, _ = inputs()
        head_time = sample["reads"][1]["result"]["timestamp"]
        inclusion = next(x["result"]["blockNumber"] for x in sample["reads"] if x["method"] == "eth_getTransactionReceipt")
        for read in sample["reads"]:
            if read["method"] == "eth_getBlockByNumber" and read["result"]["number"] == inclusion:
                read["result"]["timestamp"] = head_time
        with self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_different_header_at_same_height_refused(self):
        sample, _, _ = inputs()
        read = next(x for x in reversed(sample["reads"]) if x["method"] == "eth_getBlockByNumber")
        # Rejection-only mutation of a real hash, never an address or live input.
        value = read["result"]["hash"]
        read["result"]["hash"] = value[:-1] + ("1" if value[-1] != "1" else "2")
        with self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_independently_selected_policy_must_match(self):
        for key, value in (("minimum_raw", "1"), ("token", "IMD"), ("confirmations", 1)):
            sample, _, _ = inputs()
            sample["policy"][key] = value
            with self.subTest(key=key), self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_payment_failure_cannot_pass_just_because_time_passes(self):
        sample, policy, _ = inputs()
        policy["minimum_raw"] = str(int(policy["minimum_raw"])+1)
        sample["policy"] = copy.deepcopy(policy)
        result = self.evaluate(sample=sample, policy=policy)
        self.assertEqual(result["alerts"], ["payment_policy_not_met"])
        self.assertFalse(result["accepted"])

    def test_reverted_payment_fails(self):
        sample, _, _ = inputs()
        # Reverted execution stops before the final receipt/payment reads.
        sample["reads"] = sample["reads"][:8]
        sample["reads"][2]["result"]["status"] = "0x0"
        result = self.evaluate(sample=sample)
        self.assertIn("payment_policy_not_met", result["alerts"])
        self.assertFalse(result["accepted"])

    def test_missing_receipt_fails_with_no_finalized_anchor(self):
        sample, _, _ = inputs()
        sample["reads"] = sample["reads"][:3]
        sample["reads"][2]["result"] = None
        result = self.evaluate(sample=sample)
        self.assertEqual(result["alerts"], ["payment_policy_not_met", "finalized_anchor_missing"])

    def test_exact_transcript_requests_envelopes_and_consumption(self):
        for kind in ("boolean_version", "extra_read", "missing_read", "extra_flag", "false_vs_zero"):
            sample, _, _ = inputs()
            if kind == "boolean_version": sample["version"] = True
            if kind == "extra_read": sample["reads"].append(copy.deepcopy(sample["reads"][-1]))
            if kind == "missing_read": sample["reads"].pop()
            if kind == "extra_flag": sample["reads"][0]["accepted"] = True
            if kind == "false_vs_zero": sample["reads"][1]["params"][1] = 0
            with self.subTest(kind=kind), self.assertRaises(f.w.Error): self.evaluate(sample=sample)

    def test_invalid_time_limits_and_policy_before_transport(self):
        _, policy, time_args = inputs()
        for key, value in (("as_of", None), ("as_of", True), ("as_of", 0),
                           ("max_head_age", 0), ("max_head_age", 604801),
                           ("max_finalized_age", 1.5), ("future_skew", -1), ("future_skew", 3601)):
            invalid = dict(time_args, **{key:value})
            with self.subTest(key=key,value=value), self.assertRaises(f.w.Error):
                f.collect(policy, **invalid, rpc_factory=lambda source:self.fail("unexpected network"))
        policy["finalized"] = False
        with self.assertRaises(f.w.Error):
            f.collect(policy, **time_args, rpc_factory=lambda source:self.fail("unexpected network"))

    def test_live_capture_and_replay_have_same_decision(self):
        sample, policy, time_args = inputs()
        result = f.collect(policy, **time_args, rpc_factory=lambda source:f.r.ExactReplay(sample["reads"]))
        self.assertTrue(result["accepted"])
        replay = f.evaluate(result["sample"], policy, **time_args)
        for key in ("accepted", "state", "alerts", "anchors", "sampleSha256"):
            self.assertEqual(result[key], replay[key])

    def test_provider_failure_has_no_sample_or_fallback(self):
        _, policy, time_args = inputs()
        def unavailable(source): raise OSError("test transport unavailable")
        result = f.collect(policy, **time_args, rpc_factory=unavailable)
        self.assertEqual(f.exit_code(result), 2)
        self.assertEqual(result["state"], "provider_error")
        self.assertNotIn("sample", result)

    def test_transport_does_not_discover_environment(self):
        with patch.object(f.s.urllib.request, "getproxies", side_effect=AssertionError("environment read")):
            f.s.RPC(f.s.RPC_URL)

    def test_demo_and_cli_require_explicit_time_and_expected_policy(self):
        out = io.StringIO()
        with redirect_stdout(out): self.assertEqual(f.main(["--demo"]), 0)
        self.assertTrue(json.loads(out.getvalue())["accepted"])
        for args in (["--demo", "--as-of", "1"], ["--live"],
                     ["--replay", str(FOLDER/"live-evidence.json"), "--policy", str(FOLDER/"observed-policy.json")],
                     ["--replay", str(FOLDER/"live-evidence.json"), "--rpc", f.s.RPC_URL],
                     ["--live", "--policy", "../outside.json"]):
            with self.subTest(args=args), redirect_stdout(io.StringIO()):
                self.assertEqual(f.main(args), 2)


if __name__ == "__main__": unittest.main()
