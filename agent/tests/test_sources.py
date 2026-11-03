"""SampleFileSource: parsing and clear errors (AC-27, AC-28)."""

import json
from datetime import date
from decimal import Decimal

import pytest
from conftest import SAMPLE_4_NOV

from margin_watch.sources import SampleFileSource, SourceError


def _job(job_id="2001", **overrides):
    job = {
        "id": job_id,
        "name": "Test job",
        "client": "Test client",
        "site": "Test site",
        "stage": "In progress",
        "project_manager": "Test PM",
        "quoted_sell_ex_gst": "1000.00",
        "percent_complete": 50,
        "cost_centres": [
            {"name": "Labour", "estimated_cost": "500.00", "actual_cost_to_date": "200.00"}
        ],
    }
    job.update(overrides)
    return job


def _write(tmp_path, jobs, name="jobs.json"):
    path = tmp_path / name
    path.write_text(json.dumps({"snapshot_date": "2026-11-04", "jobs": jobs}))
    return path


def test_ac27_loads_sample_file():
    """AC-27: the 4 Nov sample has snapshot date 2026-11-04 and 14 jobs; 1042 parses as Decimals."""
    snapshot = SampleFileSource(SAMPLE_4_NOV).load()
    job = next(j for j in snapshot.jobs if j.id == "1042")
    labour = next(c for c in job.cost_centres if c.name == "Labour")

    assert snapshot.snapshot_date == date(2026, 11, 4)
    assert len(snapshot.jobs) == 14
    assert job.quoted_sell_ex_gst == Decimal("80000.00")
    assert isinstance(job.quoted_sell_ex_gst, Decimal)
    assert len(job.cost_centres) == 4
    assert labour.actual_cost_to_date == Decimal("21600.00")
    assert job.percent_complete == Decimal("60")


def test_ac27_json_numbers_load_as_exact_decimals(tmp_path):
    """AC-27: money given as the JSON number 0.1 loads as exactly Decimal("0.1"), not a float."""
    path = _write(tmp_path, [_job(quoted_sell_ex_gst=0.1)])

    job = SampleFileSource(path).load().jobs[0]

    assert job.quoted_sell_ex_gst == Decimal("0.1")
    assert str(job.quoted_sell_ex_gst) == "0.1"


def test_ac27_null_values_are_kept_for_review(tmp_path):
    """AC-27: a null percent complete loads as None (NEEDS_REVIEW later, not a file error)."""
    path = _write(tmp_path, [_job(percent_complete=None)])

    assert SampleFileSource(path).load().jobs[0].percent_complete is None


def test_ac28_missing_file(tmp_path):
    """AC-28: a missing file raises SourceError naming the file."""
    with pytest.raises(SourceError, match=r"nope\.json"):
        SampleFileSource(tmp_path / "nope.json").load()


def test_ac28_not_json(tmp_path):
    """AC-28: a file that isn't JSON raises SourceError naming the file."""
    path = tmp_path / "broken.json"
    path.write_text("{ this is not json")

    with pytest.raises(SourceError, match=r"broken\.json"):
        SampleFileSource(path).load()


def test_ac28_job_missing_client(tmp_path):
    """AC-28: a job missing `client` raises SourceError naming the job id and the field."""
    job = _job("2002")
    del job["client"]

    with pytest.raises(SourceError) as error:
        SampleFileSource(_write(tmp_path, [job])).load()

    assert "2002" in str(error.value)
    assert "client" in str(error.value)


def test_ac28_non_numeric_estimate(tmp_path):
    """AC-28: a non-numeric estimated_cost raises SourceError naming the job id and the field."""
    job = _job("2003")
    job["cost_centres"][0]["estimated_cost"] = "abc"

    with pytest.raises(SourceError) as error:
        SampleFileSource(_write(tmp_path, [job])).load()

    assert "2003" in str(error.value)
    assert "estimated_cost" in str(error.value)


def test_ac28_duplicate_job_id(tmp_path):
    """AC-28: two jobs with the same id raise SourceError naming the id."""
    with pytest.raises(SourceError) as error:
        SampleFileSource(_write(tmp_path, [_job("2004"), _job("2004")])).load()

    assert "2004" in str(error.value)
    assert "duplicate" in str(error.value).lower()


def test_ac28_jobs_list_missing(tmp_path):
    """AC-28: a file without a `jobs` list raises SourceError naming the file and the field."""
    path = tmp_path / "nojobs.json"
    path.write_text(json.dumps({"snapshot_date": "2026-11-04"}))

    with pytest.raises(SourceError) as error:
        SampleFileSource(path).load()

    assert "nojobs.json" in str(error.value)
    assert "jobs" in str(error.value)
