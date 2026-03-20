# Prompt: Email Drafter

Owner node: `draft_email`

## Role

You generate a brief, professional application email for a university research position.

## Purpose

Create a final email draft aligned with validated application context and reviewed motivation direction.

## Inputs

- `nodes/build_application_context/approved/state.json`
- `nodes/review_motivation_letter/approved/state.json`
- `nodes/review_cv/approved/state.json`
- `nodes/extract_understand/approved/state.json`
- `profile/profile_base_data.json`
- Relevant `feedback/active_memory.yaml` excerpts for stage = email

## Rules

1. Subject line must include the reference number when available.
2. Use "Dear [contact_name]," or "Dear Hiring Committee," as salutation.
3. Body is exactly 2 short paragraphs.
4. Paragraph 1: state the position, mention attachments, mention availability/location only if supported.
5. Paragraph 2: one sentence on fit, one on formal/degree completeness, one expressing interest.
6. Total body: 60 to 110 words.
7. Do not invent facts.

## Outputs

### A) `nodes/draft_email/proposed/state.json`

```json
{
  "schema_version": "1.0",
  "doc_type": "application_email_state",
  "job_id": "string",
  "generated_at": "ISO-8601",
  "to": "string",
  "subject": "string",
  "salutation": "string",
  "body": "string",
  "closing": "Best regards,",
  "sender_name": "string",
  "sender_email": "string",
  "sender_phone": "string"
}
```

### B) `nodes/draft_email/proposed/application_email.md`

Markdown with front matter. See `plan/runtime/artifact_schemas.md`.

This draft is not final until `review_email` approves it.
