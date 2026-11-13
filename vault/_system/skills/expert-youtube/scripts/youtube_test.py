"""Tests for the YouTube pack tools: language pack, hook check, title check, dead air and chapters.

Run: python -I -B youtube_test.py
No network. Temporary files go to the system temp folder and are removed by tempfile.
"""
import json
import re
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "test_data"
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE))
import chapters  # noqa: E402
import dead_air  # noqa: E402
import hook_check  # noqa: E402
import lang  # noqa: E402
import title_check  # noqa: E402

TOOLS = ["lang.py", "hook_check.py", "title_check.py", "dead_air.py", "chapters.py"]


def run_tool(script, *args):
    """Runs a tool the way the skill does: isolated mode, from another folder."""
    return subprocess.run([sys.executable, "-I", "-B", str(HERE / script), *args], capture_output=True,
                          encoding="utf-8", errors="strict", cwd=tempfile.gettempdir(), stdin=subprocess.DEVNULL)


class LanguageTest(unittest.TestCase):
    def test_turkish_lowercase_keeps_dotted_and_dotless_i(self):
        self.assertEqual(lang.normalize("İŞTE KANALIN", "tr"), "işte kanalın")

    def test_turkish_capitalize(self):
        self.assertEqual([lang.capitalize(w, "tr") for w in ("izlenme", "ırmak")], ["İzlenme", "Irmak"])

    def test_tokens_keep_turkish_letters(self):
        self.assertEqual(lang.tokens("Kanalın neden geçmiyor", "tr"), ["kanalın", "neden", "geçmiyor"])

    def test_tokens_drop_the_suffix_after_an_apostrophe(self):
        self.assertEqual(lang.tokens("YouTube'da izlendi", "tr"), ["youtube", "izlendi"])

    def test_detects_turkish(self):
        self.assertEqual(lang.detect("Bu videoda sana üç şey göstereceğim"), "tr")

    def test_detects_english(self):
        self.assertEqual(lang.detect("In this video I will show you three things"), "en")

    def test_short_text_is_unknown(self):
        self.assertEqual(lang.detect("AI RAN IT"), "unknown")

    def test_uppercase_turkish_is_turkish(self):
        self.assertEqual(lang.detect("İKİ İPUCU İLE İZLENME"), "tr")

    def test_number_keeps_its_suffix_as_one_token(self):
        self.assertEqual(lang.tokens("%97'si 30'da gidiyor", "tr"), ["97", "30", "gidiyor"])

    def test_utf16_file_fails_loudly(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "a.srt"
            path.write_bytes("1\n00:00:00,000 --> 00:00:01,000\nmerhaba\n".encode("utf-16"))
            with self.assertRaises(ValueError):
                lang.read_text(path)

    def test_reads_utf8_with_bom(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "a.txt"
            path.write_bytes("﻿İlk satır ğüşıöç".encode("utf-8"))
            self.assertEqual(lang.read_text(path), "İlk satır ğüşıöç")

    def test_reads_windows_turkish_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "a.txt"
            path.write_bytes("Başlık ğüşıöç".encode("cp1254"))
            self.assertEqual(lang.read_text(path), "Başlık ğüşıöç")


class HookCheckTest(unittest.TestCase):
    def test_regression_cases(self):
        cases = json.loads((DATA / "hook_cases.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            with self.subTest(text=case["text"]):
                result = hook_check.analyze(case["text"], case["lang"])
                for feature, level in case["expect"].items():
                    self.assertEqual(result["features"][feature]["level"], level, feature)
                if "pattern" in case:
                    self.assertEqual(result["pattern"], case["pattern"])

    def test_at_least_five_patterns_are_covered(self):
        cases = json.loads((DATA / "hook_cases.json").read_text(encoding="utf-8"))["cases"]
        self.assertGreaterEqual(len({c["pattern"] for c in cases if "pattern" in c}), 5)

    def test_noun_endings_are_not_address(self):
        for text in ("Bu dersin konusu başlıklar.", "Bu kursun içeriği uzun.", "Herkes kararını versin."):
            with self.subTest(text=text):
                self.assertEqual(hook_check.analyze(text, "tr")["features"]["address"]["level"], 0)

    def test_negative_aorist_is_address(self):
        self.assertEqual(hook_check.analyze("Bunu yapamazsın.", "tr")["features"]["address"]["level"], 2)

    def test_long_line_of_numbers_is_fast(self):
        line = " ".join(str(i) for i in range(1000)) + " oldu"
        start = time.monotonic()
        hook_check.analyze(line, "tr")
        self.assertLess(time.monotonic() - start, 0.5)

    def test_result_has_no_numeric_score(self):
        result = hook_check.analyze("Sen de bu hatayı yapıyorsun.", "tr")
        self.assertNotIn("score", result)
        self.assertNotIn("verdict", result)

    def test_weak_hook_ranks_below_strong_hook(self):
        strong = hook_check.analyze("Yeni kanal açanların %97'si 30. videodan önce bırakıyor, sen neden devam ediyorsun?", "tr")
        weak = hook_check.analyze("Merhaba arkadaşlar bugün video var.", "tr")
        self.assertEqual(hook_check.rank([weak, strong])[0], strong)

    def test_missing_features_carry_a_fix(self):
        result = hook_check.analyze("Merhaba arkadaşlar bugün video var.", "tr")
        self.assertTrue(result["features"]["specificity"]["fix"])
        self.assertIsNone(result["features"]["address"]["fix"])

    def test_cli_prints_language_per_line_and_flags_unclear_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "hooks.txt"
            path.write_text("Sen de bu hatayı yapıyorsun ve bilmiyorsun.\nYou are making this mistake right now.\nAI RAN IT\n",
                            encoding="utf-8")
            out = run_tool("hook_check.py", "--json", str(path))
        self.assertEqual(out.returncode, 0, out.stderr)
        rows = json.loads(out.stdout)
        self.assertEqual(sorted(r["lang"] for r in rows), ["en", "tr", "unknown"])
        self.assertNotIn("features", next(r for r in rows if r["lang"] == "unknown"))

    def test_cli_missing_file_is_one_line(self):
        out = run_tool("hook_check.py", "yok-boyle-bir-dosya.txt")
        self.assertEqual(out.returncode, 1)
        self.assertNotIn("Traceback", out.stderr)

    def test_cli_text_output_is_turkish(self):
        out = run_tool("hook_check.py", "--hook", "İnanılmaz efsane bir yöntem.")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("somutluk", out.stdout)
        self.assertIn("sezgisel", out.stdout)


class TitleCheckTest(unittest.TestCase):
    def codes(self, title, thumb="", code="tr"):
        return {issue["code"] for issue in title_check.check(title, thumb, code)}

    def test_empty_title(self):
        self.assertIn("empty", self.codes("   "))

    def test_over_youtube_limit_is_an_error(self):
        issues = title_check.check("a" * 101, "", "en")
        self.assertIn(("over_limit", "error"), {(i["code"], i["severity"]) for i in issues})

    def test_long_title_warns_about_search_cut(self):
        self.assertIn("search_cut", self.codes("Küçük kanallar için başlık yazarken herkesin yaptığı yedi hata ve çözümleri"))

    def test_turkish_caps_words_are_counted(self):
        self.assertIn("caps", self.codes("İNANILMAZ SONUÇLAR GERÇEKTEN 30 günde"))

    def test_two_caps_words_are_allowed(self):
        self.assertNotIn("caps", self.codes("İNANILMAZ SONUÇLAR 30 günde"))

    def test_short_acronyms_are_not_caps(self):
        self.assertNotIn("caps", self.codes("SQL ve API ile 3 proje"))

    def test_missing_concrete_item(self):
        self.assertIn("no_concrete", self.codes("Başlık nasıl yazılır"))

    def test_number_counts_as_concrete(self):
        self.assertNotIn("no_concrete", self.codes("Başlık yazmanın 5 kuralı"))

    def test_vague_word(self):
        self.assertIn("vague", self.codes("İnanılmaz bir başlık yöntemi 2026"))

    def test_thumbnail_word_limit(self):
        self.assertIn("thumb_words", self.codes("Başlık yazmanın 5 kuralı", "BU DÖRT KELİME FAZLA"))

    def test_thumbnail_repeating_title_with_consonant_change(self):
        self.assertIn("thumb_repeats", self.codes("Bu kitap kanalımı büyüttü 2026", "KİTABI"))

    def test_similar_but_different_words_are_not_repeats(self):
        for title, thumb in (("Yeni model 2026 incelemesi", "MODERN"), ("Kanal büyütme 2026", "KANAT")):
            with self.subTest(thumb=thumb):
                self.assertNotIn("thumb_repeats", self.codes(title, thumb))

    def test_plural_counts_as_repeat_in_english(self):
        self.assertIn("thumb_repeats", self.codes("5 thumbnail rules", "THUMBNAILS", "en"))

    def test_caps_words_with_apostrophe_are_counted(self):
        self.assertIn("caps", self.codes("TÜRKİYE'NİN EN BÜYÜK KANALI'NIN SIRRI"))

    def test_cli_prints_the_language(self):
        out = run_tool("title_check.py", "--title", "Başlık yazmanın 5 kuralı")
        self.assertIn("[tr]", out.stdout)

    def test_thumbnail_with_new_words_is_fine(self):
        codes = self.codes("Bu kitap kanalımı büyüttü 2026", "3 AYDA")
        self.assertNotIn("thumb_repeats", codes)
        self.assertNotIn("thumb_partial", codes)

    def test_cli_ranks_a_file_of_titles(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "titles.txt"
            path.write_text("İNANILMAZ ÇILGIN EFSANE SIR\nBaşlık yazmanın 5 kuralı\n", encoding="utf-8")
            out = run_tool("title_check.py", "--json", str(path))
        self.assertEqual(out.returncode, 0, out.stderr)
        rows = json.loads(out.stdout)
        self.assertEqual(rows[0]["title"], "Başlık yazmanın 5 kuralı")


class DeadAirTest(unittest.TestCase):
    def cuts(self, name, code):
        cues = dead_air.parse_cues(lang.read_text(DATA / name))
        return dead_air.find_cuts(cues, lang.load_pack(code))

    def test_parses_srt(self):
        cues = dead_air.parse_cues(lang.read_text(DATA / "tr.srt"))
        self.assertEqual(len(cues), 6)
        self.assertEqual((cues[2].start, cues[2].end), (3.6, 7.0))

    def test_parses_vtt_and_strips_tags(self):
        cues = dead_air.parse_cues(lang.read_text(DATA / "en.vtt"))
        self.assertEqual([c.text for c in cues], ["So today I want to show you", "um", "the one change that fixed my retention."])

    def test_parses_whisper_json(self):
        cues = dead_air.parse_cues(lang.read_text(DATA / "whisper.json"))
        self.assertEqual(cues[2].start, 5.0)

    def test_filler_only_cue_is_cut(self):
        fillers = [c for c in self.cuts("tr.srt", "tr") if c["kind"] == "filler"]
        self.assertEqual([c["text"] for c in fillers], ["Eee...", "işte"])

    def test_sentence_starting_with_filler_word_is_kept(self):
        texts = [c["text"] for c in self.cuts("tr.srt", "tr")]
        self.assertNotIn("Yani bu yöntem işe yarıyor, ama bir şartı var.", texts)

    def test_restarted_sentence_cuts_the_first_attempt(self):
        repeats = [c for c in self.cuts("tr.srt", "tr") if c["kind"] == "repeat"]
        self.assertEqual([c["text"] for c in repeats], ["Bu videoda size"])

    def test_long_gap_is_trimmed_from_the_middle(self):
        dead = [c for c in self.cuts("tr.srt", "tr") if c["kind"] == "dead"]
        self.assertEqual(len(dead), 1)
        self.assertGreater(dead[0]["start"], 7.0)
        self.assertLess(dead[0]["end"], 9.5)

    def test_english_filler(self):
        fillers = [c["text"] for c in self.cuts("en.vtt", "en") if c["kind"] == "filler"]
        self.assertEqual(fillers, ["um"])

    def test_srt_without_blank_lines_keeps_every_cue(self):
        text = "1\n00:00:00,000 --> 00:00:01,000\nbir\n2\n00:00:01,000 --> 00:00:02,000\niki\n"
        self.assertEqual([c.text for c in dead_air.parse_cues(text)], ["bir", "iki"])

    def test_whitespace_line_does_not_drop_text(self):
        text = "00:00.000 --> 00:02.000\n \nmetin burada\n"
        self.assertEqual([c.text for c in dead_air.parse_cues(text)], ["metin burada"])

    def test_crlf_srt(self):
        text = "1\r\n00:00:00,000 --> 00:00:01,000\r\nbir\r\n\r\n2\r\n00:00:02,000 --> 00:00:03,000\r\niki\r\n"
        self.assertEqual([c.text for c in dead_air.parse_cues(text)], ["bir", "iki"])

    def test_whisper_list_form(self):
        cues = dead_air.parse_cues('[{"start": 0, "end": 1, "text": "bir"}]')
        self.assertEqual([c.text for c in cues], ["bir"])

    def test_broken_whisper_json_is_a_clear_error(self):
        for text in ('{"segments": [{"start": 0}]}', '{"segments": "x"}', '{bozuk'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    dead_air.parse_cues(text)

    def test_rolling_captions_are_not_restarts(self):
        cues = [dead_air.Cue(0.0, 2.0, "so today I"), dead_air.Cue(2.0, 4.0, "so today I want to show you")]
        self.assertEqual([c for c in dead_air.find_cuts(cues, lang.load_pack("en")) if c["kind"] == "repeat"], [])

    def test_floor_below_two_breaths_is_rejected(self):
        out = run_tool("dead_air.py", str(DATA / "tr.srt"), "--floor", "0.1")
        self.assertEqual(out.returncode, 2)

    def test_clock_rounds_and_shows_hours(self):
        self.assertEqual(dead_air.clock(59.996), "01:00.00")
        self.assertEqual(dead_air.clock(3700), "1:01:40.00")

    def test_file_without_cues_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bos.srt"
            path.write_text("bu bir altyazı değil\n", encoding="utf-8")
            out = run_tool("dead_air.py", "--lang", "tr", str(path))
        self.assertEqual(out.returncode, 1)
        self.assertNotIn("Traceback", out.stderr)

    def test_cli_reports_total(self):
        out = run_tool("dead_air.py", str(DATA / "tr.srt"))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("DOLGU", out.stdout)


class ChaptersTest(unittest.TestCase):
    def problems(self, text, duration=120.0):
        entries, _ = chapters.parse_chapter_list(text)
        return {p["code"] for p in chapters.validate(entries, duration)}

    def test_valid_list(self):
        self.assertEqual(self.problems("00:00 Giriş\n0:40 Küçük resim\n1:20 İzlenme tutma"), set())

    def test_first_must_be_zero(self):
        self.assertIn("first_not_zero", self.problems("0:05 Giriş\n0:40 A\n1:20 B"))

    def test_needs_three(self):
        self.assertIn("too_few", self.problems("00:00 Giriş\n0:40 A"))

    def test_each_chapter_at_least_ten_seconds(self):
        self.assertIn("too_short", self.problems("00:00 Giriş\n0:05 A\n1:20 B"))

    def test_last_chapter_uses_video_length(self):
        self.assertIn("too_short", self.problems("00:00 Giriş\n0:40 A\n1:55 B", duration=120.0))

    def test_ascending_order(self):
        self.assertIn("not_ascending", self.problems("00:00 Giriş\n1:20 A\n0:40 B"))

    def test_hours_are_parsed(self):
        entries, _ = chapters.parse_chapter_list("1:02:03 Son")
        self.assertEqual(entries[0][0], 3723.0)

    def test_other_description_lines_are_skipped_not_invalid(self):
        entries, skipped = chapters.parse_chapter_list("Kaynaklar:\n00:00 Giriş\n0:40 A\n1:20 B")
        self.assertEqual(skipped, ["Kaynaklar:"])
        self.assertEqual(chapters.validate(entries, 120.0), [])

    def test_seconds_over_59_are_not_a_timestamp(self):
        entries, skipped = chapters.parse_chapter_list("0:75 Yanlış")
        self.assertEqual((entries, skipped), ([], ["0:75 Yanlış"]))

    def test_video_shorter_than_last_start_has_its_own_problem(self):
        self.assertIn("duration_short", self.problems("00:00 A\n0:40 B\n1:20 C", duration=60.0))

    def test_target_below_one_is_rejected(self):
        out = run_tool("chapters.py", str(DATA / "chapters_tr.srt"), "--target", "0")
        self.assertEqual(out.returncode, 2)

    def test_suggestion_finds_the_three_topics(self):
        cues = dead_air.parse_cues(lang.read_text(DATA / "chapters_tr.srt"))
        suggested = chapters.suggest(cues, lang.load_pack("tr"), target=3)
        self.assertEqual(len(suggested), 3)
        self.assertEqual(suggested[0][0], 0.0)
        self.assertEqual(chapters.validate(suggested, cues[-1].end), [])
        starts = [round(s) for s, _ in suggested]
        self.assertTrue(36 <= starts[1] <= 42 and 76 <= starts[2] <= 84, starts)

    def test_draft_titles_use_whole_words_with_turkish_capitals(self):
        cues = dead_air.parse_cues(lang.read_text(DATA / "chapters_tr.srt"))
        titles = [t for _, t in chapters.suggest(cues, lang.load_pack("tr"), target=3)]
        self.assertIn("Başlık", titles[0].split())
        self.assertIn("İzlenme", titles[2].split())

    def test_cli_check_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "list.txt"
            path.write_text("0:05 Giriş\n0:40 A\n", encoding="utf-8")
            out = run_tool("chapters.py", "--check", str(path), "--lang", "tr", "--duration", "120")
        self.assertEqual(out.returncode, 1)
        self.assertIn("geçersiz", out.stdout)


class SafetyTest(unittest.TestCase):
    BANNED = re.compile(r"\b(urllib|socket|http|requests|subprocess|os\.system|os\.remove|unlink|rmtree|"
                        r"eval\(|exec\(|write_text|write_bytes|open\([^)]*['\"][wa])")

    def test_tools_write_no_bytecode_even_without_dash_b(self):
        with tempfile.TemporaryDirectory() as folder:
            copy = Path(folder)
            for item in HERE.iterdir():
                if item.suffix in (".py", ".json"):
                    (copy / item.name).write_bytes(item.read_bytes())
            out = subprocess.run([sys.executable, "-I", str(copy / "hook_check.py"), "--hook", "Sen de bunu yapıyorsun."],
                                 capture_output=True, encoding="utf-8", stdin=subprocess.DEVNULL)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertFalse((copy / "__pycache__").exists())

    def test_tools_have_no_network_process_or_write_calls(self):
        for name in TOOLS:
            with self.subTest(tool=name):
                source = (HERE / name).read_text(encoding="utf-8")
                self.assertIsNone(self.BANNED.search(source), name)

    def test_every_tool_runs_in_isolated_mode(self):
        for name in TOOLS[1:]:
            with self.subTest(tool=name):
                out = run_tool(name, "--help")
                self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
