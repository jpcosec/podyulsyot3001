"""StepStone apply portal definition in Ariadne common language."""
from src.automation.ariadne.portal_models import (
    ApplyPortalDefinition,
    ApplyStep,
    FieldType,
    FormField,
)

STEPSTONE_APPLY = ApplyPortalDefinition(
    source_name="stepstone",
    base_url="https://www.stepstone.de",
    entry_description="StepStone Easy Apply modal triggered by the apply button on job listings",
    steps=[
        ApplyStep(name="open_modal", description="Open the StepStone Easy Apply modal", fields=[]),
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
            description="Upload CV document",
            fields=[
                FormField(name="cv", label="CV / Resume", required=True, field_type=FieldType.FILE_PDF),
            ],
        ),
        ApplyStep(name="submit", description="Submit the application", fields=[], dry_run_stop=True),
    ],
)
