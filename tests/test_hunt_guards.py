"""Tests for fool-proof guards."""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from athf.core.hunt_guards import (
    find_hunt_directory,
    parse_user_date,
    validate_date_range,
    check_period_compatibility,
    suggest_date_range,
    analyze_hunt_statuses,
    check_negative_durations,
)


class TestParseUserDate:
    """Test flexible date parsing."""

    def test_iso_format(self):
        """Parse ISO 8601 format (YYYY-MM-DD)."""
        assert parse_user_date('2024-01-15') == date(2024, 1, 15)

    def test_us_format(self):
        """Parse US format (MM/DD/YYYY)."""
        assert parse_user_date('01/15/2024') == date(2024, 1, 15)

    def test_eu_format(self):
        """Parse EU format (DD/MM/YYYY)."""
        assert parse_user_date('15/01/2024') == date(2024, 1, 15)

    def test_compact_format(self):
        """Parse compact format (YYYYMMDD)."""
        assert parse_user_date('20240115') == date(2024, 1, 15)

    def test_invalid_format(self):
        """Return None for unparseable format."""
        assert parse_user_date('not-a-date') is None

    def test_invalid_date(self):
        """Return None for invalid date values."""
        assert parse_user_date('2024-13-45') is None

    def test_ambiguous_us_vs_eu(self):
        """US format wins on ambiguous dates (01/02/2024 = Jan 2, not Feb 1)."""
        result = parse_user_date('01/02/2024')
        assert result == date(2024, 1, 2)

    def test_leap_year(self):
        """Handle leap year dates correctly."""
        assert parse_user_date('2024-02-29') == date(2024, 2, 29)

    def test_non_leap_year(self):
        """Reject invalid leap day."""
        assert parse_user_date('2023-02-29') is None

    def test_empty_string(self):
        """Return None for empty string."""
        assert parse_user_date('') is None


class TestValidateDateRange:
    """Test date range validation."""

    def test_valid_range(self):
        """Accept valid date range."""
        is_valid, msg = validate_date_range(
            date(2024, 1, 1),
            date(2024, 12, 31)
        )
        assert is_valid
        assert msg is None

    def test_reversed_dates(self):
        """Reject start date after end date."""
        is_valid, msg = validate_date_range(
            date(2024, 12, 31),
            date(2024, 1, 1)
        )
        assert not is_valid
        assert "after end date" in msg
        assert "2024-12-31" in msg
        assert "2024-01-01" in msg

    def test_same_date(self):
        """Accept same start and end date (single day range)."""
        is_valid, msg = validate_date_range(
            date(2024, 1, 1),
            date(2024, 1, 1)
        )
        assert is_valid
        assert msg is None

    def test_large_range_warning(self):
        """Warn on ranges > 2 years."""
        is_valid, msg = validate_date_range(
            date(2022, 1, 1),
            date(2024, 12, 31)
        )
        assert is_valid
        assert msg is not None
        assert "years" in msg
        assert "1096" in msg or "3.0" in msg  # 1096 days = 3.0 years

    def test_exactly_two_years(self):
        """No warning at exactly 730 days (boundary)."""
        is_valid, msg = validate_date_range(
            date(2022, 1, 1),
            date(2024, 1, 1)
        )
        assert is_valid
        assert msg is None

    def test_just_over_two_years(self):
        """Warn at 731 days."""
        is_valid, msg = validate_date_range(
            date(2022, 1, 1),
            date(2024, 1, 2)
        )
        assert is_valid
        assert msg is not None
        assert "731" in msg


