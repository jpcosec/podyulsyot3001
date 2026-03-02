from docx.shared import Pt, Inches, RGBColor

class CVStyles:
    # Margins
    MARGIN_TOP = Inches(0.5)
    MARGIN_BOTTOM = Inches(0.5)
    MARGIN_LEFT = Inches(0.5)
    MARGIN_RIGHT = Inches(0.5)

    # Colors
    PRIMARY_COLOR = RGBColor(42, 92, 93)  # Dark Teal
    SECONDARY_COLOR = RGBColor(100, 100, 100)  # Dark Gray

    # Fonts
    FONT_NAME = 'Arial'
    
    # Text Sizes
    SIZE_NAME = Pt(22)
    SIZE_TITLE = Pt(11)
    SIZE_CONTACT = Pt(9.5)
    SIZE_HEADER = Pt(12)
    SIZE_BODY = Pt(9.5)
    SIZE_BOLD_BODY = Pt(10)
    SIZE_SMALL = Pt(9)
