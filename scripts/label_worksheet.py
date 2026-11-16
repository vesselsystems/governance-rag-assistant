"""Write evaluation/label_review.md: a worksheet for checking challenge-set labels by hand.

It shows each question beside the exact text of the chunk(s) it is labelled with. It
deliberately shows no retrieval results, so the reviewer judges the label, not the system.

    python scripts/label_worksheet.py
"""

from __future__ import annotations

import json
from pathlib import Path

from governance_rag.retrieval import TfidfRetriever

ROOT = Path(__file__).resolve().parents[1]
CHALLENGE = ROOT / "evaluation" / "challenge_questions.json"
WORKSHEET = ROOT / "evaluation" / "label_review.md"

INSTRUCTIONS = """# Challenge-set label review

The 32 questions in `evaluation/challenge_questions.json` and their expected chunks were
drafted with AI assistance. Until a person checks them, every result computed from them is
provisional. This review is the human evaluation step for the retrieval benchmark, and it is
yours to do: do not delegate it back to an AI.

**Time:** about 30-45 minutes. **Do not open `reports/retriever_comparison.md` until you
finish;** knowing what the system retrieved biases the judgment.

For each item below:

1. Read the question, then the quoted chunk text.
2. Answerable item: does the chunk directly answer the question? Does any *other* chunk also
   answer it? The full documents are in `data/documents/`.
   - Label right: set `"label_status": "human_verified"` for that item in the JSON.
   - Label wrong or incomplete: fix `expected_citations`, set
     `"label_status": "human_corrected"`, and add `"label_note"` saying what changed and why.
3. Unanswerable item: confirm that no document answers it. If one does, make it answerable:
   add the citation(s), set `"answerable": true`, and mark it `human_corrected` with a note.
4. If a question is itself ambiguous, say so in `label_note`; rewording is fine but record it.

When finished:

```bash
python scripts/label_worksheet.py      # refresh this file
python scripts/compare_retrievers.py   # recompute results with your labels
pytest
```

The comparison report then shows how many labels are human-verified and adds a
"human-verified only" result.

---
"""


def main() -> int:
    challenge = json.loads(CHALLENGE.read_text(encoding="utf-8"))["questions"]
    chunks = {
        chunk.citation: chunk.text
        for chunk in TfidfRetriever.from_directory(ROOT / "data" / "documents").chunks
    }
    lines = [INSTRUCTIONS]
    for item in challenge:
        status = item["label_status"]
        lines += [
            f"## {item['id']} ({item['split']}, {item['design']}) - status: `{status}`",
            "",
            f"**Question:** {item['question']}",
            "",
        ]
        if item["answerable"]:
            for citation in item["expected_citations"]:
                lines += [f"**Labelled chunk `{citation}`:**", "", f"> {chunks[citation]}", ""]
        else:
            lines += [
                "**Labelled unanswerable.** Confirm that no document in `data/documents/` "
                "answers this question.",
                "",
            ]
        lines += [f"*Drafting rationale:* {item['rationale']}", "", "---", ""]
    WORKSHEET.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {WORKSHEET.relative_to(ROOT)} ({len(challenge)} items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