class TestCheckPeriodCompatibility:
    """Test period comparison validation."""

    def test_quarter_to_quarter(self):
        """Allow comparing quarters."""
        is_compat, msg = check_period_compatibility('2024-Q4', '2024-Q3')
        assert is_compat
        assert msg is None

    def test_year_to_year(self):
        """Allow comparing years."""
        is_compat, msg = check_period_compatibility('2024', '2023')
        assert is_compat
        assert msg is None

    def test_quarter_to_year(self):
        """Reject comparing quarter to full year."""
        is_compat, msg = check_period_compatibility('2024-Q4', '2023')
        assert not is_compat
        assert "Cannot compare" in msg
        assert "quarter to full year" in msg

    def test_year_to_quarter(self):
        """Reject comparing year to quarter."""
        is_compat, msg = check_period_compatibility('2024', '2024-Q3')
        assert not is_compat
        assert "Cannot compare" in msg

    def test_same_quarter(self):
        """Allow comparing same quarter (edge case for testing)."""
        is_compat, msg = check_period_compatibility('2024-Q4', '2024-Q4')
        assert is_compat

    def test_arbitrary_quarter_format(self):
        """Work with different quarter numbers."""
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            is_compat, msg = check_period_compatibility(f'2024-{q}', f'2023-{q}')
            assert is_compat


