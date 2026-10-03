from app.visual_knowledge import (
    Exhibit,
    HistoricalObject,
    MediaAsset,
    MediaKind,
    TimelineEvent,
    visual_store,
)


def test_medical_object_receives_historical_warning() -> None:
    item = HistoricalObject(
        id="obj-unique-warning",
        manuscript_id="m",
        name="أداة",
        category="surgery",
        media=[
            MediaAsset(
                id="model",
                kind=MediaKind.MODEL_3D,
                url="https://example.test/model.glb",
                license="CC0",
            )
        ],
    )
    stored = visual_store.put_object(item)
    assert stored.warnings
    assert stored.media[0].kind == MediaKind.MODEL_3D


def test_timeline_sorted_and_exhibit() -> None:
    visual_store.put_event(TimelineEvent(id="late", title="متأخر", start_year=1100))
    visual_store.put_event(TimelineEvent(id="early", title="مبكر", start_year=900))
    assert visual_store.list_events()[0].id == "early"
    exhibit = visual_store.put_exhibit(Exhibit(id="e", title="معرض"))
    assert exhibit.title == "معرض"
