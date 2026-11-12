"""Tests for athf.core.template_engine - hunt template rendering."""

import pytest
import yaml

from athf.core.template_engine import render_hunt_template, yaml_flow_seq, yaml_str


def _frontmatter(content: str) -> dict:
    """Parse the YAML frontmatter the way every consumer of a hunt file does."""
    assert content.startswith("---\n"), content[:40]
    block = content.split("\n---", 1)[0][4:]
    return yaml.safe_load(block)


@pytest.mark.unit
class TestRenderHuntTemplate:
    """Test the render_hunt_template function."""

    def test_hypothesis_duration_included_when_provided(self):
        """hypothesis_duration_minutes appears in frontmatter when passed."""
        content = render_hunt_template(
            hunt_id="H-0099",
            title="Test Hunt",
            technique="T1003.001",
            hypothesis_duration_minutes=2.3,
        )

        assert "hypothesis_duration_minutes: 2.3" in content

    def test_hypothesis_duration_omitted_when_not_provided(self):
        """hypothesis_duration_minutes is absent from frontmatter when None."""
        content = render_hunt_template(
            hunt_id="H-0099",
            title="Test Hunt",
            technique="T1003.001",
        )

        assert "hypothesis_duration_minutes" not in content

    def test_hypothesis_duration_omitted_when_zero(self):
        """hypothesis_duration_minutes=0 is falsy, should be omitted."""
        content = render_hunt_template(
            hunt_id="H-0099",
            title="Test Hunt",
            technique="T1003.001",
            hypothesis_duration_minutes=0,
        )

        # Jinja2 treats 0 as falsy, so the field should not appear
        assert "hypothesis_duration_minutes" not in content

    def test_hypothesis_duration_with_spawned_from(self):
        """Both spawned_from and hypothesis_duration_minutes render correctly."""
        content = render_hunt_template(
            hunt_id="H-0099",
            title="Test Hunt",
            technique="T1003.001",
            spawned_from="R-0019",
            hypothesis_duration_minutes=0.8,
        )

        assert "spawned_from: R-0019" in content
        assert "hypothesis_duration_minutes: 0.8" in content

    def test_basic_template_renders(self):
        """Sanity check: basic template renders with required fields."""
        content = render_hunt_template(
            hunt_id="H-0001",
            title="Basic Hunt",
        )

        assert "hunt_id: H-0001" in content
        assert "status: planning" in content
        assert _frontmatter(content)["title"] == "Basic Hunt"


@pytest.mark.unit
class TestYamlQuoting:
    """The scalar and sequence helpers emit YAML that round-trips as typed."""

    def test_yaml_str_is_a_valid_double_quoted_scalar(self):
        value = 'AT&T <x> café: it\'s "quoted"\nsecond line'
        assert yaml.safe_load(f"k: {yaml_str(value)}")["k"] == value

    def test_yaml_str_does_not_escape_readable_characters(self):
        """Hunt files are grepped and diffed; ``rg café`` has to keep finding them."""
        assert yaml_str("café & <x>") == '"café & <x>"'

    def test_yaml_flow_seq_keeps_every_element_a_string(self):
        values = ["EDR telemetry - Fields: process.name", "CloudTrail, S3", "José & co", "[bracketed]"]
        assert yaml.safe_load(f"k: {yaml_flow_seq(values)}")["k"] == values

    def test_yaml_flow_seq_empty(self):
        assert yaml_flow_seq(None) == "[]"
        assert yaml_flow_seq([]) == "[]"


