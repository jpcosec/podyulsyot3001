# Profile Record

Canonical profile document for automation agents and human reviewers.

This file is intentionally structured to be machine-friendly and human-readable.

## Canonical Data (YAML)

```yaml
schema_version: "1.1"
last_updated: "2026-02-26"

owner:
  full_name: "Juan Pablo Andres Ruiz Rodriguez"
  preferred_name: "Juan Pablo Ruiz Rodriguez"
  first_name: "Juan Pablo"
  middle_name: "Andres"
  last_name: "Ruiz Rodriguez"
  birth_date: "1992-11-20"
  nationality: "Chilean"
  location:
    current_city: "Berlin"
    current_country: "Germany"
    relocation:
      open_to_relocation: true
      note: "Currently based in Berlin; open to relocation for strong role fit."
  contact:
    primary_email: "juanpablo.ruiz.r@gmail.com"
    primary_phone: "015222144630"
    addresses:
      - label: "current"
        value: "Ostendstrasse 27, 12459 Berlin, Germany"
      - label: "historic_cv_record"
        value: "Jordanbad 4, 88400 Biberach an der Riss, Germany"
  links:
    linkedin: "https://www.linkedin.com/in/juanpabloruizr/"
    github: "https://github.com/jpcosec"
  legal_status:
    germany_visa:
      type: "Chancenkarte"
      status: "active"
      evidence_file: "/home/jp/buscapega/pega alemania/Visum.jpg"
    work_authorization:
      germany: true
      note: "Also reflected in CV JSON source as work_permission=Germany."

professional_identity:
  primary_headline: "Machine Learning Engineer"
  secondary_headlines:
    - "Data Scientist"
    - "AI Research Engineer"
  focus_areas:
    - "Machine Learning"
    - "Computer Vision"
    - "Affective Computing"
    - "AI in Education"
    - "Data Engineering"
    - "LLM-enabled document and workflow automation"
  current_research:
    - "Intelligent Tutoring Systems (ITS)"
    - "LAETEC-Vision stress-detection computer vision module"
    - "RAG and LLM-based pedagogical interventions"

education:
  - degree: "Electrical Engineering"
    specialization: "Computational Intelligence"
    institution: "Universidad de Chile"
    location: "Santiago, Chile"
    start_date: "2011-03"
    end_date: "2019-06"
    level_reference: "EQF 6"
    equivalency_note: "Program exceeds 300 ECTS and is validated by Anabin as equivalent to German Master's/Diplom."

experience:
  - role: "Research Associate (AI in Education)"
    organization: "Universidad de Playa Ancha (UPLA)"
    location: "Valparaiso, Chile (remote/hybrid)"
    start_date: "2024-11"
    end_date: "present"
    status: "ongoing"
    remuneration_status: "unknown"
    keywords: ["ITS", "PyTorch", "TensorFlow", "Experiment Design", "Learning Analytics"]
  - role: "Machine Learning Consultant"
    organization: "AraraDS"
    location: "Santiago, Chile"
    start_date: "2025-07"
    end_date: "2025-09"
    keywords: ["Kafka", "Airflow", "LLMs", "GenAI", "Document Processing", "OCR"]
  - role: "Data Engineer"
    organization: "Globalconexus"
    location: "Santiago, Chile"
    start_date: "2024-04"
    end_date: "2025-06"
    keywords: ["Azure Data Factory", "Databricks", "PySpark", "Power BI", "Delta Lake"]
  - role: "Data Engineer"
    organization: "Walmart"
    location: "Santiago, Chile"
    start_date: "2023-03"
    end_date: "2023-10"
    keywords: ["Cloud Pipelines", "Spark", "Data Contracts"]
  - role: "Data Science Consultant"
    organization: "Deloitte"
    location: "Santiago, Chile"
    start_date: "2021-09"
    end_date: "2023-03"
    keywords: ["ML Prototypes", "NLP", "FastAPI/Flask", "Docker"]
  - role: "Machine Learning Engineer"
    organization: "Kwali"
    location: "Santiago, Chile"
    start_date: "2019-03"
    end_date: "2021-08"
    keywords: ["Computer Vision", "Inspection Pipelines", "Backend Services"]

projects:
  - name: "Metadata-Driven Code Generation Framework"
    role: "Creator"
    summary: "Python framework generating REST APIs, Admin UI, and CLI from decorators, including Prefect orchestration and type-safe pipelines."
    stack: ["Python", "FastAPI", "Beanie/Pydantic", "Jinja2", "React/TypeScript", "Prefect", "Docker"]

publications:
  - year: 2025
    title: "Exploration of Incremental Synthetic Non-Morphed Images for Single Morphing Attack Detection"
    venue: "NeurIPS 2025 (Workshop)"
    role: "Co-author"
    url: "https://arxiv.org/abs/2510.09836"
  - year: 2025
    title: "Intelligent Tutor for Tasks in the Domain of Linear Algebra"
    venue: "ICITED 2025"
    role: "Co-author"

languages:
  - name: "Spanish"
    level: "CEFR C2"
    note: "Native"
  - name: "English"
    level: "CEFR C1"
  - name: "German"
    level: "CEFR A2"

technical_skills:
  programming_languages: ["Python", "JavaScript", "Java", "C", "Verilog"]
  ml_ai: ["scikit-learn", "TensorFlow/Keras", "PyTorch", "LLM prompting", "guardrails", "model evaluation"]
  data_platforms: ["Azure Data Factory", "Databricks", "Spark", "Delta Lake", "Power BI"]
  backend: ["FastAPI", "Flask", "REST", "gRPC", "Kafka", "PostgreSQL", "MongoDB", "Neo4j", "Redis"]
  orchestration_devops: ["Airflow", "Prefect", "Docker", "Git", "CI/CD"]
  llm_tools: ["LangChain", "prompt templates", "evaluation harnesses"]

application_targets:
  preferred_role_types:
    - "PhD Candidate"
    - "Research Assistant"
    - "Research Associate (PostDoc-track)"
    - "Machine Learning Engineer"
    - "Data Scientist"
  geographic_preferences:
    base_city: "Berlin"
    open_to_relocation: true
  package_constraints:
    - "Single PDF submission is often required"
    - "Target file size under 5 MB"

job_summary_snapshot:
  source_file: "/home/jp/phd/data/pipelined_data/tu_berlin/summary.csv"
  captured_on: "2026-02-26"
  total_jobs: 28
  observed_counts:
    research_assistant_titles: 15
    research_associate_or_postdoc_titles: 7
    phd_or_qualification_titles: 2
    german_language_titles: 5
    part_time_markers:
      "0.5": 1
      "0.75": 5
      "0.8": 1
      "0.9": 1
  observed_salary_bands: ["TV-L E13", "TV-L E14"]
  deadline_range:
    earliest: "2026-02-27"
    latest: "2026-03-20"
  known_data_gaps:
    - field: "duration"
      unknown_count: 5
      note: "Mostly in German-language title pages where parser extraction missed normalized fields."
      records:
        - job_id: "200069"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/200069"
        - job_id: "201399"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201399"
        - job_id: "201553"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201553"
        - job_id: "201010"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201010"
        - job_id: "201188"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201188"
    - field: "salary"
      unknown_count: 5
      note: "Same records as duration; parser likely not capturing localized table labels for these pages."
      records:
        - job_id: "200069"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/200069"
        - job_id: "201399"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201399"
        - job_id: "201553"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201553"
        - job_id: "201010"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201010"
        - job_id: "201188"
          url: "https://www.jobs.tu-berlin.de/en/job-postings/201188"

documents:
  supporting_files:
    anabin_validation_pdf: "/home/jp/phd/data/reference_data/application_assets/documents/Anabin Titelvalidierung.pdf"
    language_certificate_pdf: "/home/jp/phd/data/reference_data/application_assets/documents/Language Certificate.pdf"
    study_certificate_pdf: "/home/jp/phd/data/reference_data/application_assets/documents/Study certificate.pdf"
    visa_evidence_image: "/home/jp/buscapega/pega alemania/Visum.jpg"

agent_preferences:
  documentation_style:
    machine_friendly: true
    human_readable: true
    concise: true
  execution_style:
    default_language: "English"
    preserve_manual_edits: true
    avoid_destructive_actions: true
    explicit_assumptions: true

source_of_truth:
  canonical_profile: "/home/jp/phd/src/cv_generator/src/data/profile.json"
  note: "profile.json is the single multilingual source of truth for CV generation. All per-language JSON variants have been archived to src/cv_generator/src/data/archive/."
  primary_files:
    - "/home/jp/phd/src/cv_generator/src/data/profile.json"
    - "/home/jp/phd/src/cv_generator/main.tex"
    - "/home/jp/phd/src/cv_generator/Txt/1-CV-body.tex"
    - "/home/jp/phd/src/cv_generator/Txt/p1_sidebar.tex"
    - "/home/jp/phd/data/reference_data/agent_feedback/templates/application_master_template.md"
    - "/home/jp/phd/data/pipelined_data/tu_berlin/summary.csv"
```

