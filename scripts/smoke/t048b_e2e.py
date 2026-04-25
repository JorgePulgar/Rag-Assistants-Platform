"""
T048b — Real-content end-to-end smoke test.

Uploads real documents to two distinct assistants, runs full chat flows,
and logs every observable anomaly so they can be added to bugs_t048.md.

Documents:
  Assistant 1 ("LLM Expert")   ← Documentacion_LLM_Completa.docx
  Assistant 2 ("RAG Expert")   ← RAG_Documentation.pptx

Run from repo root:
    python scripts/smoke/t048b_e2e.py
"""

import json
import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:8000"
DOCS_DIR = Path(__file__).parent.parent.parent / "backend" / "tests" / "test_documents"

DOCX_FILE = DOCS_DIR / "Documentacion_LLM_Completa.docx"
PPTX_FILE = DOCS_DIR / "RAG_Documentation.pptx"

BUGS: list[str] = []
PASSES: list[str] = []


def _ok(label: str) -> None:
    print(f"  [PASS] {label}")
    PASSES.append(label)


def _bug(label: str, detail: str) -> None:
    msg = f"{label}: {detail}"
    print(f"  [BUG ] {msg}")
    BUGS.append(msg)


def _check(label: str, condition: bool, detail: str = "") -> bool:
    if condition:
        _ok(label)
    else:
        _bug(label, detail or "unexpected value")
    return condition


def post(path: str, **kwargs) -> requests.Response:
    return requests.post(f"{BASE}{path}", **kwargs)


def get(path: str) -> requests.Response:
    return requests.get(f"{BASE}{path}")


def delete(path: str) -> requests.Response:
    return requests.delete(f"{BASE}{path}")


# ── setup: check files exist ────────────────────────────────────────────────

def check_files() -> None:
    print("\n── Checking test documents ──")
    for f in [DOCX_FILE, PPTX_FILE]:
        _check(f"file exists: {f.name}", f.exists(), f"not found at {f}")


# ── create assistants ───────────────────────────────────────────────────────

def create_assistant(name: str, instructions: str) -> str:
    r = post("/api/assistants", json={"name": name, "instructions": instructions})
    _check(f"create assistant '{name}' → 201", r.status_code == 201,
           f"got {r.status_code}: {r.text}")
    data = r.json()
    _check(f"assistant '{name}' has id", bool(data.get("id")))
    _check(f"assistant '{name}' has search_index", bool(data.get("search_index")))
    return data["id"]


# ── upload document ──────────────────────────────────────────────────────────

def upload_document(assistant_id: str, filepath: Path) -> str | None:
    print(f"\n  Uploading {filepath.name} to assistant {assistant_id[:8]}…")
    with open(filepath, "rb") as fh:
        r = post(
            f"/api/assistants/{assistant_id}/documents",
            files={"file": (filepath.name, fh)},
        )
    _check(f"upload {filepath.name} → 201", r.status_code == 201,
           f"got {r.status_code}: {r.text[:200]}")
    if r.status_code != 201:
        return None
    data = r.json()
    doc_id = data.get("id")
    status = data.get("status")
    _check(f"document status is 'indexed'", status == "indexed",
           f"got status={status!r}")
    return doc_id


# ── conversation helpers ────────────────────────────────────────────────────

def create_conversation(assistant_id: str) -> str:
    r = post("/api/conversations", json={"assistant_id": assistant_id})
    _check("create conversation → 201", r.status_code == 201,
           f"got {r.status_code}: {r.text}")
    return r.json()["id"]


def send(conv_id: str, content: str) -> dict:
    r = post(f"/api/conversations/{conv_id}/messages", json={"content": content})
    _check(f"send message → 200", r.status_code == 200,
           f"got {r.status_code}: {r.text[:300]}")
    if r.status_code != 200:
        return {}
    return r.json().get("message", {})


def check_message(label: str, msg: dict) -> None:
    """Run a battery of checks on a single assistant message."""
    content: str = msg.get("content", "")
    citations: list = msg.get("citations") or []

    _check(f"{label}: content non-empty", bool(content.strip()),
           "content is empty")

    # No residual [CITE:...] literals in content
    _check(f"{label}: no residual [CITE:...] in content",
           "[CITE:" not in content,
           f"residual marker found in: {content[:200]}")

    # Citations are structured objects, not strings
    for i, c in enumerate(citations):
        _check(f"{label}: citation[{i}] has document_id",
               bool(c.get("document_id")))
        _check(f"{label}: citation[{i}] has document_name",
               bool(c.get("document_name")))
        _check(f"{label}: citation[{i}] has chunk_text",
               bool(c.get("chunk_text")))

    # If citations present, inline [N] markers should appear in content
    if citations:
        has_inline = any(f"[{i+1}]" in content for i in range(len(citations)))
        _check(f"{label}: inline [N] pills present when citations exist",
               has_inline, f"content: {content[:300]}")

    print(f"         content[:120]: {content[:120].replace(chr(10), ' ')!r}")
    print(f"         citations: {len(citations)}")


# ── isolation check ─────────────────────────────────────────────────────────

def check_isolation(asst_id_a: str, topic_from_b: str) -> None:
    """Ask assistant A a question only answerable from B's document."""
    conv = create_conversation(asst_id_a)
    msg = send(conv, topic_from_b)
    if not msg:
        return
    content: str = msg.get("content", "")
    idk_marker = "did not find" in content.lower() or "don't have" in content.lower() or "no information" in content.lower()
    _check("isolation: assistant A cannot answer B's topic",
           idk_marker,
           f"cross-contamination? content: {content[:200]}")


# ── main flow ───────────────────────────────────────────────────────────────

