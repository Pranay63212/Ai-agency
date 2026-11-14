import csv

import pytest

from estimate_recovery.samples import JOBS, build


@pytest.mark.parametrize("trade", list(JOBS))
def test_samples_are_short_specific_and_have_opt_out(tmp_path, trade):
    qpath, mpath, best = build(trade, str(tmp_path), {"name": "Acme", "sender": "Sam"})
    quotes = list(csv.DictReader(open(qpath)))
    msgs = list(csv.DictReader(open(mpath)))
    assert len(quotes) == len(msgs) == 20
    for m in msgs:
        assert len(m["message"].split()) < 40
        assert m["message"].endswith("Reply STOP to opt out.")
        assert m["customer_name"].split()[0] in m["message"]
    assert len({b["job_type"] for b in best}) == 3


def test_unknown_trade(tmp_path):
    with pytest.raises(SystemExit):
        build("dentist", str(tmp_path), {"name": "A", "sender": "B"})