@pytest.mark.unit
class TestFrontmatterRoundTrip:
    """Everything ``hunt new`` writes must parse back to what was typed.

    Bare values are the failure mode here, and it is a quiet one: a colon in a
    list element turns a string into a mapping, a bracketed hunter placeholder
    becomes a list, and ``yaml.safe_load`` raises for none of it.
    """

    def test_list_fields_survive_colons_commas_and_non_ascii(self):
        data_sources = ["EDR telemetry - Fields: process.name", "CloudTrail, S3", "José's SIEM & co"]
        platform = ["Windows", "macOS: Sonoma"]
        tactics = ["credential-access", "defense-evasion, kind of"]

        content = render_hunt_template(
            hunt_id="H-0100",
            title="List fields",
            tactics=tactics,
            platform=platform,
            data_sources=data_sources,
        )

        fm = _frontmatter(content)
        assert fm["data_sources"] == data_sources
        assert fm["platform"] == platform
        assert fm["tactics"] == tactics

    def test_title_and_hunter_survive_colons_quotes_and_non_ascii(self):
        title = 'Endpoint Suppression: Defender Abuse and "macOS" Stripping (AT&T, café)'
        hunter = "José Marrone: on call"

        content = render_hunt_template(hunt_id="H-0101", title=title, hunter=hunter)

        fm = _frontmatter(content)
        assert fm["title"] == title
        assert fm["hunter"] == hunter
        # The markdown heading is prose, not YAML: it stays unquoted.
        assert f"# H-0101: {title}" in content

    def test_default_hunter_placeholder_is_a_string_not_a_list(self):
        """``hunter: [Your Name]`` bare is a one-element list to YAML."""
        content = render_hunt_template(hunt_id="H-0102", title="Default hunter")
        assert isinstance(_frontmatter(content)["hunter"], str)

    def test_stale_workspace_snapshot_gets_the_fix(self, tmp_path, monkeypatch):
        """A ``templates/HUNT_TEMPLATE.j2`` snapshotted before the fix still writes valid YAML.

        ``athf init`` copies the bundled template into the workspace and that
        copy wins, so fixing the bundled template alone leaves every existing
        workspace on the old, bare form. The repair happens on the rendered
        output so the snapshot does not need to be touched.
        """
        monkeypatch.chdir(tmp_path)
        (tmp_path / "templates").mkdir()
        # The pre-fix bundled template emitted these fields bare. Pinned here
        # rather than derived from HUNT_TEMPLATE so the test keeps describing
        # the old form after the bundled template moves on.
        stale = (
            "{#- Customizable Jinja2 template for 'athf hunt new' -#}\n"
            "---\n"
            "hunt_id: {{ hunt_id }}\n"
            "title: {{ title }}\n"
            "status: {{ status }}\n"
            "date: {{ date }}\n"
            "hunter: {{ hunter }}\n"
            "platform: {{ platform }}\n"
            "tactics: {{ tactics }}\n"
            "techniques: {{ techniques }}\n"
            "data_sources: {{ data_sources }}\n"
            "tags: {{ tags }}\n"
            "---\n"
            "\n"
            "# {{ hunt_id }}: {{ title }}\n"
        )
        (tmp_path / "templates" / "HUNT_TEMPLATE.j2").write_text(stale, encoding="utf-8")

        title = "Technique: Variant"
        content = render_hunt_template(
            hunt_id="H-0103",
            title=title,
            hunter="A: B",
            data_sources=["EDR - Fields: process.name"],
        )

        fm = _frontmatter(content)
        assert fm["title"] == title
        assert fm["hunter"] == "A: B"
        assert fm["data_sources"] == ["EDR - Fields: process.name"]

    def test_custom_template_that_already_quotes_is_left_alone(self, tmp_path, monkeypatch):
        """A workspace that fixed its own snapshot must not end up double-quoted."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "templates").mkdir()
        custom = (
            "---\n"
            "hunt_id: {{ hunt_id }}\n"
            "title: {{ title | tojson }}\n"
            'hunter: "{{ hunter }}"\n'
            "platform: {{ platform }}\n"
            "---\n"
            "\n"
            "# {{ hunt_id }}: {{ title }}\n"
        )
        (tmp_path / "templates" / "HUNT_TEMPLATE.j2").write_text(custom, encoding="utf-8")

        content = render_hunt_template(hunt_id="H-0104", title="Plain title", hunter="Plain Hunter")

        fm = _frontmatter(content)
        assert fm["title"] == "Plain title"
        assert fm["hunter"] == "Plain Hunter"
        assert '""' not in content.split("\n---", 1)[0]
