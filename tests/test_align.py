from pipeline import align


def test_proportional_covers_duration(monkeypatch):
    monkeypatch.setattr(align.util, "probe_duration", lambda _p: 12.0)
    words = align._proportional("x.wav", "One two three. Four five six seven.")
    assert words[0]["start"] == 0.0
    assert abs(words[-1]["end"] - 12.0) < 0.01
    for a, b in zip(words, words[1:]):
        assert b["start"] >= a["start"]


def test_align_words_monotonic_and_clamped(monkeypatch):
    monkeypatch.setattr(align.util, "probe_duration", lambda _p: 5.0)
    monkeypatch.setattr(align, "_faster_whisper", lambda _p: None)
    monkeypatch.setattr(align, "_gemini", lambda _p: None)
    words = align.align_words("x.wav", "alpha bravo charlie delta echo foxtrot")
    assert words[0]["start"] >= 0
    assert words[-1]["end"] <= 5.0 + 1e-6
    for a, b in zip(words, words[1:]):
        assert b["start"] >= a["start"] - 1e-9


def test_group_words_respects_max_per_pop():
    words = [{"word": f"w{i}", "start": i * 0.5, "end": i * 0.5 + 0.4} for i in range(10)]
    groups = align.group_words(words, 3)
    assert all(len(g["text"].split()) <= 3 for g in groups)
    assert groups[0]["start"] == 0.0


def test_group_words_breaks_on_sentence_end():
    words = [
        {"word": "Hello", "start": 0.0, "end": 0.4},
        {"word": "there.", "start": 0.4, "end": 0.8},
        {"word": "Now", "start": 0.8, "end": 1.2},
        {"word": "go", "start": 1.2, "end": 1.6},
    ]
    groups = align.group_words(words, 5)
    assert groups[0]["text"] == "Hello there."
    assert groups[1]["text"] == "Now go"
