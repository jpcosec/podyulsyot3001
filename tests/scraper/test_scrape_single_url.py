from src.scraper.scrape_single_url import (
    detect_english_status,
    extract_full_text_markdown,
    parse_structured_from_markdown,
)


SAMPLE_HTML = """
<html>
  <head><title>Job Posting III-51/26: Research Assistant – Job Postings at Technische Universität Berlin</title></head>
  <body>
    <main>
      <h1>Research Assistant</h1>
      <h2>Your responsibility</h2>
      <ul>
        <li>Build FAIR-compliant hybrid modelling workflows</li>
        <li>Support reproducible experimentation</li>
      </ul>
      <h2>Your profile</h2>
      <ul>
        <li>Strong Python skills</li>
        <li>Experience with workflow orchestration tools (e.g. Airflow)</li>
      </ul>
      <h2>How to apply</h2>
      <p>Please apply by email to sekretariat@example.org quoting the reference number.</p>
      <h2>Contact</h2>
      <table>
        <tr><th>Reference number</th><td>III-51/26</td></tr>
        <tr><th>Application deadline</th><td>20.03.2026</td></tr>
        <tr><th>Category</th><td>Research assistant</td></tr>
        <tr><th>Duration</th><td>limited for 3 years</td></tr>
        <tr><th>Salary</th><td>Salary grade 13 TV-L Berliner Hochschulen</td></tr>
        <tr><th>Contact person</th><td>Dr. M. Nicolas Cruz Bournazou</td></tr>
        <tr><th>Contact email</th><td>sekretariat@example.org</td></tr>
      </table>
    </main>
  </body>
</html>
"""


def test_extract_and_parse_structured_markdown():
    url = "https://www.jobs.tu-berlin.de/en/job-postings/201084"
    markdown = extract_full_text_markdown(SAMPLE_HTML, url=url)
    assert "## Your profile" in markdown
    assert "- Strong Python skills" in markdown

    language = detect_english_status(markdown)
    assert language["is_english"] is True

    structured = parse_structured_from_markdown(markdown, url=url, job_id="201084")
    assert structured["reference_number"] == "III-51/26"
    assert structured["deadline"] == "20.03.2026"
    assert structured["contact_person"] == "Dr. M. Nicolas Cruz Bournazou"
    assert structured["contact_email"] == "sekretariat@example.org"
    assert len(structured["requirements"]) == 2
    assert len(structured["responsibilities"]) == 2
