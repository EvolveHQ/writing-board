"""Portable story planning, using only Python's standard library.

The local JSON schema uses a deliberately small documented subset of JSON Schema
(types, properties, required, refs, enums and basic limits). This is not a general
JSON Schema engine. Structural checks never approve prose, artwork or story continuity.
All writes require a new output path; project bibles are managed separately.
"""
from __future__ import annotations

import argparse
import copy
import csv
import io
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/story.schema.json"
TEMPLATE = ROOT / "templates/story.json"
COMPOSITION_FIELDS = ("focus", "framing", "word_contribution", "art_contribution", "text_zone", "gutter_notes")
MAX_SAFE_INTEGER = 2**53 - 1


def load(path):
    def invalid_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key would lose data: {key}")
            result[key] = value
        return result
    def finite_float(value):
        parsed = float(value)
        if not math.isfinite(parsed):
            raise ValueError(f"Non-finite JSON number: {value}")
        return parsed
    def safe_integer(value):
        parsed = int(value)
        if abs(parsed) > MAX_SAFE_INTEGER:
            raise ValueError("JSON integer exceeds the browser's exact range; encode precision-sensitive values as strings")
        return parsed
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=invalid_constant,
                      parse_float=finite_float, parse_int=safe_integer, object_pairs_hook=unique_keys)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def save_new(path, text):
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite {path}; choose a new output path")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def schema_errors(value, rule, definitions, path="$", errors=None):
    errors = [] if errors is None else errors
    if "$ref" in rule:
        return schema_errors(value, definitions[rule["$ref"].split("/")[-1]], definitions, path, errors)
    types = rule.get("type", [])
    types = [types] if isinstance(types, str) else types
    matches = {"object": isinstance(value, dict), "array": isinstance(value, list),
               "string": isinstance(value, str), "integer": type(value) is int,
               "number": type(value) in (int, float), "null": value is None, "boolean": type(value) is bool}
    if types and not any(matches[t] for t in types):
        errors.append(f"{path}: expected {' or '.join(types)}")
        return errors
    if type(value) is float and not math.isfinite(value):
        errors.append(f"{path}: non-finite number")
        return errors
    if type(value) is int and abs(value) > MAX_SAFE_INTEGER:
        errors.append(f"{path}: integer exceeds the browser's exact range")
        return errors
    if "const" in rule and value != rule["const"]:
        errors.append(f"{path}: expected {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        errors.append(f"{path}: expected one of {rule['enum']}")
    if isinstance(value, dict):
        for key in rule.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required field missing")
        properties = rule.get("properties", {})
        for key, child in value.items():
            if key in properties:
                schema_errors(child, properties[key], definitions, f"{path}.{key}", errors)
            elif rule.get("additionalProperties") is False:
                errors.append(f"{path}.{key}: unsupported field; retain author metadata in extensions")
            else:
                schema_errors(child, {}, definitions, f"{path}.{key}", errors)
    elif isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            errors.append(f"{path}: too few items")
        if len(value) > rule.get("maxItems", float("inf")):
            errors.append(f"{path}: too many items")
        if rule.get("uniqueItems") and any(value[index] in value[:index] for index in range(len(value))):
            errors.append(f"{path}: duplicate items")
        for index, child in enumerate(value):
            schema_errors(child, rule.get("items", {}), definitions, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            errors.append(f"{path}: string is too short")
        if len(value) > rule.get("maxLength", float("inf")):
            errors.append(f"{path}: string is too long")
        if "pattern" in rule and not re.search(rule["pattern"], value):
            errors.append(f"{path}: invalid stable identifier {value!r}")
    elif type(value) in (int, float):
        if value < rule.get("minimum", float("-inf")):
            errors.append(f"{path}: below minimum {rule['minimum']}")
        if value > rule.get("maximum", float("inf")):
            errors.append(f"{path}: above maximum {rule['maximum']}")
    return errors


def check_packet(packet, *, known_ids=None, schema=None):
    """Check packet structure and internal continuity, optionally against a bible cast.

    A standalone packet supplies its own character namespace through ``cast``.
    Speech modes, setting rules and source authority belong to project validation.
    """
    schema = load(SCHEMA) if schema is None else schema
    errors = schema_errors(packet, schema, schema["$defs"])
    warnings = []
    if errors:
        return {"errors": errors, "warnings": warnings, "editorial_status": "not_determined_by_cli"}
    known_ids = {c["character_id"] for c in packet["cast"]} if known_ids is None else set(known_ids)

    def unique(values, label):
        if len(values) != len(set(values)):
            errors.append(f"{label}: duplicate identifiers/order values")

    def reference(value, allowed, label):
        if value not in allowed:
            errors.append(f"{label}: unknown reference {value!r}")

    cast_ids = [c["character_id"] for c in packet["cast"]]
    unique(cast_ids, "cast")
    for character in packet["cast"]:
        reference(character["character_id"], known_ids, "cast")
        if character["age_years"] is not None:
            warnings.append(f"{character['character_id']}: explicit age needs authoritative source review; unknown ages must remain null")
    reference(packet["premise"]["protagonist_id"], cast_ids, "premise protagonist")
    locations = {p["id"] for p in packet["locations"]}
    unique([p["id"] for p in packet["locations"]], "locations")
    for location in packet["locations"]:
        if location["source_status"] == "canonical" and not location["source_ref"]:
            errors.append(f"{location['id']}: canonical location needs a source reference (still subject to source review)")
    beats = {b["id"]: b for b in packet["beats"]}
    reading_order = [b["id"] for b in packet["beats"]]
    unique(reading_order, "beats")
    unique([b["chronology"] for b in packet["beats"]], "beat chronology")
    first_chronology = min(b["chronology"] for b in packet["beats"])
    for beat in packet["beats"]:
        label = beat["id"]
        unique(beat["character_ids"], f"{label} cast")
        unique(beat["cause_from"], f"{label} causes")
        reference(beat["location_id"], locations, f"{label} location")
        for character in beat["character_ids"]:
            reference(character, cast_ids, f"{label} character")
        for cause in beat["cause_from"]:
            reference(cause, beats, f"{label} cause")
            if cause in beats and beats[cause]["chronology"] >= beat["chronology"]:
                errors.append(f"{label}: cause {cause} must be strictly earlier in chronology")
        for line in beat["dialogue"]:
            reference(line["speaker_id"], beat["character_ids"], f"{label} dialogue speaker")
            if line["kind"] == "nonverbal" and any(c in line["text"] for c in '\"“”«»„'):
                errors.append(f"{label}: nonverbal sound cues cannot contain quoted dialogue")
        empty = [k for k in ("action", "consequence", "emotion", "visual_reveal") if not beat[k].strip()]
        if empty:
            warnings.append(f"{label}: unfinished {', '.join(empty)}; structural validity does not make a story")
        if beat["chronology"] > first_chronology and not beat["cause_from"]:
            warnings.append(f"{label}: no causal predecessor recorded; review whether this is an intentional parallel event")
        if any(c in beat["text"] for c in '“”«»\"') and not beat["dialogue"]:
            warnings.append(f"{label}: quoted prose has no structured dialogue attribution; review voices manually")
    chronology = sorted(packet["beats"], key=lambda b: b["chronology"])
    if reading_order != [b["id"] for b in chronology]:
        warnings.append("Reading order differs from chronology; review flashback, anticipation and knowledge cues")
    for key, value in packet["premise"].items():
        if isinstance(value, str) and not value.strip():
            warnings.append(f"premise.{key}: not developed yet")
    if {b["act"] for b in packet["beats"]} != {"setup", "development", "resolution"}:
        warnings.append("Review the act progression: not all three planning acts are represented")

    plan = packet["page_plan"]
    front, back = plan["front_matter_pages"], plan["back_matter_pages"]
    if front != list(range(1, len(front) + 1)):
        errors.append("page_plan: front matter must occupy consecutive initial interior pages")
    if back != list(range(plan["interior_pages"] - len(back) + 1, plan["interior_pages"] + 1)):
        errors.append("page_plan: back matter must occupy consecutive final interior pages")
    unique([s["id"] for s in plan["story_spreads"]], "spreads")
    pages = list(plan["front_matter_pages"]) + list(plan["back_matter_pages"])
    spread_order = []
    for spread in sorted(plan["story_spreads"], key=lambda s: s["left_page"]):
        if spread["left_page"] % 2 or spread["right_page"] != spread["left_page"] + 1:
            errors.append(f"{spread['id']}: a physical spread needs an even left page and the next odd right page")
        pages += [spread["left_page"], spread["right_page"]]
        spread_order += spread["beat_ids"]
        for beat_id in spread["beat_ids"]:
            reference(beat_id, beats, f"{spread['id']} beat")
    if plan["interior_pages"] % 2:
        errors.append("page_plan: interior page count must be even; covers are separate")
    if len(pages) != plan["interior_pages"] or any(page != index for index, page in enumerate(sorted(pages), 1)):
        errors.append("page_plan: every physical interior page must occur exactly once, without gaps or overlaps")
    if spread_order != reading_order:
        errors.append("page_plan: each beat must occur once across physical spreads in current reading order")
    if plan["status"] == "needs_review":
        warnings.append("Page-turn/reveal notes need review after a composition change; no existing proof remains approved")

    def state_references(state, label):
        reference(state["location_id"], locations, label + " location")
        if state["holder_id"] is not None:
            reference(state["holder_id"], cast_ids, label + " holder")

    for group in ("props", "knowledge", "relationships"):
        unique([item["id"] for item in packet[group]], group)
        for item in packet[group]:
            label = f"{group}.{item['id']}"
            if group == "props":
                state_references(item["initial_state"], label + " initial")
            elif group == "knowledge":
                reference(item["character_id"], cast_ids, label + " character")
            else:
                reference(item["from_id"], cast_ids, label + " from")
                reference(item["to_id"], cast_ids, label + " to")
                if item["from_id"] == item["to_id"]:
                    errors.append(label + ": a relationship needs two different characters")
            unique([c["beat_id"] for c in item["changes"]], label + " changes")
            expected = item["initial_state"]
            changes = sorted(item["changes"], key=lambda c: beats.get(c["beat_id"], {}).get("chronology", 0))
            for change in changes:
                beat_id = change["beat_id"]
                reference(beat_id, beats, label + " change")
                if change["before"] != expected:
                    errors.append(f"{label} at {beat_id}: before-state drifts from previous chronological after-state")
                expected = change["after"]
                if group == "props":
                    state_references(change["before"], label + " before")
                    state_references(change["after"], label + " after")
                elif group == "knowledge":
                    if beat_id in beats and item["character_id"] not in beats[beat_id]["character_ids"]:
                        errors.append(f"{label}: {item['character_id']} is not present in learning beat {beat_id}; record the observed/reported learning event")
                    source = change["source_beat_id"]
                    if source is not None:
                        reference(source, beats, label + " knowledge source")
                        if source in beats and beat_id in beats and beats[source]["chronology"] > beats[beat_id]["chronology"]:
                            errors.append(f"{label}: knowledge comes from a future chronological event")
                    else:
                        warnings.append(f"{label} at {beat_id}: learning source unspecified; review how the character knows")

    for group in ("facts", "open_threads", "reviews", "proofs"):
        unique([item["id"] for item in packet[group]], group)
    for fact in packet["facts"]:
        if fact["status"] == "sourced" and not fact["source_ref"]:
            errors.append(f"{fact['id']}: a sourced fact needs a source reference; a packet label is not canon approval")
        for character in fact["character_ids"]:
            reference(character, cast_ids, f"{fact['id']} character")
        for beat in fact["beat_ids"]:
            reference(beat, beats, f"{fact['id']} beat")
    for thread in packet["open_threads"]:
        start, end = thread["introduced_beat_id"], thread["resolved_beat_id"]
        for beat in (start, end):
            if beat is not None:
                reference(beat, beats, f"{thread['id']} thread")
        if (thread["status"] == "resolved") != (end is not None):
            errors.append(f"{thread['id']}: resolved status and resolution beat must agree")
        if start in beats and end in beats and beats[end]["chronology"] < beats[start]["chronology"]:
            errors.append(f"{thread['id']}: thread resolves before its introduction")
        if thread["status"] == "open":
            warnings.append(f"{thread['id']}: unresolved story thread; review payoff or intentional continuation")
    for group, approved in (("reviews", "passed"), ("proofs", "reviewed")):
        for record in packet[group]:
            revision = record["packet_revision"]
            if revision is not None and revision > packet["revision"]:
                errors.append(f"{record['id']}: evidence points to a future packet revision")
            if record["status"] == approved:
                if revision != packet["revision"]:
                    errors.append(f"{record['id']}: stale {group} claim must be marked stale")
                if group == "reviews" and not (record["reviewer"] or "").strip():
                    errors.append(f"{record['id']}: a passed review needs a named reviewer")
    if plan["status"] == "reviewed" and not any(r["kind"] == "layout" and r["status"] == "passed" and
                                               r["packet_revision"] == packet["revision"] and r["reviewer"] for r in packet["reviews"]):
        errors.append("page_plan: reviewed status needs a current named layout review; structure alone is not review evidence")
    return {"errors": errors, "warnings": warnings, "editorial_status": "not_determined_by_cli"}


def require_valid(packet, *, known_ids=None, schema=None):
    report = check_packet(packet, known_ids=known_ids, schema=schema)
    if report["errors"]:
        raise ValueError("\n".join(report["errors"]))
    return report


def new_packet(story_id, title, protagonist, spreads=14, *, known_ids=None):
    """Make an unfinished, independently editable scaffold with a generic location."""
    if type(spreads) is not int or spreads < 1:
        raise ValueError("Spread count must be a positive integer")
    packet = load(TEMPLATE)
    packet.update(id=story_id, title=title)
    packet["premise"]["protagonist_id"] = protagonist
    packet["cast"][0]["character_id"] = protagonist
    if spreads != len(packet["page_plan"]["story_spreads"]):
        beat_template = packet["beats"][0]
        spread_template = packet["page_plan"]["story_spreads"][0]
        packet["beats"] = []
        packet["page_plan"]["story_spreads"] = []
        bookend = max(1, spreads // 4)
        for number in range(1, spreads + 1):
            beat = copy.deepcopy(beat_template)
            beat.update(id=f"beat-{number:02d}", chronology=number,
                        act="setup" if number <= bookend else "resolution" if number > spreads - bookend else "development",
                        cause_from=[] if number == 1 else [f"beat-{number - 1:02d}"])
            packet["beats"].append(beat)
            spread = copy.deepcopy(spread_template)
            spread.update(id=f"spread-{number:02d}", left_page=2 * number + 2,
                          right_page=2 * number + 3, beat_ids=[beat["id"]])
            packet["page_plan"]["story_spreads"].append(spread)
        packet["page_plan"].update(interior_pages=2 * spreads + 4,
                                   front_matter_pages=[1, 2, 3], back_matter_pages=[2 * spreads + 4])
    for beat in packet["beats"]:
        beat["character_ids"] = [protagonist]
    require_valid(packet, known_ids=known_ids)
    return packet


def invalidate_evidence(packet, revision):
    packet["revision"] = revision
    packet["status"] = "draft"
    packet["page_plan"]["status"] = "needs_review"
    for group in ("reviews", "proofs"):
        for record in packet[group]:
            record["status"] = "stale"
    packet.setdefault("extensions", {})["workbench_base_revision"] = revision


def reorder_packet(packet, request):
    require_valid(packet)
    required = {"schema_version", "packet_id", "base_revision", "reading_order"}
    if not isinstance(request, dict) or set(request) != required or type(request["schema_version"]) is not int or request["schema_version"] != 1 or type(request["base_revision"]) is not int:
        raise ValueError("Reorder request needs schema_version, packet_id, base_revision and reading_order only")
    if request["packet_id"] != packet["id"] or request["base_revision"] != packet["revision"]:
        raise ValueError("Stale or unrelated reorder request; reload the current packet")
    order = request["reading_order"]
    old = {beat["id"]: beat for beat in packet["beats"]}
    if not isinstance(order, list) or not all(isinstance(item, str) for item in order) or len(order) != len(old) or set(order) != set(old):
        raise ValueError("Reorder must name every existing beat ID exactly once")
    result = copy.deepcopy(packet)
    result["beats"] = [copy.deepcopy(old[key]) for key in order]
    offset = 0
    for spread in sorted(result["page_plan"]["story_spreads"], key=lambda s: s["left_page"]):
        count = len(spread["beat_ids"])
        spread["beat_ids"] = order[offset:offset + count]
        offset += count
    invalidate_evidence(result, packet["revision"] + 1)
    require_valid(result)
    return result


def import_packet(base, edited):
    require_valid(base)
    # Validate shape first; stale review claims are intentionally invalidated
    # before semantic checking. Unsupported future fields are never dropped.
    schema = load(SCHEMA)
    errors = schema_errors(edited, schema, schema["$defs"])
    if errors:
        raise ValueError("\n".join(errors))
    origin_revision = edited.get("extensions", {}).get("workbench_base_revision", edited["revision"])
    if edited["id"] != base["id"] or type(origin_revision) is not int or origin_revision != base["revision"]:
        raise ValueError("Stale or unrelated edited packet; reload the current base")
    original = {b["id"]: b["chronology"] for b in base["beats"]}
    changed = {b["id"]: b["chronology"] for b in edited["beats"]}
    if original != changed or len(edited["beats"]) != len(base["beats"]):
        raise ValueError("Board import must preserve every beat ID and chronology; edit the source packet deliberately to add events")
    result = copy.deepcopy(edited)
    invalidate_evidence(result, base["revision"] + 1)
    require_valid(result)
    return result


def md(value):
    return str(value).replace("|", "\\|").replace("\n", "<br>")


def csv_text(headers, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(headers)
    writer.writerows(rows)
    return stream.getvalue()


def state_text(value):
    if isinstance(value, dict):
        return f"{value['location_id']} / holder={value['holder_id'] or 'none'} / {value['condition']}"
    return value


def render_views(packet):
    report = require_valid(packet)
    header = f"# {packet['title']}\n\nPacket `{packet['id']}`, revision {packet['revision']}. Proposed development; structural checks do not approve editorial quality or canon.\n"
    sheets = [header, "\n## Story purpose\n\nEditorial intent, not measured learning outcomes.\n"]
    purpose = packet.get("purpose", {})
    for key, label in (("intent", "Purpose"), ("teaching_goal", "Teaching goal"),
                       ("lesson", "Lesson to take away"), ("theme", "Meaning / theme"),
                       ("delivery", "How the story delivers it")):
        value = packet["premise"]["theme"] if key == "theme" else purpose.get(key, "")
        sheets.append(f"\n**{label}:** {value or '[to develop]'}\n")
    sheets.append("\n## Premise\n")
    sheets += [f"- **{key.replace('_', ' ')}:** {value or '[to develop]'}\n" for key, value in packet["premise"].items()]
    sheets.append("\n## Beats in reading order\n")
    scene_rows = []
    for index, beat in enumerate(packet["beats"], 1):
        sheets.append(f"\n### {index}. {beat['id']} — {beat['act']}\n\nChronology: {beat['chronology']}. Location: {beat['location_id']}. Cast: {', '.join(beat['character_ids'])}.\n")
        for key in ("action", "consequence", "emotion", "visual_reveal", "text"):
            sheets.append(f"\n**{key.replace('_', ' ')}:** {beat[key] or '[to develop]'}\n")
        sheets.append(f"\n**Caused by:** {', '.join(beat['cause_from']) or 'opening / unspecified'}\n")
        for line in beat["dialogue"]:
            sheets.append(f"\n{line['speaker_id']} ({line['kind']}): {line['text']}\n")
        scene_rows.append([index, beat["id"], beat["chronology"], beat["act"], ", ".join(beat["character_ids"]), beat["location_id"],
                           beat["action"], beat["consequence"], beat["emotion"], beat["visual_reveal"], ", ".join(beat["cause_from"]), beat["text"]])
    sheets.append("\n## Development reminders\n\n")
    sheets += [f"- {warning}\n" for warning in report["warnings"]]
    if not report["warnings"]:
        sheets.append("No structural development reminders. See packet reviews for editorial and human checks.\n")
    timeline = [header, "\n## Chronology (independent of page order)\n\n| Event order | Beat | Reading position | Action | Consequence |\n|---|---|---|---|---|\n"]
    order = {b["id"]: i for i, b in enumerate(packet["beats"], 1)}
    for beat in sorted(packet["beats"], key=lambda b: b["chronology"]):
        timeline.append(f"| {beat['chronology']} | {beat['id']} | {order[beat['id']]} | {md(beat['action'])} | {md(beat['consequence'])} |\n")
    continuity = [header, "\n## Prop, knowledge and relationship changes\n"]
    chronology = {b["id"]: b["chronology"] for b in packet["beats"]}
    for group in ("props", "knowledge", "relationships"):
        for item in packet[group]:
            continuity.append(f"\n### {group}: {item['id']}\n\nInitial: {state_text(item['initial_state'])}\n\n| Beat | Before | After | Reason |\n|---|---|---|---|\n")
            for change in sorted(item["changes"], key=lambda c: chronology[c["beat_id"]]):
                continuity.append(f"| {change['beat_id']} | {md(state_text(change['before']))} | {md(state_text(change['after']))} | {md(change['reason'])} |\n")
    continuity.append("\n## Facts and open threads\n\nSourced labels are author claims to verify against the referenced authority. New material is not adopted by this export.\n")
    for fact in packet["facts"]:
        continuity.append(f"\n- {fact['id']} ({fact['status']}): {fact['statement']} — source: {fact['source_ref'] or 'proposed / unsourced'}\n")
    for thread in packet["open_threads"]:
        continuity.append(f"\n- {thread['id']} ({thread['status']}): {thread['question']} — introduced: {thread['introduced_beat_id']}; resolved: {thread['resolved_beat_id']}\n")
    composition = [header, f"\n## Physical page plan: {packet['page_plan']['status']}\n\n{packet['page_plan']['interior_pages']} interior pages. Covers are separate.\n\n",
                   f"Front matter: {packet['page_plan']['front_matter_pages']}. Back matter: {packet['page_plan']['back_matter_pages']}.\n\n",
                   "| Spread | Pages | Beats in reading order | Page turn | Reveal |\n|---|---|---|---|---|\n"]
    for spread in sorted(packet["page_plan"]["story_spreads"], key=lambda s: s["left_page"]):
        composition.append(f"| {spread['id']} | {spread['left_page']}–{spread['right_page']} | {', '.join(spread['beat_ids'])} | {md(spread['page_turn'])} | {md(spread['reveal'])} |\n")
    for spread in sorted(packet["page_plan"]["story_spreads"], key=lambda s: s["left_page"]):
        details = spread.get("composition", {})
        if details:
            composition.append(f"\n### {spread['id']} composition · pages {spread['left_page']}–{spread['right_page']}\n")
            for key in COMPOSITION_FIELDS:
                if key in details:
                    composition.append(f"\n**{key.replace('_', ' ').capitalize()}:** {details[key] or '[to develop]'}\n")
    arcs = {"packet_id": packet["id"], "revision": packet["revision"], "canon_adoption": "none", "cast": packet["cast"],
            "relationships": packet["relationships"], "facts": packet["facts"], "open_threads": packet["open_threads"], "localization_notes": packet["localization_notes"]}
    return {"beats.md": "".join(sheets), "scenes.csv": csv_text(["reading_position", "beat_id", "chronology", "act", "character_ids", "location_id", "action", "consequence", "emotion", "visual_reveal", "cause_from", "text"], scene_rows),
            "chronology.md": "".join(timeline), "continuity.md": "".join(continuity), "composition.md": "".join(composition),
            "arcs.json": json_text(arcs), "check.json": json_text(report), "packet.json": json_text(packet)}


def render_directory(packet, output):
    views = render_views(packet)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, text in views.items():
        save_new(output / name, text)


def render_collection(packets, output):
    ids = [p["id"] for p in packets]
    if len(ids) != len(set(ids)):
        raise ValueError("Collection packet IDs must be unique")
    # Prepare every view before creating the destination, so an invalid packet
    # cannot leave a misleading partially validated collection.
    views = [(packet, render_views(packet)) for packet in packets]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    rows, arcs = [], []
    for index, (packet, files) in enumerate(views, 1):
        for name, text in files.items():
            save_new(output / packet["id"] / name, text)
        for character in packet["cast"]:
            rows.append([index, packet["id"], packet["title"], character["character_id"], character["want"], character["need"], character["starting_state"], character["ending_state"]])
        arcs.append({"packet_id": packet["id"], "display_position": index, "chronological_date": None,
                     "relationships": packet["relationships"], "open_threads": packet["open_threads"]})
    save_new(output / "series-grid.csv", csv_text(["display_position_only", "packet_id", "title", "character_id", "want", "need", "starting_state", "ending_state"], rows))
    save_new(output / "series-arcs.json", json_text({"status": "proposed", "ordering": "input display order only; no cross-story chronology or dates inferred", "stories": arcs}))
    save_new(output / "README.md", "# Story development collection\n\nThese are editable development views. Input order is display order, not established series chronology. Unknown dates remain null. This export does not adopt story facts or relationships into a project bible.\n\n" + "".join(f"- [{p['title']}]({p['id']}/beats.md)\n" for p in packets))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Create an editable planning scaffold (32 interior pages by default)")
    for field in ("id", "title", "protagonist", "output"):
        new.add_argument("--" + field, required=True)
    new.add_argument("--spreads", type=int, default=14, help="Positive story-spread count; interior pages = 2 × spreads + 4 (default: 14)")
    check = sub.add_parser("check", help="Validate structure; report editorial reminders separately")
    check.add_argument("packets", nargs="+")
    check.add_argument("--json", action="store_true")
    for command in ("render", "render-all"):
        render = sub.add_parser(command, help="Export editable human planning views to a new directory")
        render.add_argument("packets", nargs="+" if command == "render-all" else 1)
        render.add_argument("--output", required=True)
    for command, option in (("reorder", "order"), ("import", "edited")):
        edit = sub.add_parser(command, help="Apply an edit to a new file and invalidate existing review/proof claims")
        edit.add_argument("packet")
        edit.add_argument("--" + option, required=True)
        edit.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            save_new(args.output, json_text(new_packet(args.id, args.title, args.protagonist, args.spreads)))
            print(f"Created editable draft: {args.output}. Premise and beats still need development.")
        elif args.command == "check":
            reports = [{"path": path, **check_packet(load(path))} for path in args.packets]
            if args.json:
                print(json_text(reports), end="")
            else:
                for report in reports:
                    print(f"{'FAIL' if report['errors'] else 'PASS structure'}: {report['path']}; {len(report['warnings'])} development reminders. Editorial acceptance is separate.")
                    for category in ("errors", "warnings"):
                        for message in report[category]:
                            print(f"  {category[:-1].upper()}: {message}")
            return 1 if any(r["errors"] for r in reports) else 0
        elif args.command in ("render", "render-all"):
            packets = [load(path) for path in args.packets]
            if args.command == "render":
                render_directory(packets[0], args.output)
            else:
                render_collection(packets, args.output)
            print(f"Rendered development views: {args.output}. No database or canon changes.")
        else:
            base = load(args.packet)
            result = reorder_packet(base, load(args.order)) if args.command == "reorder" else import_packet(base, load(args.edited))
            save_new(args.output, json_text(result))
            print(f"Saved revision {result['revision']}: {args.output}. Reviews/proofs stale; page plan needs review.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
