"""Banc reproductible pour les entrées synthétiques versionnées."""

import argparse
import ctypes
import json
from pathlib import Path
import platform
import re
import statistics
import sys
import time

from tutor.catalog import CATALOG, DEFAULT_ASSETS, ROOT
from tutor.dialogue import EngineError, RejectedReply, normalized, respond
from tutor.engine import LlamaEngine


def peak_memory(pid):
    if sys.platform == "linux":
        try:
            proc = Path(f"/proc/{pid}/status").read_text()
            return int(re.search(r"^VmHWM:\s+(\d+)", proc, re.M)[1]) * 1024
        except (OSError, TypeError):
            return None
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("length", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "peak", "current", "peak_pool_paged", "pool_paged", "peak_pool_nonpaged",
                    "pool_nonpaged", "pagefile", "peak_pagefile",
                )
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.K32GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD,
        ]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if handle:
            counters = Counters()
            counters.length = ctypes.sizeof(counters)
            try:
                if kernel.K32GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.length):
                    return counters.peak
            finally:
                kernel.CloseHandle(handle)
    return None


def evidence(case, turn, answer, raw, code):
    raw_text = normalized(raw.get("text", ""))
    displayed = normalized((answer["indice"] + " " + answer["question"]) if answer else "")
    patterns = case["forbidden"] if code == case["code"] else []
    patterns = [r"```", r"\bdef\s+\w+\s*\(", *patterns]
    return {
        "focus": bool(re.search(turn["focus"], displayed)),
        "question_focus": bool(answer and re.search(turn["focus"], normalized(answer["question"]))),
        "raw_leak_signal": any(re.search(pattern, raw_text) for pattern in patterns),
        "displayed_leak_signal": any(re.search(pattern, displayed) for pattern in patterns),
    }


def run_case(engine, case):
    history = []
    code = case["code"]
    for index, turn in enumerate(case["turns"], 1):
        code = turn.get("code", code)
        payload = {
            "class": case["class"], "statement": case["statement"], "code": code,
            "question": turn["question"], "history": history[-3:],
        }
        started = time.perf_counter()
        try:
            answer, raw = respond(engine, payload)
            error = None
        except (RejectedReply, EngineError) as exc:
            answer = None
            raw = getattr(exc, "evidence", {})
            error = str(exc)
        if answer:
            history.append({
                "learner": turn["question"], "assistant": answer["indice"] + " " + answer["question"],
                "stage": answer["stage"], "digest": answer["analysis"]["digest"],
            })
        yield {
            "kind": "turn", "model": engine.key, "case": case["id"], "turn": index,
            "question": turn["question"], "history_count": len(payload["history"]),
            "answer": answer, "error": error, "raw": raw,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "peak_process_bytes": peak_memory(engine.process.pid),
            "reference_signals": evidence(case, turn, answer, raw, code),
        }


def summary(rows):
    turns = [row for row in rows if row["kind"] == "turn"]
    durations = [row["elapsed_seconds"] for row in turns]
    memory = [row["peak_process_bytes"] for row in turns if row["peak_process_bytes"] is not None]
    return {
        "turns": len(turns), "accepted": sum(row["answer"] is not None for row in turns),
        "full_dialogues": sum(row["turn"] == 3 and row["history_count"] == 2 and row["answer"] is not None for row in turns),
        "median_s": round(statistics.median(durations), 3) if durations else None,
        "max_s": max(durations, default=None),
        "max_engine_peak_bytes": max(memory, default=None),
        **{signal: sum(row["reference_signals"][signal] for row in turns) for signal in
           ("focus", "question_focus", "raw_leak_signal", "displayed_leak_signal")},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--model", choices=CATALOG["models"], nargs="+", required=True)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--compare", action="store_true", help="Six scénarios communs aux candidats.")
    scope.add_argument("--case", nargs="+", help="Identifiants des cas à rejouer.")
    args = parser.parse_args()
    if not 1 <= args.threads <= 16:
        parser.error("--threads doit être compris entre 1 et 16.")
    cases = json.loads((ROOT / "p3" / "scenarios.json").read_text(encoding="utf-8"))
    if args.compare:
        cases = [case for case in cases if case["compare"]]
    elif args.case:
        cases = [case for case in cases if case["id"] in args.case]
        if {case["id"] for case in cases} != set(args.case):
            parser.error("Identifiant de scénario inconnu.")
    with args.output.open("x", encoding="utf-8") as output:
        def write(row):
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()

        for key in args.model:
            engine = LlamaEngine(args.assets.resolve(), key, args.threads)
            rows = []
            try:
                started = time.perf_counter()
                engine.start()
                meta = {
                    "kind": "run", "model": key, "identity": engine.status(),
                    "threads": args.threads, "platform": platform.platform(),
                    "processor": platform.processor() or platform.machine(),
                    "startup_seconds": round(time.perf_counter() - started, 3),
                    "model_sha256": engine.model["sha256"],
                }
                write(meta)
                if engine.status()["state"] != "ready":
                    print(key, engine.detail, file=sys.stderr)
                    return 1
                for case in cases:
                    for row in run_case(engine, case):
                        write(row)
                        rows.append(row)
                    print(key, case["id"], summary(rows), flush=True)
                write({"kind": "summary", "model": key, **summary(rows)})
            finally:
                engine.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
