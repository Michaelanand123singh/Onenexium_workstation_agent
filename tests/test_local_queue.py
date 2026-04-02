from pathlib import Path

from onenexium_agent.local_store import LocalQueue


def test_enqueue_flush(tmp_path: Path) -> None:
    db = tmp_path / "q.sqlite"
    q = LocalQueue(db)
    q.enqueue({"a": 1})
    q.enqueue({"b": 2})
    assert q.pending_count() == 2
    batch = q.fetch_batch(10)
    assert len(batch) == 2
    q.delete_ids([row[0] for row in batch])
    assert q.pending_count() == 0
