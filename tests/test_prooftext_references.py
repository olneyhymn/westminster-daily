"""Regression guard for proof-text references.

The proof texts follow the OPC edition of the Westminster Standards (migrated
2026-07; see print/audit/provenance-audit-report.md and scripts/opc-migration/).
This test freezes every unit's normalized reference lists so that future edits
to content/*/data.json can't silently alter a citation.

To intentionally change references, regenerate the baseline:
    python tests/test_prooftext_references.py --regenerate
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
BASELINE = Path(__file__).resolve().parent / "prooftext_baseline.json"

H5_RE = re.compile(r"<h5>(.*?)</h5>")


def norm_ref(ref):
    ref = ref.replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", ref).strip()


def current_references():
    """unit -> footnote -> [normalized refs], for WCF/WSC/WLC across all days."""
    out = {}
    for data_path in sorted(CONTENT.glob("*/*/data.json")):
        data = json.loads(data_path.read_text())
        for item in data.get("content_with_prooftexts", []):
            abbv = item.get("abbv")
            if abbv == "wcf":
                unit = f"WCF {item['chapter']}.{item['paragraph']}"
            elif abbv in ("wsc", "wlc"):
                unit = f"{abbv.upper()} {item['number']}"
            else:
                continue
            refs = {
                fn: [norm_ref(r) for r in H5_RE.findall(html)]
                for fn, html in item.get("prooftexts", {}).items()
            }
            if unit in out:
                assert out[unit] == refs, (
                    f"{unit} appears on multiple days with different references"
                )
            out[unit] = refs
    return out


def test_references_match_baseline():
    assert BASELINE.exists(), "baseline missing; run --regenerate"
    baseline = json.loads(BASELINE.read_text())
    current = current_references()
    assert set(current) == set(baseline), (
        f"unit set changed: +{sorted(set(current) - set(baseline))[:5]} "
        f"-{sorted(set(baseline) - set(current))[:5]}"
    )
    diffs = [u for u in baseline if baseline[u] != current[u]]
    assert not diffs, f"references changed in {len(diffs)} units, e.g. {diffs[:10]}"


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        BASELINE.write_text(json.dumps(current_references(), indent=1, sort_keys=True))
        print(f"baseline written: {BASELINE}")
    else:
        print(__doc__)
