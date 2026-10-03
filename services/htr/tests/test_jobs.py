import pytest

from htr.jobs import HtrJob, HtrJobState


def test_valid_job_flow() -> None:
    job = HtrJob(id="j1", manuscript_id="m1", page_id="p1")
    job = job.transition(HtrJobState.FETCHING)
    job = job.transition(HtrJobState.SEGMENTING)
    assert job.state == HtrJobState.SEGMENTING


def test_invalid_job_flow() -> None:
    job = HtrJob(id="j1", manuscript_id="m1", page_id="p1")
    with pytest.raises(ValueError):
        job.transition(HtrJobState.SUCCEEDED)