def main() -> int:
    print("=" * 60)
    print("T048b — Real-content E2E smoke test")
    print("=" * 60)

    check_files()

    # 1. Create two assistants
    print("\n── Creating assistants ──")
    asst1_id = create_assistant(
        "LLM Expert",
        "You are an expert on Large Language Models. Answer questions based only on the provided documents.",
    )
    asst2_id = create_assistant(
        "RAG Expert",
        "You are an expert on Retrieval-Augmented Generation systems. Answer questions based only on the provided documents.",
    )

    # 2. Upload documents
    print("\n── Uploading documents ──")
    doc1_id = upload_document(asst1_id, DOCX_FILE)
    doc2_id = upload_document(asst2_id, PPTX_FILE)

    if not doc1_id or not doc2_id:
        print("\n[ABORT] One or both uploads failed — cannot continue.")
        return 1

    # 3. ── Flow A: LLM Expert (DOCX) ──────────────────────────────────────
    print("\n── Flow A: LLM Expert (DOCX) ──")
    conv_a = create_conversation(asst1_id)

    print("\n  Turn A1: broad question about LLMs")
    msg_a1 = send(conv_a, "¿Qué es un Large Language Model y cómo funciona?")
    check_message("A1", msg_a1)

    print("\n  Turn A2: referential follow-up (tests query rewriting)")
    msg_a2 = send(conv_a, "¿Puedes explicar más sobre lo último que mencionaste?")
    check_message("A2", msg_a2)
    content_a2 = msg_a2.get("content", "")
    idk_a2 = "did not find" in content_a2.lower() or "don't have" in content_a2.lower()
    _check("A2: follow-up does not trigger I-don't-know", not idk_a2,
           f"query rewriting may have failed; content: {content_a2[:200]}")

    print("\n  Turn A3: summarise the conversation (tests memory)")
    msg_a3 = send(conv_a, "Resume en dos frases lo que hemos discutido.")
    check_message("A3", msg_a3)
    content_a3 = msg_a3.get("content", "")
    idk_a3 = "did not find" in content_a3.lower() or "don't have" in content_a3.lower()
    _check("A3: summary does not trigger I-don't-know", not idk_a3,
           "conversational memory / no-search-intent path may not be firing")

    # 4. ── Flow B: RAG Expert (PPTX) ──────────────────────────────────────
    print("\n── Flow B: RAG Expert (PPTX) ──")
    conv_b = create_conversation(asst2_id)

    print("\n  Turn B1: broad question about RAG")
    msg_b1 = send(conv_b, "¿Qué es RAG y cuáles son sus componentes principales?")
    check_message("B1", msg_b1)

    print("\n  Turn B2: referential follow-up")
    msg_b2 = send(conv_b, "¿Puedes dar más detalles sobre el primer componente que mencionaste?")
    check_message("B2", msg_b2)
    content_b2 = msg_b2.get("content", "")
    idk_b2 = "did not find" in content_b2.lower() or "don't have" in content_b2.lower()
    _check("B2: follow-up does not trigger I-don't-know", not idk_b2,
           f"query rewriting may have failed; content: {content_b2[:200]}")

    print("\n  Turn B3: out-of-scope question (should trigger I-don't-know)")
    msg_b3 = send(conv_b, "¿Cuál es la capital de Francia?")
    check_message("B3", msg_b3)
    content_b3 = msg_b3.get("content", "")
    idk_b3 = "did not find" in content_b3.lower() or "don't have" in content_b3.lower()
    _check("B3: off-topic question triggers I-don't-know",
           idk_b3,
           f"expected fallback, got: {content_b3[:200]}")

    # 5. ── Isolation check ─────────────────────────────────────────────────
    print("\n── Isolation check ──")
    print("  Asking LLM Expert a question only answerable from RAG doc…")
    check_isolation(
        asst1_id,
        "¿Qué es un vector store y cómo se usa en RAG?",
    )

    print("\n  Asking RAG Expert a question only answerable from LLM doc…")
    check_isolation(
        asst2_id,
        "¿Qué son los transformers y cómo se entrenan los LLMs?",
    )

    # 6. ── Persistence check ───────────────────────────────────────────────
    print("\n── Persistence check ──")
    msgs_r = get(f"/api/conversations/{conv_a}/messages")
    _check("reload conv_a messages → 200", msgs_r.status_code == 200)
    if msgs_r.status_code == 200:
        history = msgs_r.json()
        _check("history has 6 messages (3 user + 3 assistant)",
               len(history) == 6,
               f"got {len(history)} messages")
        if history:
            roles = [m["role"] for m in history]
            _check("history roles alternate user/assistant",
                   roles == ["user", "assistant", "user", "assistant", "user", "assistant"],
                   f"roles: {roles}")

    # 7. ── List / delete cleanup ───────────────────────────────────────────
    print("\n── Cleanup ──")
    # List conversations
    r_list = get(f"/api/assistants/{asst1_id}/conversations")
    _check("list conversations for asst1 → 200", r_list.status_code == 200)

    # Delete both assistants (cascades documents + conversations + Azure index)
    r_del1 = delete(f"/api/assistants/{asst1_id}")
    _check("delete asst1 → 204", r_del1.status_code == 204)
    r_del2 = delete(f"/api/assistants/{asst2_id}")
    _check("delete asst2 → 204", r_del2.status_code == 204)

    # Verify gone
    r_gone = get(f"/api/assistants/{asst1_id}")
    _check("deleted asst1 returns 404", r_gone.status_code == 404)

    # 8. ── Summary ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"PASSES : {len(PASSES)}")
    print(f"BUGS   : {len(BUGS)}")
    if BUGS:
        print("\nBugs found:")
        for b in BUGS:
            print(f"  • {b}")
    else:
        print("No bugs found.")
    print("=" * 60)

    return 0 if not BUGS else 1


if __name__ == "__main__":
    sys.exit(main())
