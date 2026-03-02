# ATS Resume Guidelines

**Scope:** Rules for generating ATS-compliant CV documents (DOCX and PDF) for European academic/research job applications.

Operational rule in this repository: generate final PDF, then validate ATS on PDF text (`--ats-target pdf`).

---

## What Is ATS Parsing

Most institutions route applications through an Applicant Tracking System (ATS) before a human reads anything. The ATS extracts plain text from your document and indexes it against job requirements. If the text extraction fails, your CV is invisible — regardless of how well-qualified you are.

ATS systems parse DOCX files by reading `document.paragraphs` in order (top to bottom). They skip:
- Table cell content
- Text inside text boxes or shapes
- Header / footer regions
- Image data (photos, icons, logos)
- Content inside multi-column section flows (behaviour varies — often scrambled)

---

## Hard Rules (Never Violate)

### Layout
- **Single column only.** Two-column layouts cause ATS to scramble reading order or drop content.
- **No tables.** Even a 1×2 table for "name left / photo right" makes your name invisible. Our own `extract_docx_text` skips tables — so does most ATS software.
- **No text boxes.** Content inside text boxes is not part of `doc.paragraphs` and is dropped.
- **No Word headers or footers for content.** Contact information placed in the Word header/footer region is missed by ~25% of ATS systems. Put everything in the document body.

### Content
- **Name and contact must be plain paragraphs** — the very first lines of the document body, before any section.
- **Standard section heading labels.** Use canonical names: `EXPERIENCE`, `EDUCATION`, `SKILLS`, `PUBLICATIONS`, `LANGUAGES`, `SUMMARY`. Creative alternatives (`What I've Built`, `Background`) confuse ATS categorisation.
- **No critical information inside images.** If your name, dates, or skills are only present as part of a graphic, they don't exist to the ATS.

### Typography
- **Standard fonts only.** Arial, Calibri, Garamond, Georgia, Helvetica. Decorative or custom fonts may render as gibberish when extracted.
- **Body text: 9.5–11 pt. Section headers: 11–13 pt.** Avoid extremes.
- **No special Unicode bullets or symbols.** Use `•` (U+2022) or `-`. Fancy glyphs (→, ★, ✔) are often stripped or misread.

---

## What Is Safe (ATS Reads Fine)

| Element | Safe? | Notes |
|---|---|---|
| Font colour | ✅ | Text is read regardless of colour |
| Bold / italic | ✅ | Ignored by ATS, useful for humans |
| Paragraph bottom border (section rule) | ✅ | Cosmetic only — paragraph text still parsed |
| Tab stops | ✅ | Right-aligned dates without a table |
| Inline images (photo) | ⚠️ | Skipped by ATS — safe **if no text inside the image** |
| Floating / anchored images | ⚠️ | Skipped by ATS — safe as long as no text is anchored inside |
| Colour fills on paragraphs | ✅ | Cosmetic, text still parsed |
| Page margins | ✅ | No effect on parsing |
| Line spacing | ✅ | No effect on parsing |

---

## Photo Policy

Photos are **ignored** by ATS — they become a zero-byte token during extraction. This means:

- A photo **does not hurt** ATS parsing, as long as no text lives inside it.
- A photo inside a **table** does hurt parsing (the whole table cell is skipped, potentially taking your name with it).
- The safe pattern: photo as a **floating anchored image** (XML `wp:anchor`) positioned at top-right of the page. All text paragraphs (name, contact, sections) remain in the normal paragraph flow and are fully parsed. The floating image layers over the page visually without disrupting text order.

Note: In European academic applications a photo is expected and appropriate. For US tech applications, omit it.

---

## Section Order (Academic / Research Applications)

From `Academic_CV_Renderer_Agent_Prompt.txt` — this ordering is non-negotiable for the renderer agent:

1. Header (name + tagline + contact)
2. Professional Summary
3. Education
4. Research & Professional Experience
5. Publications
6. Technical Skills
7. Languages

---

## ATS Scoring in This Project

Our deterministic code analysis (`src/ats_tester/deterministic_evaluator.py` backed by `src/utils/nlp/text_analyzer.py`) scores along four axes:

| Dimension | Weight (with JD) | What it checks |
|---|---|---|
| Keyword match | 35% | Overlap between CV terms and job description |
| Format | 25% | Presence of contact block, standard sections, bullet structure |
| Content | 25% | Summary length, experience density, education |
| Readability | 15% | Sentence length, token/sentence ratio |

The Gemini LLM engine (weight 40% of combined score) evaluates semantic alignment with the job description.

For implementation details and troubleshooting, see `docs/cv/ats_checker_deep_dive.md`.

---

## Checklist Before Submitting a Generated CV

- [ ] Name appears as the first plain-text line of the document body
- [ ] Contact (email + phone + location) appears as plain text within the first 5 lines
- [ ] No tables anywhere in the document
- [ ] No text boxes
- [ ] Content section headers use canonical labels
- [ ] All bullet points use `•` or `-`
- [ ] Font is Arial or Calibri
- [ ] `python src/cli/pipeline.py cv-validate-ats <job_id> --ats-target pdf` completes successfully
- [ ] `python src/cli/pipeline.py cv-template-test <job_id> english --via docx --target docx --require-perfect` passes (100% deterministic parity)
- [ ] `ats_target: "pdf"` in ATS report
- [ ] `engines.code.used_fallback: false` in ATS report (or documented reason if fallback is expected)
- [ ] `content_parity` is available and passes (expected after current render/build flows)

---

## References

- [Jobscan — Can ATS Read Tables and Columns?](https://www.jobscan.co/blog/resume-tables-columns-ats/)
- [Jobscan — ATS Formatting Mistakes](https://www.jobscan.co/blog/ats-formatting-mistakes/)
- [SGS Consulting — ATS-Optimised Resume Guide 2025](https://sgsconsulting.com/blogs/a-2025-guide-to-building-an-ats-optimized-resume)
- `data/reference_data/prompts/Academic_CV_Renderer_Agent_Prompt.txt`
- `data/reference_data/prompts/Academic_ATS_Prompt_Architecture.txt`
- `docs/cv/ats_checker_deep_dive.md`
