"""Tests for athf.core.template_engine - hunt template rendering."""

import pytest

from athf.core.template_engine import render_hunt_template


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
        assert "title: Basic Hunt" in content
        assert "status: planning" in content
