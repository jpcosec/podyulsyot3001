from docx.shared import Pt, Inches, RGBColor


class CVStyles:
    """Classic: Arial, dark teal accents, compact margins."""
    MARGIN_TOP = Inches(0.5)
    MARGIN_BOTTOM = Inches(0.5)
    MARGIN_LEFT = Inches(0.5)
    MARGIN_RIGHT = Inches(0.5)

    PRIMARY_COLOR = RGBColor(42, 92, 93)   # Dark Teal
    PRIMARY_COLOR_HEX = "2A5C5D"
    SECONDARY_COLOR = RGBColor(100, 100, 100)

    FONT_NAME = "Arial"

    SIZE_NAME = Pt(22)
    SIZE_TITLE = Pt(11)
    SIZE_CONTACT = Pt(9.5)
    SIZE_HEADER = Pt(12)
    SIZE_BODY = Pt(9.5)
    SIZE_BOLD_BODY = Pt(10)
    SIZE_SMALL = Pt(9)


class CVStylesModern:
    """Modern: Calibri, navy blue accents, slightly wider margins."""
    MARGIN_TOP = Inches(0.55)
    MARGIN_BOTTOM = Inches(0.55)
    MARGIN_LEFT = Inches(0.6)
    MARGIN_RIGHT = Inches(0.6)

    PRIMARY_COLOR = RGBColor(28, 72, 114)  # Navy Blue
    PRIMARY_COLOR_HEX = "1C4872"
    SECONDARY_COLOR = RGBColor(72, 72, 72)

    FONT_NAME = "Calibri"

    SIZE_NAME = Pt(24)
    SIZE_TITLE = Pt(11)
    SIZE_CONTACT = Pt(9.5)
    SIZE_HEADER = Pt(12)
    SIZE_BODY = Pt(10)
    SIZE_BOLD_BODY = Pt(10.5)
    SIZE_SMALL = Pt(9)


class CVStylesHarvard:
    """Harvard: Georgia serif, monochrome, generous margins — academic standard."""
    MARGIN_TOP = Inches(0.75)
    MARGIN_BOTTOM = Inches(0.75)
    MARGIN_LEFT = Inches(0.75)
    MARGIN_RIGHT = Inches(0.75)

    PRIMARY_COLOR = RGBColor(20, 20, 20)   # Near-black
    PRIMARY_COLOR_HEX = "141414"
    SECONDARY_COLOR = RGBColor(70, 70, 70)

    FONT_NAME = "Georgia"

    SIZE_NAME = Pt(18)
    SIZE_TITLE = Pt(10.5)
    SIZE_CONTACT = Pt(9.5)
    SIZE_HEADER = Pt(11)
    SIZE_BODY = Pt(10)
    SIZE_BOLD_BODY = Pt(10)
    SIZE_SMALL = Pt(9)


class CVStylesExecutive:
    """Executive: Cambria, dark slate, generous proportions — senior / research roles."""
    MARGIN_TOP = Inches(0.65)
    MARGIN_BOTTOM = Inches(0.65)
    MARGIN_LEFT = Inches(0.7)
    MARGIN_RIGHT = Inches(0.7)

    PRIMARY_COLOR = RGBColor(45, 55, 90)   # Dark Slate Blue
    PRIMARY_COLOR_HEX = "2D375A"
    SECONDARY_COLOR = RGBColor(85, 85, 85)

    FONT_NAME = "Cambria"

    SIZE_NAME = Pt(20)
    SIZE_TITLE = Pt(11)
    SIZE_CONTACT = Pt(9.5)
    SIZE_HEADER = Pt(11)
    SIZE_BODY = Pt(10)
    SIZE_BOLD_BODY = Pt(10.5)
    SIZE_SMALL = Pt(9)


def resolve_docx_style(template_name: str):
    templates = {
        "classic": CVStyles,
        "modern": CVStylesModern,
        "harvard": CVStylesHarvard,
        "executive": CVStylesExecutive,
    }
    if template_name not in templates:
        raise ValueError(
            f"Unknown DOCX template: {template_name}. "
            f"Available: {', '.join(templates)}"
        )
    return templates[template_name]
