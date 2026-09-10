"""Meaningful structure, state, editing and no-overwrite checks for story tools."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import story_workbench as workbench


class StoryWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.packet = workbench.load(workbench.TEMPLATE)

    def report(self, packet=None):
        return workbench.check_packet(self.packet if packet is None else packet)

    def assert_error(self, fragment):
        self.assertTrue(any(fragment in message for message in self.report()["errors"]), self.report())

    def add_cast(self, name):
        entry = copy.deepcopy(self.packet["cast"][0])
        entry.update(character_id=name, role="friend")
        self.packet["cast"].append(entry)

    def add_prop(self):
        shelf = {"location_id": "home", "holder_id": None, "condition": "on shelf"}
        held = {"location_id": "home", "holder_id": "hero", "condition": "held"}
        table = {"location_id": "home", "holder_id": None, "condition": "on low table"}
        self.packet["props"] = [{"id": "cup", "name": "Small cup", "initial_state": shelf,
                                 "changes": [{"beat_id": "beat-02", "before": shelf, "after": held, "reason": "offer"},
                                             {"beat_id": "beat-03", "before": held, "after": table, "reason": "place"}]}]

    def order_request(self, order=None):
        return {"schema_version": 1, "packet_id": self.packet["id"], "base_revision": self.packet["revision"],
                "reading_order": order or [b["id"] for b in reversed(self.packet["beats"])]}

    def add_evidence(self):
        self.packet["reviews"] = [{"id": "editorial-01", "kind": "editorial", "status": "passed", "reviewer": "Example reviewer",
                                   "packet_revision": 1, "notes": "Historical review record"}]
        self.packet["proofs"] = [{"id": "layout-proof", "path": "old-proof.pdf", "status": "reviewed", "packet_revision": 1, "notes": "Historical proof record"}]

    def test_blank_scaffold_valid_but_unfinished(self):
        report = self.report()
        self.assertEqual(report["errors"], [])
        self.assertTrue(report["warnings"])
        self.assertEqual(report["editorial_status"], "not_determined_by_cli")
        self.assertEqual(self.packet["cast"][0]["age_years"], None)
        self.assertEqual(self.packet["page_plan"]["interior_pages"], 32)

    def test_schema_type_checks_exclude_boolean_integer(self):
        self.packet["revision"] = True
        self.assert_error("expected integer")

    def test_unknown_top_level_field_rejected_without_loss(self):
        self.packet["future_author_field"] = {"keep": "this"}
        self.assert_error("unsupported field")
        self.assertEqual(self.packet["future_author_field"], {"keep": "this"})

    def test_extensions_preserved_without_authority_claim(self):
        self.packet["extensions"] = {"map": {"x": [1, 2]}, "declared_canon": True}
        self.assertEqual(self.report()["errors"], [])
        views = workbench.render_views(self.packet)
        self.assertEqual(json.loads(views["packet.json"])["extensions"], self.packet["extensions"])
        self.assertEqual(json.loads(views["arcs.json"])["canon_adoption"], "none")

    def test_unknown_character_reference(self):
        self.packet["beats"][0]["character_ids"].append("invented-friend")
        self.assert_error("unknown reference")

    def test_duplicate_beat_id(self):
        self.packet["beats"][1]["id"] = "beat-01"
        self.assert_error("beats: duplicate")

    def test_invalid_identifier(self):
        self.packet["id"] = "../escape"
        self.assert_error("invalid stable identifier")

    def test_unknown_cause(self):
        self.packet["beats"][1]["cause_from"] = ["absent-beat"]
        self.assert_error("unknown reference")

    def test_future_and_self_causes_are_errors(self):
        self.packet["beats"][0]["cause_from"] = ["beat-02"]
        self.assert_error("strictly earlier")
        self.packet["beats"][0]["cause_from"] = ["beat-01"]
        self.assert_error("strictly earlier")

    def test_physical_page_count_gaps_and_wrong_sides(self):
        self.packet["page_plan"]["interior_pages"] = 31
        self.assert_error("must be even")
        self.packet["page_plan"]["interior_pages"] = 32
        self.packet["page_plan"]["story_spreads"][0]["right_page"] = 6
        self.assert_error("even left page")
        self.assert_error("without gaps or overlaps")

    def test_page_plan_reading_order_not_chronology(self):
        self.packet["beats"][0], self.packet["beats"][1] = self.packet["beats"][1], self.packet["beats"][0]
        self.assert_error("current reading order")

    def test_variable_beat_count_and_multiple_beats_in_spread(self):
        extra = copy.deepcopy(self.packet["beats"][-1])
        extra.update(id="extra-ending", chronology=15, cause_from=["beat-14"])
        self.packet["beats"].append(extra)
        self.packet["page_plan"]["story_spreads"][-1]["beat_ids"].append("extra-ending")
        self.assertEqual(self.report()["errors"], [])

    def test_optional_composition_keeps_old_packets_valid_without_extra_warnings(self):
        before = self.report()
        for spread in self.packet["page_plan"]["story_spreads"]:
            spread.pop("composition", None)
        self.assertEqual(self.report(), before)
        self.packet["page_plan"]["story_spreads"][0]["composition"] = {"framing": "Close view"}
        self.assertEqual(self.report(), before)

    def test_composition_rejects_wrong_types_and_unknown_fields(self):
        spread = self.packet["page_plan"]["story_spreads"][0]
        spread["composition"] = {"text_zone": ["sky"]}
        self.assert_error("composition.text_zone: expected string")
        spread["composition"] = {"made_up_field": "retain this for manual migration"}
        self.assert_error("unsupported field")
        self.assertEqual(spread["composition"]["made_up_field"], "retain this for manual migration")

    def test_composition_renders_all_fields_and_stays_with_physical_spread(self):
        details = {"focus": "Friend notices the cup.", "framing": "Low, wide view.",
                   "word_contribution": "Narrator names a quiet pause.", "art_contribution": "A leaf moves behind Friend.",
                   "text_zone": "Pale sky at upper left.", "gutter_notes": "Keep the necklace away from the fold."}
        self.packet["page_plan"]["story_spreads"][0]["composition"] = details
        reordered = workbench.reorder_packet(self.packet, self.order_request())
        self.assertEqual(reordered["page_plan"]["story_spreads"][0]["composition"], details)
        rendered = workbench.render_views(reordered)["composition.md"]
        self.assertIn("spread-01 composition · pages 4–5", rendered)
        for text in details.values():
            self.assertIn(text, rendered)
        self.assertEqual(reordered["page_plan"]["status"], "needs_review")

    def test_new_packet_supports_small_and_large_spread_counts(self):
        for count in (1, 2, 3, 8, 18):
            with self.subTest(count=count):
                packet = workbench.new_packet("flexible-story", "Flexible story", "friend", count)
                self.assertEqual(self.report(packet)["errors"], [])
                self.assertEqual(len(packet["beats"]), count)
                self.assertEqual(len(packet["page_plan"]["story_spreads"]), count)
                self.assertEqual(packet["page_plan"]["interior_pages"], 2 * count + 4)
                self.assertTrue(all(beat["character_ids"] == ["friend"] for beat in packet["beats"]))
        default = workbench.new_packet("default-story", "Default story", "hero")
        self.assertEqual(default["page_plan"]["interior_pages"], 32)
        for invalid in (0, -1, True, 1.5):
            with self.assertRaisesRegex(ValueError, "positive integer"):
                workbench.new_packet("bad-story", "Bad story", "friend", invalid)

    def test_prop_before_after_drift(self):
        self.add_prop()
        self.assertEqual(self.report()["errors"], [])
        self.packet["props"][0]["changes"][1]["before"] = copy.deepcopy(self.packet["props"][0]["initial_state"])
        self.assert_error("before-state drifts")

    def test_prop_holder_reference(self):
        self.add_prop()
        self.packet["props"][0]["initial_state"]["holder_id"] = "absent-character"
        self.assert_error("holder: unknown reference")

    def test_knowledge_sources_current_ok_future_rejected(self):
        self.packet["knowledge"] = [{"id": "cup-place", "character_id": "hero", "topic": "Cup position", "initial_state": "unknown",
                                     "changes": [{"beat_id": "beat-02", "before": "unknown", "after": "seen", "source_beat_id": "beat-02", "reason": "direct observation"}]}]
        self.assertEqual(self.report()["errors"], [])
        self.packet["knowledge"][0]["changes"][0]["source_beat_id"] = "beat-03"
        self.assert_error("future chronological event")

    def test_relationship_state_drift(self):
        self.add_cast("friend")
        self.packet["relationships"] = [{"id": "shared-care", "from_id": "hero", "to_id": "friend", "initial_state": "friends",
                                         "changes": [{"beat_id": "beat-02", "before": "strangers", "after": "shared a visit", "reason": "new proposed scene"}]}]
        self.assert_error("before-state drifts")

    def test_speech_is_not_restricted_without_project_context(self):
        self.packet["beats"][0]["dialogue"] = [{"speaker_id": "hero", "kind": "speech", "text": "Hello"}]
        self.assertEqual(self.report()["errors"], [])
        self.packet["beats"][0]["dialogue"][0]["speaker_id"] = "absent-character"
        self.assert_error("dialogue speaker: unknown reference")

    def test_optional_bible_context_controls_cast_membership(self):
        self.assertEqual(workbench.check_packet(self.packet, known_ids={"hero"})["errors"], [])
        self.assertTrue(workbench.check_packet(self.packet, known_ids={"someone-else"})["errors"])
        with self.assertRaisesRegex(ValueError, "unknown reference"):
            workbench.new_packet("new-story", "Title", "hero", known_ids={"someone-else"})

    def test_nonverbal_quote_not_speech_loophole(self):
        self.packet["beats"][0]["dialogue"] = [{"speaker_id": "hero", "kind": "nonverbal", "text": "“Hello, friends.”"}]
        self.assert_error("quoted dialogue")

    def test_sourced_fact_needs_reference(self):
        self.packet["facts"] = [{"id": "claim", "statement": "An author claim", "status": "sourced", "source_ref": None, "character_ids": [], "beat_ids": []}]
        self.assert_error("packet label is not canon approval")

    def test_thread_cannot_resolve_before_introduction(self):
        self.packet["open_threads"] = [{"id": "question", "question": "Where?", "introduced_beat_id": "beat-03", "resolved_beat_id": "beat-02", "status": "resolved"}]
        self.assert_error("resolves before")

    def test_stale_review_cannot_remain_passed(self):
        self.add_evidence()
        self.packet["revision"] = 2
        self.assert_error("stale reviews claim")
        self.assert_error("stale proofs claim")

    def test_reviewed_page_plan_needs_current_review_evidence(self):
        self.packet["page_plan"]["status"] = "reviewed"
        self.assert_error("current named layout review")

    def test_reorder_preserves_ids_chronology_and_states_invalidates_evidence(self):
        self.add_prop()
        self.add_evidence()
        original = copy.deepcopy(self.packet)
        edited = workbench.reorder_packet(self.packet, self.order_request())
        self.assertEqual(self.packet, original)
        self.assertEqual({b["id"]: b["chronology"] for b in edited["beats"]}, {b["id"]: b["chronology"] for b in original["beats"]})
        self.assertEqual(edited["props"], original["props"])
        self.assertEqual(edited["revision"], 2)
        self.assertEqual(edited["page_plan"]["status"], "needs_review")
        self.assertEqual(edited["reviews"][0]["status"], "stale")
        self.assertEqual(edited["proofs"][0]["status"], "stale")
        self.assertEqual(self.report(edited)["errors"], [])
        self.assertTrue(any("differs from chronology" in s for s in self.report(edited)["warnings"]))

    def test_bad_or_stale_reorder_requests_rejected(self):
        request = self.order_request()
        request["reading_order"][0] = request["reading_order"][1]
        with self.assertRaisesRegex(ValueError, "exactly once"):
            workbench.reorder_packet(self.packet, request)
        request = self.order_request()
        request["base_revision"] = 0
        with self.assertRaisesRegex(ValueError, "Stale"):
            workbench.reorder_packet(self.packet, request)

    def test_import_preserves_extension_and_rejects_chronology_change(self):
        edited = copy.deepcopy(self.packet)
        edited["extensions"] = {"workbench_base_revision": 1, "map": {"a": 1}}
        edited["revision"] = 9  # Many local board actions from the same base.
        edited["beats"][0]["action"] = "An edited proposed action"
        accepted = workbench.import_packet(self.packet, edited)
        self.assertEqual(accepted["revision"], 2)
        self.assertEqual(accepted["extensions"]["map"], {"a": 1})
        edited["beats"][0]["chronology"] = 100
        with self.assertRaisesRegex(ValueError, "preserve every beat ID and chronology"):
            workbench.import_packet(self.packet, edited)

    def test_stale_import_rejected_without_altering_base(self):
        edited = copy.deepcopy(self.packet)
        edited["extensions"]["workbench_base_revision"] = 0
        original = copy.deepcopy(self.packet)
        with self.assertRaisesRegex(ValueError, "Stale"):
            workbench.import_packet(self.packet, edited)
        self.assertEqual(self.packet, original)

    def test_cli_new_does_not_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            target = Path(folder) / "existing.json"
            target.write_text("keep original", encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                result = workbench.main(["new", "--id", "new-story", "--title", "A title", "--protagonist", "hero", "--output", str(target)])
            self.assertEqual(result, 1)
            self.assertEqual(target.read_text(), "keep original")

    def test_cli_new_spread_option_and_zero_refusal(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            target = Path(folder) / "eight-spreads.json"
            args = ["new", "--id", "eight-spreads", "--title", "A title", "--protagonist", "friend", "--output", str(target), "--spreads"]
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(workbench.main(args + ["0"]), 1)
                self.assertFalse(target.exists())
                self.assertEqual(workbench.main(args + ["8"]), 0)
            self.assertEqual(workbench.load(target)["page_plan"]["interior_pages"], 20)

    def test_render_views_and_existing_directory_are_safe(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            output = Path(folder) / "views"
            workbench.render_directory(self.packet, output)
            self.assertEqual(workbench.load(output / "packet.json"), self.packet)
            self.assertIn("Chronology", (output / "chronology.md").read_text(encoding="utf-8"))
            self.assertIn("front", (output / "composition.md").read_text(encoding="utf-8").lower())
            with self.assertRaises(FileExistsError):
                workbench.render_directory(self.packet, output)

    def test_collection_has_unknown_dates_no_invented_series_chronology(self):
        other = copy.deepcopy(self.packet)
        other["id"] = "another-story"
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            output = Path(folder) / "collection"
            workbench.render_collection([self.packet, other], output)
            arcs = workbench.load(output / "series-arcs.json")
            self.assertTrue(all(row["chronological_date"] is None for row in arcs["stories"]))
            self.assertIn("no cross-story chronology", arcs["ordering"])
            self.assertEqual(len((output / "series-grid.csv").read_text(encoding="utf-8").splitlines()), 3)

    def test_optional_purpose_supports_old_packets_and_rejects_invalid_types(self):
        self.packet.pop("purpose", None)
        self.assertFalse(self.report()["errors"])
        self.assertIn("**Teaching goal:** [to develop]", workbench.render_views(self.packet)["beats.md"])
        self.packet["purpose"] = {"teaching_goal": ["invalid list"]}
        self.assert_error("purpose.teaching_goal")

    def test_purpose_roundtrip_keeps_theme_and_full_delivery(self):
        self.packet["purpose"] = {"intent": "A warm mystery", "teaching_goal": "Retrace actions",
                                  "lesson": "Look again", "delivery": "Clue at beat-02.\nPayoff at beat-12. Příběh."}
        self.packet["premise"]["theme"] = "Belonging"
        views = workbench.render_views(self.packet)
        self.assertEqual(json.loads(views["packet.json"])["purpose"], self.packet["purpose"])
        self.assertIn("**Meaning / theme:** Belonging", views["beats.md"])
        self.assertIn(self.packet["purpose"]["delivery"], views["beats.md"])

    def test_json_nonfinite_numbers_rejected(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"value": NaN}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Non-finite"):
                workbench.load(path)

    def test_duplicate_json_fields_rejected_before_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            path = Path(folder) / "bad.json"
            path.write_text('{"id": "keep", "id": "lost"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                workbench.load(path)

    def test_exponent_overflow_and_unsafe_integer_rejected_before_browser_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="writing-board-test-") as folder:
            path = Path(folder) / "bad.json"
            for raw, message in [('{"value": 1e999}', "Non-finite"),
                                 ('{"value": 9007199254740993}', "exact range")]:
                with self.subTest(raw=raw):
                    path.write_text(raw, encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, message):
                        workbench.load(path)

    def test_in_memory_nonfinite_and_unsafe_extension_values_rejected(self):
        self.packet["extensions"] = {"author_metadata": {"measurements": [float("inf")]}}
        self.assert_error("non-finite")
        self.packet["extensions"] = {"counter": 2**53 + 1}
        self.assert_error("exact range")

    def test_huge_declared_page_count_reports_gap_without_allocating_pages(self):
        self.packet["page_plan"]["interior_pages"] = 10**12
        self.assert_error("without gaps or overlaps")

    def test_bounds_and_unique_items_supported_by_local_schema_subset(self):
        self.assertTrue(workbench.schema_errors(4, {"type": "integer", "maximum": 3}, {}))
        self.assertTrue(workbench.schema_errors("", {"type": "string", "minLength": 1}, {}))
        self.assertTrue(workbench.schema_errors("four", {"type": "string", "maxLength": 3}, {}))
        self.assertTrue(workbench.schema_errors(["a", "b"], {"type": "array", "maxItems": 1}, {}))
        self.assertTrue(workbench.schema_errors([{"a": 1}, {"a": 1}], {"type": "array", "uniqueItems": True}, {}))

    def test_art_review_is_separate_from_layout_and_becomes_stale(self):
        self.packet["reviews"] = [{"id": "art-review", "kind": "art", "status": "passed",
                                   "reviewer": "Example art reviewer", "packet_revision": 1,
                                   "notes": "Checked prop support and character appearance in revision 1."}]
        self.assertEqual(self.report()["errors"], [])
        edited = copy.deepcopy(self.packet)
        edited["beats"][0]["visual_reveal"] = "A changed illustration brief."
        result = workbench.import_packet(self.packet, edited)
        self.assertEqual(result["reviews"][0]["status"], "stale")

    def test_original_sample_is_valid_and_not_marked_approved(self):
        folder = workbench.ROOT / "examples/rainy-day"
        packet = workbench.load(folder / "stories/pip-and-the-rain-map.json")
        bible = workbench.load(folder / "bible.json")
        report = workbench.check_packet(packet, known_ids={character["id"] for character in bible["characters"]})
        self.assertEqual(report["errors"], [])
        self.assertEqual(len(packet["page_plan"]["story_spreads"]), 6)
        self.assertEqual(packet["status"], "draft")
        self.assertTrue(all(review["status"] == "pending" for review in packet["reviews"]))
        self.assertTrue(packet["purpose"]["teaching_goal"])
        self.assertTrue(packet["props"] and packet["knowledge"] and packet["relationships"])
        self.assertEqual(packet["open_threads"][0]["status"], "resolved")


if __name__ == "__main__":
    unittest.main()