## Human Snapshot

Juan Pablo Ruiz Rodriguez is a Berlin-based machine learning engineer and data scientist with experience across applied AI research, computer vision, data engineering, and production ML systems. His recent work spans intelligent tutoring systems, LLM-enabled document workflows, and enterprise data platforms. He is actively targeting both research and industry roles, including PhD-track, research assistant/associate, and ML engineering opportunities.

## Credential Wording Snippets

Use these exact snippets in applications when relevant.

```yaml
credential_snippets:
  visa_status_short: "I currently hold an active Chancenkarte visa in Germany."
  work_authorization_short: "I am authorized to reside and work in Germany under my active Chancenkarte status."
  degree_equivalency_short: "My Electrical Engineering degree (300+ ECTS) is validated by Anabin/ZAB as equivalent to a German Master's/Diplom."
```

## Open Questions and Clarifications

```yaml
open_questions:
  - id: legal_name_for_contracts
    question: "Should all formal submissions always include middle name 'Andres'?"
    current_default: "Use preferred_name in drafts; use full_name for legal/contract forms."
    status: "open"
  - id: current_address_source_of_truth
    question: "Should Berlin address fully replace the older Biberach address in all CV sources?"
    current_default: "Treat Berlin as current; retain Biberach as historical record only."
    status: "open"
  - id: compensation_constraints
    question: "Are there hard minimum salary/contract constraints for role filtering?"
    current_default: "No hard floor applied in automated filtering."
    status: "open"
  - id: parser_gap_handling_for_job_summary
    question: "Should jobs with unknown salary/duration be re-scraped and manually verified before prioritization?"
    current_default: "Yes, verify the 5 gap records before final ranking."
    status: "open"
  - id: upla_remuneration_status
    question: "Should UPLA Research Associate be explicitly marked as unpaid/non-remunerated in all profile outputs?"
    current_default: "Keep remuneration_status as unknown unless explicitly confirmed."
    status: "open"
```

## Agent Guidance for Missing Data

- If a field is unknown, use `null` or `"unknown"`; never invent values.
- Keep dates ISO-like (`YYYY-MM` or `YYYY-MM-DD`).
- Prefer this file over scattered CV snippets when generating tailored content.
- When sources conflict, prefer the newest source and record the conflict in `open_questions`.
