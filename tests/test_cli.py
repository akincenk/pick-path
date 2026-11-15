import csv

from pick_path.cli import main


def args(examples, *extra):
    return [*extra[:1], str(examples / "picks.csv"), "--layout", str(examples / "layout.toml"), *extra[1:]]


def test_route_prints_table(examples, capsys):
    assert main(args(examples, "route", "--strategy", "s-shape")) == 0
    out = capsys.readouterr().out
    assert "WIDGET-0042" in out and "s-shape:" in out and "for 8 picks" in out


def test_route_csv(examples, tmp_path):
    out = tmp_path / "route.csv"
    assert main(args(examples, "route", "-o", str(out))) == 0
    rows = list(csv.DictReader(out.open()))
    assert len(rows) == 8
    assert list(rows[0]) == ["step", "location", "walked_m", "order", "sku", "qty"]
    walked = [float(r["walked_m"]) for r in rows]
    assert walked == sorted(walked)


def test_compare(examples, capsys):
    assert main(args(examples, "compare")) == 0
    out = capsys.readouterr().out
    assert "exact" in out and "best" in out
    for name in ("s-shape", "return", "midpoint", "largest-gap", "nearest", "two-opt"):
        assert name in out


def test_compare_skips_exact_when_too_many(tmp_path, examples, capsys):
    picks = tmp_path / "many.csv"
    picks.write_text("location\n" + "".join(f"A0{a}-{b:02}\n" for a in range(1, 9) for b in (2, 19)))
    assert main([str(x) for x in ("compare", picks, "--layout", examples / "layout.toml")]) == 0
    assert "skipped: exact needs 12" in capsys.readouterr().out


def test_strategies(capsys):
    assert main(["strategies"]) == 0
    assert "largest-gap" in capsys.readouterr().out


def test_errors_exit_2(tmp_path, examples, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("location\nA99-01\n")
    assert main(["route", str(bad), "--layout", str(examples / "layout.toml")]) == 2
    assert "aisle 99" in capsys.readouterr().err
    assert main(["route", str(bad), "--layout", str(tmp_path / "missing.toml")]) == 2
