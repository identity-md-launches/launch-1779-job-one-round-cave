#!/usr/bin/env python3
"""Check finalized ZTO/IMD payment evidence against an explicit time budget."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    "freshness_recheck", Path(__file__).resolve().parent.parent / "payment-recheck" / "recheck.py")
r = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(r)
w, s, a = r.w, r.s, r.a
TIME_MAX = 253402300799
LIMIT = ("Provider-supplied block timestamps checked against caller-supplied time; "
         "neither is authenticated. This is not a consensus/receipt proof or a guarantee "
         "of current canonicality. Offline acceptance is only as of the supplied time.")


def integer(value, name, minimum=0, maximum=TIME_MAX):
    if type(value) is not int or not minimum <= value <= maximum:
        raise w.Error("invalid " + name)
    return value


def validate(expected_policy, as_of, max_head_age, max_finalized_age, future_skew):
    policy = a.validate_policy(expected_policy)
    if policy["finalized"] is not True:
        raise w.Error("freshness checks require a finalized payment policy")
    bounds = {"asOfUnix": integer(as_of, "as-of time", 1),
              "maxHeadAgeSeconds": integer(max_head_age, "head age", 1, 604800),
              "maxFinalizedAgeSeconds": integer(max_finalized_age, "finalized age", 1, 604800),
              "futureSkewSeconds": integer(future_skew, "future skew", 0, 3600)}
    return policy, bounds


class TimestampRecorder(w.Recorder):
    """Keep timestamps on every block read; older witness samples omit them."""
    def call(self, method, params):
        result = self.rpc.call(method, params)
        saved = ({k: result.get(k) for k in ("number", "hash", "timestamp")}
                 if method == "eth_getBlockByNumber" and isinstance(result, dict) else result)
        self.reads.append({"method": method, "params": params, "result": saved})
        return result


def headers(sample):
    """Bind each timestamp to an observed block identity and check rereads."""
    by_height = {}
    by_hash = {}
    for read in sample["reads"]:
        if read["method"] != "eth_getBlockByNumber":
            continue
        header = read["result"]
        if not isinstance(header, dict):
            raise w.Error("timestamp-bearing block unavailable")
        number = s.quantity(header.get("number"))
        block_hash = s.hash32(header.get("hash"))
        timestamp = integer(s.quantity(header.get("timestamp")), "block timestamp")
        item = {"number": number, "hash": block_hash, "timestampUnix": timestamp}
        if number in by_height and by_height[number] != item:
            raise w.Error("same-height header changed during observation")
        if block_hash in by_hash and by_hash[block_hash] != item:
            raise w.Error("block hash reused for different header")
        by_height[number] = by_hash[block_hash] = item
    ordered = [by_height[key] for key in sorted(by_height)]
    if any(left["timestampUnix"] >= right["timestampUnix"]
           for left, right in zip(ordered, ordered[1:])):
        raise w.Error("block timestamps do not increase with block height")
    return by_height


def evaluate(sample, expected_policy, as_of, max_head_age, max_finalized_age, future_skew=0):
    policy, bounds = validate(expected_policy, as_of, max_head_age, max_finalized_age, future_skew)
    # Compare the independently chosen policy before any evidence evaluation.
    if not isinstance(sample, dict) or a.validate_policy(sample.get("policy")) != policy:
        raise w.Error("evidence policy differs from expected payment policy")
    _, payment = r.replay(sample)
    blocks = headers(sample)
    alerts = []
    if payment.get("accepted") is not True:
        alerts.append("payment_policy_not_met")
    anchors = {}
    for name, key, budget in (("head", "head", max_head_age),
                              ("finalized", "finalizedHead", max_finalized_age)):
        anchor = payment.get(key)
        if anchor is None:
            alerts.append(name + "_anchor_missing")
            continue
        header = blocks.get(anchor["number"])
        if header is None or header["hash"] != anchor["hash"]:
            raise w.Error("timestamp does not bind to payment anchor")
        age = as_of - header["timestampUnix"]
        anchors[name] = dict(header, ageSeconds=age, maxAgeSeconds=budget)
        if age > budget:
            alerts.append(name + "_too_old")
        if age < -future_skew:
            alerts.append(name + "_in_future")
    return {"accepted": not alerts, "state": "within_time_budget" if not alerts else "review_required",
            "alerts": alerts, "policy": policy, "timePolicy": bounds, "anchors": anchors,
            "payment": r.summary(payment), "sampleSha256": r.digest(sample),
            "evidenceMode": "offline historical evaluation at explicit time", "evidenceLimit": LIMIT}


def collect(expected_policy, as_of, max_head_age, max_finalized_age, future_skew=0,
            source=s.RPC_URL, rpc_factory=s.RPC):
    policy, _ = validate(expected_policy, as_of, max_head_age, max_finalized_age, future_skew)
    if source not in a.PROVIDERS:
        raise w.Error("choose a documented public Ethereum source")
    try:
        recorder = TimestampRecorder(rpc_factory(source))
        w.verify(recorder, **policy)
        sample = {"version": 1, "policy": policy, "reads": recorder.reads}
        result = evaluate(sample, policy, as_of, max_head_age, max_finalized_age, future_skew)
    except (w.Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        return {"accepted": False, "state": "provider_error",
                "reason": "Could not obtain complete consistent timestamp-bearing payment evidence",
                "source": source, "evidenceLimit": LIMIT}
    result.update(sample=sample, source=source, evidenceMode="live read-only observation at explicit time")
    return result


def exit_code(result):
    return 0 if result["accepted"] else 2 if result["state"] in ("input_error", "provider_error") else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="replay actual ZTO observation at its recorded trial time")
    mode.add_argument("--replay", help="workspace-relative timestamp-bearing witness sample")
    mode.add_argument("--live", action="store_true")
    parser.add_argument("--policy", help="workspace-relative independently chosen payment policy")
    parser.add_argument("--as-of", type=int, help="explicit Unix seconds; no implicit or saved clock")
    parser.add_argument("--max-head-age", type=int)
    parser.add_argument("--max-finalized-age", type=int)
    parser.add_argument("--future-skew", type=int, default=None)
    parser.add_argument("--rpc", choices=a.PROVIDERS)
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if any(x is not None for x in (args.policy, args.as_of, args.max_head_age,
                                           args.max_finalized_age, args.future_skew, args.rpc)):
                raise w.Error("demo refuses overrides")
            folder = Path(__file__).resolve().parent.relative_to(Path.cwd())
            trial = w.load_workspace_json(folder / "trial.json")
            policy = w.load_workspace_json(folder / "observed-policy.json")
            sample = w.load_workspace_json(folder / "live-evidence.json")
            result = evaluate(sample, policy, **trial["timeArguments"])
            result["demoNote"] = "Historical ZTO trial, not today's freshness or an independently issued invoice."
        else:
            if args.policy is None or (args.rpc is not None and not args.live):
                raise w.Error("supply expected policy; RPC applies only to live mode")
            policy = w.load_workspace_json(args.policy)
            inputs = (policy, args.as_of, args.max_head_age, args.max_finalized_age,
                      args.future_skew if args.future_skew is not None else 0)
            validate(*inputs)
            if args.live:
                result = collect(*inputs, source=args.rpc or s.RPC_URL)
            else:
                result = evaluate(w.load_workspace_json(args.replay), *inputs)
        print(json.dumps(result, indent=2, allow_nan=False))
        return exit_code(result)
    except (w.Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        print(json.dumps({"accepted": False, "state": "input_error",
                          "reason": "Invalid time/policy input or inconsistent timestamp-bearing evidence"}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
