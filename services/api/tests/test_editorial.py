import pytest

from app.editorial import (
    EditorialRole,
    EditorialStore,
    ReviewState,
    TextRevision,
    can_verify,
    confidence_bucket,
    revision_diff,
)
from app.models import TextLayerKind


def test_revision_history_and_parent_guard(tmp_path) -> None:
    editorial_store = EditorialStore(tmp_path / "legacy.sqlite3")
    first = TextRevision(
        manuscript_id="mx",
        page_id="px",
        region_id="rx",
        layer_kind=TextLayerKind.DIPLOMATIC,
        text="النص الأول",
        state=ReviewState.DRAFT,
        created_by="editor",
    )
    editorial_store.add_revision(first)
    second = TextRevision(
        manuscript_id="mx",
        page_id="px",
        region_id="rx",
        layer_kind=TextLayerKind.DIPLOMATIC,
        text="النص الثاني",
        state=ReviewState.VERIFIED,
        created_by="reviewer",
        parent_revision_id=first.id,
    )
    editorial_store.add_revision(second)
    assert editorial_store.history("mx", "px", "rx")[-1].id == second.id

    assert EditorialStore(editorial_store.store.path).history("mx", "px", "rx")[-1].id == second.id

    stale = second.model_copy(update={"id": "stale", "parent_revision_id": first.id})
    with pytest.raises(ValueError):
        editorial_store.add_revision(stale)


def test_review_helpers() -> None:
    assert confidence_bucket(0.50) == "critical"
    assert confidence_bucket(0.95) == "high"
    assert can_verify(EditorialRole.REVIEWER)
    assert not can_verify(EditorialRole.TRANSCRIBER)
    assert revision_diff("أ ب", "أ ج")
