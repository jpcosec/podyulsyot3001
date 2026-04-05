"""LinkedIn apply portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
)

LINKEDIN_APPLY = ApplyPortalDefinition(
    source_name="linkedin",
    base_url="https://www.linkedin.com",
    entry_description="LinkedIn Easy Apply modal triggered by the 'Easy Apply' button on job listings",
    steps=[
        ApplyStep(name="open_modal", description="Open the LinkedIn Easy Apply modal", fields=[]),
        ApplyStep(
            name="fill_contact",
            description="Fill contact information fields",
            fields=[
                FormField(name="first_name", label="First name", required=False, field_type=FieldType.TEXT),
                FormField(name="last_name", label="Last name", required=False, field_type=FieldType.TEXT),
                FormField(name="email", label="Email", required=False, field_type=FieldType.EMAIL),
                FormField(name="phone", label="Phone", required=False, field_type=FieldType.PHONE),
            ],
        ),
        ApplyStep(
            name="upload_cv",
            description="Select or upload CV document",
            fields=[
                FormField(name="cv", label="CV / Resume", required=True, field_type=FieldType.FILE_PDF),
            ],
        ),
        ApplyStep(name="submit", description="Submit the application", fields=[], dry_run_stop=True),
    ],
)
