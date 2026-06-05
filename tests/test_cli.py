import pytest

from remixtree.cli import parse_args


def test_single_project_id():
    args = parse_args(["123"])
    assert args.project_ids == [123]
    assert args.depth is None
    assert args.timeout == 300
    assert args.format is None
    assert args.stats is False
    assert args.color is False


def test_batch_project_ids():
    args = parse_args(["1", "2", "3"])
    assert args.project_ids == [1, 2, 3]


def test_all_the_flags():
    args = parse_args(["1", "-d", "3", "-t", "60", "-s", "-c", "--format", "json", "-o", "t.json", "-v"])
    assert args.depth == 3
    assert args.timeout == 60
    assert args.stats is True
    assert args.color is True
    assert args.format == "json"
    assert args.output == "t.json"
    assert args.verbose is True


def test_format_only_allows_known_choices():
    with pytest.raises(SystemExit):
        parse_args(["1", "--format", "xml"])


def test_project_id_must_be_int():
    with pytest.raises(SystemExit):
        parse_args(["notanumber"])


def test_at_least_one_id_required():
    with pytest.raises(SystemExit):
        parse_args([])