class TestSuggestDateRange:
    """Test date range suggestion."""

    def test_suggests_latest_quarter(self):
        """Suggest quarter containing latest hunt."""
        hunts = [
            {'date': '2024-01-15'},
            {'date': '2024-10-20'},  # Q4
            {'date': '2024-11-10'},  # Q4
        ]

        suggestion, earliest, latest = suggest_date_range(hunts)
        assert suggestion == '2024-Q4'
        assert earliest == date(2024, 1, 15)
        assert latest == date(2024, 11, 10)

    def test_q1_jan(self):
        """Q1 for January."""
        hunts = [{'date': '2024-01-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q1'

    def test_q1_feb(self):
        """Q1 for February."""
        hunts = [{'date': '2024-02-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q1'

    def test_q1_mar(self):
        """Q1 for March."""
        hunts = [{'date': '2024-03-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q1'

    def test_q2_apr(self):
        """Q2 for April."""
        hunts = [{'date': '2024-04-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q2'

    def test_q3_jul(self):
        """Q3 for July."""
        hunts = [{'date': '2024-07-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q3'

    def test_q4_dec(self):
        """Q4 for December."""
        hunts = [{'date': '2024-12-15'}]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q4'

    def test_empty_hunts(self):
        """Return None for empty hunt list."""
        result = suggest_date_range([])
        assert result is None

    def test_hunts_without_dates(self):
        """Return None when no valid dates."""
        hunts = [
            {'title': 'No date'},
            {'date': 'invalid'},
            {'date': None},
        ]
        result = suggest_date_range(hunts)
        assert result is None

    def test_mixed_valid_invalid_dates(self):
        """Ignore invalid dates, use valid ones."""
        hunts = [
            {'date': '2024-10-15'},
            {'date': 'invalid'},
            {'date': None},
        ]
        suggestion, _, _ = suggest_date_range(hunts)
        assert suggestion == '2024-Q4'


class TestAnalyzeHuntStatuses:
    """Test status analysis."""

    def test_counts_statuses(self):
        """Count hunts by status."""
        hunts = [
            {'status': 'completed'},
            {'status': 'completed'},
            {'status': 'planning'},
            {'status': 'in-progress'},
        ]

        statuses = analyze_hunt_statuses(hunts)
        assert statuses['completed'] == 2
        assert statuses['planning'] == 1
        assert statuses['in-progress'] == 1

    def test_unknown_status(self):
        """Count missing status as 'unknown'."""
        hunts = [{'title': 'No status'}]
        statuses = analyze_hunt_statuses(hunts)
        assert statuses['unknown'] == 1

    def test_empty_list(self):
        """Return empty dict for no hunts."""
        statuses = analyze_hunt_statuses([])
        assert statuses == {}

    def test_all_same_status(self):
        """Handle all hunts with same status."""
        hunts = [
            {'status': 'completed'},
            {'status': 'completed'},
            {'status': 'completed'},
        ]
        statuses = analyze_hunt_statuses(hunts)
        assert statuses == {'completed': 3}

    def test_many_different_statuses(self):
        """Handle many different status values."""
        hunts = [
            {'status': 'planning'},
            {'status': 'research'},
            {'status': 'in-progress'},
            {'status': 'review'},
            {'status': 'completed'},
        ]
        statuses = analyze_hunt_statuses(hunts)
        assert len(statuses) == 5
        assert all(count == 1 for count in statuses.values())


class TestCheckNegativeDurations:
    """Test negative duration detection."""

    def test_finds_negative_duration(self):
        """Detect completed_date before start date."""
        hunts = [
            {
                'hunt_id': 'H-0001',
                'status': 'completed',
                'date': '2024-01-15',
                'completed_date': '2024-01-10',  # 5 days before start!
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 1
        assert negative[0][0] == 'H-0001'
        assert negative[0][1] == -5

    def test_ignores_valid_duration(self):
        """Accept normal forward duration."""
        hunts = [
            {
                'hunt_id': 'H-0002',
                'status': 'completed',
                'date': '2024-01-10',
                'completed_date': '2024-01-15',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_ignores_non_completed(self):
        """Only check completed hunts."""
        hunts = [
            {
                'hunt_id': 'H-0003',
                'status': 'planning',
                'date': '2024-01-15',
                'completed_date': '2024-01-10',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_ignores_in_progress(self):
        """Ignore in-progress hunts even with dates."""
        hunts = [
            {
                'hunt_id': 'H-0004',
                'status': 'in-progress',
                'date': '2024-01-15',
                'completed_date': '2024-01-10',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_multiple_negative(self):
        """Find all negative durations."""
        hunts = [
            {
                'hunt_id': 'H-0001',
                'status': 'completed',
                'date': '2024-01-15',
                'completed_date': '2024-01-10',
            },
            {
                'hunt_id': 'H-0002',
                'status': 'completed',
                'date': '2024-02-20',
                'completed_date': '2024-02-18',
            },
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 2
        assert negative[0][0] == 'H-0001'
        assert negative[1][0] == 'H-0002'

    def test_missing_dates(self):
        """Ignore hunts with missing date fields."""
        hunts = [
            {
                'hunt_id': 'H-0005',
                'status': 'completed',
                'date': '2024-01-15',
                # missing completed_date
            },
            {
                'hunt_id': 'H-0006',
                'status': 'completed',
                # missing date
                'completed_date': '2024-01-15',
            },
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_invalid_date_format(self):
        """Ignore hunts with unparseable dates."""
        hunts = [
            {
                'hunt_id': 'H-0007',
                'status': 'completed',
                'date': 'not-a-date',
                'completed_date': '2024-01-10',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_zero_duration(self):
        """Accept zero-day duration (same-day completion)."""
        hunts = [
            {
                'hunt_id': 'H-0008',
                'status': 'completed',
                'date': '2024-01-15',
                'completed_date': '2024-01-15',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 0

    def test_unknown_hunt_id(self):
        """Handle missing hunt_id."""
        hunts = [
            {
                'status': 'completed',
                'date': '2024-01-15',
                'completed_date': '2024-01-10',
            }
        ]

        negative = check_negative_durations(hunts)
        assert len(negative) == 1
        assert negative[0][0] == 'Unknown'


class TestFindHuntDirectory:
    """Test hunt directory discovery."""

    def test_finds_local_directory(self, tmp_path, monkeypatch):
        """Find hunts/production in current directory."""
        hunt_dir = tmp_path / "hunts" / "production"
        hunt_dir.mkdir(parents=True)

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv('ATHF_HUNT_DIR', raising=False)
        monkeypatch.setattr(Path, 'home', lambda: tmp_path / "fakehome")
        result = find_hunt_directory()
        # Function returns relative path, resolve it for comparison
        assert result.resolve() == hunt_dir

    def test_finds_sibling_hunt_vault(self, tmp_path, monkeypatch):
        """Find ../hunt-vault/hunts/production."""
        work_dir = tmp_path / "detect-vault"
        hunt_dir = tmp_path / "hunt-vault" / "hunts" / "production"

        work_dir.mkdir()
        hunt_dir.mkdir(parents=True)

        monkeypatch.chdir(work_dir)
        monkeypatch.delenv('ATHF_HUNT_DIR', raising=False)
        monkeypatch.setattr(Path, 'home', lambda: tmp_path / "fakehome")
        result = find_hunt_directory()
        # Function returns relative path, resolve it for comparison
        assert result.resolve() == hunt_dir

    def test_finds_home_directory(self, tmp_path, monkeypatch):
        """Find ~/athf/hunt-vault/hunts/production."""
        hunt_dir = tmp_path / "athf" / "hunt-vault" / "hunts" / "production"
        hunt_dir.mkdir(parents=True)

        # Ensure no local or sibling directories exist
        work_dir = tmp_path / "workdir"
        work_dir.mkdir()

        monkeypatch.chdir(work_dir)
        monkeypatch.delenv('ATHF_HUNT_DIR', raising=False)
        monkeypatch.setattr(Path, 'home', lambda: tmp_path)
        result = find_hunt_directory()
        assert result == hunt_dir

    def test_env_var_priority(self, tmp_path, monkeypatch):
        """ATHF_HUNT_DIR takes priority."""
        env_dir = tmp_path / "custom" / "hunts"
        local_dir = tmp_path / "hunts" / "production"

        env_dir.mkdir(parents=True)
        local_dir.mkdir(parents=True)

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv('ATHF_HUNT_DIR', str(env_dir))
        monkeypatch.setattr(Path, 'home', lambda: tmp_path / "fakehome")

        result = find_hunt_directory()
        assert result == env_dir

    def test_returns_none_if_not_found(self, tmp_path, monkeypatch):
        """Return None when no hunt directory exists."""
        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv('ATHF_HUNT_DIR', raising=False)
        monkeypatch.setattr(Path, 'home', lambda: tmp_path / "fakehome")

        result = find_hunt_directory()
        assert result is None

    def test_skips_non_directory(self, tmp_path, monkeypatch):
        """Skip if path exists but is not a directory."""
        fake_dir = tmp_path / "hunts" / "production"
        fake_dir.parent.mkdir(parents=True)
        fake_dir.touch()  # Create as file, not directory

        monkeypatch.chdir(tmp_path)
        monkeypatch.delenv('ATHF_HUNT_DIR', raising=False)
        monkeypatch.setattr(Path, 'home', lambda: tmp_path / "fakehome")
        result = find_hunt_directory()
        assert result is None


# Integration test
class TestGuardsIntegration:
    """Test guards working together."""

    def test_full_workflow(self):
        """Test typical usage workflow."""
        # Parse user input
        start = parse_user_date('01/01/2024')
        end = parse_user_date('12/31/2024')

        # Validate range
        is_valid, msg = validate_date_range(start, end)
        assert is_valid

        # Analyze hunts
        hunts = [
            {'hunt_id': 'H-0001', 'status': 'completed', 'date': '2024-10-15', 'completed_date': '2024-10-20'},
            {'hunt_id': 'H-0002', 'status': 'completed', 'date': '2024-11-01', 'completed_date': '2024-11-05'},
            {'hunt_id': 'H-0003', 'status': 'in-progress', 'date': '2024-11-15'},
        ]

        # Get suggestion
        suggestion, earliest, latest = suggest_date_range(hunts)
        assert suggestion == '2024-Q4'

        # Check statuses
        statuses = analyze_hunt_statuses(hunts)
        assert statuses['completed'] == 2
        assert statuses['in-progress'] == 1

        # Check for issues
        negative = check_negative_durations(hunts)
        assert len(negative) == 0
