"""Tests for the redesigned CLI using new step-based structure."""

from src.cli.pipeline import _build_parser, _is_archive_marked, _is_continue_marked


def test_parse_job_ingest_defaults():
    """Test: pipeline job 201084 ingest"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "ingest"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "ingest"
    assert args.source == "tu_berlin"
    assert args.force is False


def test_parse_job_match_defaults():
    """Test: pipeline job 201084 match"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "match"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "match"
    assert args.force is False


def test_parse_job_render_defaults():
    """Test: pipeline job 201084 render"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "render"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "render"
    assert args.via == "docx"
    assert args.docx_template == "modern"
    assert args.language == "english"


def test_parse_job_render_custom_options():
    """Test: pipeline job 201084 render --via latex --language german"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "job",
            "201084",
            "render",
            "--via",
            "latex",
            "--language",
            "german",
            "--force",
        ]
    )

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "render"
    assert args.via == "latex"
    assert args.language == "german"
    assert args.force is True


def test_parse_job_package_defaults():
    """Test: pipeline job 201084 package"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "package"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "package"
    assert args.force is False


def test_parse_job_status():
    """Test: pipeline job 201084 status"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "status"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "status"


def test_parse_job_run():
    """Test: pipeline job 201084 run"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "run"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "run"
    assert args.resume is False


def test_parse_job_run_resume():
    """Test: pipeline job 201084 run --resume"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "run", "--resume"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "run"
    assert args.resume is True


def test_parse_job_graph_status():
    """Test: pipeline job 201084 graph-status"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "graph-status"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "graph-status"


def test_parse_job_regenerate():
    """Test: pipeline job 201084 regenerate matching"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "regenerate", "matching"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "regenerate"
    assert args.regenerate_step == "matching"


def test_parse_job_validate_ats():
    """Test: pipeline job 201084 validate-ats"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "validate-ats"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "validate-ats"
    assert args.ats_target == "pdf"


def test_parse_job_validate_ats_docx():
    """Test: pipeline job 201084 validate-ats --ats-target docx"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "validate-ats", "--ats-target", "docx"])

    assert args.command == "job"
    assert args.verb == "validate-ats"
    assert args.ats_target == "docx"


def test_parse_job_template_test():
    """Test: pipeline job 201084 template-test"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "template-test"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "template-test"
    assert args.target == "pdf"
    assert args.require_perfect is False


def test_parse_job_template_test_require_perfect():
    """Test: pipeline job 201084 template-test --require-perfect"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "template-test", "--require-perfect"])

    assert args.command == "job"
    assert args.verb == "template-test"
    assert args.require_perfect is True


def test_parse_jobs_list_defaults():
    """Test: pipeline jobs"""
    parser = _build_parser()
    args = parser.parse_args(["jobs"])

    assert args.command == "jobs"
    assert args.expiring is None
    assert args.expired is False
    assert args.keyword is None
    assert args.category is None


def test_parse_jobs_expiring():
    """Test: pipeline jobs --expiring 7"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--expiring", "7"])

    assert args.command == "jobs"
    assert args.expiring == 7
    assert args.expired is False


def test_parse_jobs_expired():
    """Test: pipeline jobs --expired"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--expired"])

    assert args.command == "jobs"
    assert args.expired is True


def test_parse_jobs_keyword():
    """Test: pipeline jobs --keyword bioprocess"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--keyword", "bioprocess"])

    assert args.command == "jobs"
    assert args.keyword == "bioprocess"


def test_parse_jobs_category():
    """Test: pipeline jobs --category research"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--category", "research"])

    assert args.command == "jobs"
    assert args.category == "research"


def test_parse_jobs_filter_by_keyword_alias():
    """Test: pipeline jobs --filter-by-keyword bioprocess"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--filter-by-keyword", "bioprocess"])

    assert args.command == "jobs"
    assert args.filter_by_keyword == "bioprocess"


def test_parse_jobs_filter_by_property():
    """Test: pipeline jobs --filter-by-property category=Student assistant"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "jobs",
            "--filter-by-property",
            "category=Student assistant",
        ]
    )

    assert args.command == "jobs"
    assert args.filter_by_property == "category=Student assistant"


