from __future__ import annotations
import json, hashlib, sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from soficca_core.engine import evaluate  # noqa: E402

def _hash_report(r: Dict[str, Any]) -> str:
    s = json.dumps(r, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _contains_any_substring(haystack: List[str], subs: List[str]) -> bool:
    joined = "\n".join(haystack or [])
    for s in subs or []:
        if s.lower() in joined.lower():
            return True
    return False

def _assert_case(output: Dict[str, Any], exp: Dict[str, Any]) -> Tuple[bool, List[str]]:
    problems: List[str] = []

    if exp.get("must_have_versions"):
        v = output.get("versions") or {}
        for k in ("engine", "ruleset", "safety_policy"):
            if not isinstance(v.get(k), str) or not v.get(k):
                problems.append(f"missing versions.{k}")

    if exp.get("must_have_nonempty_rules_evaluated"):
        lst = (output.get("trace") or {}).get("rules_evaluated")
        if not isinstance(lst, list) or len(lst) == 0:
            problems.append("trace.rules_evaluated must be non-empty")

    if exp.get("must_have_nonempty_policy_evaluated"):
        lst = ((output.get("trace") or {}).get("policy_trace") or {}).get("evaluated")
        if not isinstance(lst, list) or len(lst) == 0:
            problems.append("trace.policy_trace.evaluated must be non-empty")

    if "safety" in exp:
        for k, v in (exp["safety"] or {}).items():
            if (output.get("safety") or {}).get(k) != v:
                problems.append(f"safety.{k} expected {v!r} got {(output.get('safety') or {}).get(k)!r}")

    if "decision" in exp:
        for k, v in (exp["decision"] or {}).items():
            if (output.get("decision") or {}).get(k) != v:
                problems.append(f"decision.{k} expected {v!r} got {(output.get('decision') or {}).get(k)!r}")

    if "must_contain_flags" in exp:
        flags = set((output.get("decision") or {}).get("flags") or [])
        for f in exp["must_contain_flags"]:
            if f not in flags:
                problems.append(f"missing decision.flag: {f}")

    if "must_contain_rules_triggered" in exp:
        rt = set((output.get("trace") or {}).get("rules_triggered") or [])
        for rid in exp["must_contain_rules_triggered"]:
            if rid not in rt:
                problems.append(f"missing rules_triggered: {rid}")

    if "must_require_fields" in exp:
        rf = (output.get("decision") or {}).get("required_fields") or []
        for field in exp["must_require_fields"]:
            if field not in rf:
                problems.append(f"required_fields missing: {field}")

    if "must_contain_uncertainty_substrings" in exp:
        notes = (output.get("trace") or {}).get("uncertainty_notes") or []
        joined = " ".join([str(x) for x in notes]).lower()
        for sub in exp["must_contain_uncertainty_substrings"]:
            if sub.lower() not in joined:
                problems.append(f"uncertainty_notes missing substring: {sub}")

    if "must_not_contain_recommendations_substrings" in exp:
        recs = (output.get("decision") or {}).get("recommendations") or []
        if _contains_any_substring(recs, exp["must_not_contain_recommendations_substrings"]):
            problems.append("recommendations contained forbidden substrings")

    return (len(problems) == 0), problems

def main() -> None:
    cases_path = ROOT / "golden_cases.json"
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    cases = data.get("cases") or []

    results = []
    passed = 0

    for c in cases:
        cid = c.get("id")
        inp = c.get("input") or {}
        exp = c.get("expected") or {}

        out = evaluate(inp)

        if exp.get("determinism_check"):
            out2 = evaluate(inp)
            ok = (_hash_report(out) == _hash_report(out2))
            problems = [] if ok else ["hash mismatch on repeated evaluation"]
        else:
            ok, problems = _assert_case(out, exp)

        results.append({"id": cid, "ok": ok, "problems": problems})
        if ok:
            passed += 1
        else:
            print(f"FAIL {cid}:")
            for p in problems:
                print(f"  - {p}")

    total = len(cases)
    print(f"\nGolden cases: {passed}/{total} PASS")

    (ROOT / "evaluation_report.json").write_text(
        json.dumps({"passed": passed, "total": total, "results": results}, indent=2),
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
