"""Vision Motor — Visual Analysis & Screen Interaction.

This motor is planned to support vision-first automation (e.g., using GPT-4V or 
OmniParser) for portals where traditional DOM/CSS scraping is insufficient or
where pixel-perfect interaction is required.
"""

from .provider import VisionMotorProvider, VisionMotorSession

__all__ = ["VisionMotorProvider", "VisionMotorSession"]