def test_parse_run_marked_defaults():
    """Test: pipeline run-marked"""
    parser = _build_parser()
    args = parser.parse_args(["run-marked"])

    assert args.command == "run-marked"
    assert args.tags == "continue,yes"
    assert args.mode == "next"
    assert args.force is False


def test_parse_run_marked_custom():
    """Test: pipeline run-marked --tags review,comments --mode all --force"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "run-marked",
            "--tags",
            "review,comments",
            "--mode",
            "all",
            "--force",
        ]
    )

    assert args.command == "run-marked"
    assert args.tags == "review,comments"
    assert args.mode == "all"
    assert args.force is True


def test_parse_ingest_url_single():
    """Test: pipeline ingest-url <url>"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "ingest-url",
            "https://www.jobs.tu-berlin.de/en/job-postings/201084",
        ]
    )

    assert args.command == "ingest-url"
    assert args.urls == ["https://www.jobs.tu-berlin.de/en/job-postings/201084"]


def test_parse_ingest_url_multiple():
    """Test: pipeline ingest-url <url1> <url2>"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "ingest-url",
            "https://www.jobs.tu-berlin.de/en/job-postings/201084",
            "https://www.jobs.tu-berlin.de/en/job-postings/201085",
        ]
    )

    assert args.command == "ingest-url"
    assert len(args.urls) == 2


def test_parse_ingest_listing():
    """Test: pipeline ingest-listing <url>"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "ingest-listing",
            "https://www.jobs.tu-berlin.de/en/job-postings",
        ]
    )

    assert args.command == "ingest-listing"
    assert args.url == "https://www.jobs.tu-berlin.de/en/job-postings"
    assert args.delay == 0.5


def test_parse_ingest_listing_with_delay():
    """Test: pipeline ingest-listing <url> --delay 1.5"""
    parser = _build_parser()
    args = parser.parse_args(
        [
            "ingest-listing",
            "https://www.jobs.tu-berlin.de/en/job-postings",
            "--delay",
            "1.5",
        ]
    )

    assert args.command == "ingest-listing"
    assert args.delay == 1.5


def test_parse_archive_specific_job():
    """Test: pipeline archive 201084"""
    parser = _build_parser()
    args = parser.parse_args(["archive", "201084"])

    assert args.command == "archive"
    assert args.job_id == "201084"
    assert args.expired is False


def test_parse_archive_expired():
    """Test: pipeline archive --expired"""
    parser = _build_parser()
    args = parser.parse_args(["archive", "--expired"])

    assert args.command == "archive"
    assert args.expired is True


def test_parse_archive_marked():
    """Test: pipeline archive --marked"""
    parser = _build_parser()
    args = parser.parse_args(["archive", "--marked"])

    assert args.command == "archive"
    assert args.marked is True


def test_is_archive_marked_by_boolean_property():
    """Frontmatter archive: true should trigger archiving."""
    assert _is_archive_marked({"archive": "true"}) is True


def test_is_archive_marked_by_status():
    """Frontmatter status: archived should trigger archiving."""
    assert _is_archive_marked({"status": "archived"}) is True


def test_is_archive_marked_by_tags():
    """Frontmatter tags containing archive should trigger archiving."""
    assert _is_archive_marked({"tags": ["urgent", "#archive"]}) is True


def test_is_archive_marked_false_without_marker():
    """No archive marker should not trigger archiving."""
    assert _is_archive_marked({"status": "Open", "tags": ["review"]}) is False


def test_is_continue_marked_by_tag():
    """Tags containing continue should trigger continuation marker."""
    assert _is_continue_marked({"tags": ["continue"]}, {"continue", "yes"}) is True


def test_is_continue_marked_by_boolean_property():
    """continue: true should trigger continuation marker."""
    assert _is_continue_marked({"continue": "true"}, {"continue", "yes"}) is True


def test_is_continue_marked_false_without_marker():
    """No continue marker should not trigger continuation marker."""
    assert _is_continue_marked({"tags": ["review"]}, {"continue", "yes"}) is False


def test_parse_index():
    """Test: pipeline index"""
    parser = _build_parser()
    args = parser.parse_args(["index"])

    assert args.command == "index"


def test_parse_backup():
    """Test: pipeline backup"""
    parser = _build_parser()
    args = parser.parse_args(["backup"])

    assert args.command == "backup"
