#!/usr/bin/env python3
"""Explain EIP-712 encoding offline, down to every field word and hash input."""
import argparse
import json
import sys

from typed_digest import (ARRAY, INTEGER, Encoder, TypedDataError, digest,
                          keccak256, load_workspace_json, parse_hex, parse_integer)

MAX_TRACE_BYTES = 1_048_576


def hex_bytes(value):
    return "0x" + value.hex()


def pointer(parent, part):
    return parent + "/" + str(part).replace("~", "~0").replace("/", "~1")


class Trace:
    """Used only after the bounded public digest function validates the request."""
    def __init__(self, encoder):
        self.encoder = encoder
        self.nodes = []
        self.bytes_used = 0

    def record(self, node, word):
        node["word"] = hex_bytes(word)
        self.bytes_used += len(json.dumps(node, ensure_ascii=True, indent=2).encode("utf-8"))
        if self.bytes_used > MAX_TRACE_BYTES:
            raise TypedDataError("encoding trace exceeds 1048576-byte output limit")
        self.nodes.append(node)
        return word

    def value(self, kind, value, path):
        node = {"path": path, "type": kind}
        array = ARRAY.fullmatch(kind)
        if array:
            inner, _ = array.groups()
            children = [pointer(path, index) for index in range(len(value))]
            words = [self.value(inner, item, child)
                     for item, child in zip(value, children)]
            preimage = b"".join(words)
            node.update(kind="array", elements=[
                {"path": child, "offsetBytes": index * 32, "word": hex_bytes(word)}
                for index, (child, word) in enumerate(zip(children, words))])
        elif kind in self.encoder.types:
            encoding = self.encoder.type_encoding(kind)
            type_hash = keccak256(encoding.encode("utf-8"))
            fields = []
            words = [type_hash]
            for index, field in enumerate(self.encoder.types[kind]):
                child = pointer(path, field["name"])
                word = self.value(field["type"], value[field["name"]], child)
                words.append(word)
                fields.append({"name": field["name"], "type": field["type"],
                               "path": child, "offsetBytes": (index + 1) * 32,
                               "word": hex_bytes(word)})
            preimage = b"".join(words)
            node.update(kind="struct", typeEncoding=encoding,
                        typeHash=hex_bytes(type_hash), fields=fields)
        elif kind in ("string", "bytes"):
            preimage = value.encode("utf-8") if kind == "string" else parse_hex(value)
            node.update(kind="dynamic", inputBytes=len(preimage))
        else:
            # Reuse the already checked atomic encoding (including sign extension
            # and opposite padding directions for addresses and fixed bytes).
            word = self.encoder.value_word(kind, value)
            normalized = (str(parse_integer(value)) if INTEGER.fullmatch(kind)
                          else value.lower() if kind == "address" or kind.startswith("bytes")
                          else value)
            node.update(kind="atomic", normalizedValue=normalized)
            return self.record(node, word)
        node["preimage"] = hex_bytes(preimage)
        node["preimageBytes"] = len(preimage)
        return self.record(node, keccak256(preimage))


def explain(data, expected=None):
    """Validate before tracing; cross-check the traced result with the ancestor."""
    baseline = digest(data)
    expected_bytes = parse_hex(expected, 32) if expected is not None else None
    tracer = Trace(Encoder(data["types"]))
    domain = tracer.value("EIP712Domain", data["domain"], "/domain")
    message = tracer.value(data["primaryType"], data["message"], "/message")
    preimage = b"\x19\x01" + domain + message
    result = keccak256(preimage)
    if (hex_bytes(domain) != baseline["domainSeparator"] or
            hex_bytes(message) != baseline["messageHash"] or
            hex_bytes(result) != baseline["digest"]):
        raise TypedDataError("trace disagrees with the validated digest")
    report = {"traceVersion": 1, **baseline,
              "nodeOrder": "children before parents",
              "nodes": tracer.nodes,
              "envelope": {"prefix": "0x1901", "domainOffsetBytes": 2,
                           "messageOffsetBytes": 34, "preimage": hex_bytes(preimage),
                           "preimageBytes": 66, "digest": hex_bytes(result)}}
    if expected_bytes is not None:
        report["matchesExpected"] = expected_bytes == result
    if len(json.dumps(report, ensure_ascii=True, indent=2).encode("utf-8")) > MAX_TRACE_BYTES:
        raise TypedDataError("encoding trace exceeds 1048576-byte output limit")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="typed-data JSON beneath cwd; max 65536 bytes, no symlinks")
    parser.add_argument("--expect", help="exact 32-byte digest from an independent source")
    parser.add_argument("--summary", action="store_true", help="print hashes and node count only")
    args = parser.parse_args(argv)
    try:
        report = explain(load_workspace_json(args.input), args.expect)
        if args.summary:
            summary = {key: report[key] for key in
                       ("primaryType", "domainSeparator", "messageHash", "digest")}
            summary["traceNodes"] = len(report["nodes"])
            if "matchesExpected" in report:
                summary["matchesExpected"] = report["matchesExpected"]
            report = summary
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0 if report.get("matchesExpected", True) else 1
    except (ValueError, OSError, RecursionError) as exc:
        print(f"typed-trace: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
