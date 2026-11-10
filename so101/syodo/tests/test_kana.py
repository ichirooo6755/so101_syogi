"""Kana trajectory loading for professional brush curriculum."""

from __future__ import annotations

from so101_calligraphy.trajectory.kana import kana_characters, load_kana_trajectories


def test_kana_set_covers_gojuon() -> None:
    glyphs = kana_characters()
    assert "あ" in glyphs and "ん" in glyphs
    assert "ア" in glyphs and "ン" in glyphs
    assert "が" in glyphs and "パ" in glyphs
    assert len(glyphs) > 140


def test_load_sample_kana(tmp_path) -> None:
    trajectories = load_kana_trajectories(
        ("あ", "ア", "を"), kanjivg_cache=tmp_path / "kanjivg"
    )
    assert len(trajectories) == 3
    assert trajectories[0].character == "あ"
    assert len(trajectories[0].strokes) >= 2
