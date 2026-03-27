# 1. Task Context
You are analyzing the following job posting for Job ID: {{ job_id }}.
Your goal is to transform natural language from the posting into a strict, auditable data structure.

# 2. Input Data (Raw)
<input_data>
{{ source_text_md }}
</input_data>

{% if active_feedback %}
# 3. Prior Learning Rules
Apply these rules from previous mistakes:
<feedback_rules>
{% for rule in active_feedback %}
- Rule: {{ rule.rule }}
{% endfor %}
</feedback_rules>
{% endif %}

# 4. Analysis Process
Before generating JSON, follow this process:
1. **Requirements Scan:** Identify each technology, role, years-of-experience signal, and soft skill. Classify each as `must` or `nice`.
2. **Constraint Evaluation:** Explicitly look for work mode (remote/hybrid/onsite), timezone, legal status, visas, process, deadline, contract constraints, and salary grade.
3. **Contact Extraction:** Explicitly look for PI or contact person name and email. If an email exists, populate `contact_info.email`. If the name is absent, keep `contact_info.name` as null. If there are multiple contacts, list all of them in `contact_infos`.
4. **Risk Analysis:** Identify contradictions or red flags that may affect candidate fit or process viability.
5. **Validation:** Ensure requirement IDs are unique and descriptive.

# 5. Output Format
Generate JSON strictly following the `JobUnderstandingExtract` schema.
Do not add explanatory text outside JSON.
All natural-language fields in the JSON must be in English.
If `salary_grade` is not present in the posting, return `null`.
