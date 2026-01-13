"""Theme definitions for CC Snapshot cards."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# Type aliases for Python 3.9 compatibility
RGBA = Tuple[int, int, int, int]
RGB = Tuple[int, int, int]


@dataclass
class GlowParams:
    """Glow effect parameters (for neon themes)."""
    enabled: bool = False
    color: RGBA = (0, 255, 255, 180)  # Cyan glow
    blur_radius: int = 8
    strength: float = 0.6


@dataclass
class ThemeTokens:
    """Complete theme styling tokens."""
    # Background gradient (top to bottom)
    bg_gradient_top: RGB = (26, 26, 46)
    bg_gradient_bottom: RGB = (22, 33, 62)

    # Panel styling
    panel_fill: RGBA = (30, 41, 59, 255)
    panel_border: RGBA = (0, 0, 0, 0)  # No border by default
    panel_border_width: int = 0
    panel_highlight: Optional[RGBA] = None  # Optional highlight streak

    # Typography colors
    title_text: RGB = (255, 255, 255)
    primary_text: RGB = (255, 255, 255)
    secondary_text: RGB = (148, 163, 184)

    # Accent color (badges, buttons)
    accent_color: RGB = (99, 102, 241)

    # Chart bar colors
    chart_bar_fill: RGB = (99, 102, 241)
    chart_bar_empty: RGB = (51, 65, 85)

    # Glow effect (neon themes only)
    glow: GlowParams = field(default_factory=GlowParams)

    # Font configuration
    font_family: str = "system"  # system, monospace, sans-serif

    # Theme metadata
    name: str = "default"
    display_name: str = "Default"


# ============================================================================
# LIQUID GLASS THEME (default)
# Bright, airy, frosted glass aesthetic
# ============================================================================

LIQUID_GLASS = ThemeTokens(
    name="liquid_glass",
    display_name="Liquid Glass",

    # Bright airy gradient - soft blue to lavender
    bg_gradient_top=(230, 235, 250),      # Light blue-white
    bg_gradient_bottom=(200, 210, 235),   # Soft lavender-blue

    # Frosted glass panel - translucent white
    panel_fill=(255, 255, 255, 180),      # Semi-transparent white
    panel_border=(255, 255, 255, 120),    # Subtle white border
    panel_border_width=2,
    panel_highlight=(255, 255, 255, 200), # Gentle highlight streak

    # Typography - dark text on light background
    title_text=(30, 41, 59),              # Dark slate
    primary_text=(30, 41, 59),            # Dark slate
    secondary_text=(100, 116, 139),       # Medium gray

    # Accent - soft indigo
    accent_color=(99, 102, 241),          # Indigo

    # Chart bars
    chart_bar_fill=(99, 102, 241),        # Indigo
    chart_bar_empty=(200, 210, 235),      # Light lavender (matches bg)

    # No glow for liquid glass
    glow=GlowParams(enabled=False),

    font_family="system",
)


# ============================================================================
# DARK NEON GLASS THEME
# Dark background with neon cyan/purple accents
# ============================================================================

DARK_NEON_GLASS = ThemeTokens(
    name="dark_neon_glass",
    display_name="Dark Neon Glass",

    # Dark gradient - deep navy to dark purple
    bg_gradient_top=(15, 15, 35),         # Very dark navy
    bg_gradient_bottom=(25, 15, 45),      # Dark purple-navy

    # Dark glass panel - translucent dark
    panel_fill=(30, 30, 50, 200),         # Dark translucent
    panel_border=(0, 255, 255, 180),      # Neon cyan border
    panel_border_width=2,
    panel_highlight=None,                  # No highlight (neon border is the accent)

    # Typography - light text
    title_text=(255, 255, 255),           # White
    primary_text=(255, 255, 255),         # White
    secondary_text=(180, 180, 200),       # Light gray-purple

    # Accent - neon cyan
    accent_color=(0, 255, 255),           # Neon cyan

    # Chart bars - neon gradient feel
    chart_bar_fill=(0, 200, 255),         # Bright cyan
    chart_bar_empty=(40, 40, 70),         # Dark purple-gray

    # Neon glow effect
    glow=GlowParams(
        enabled=True,
        color=(0, 255, 255, 120),         # Cyan glow
        blur_radius=6,
        strength=0.5,
    ),

    font_family="system",
)


# ============================================================================
# THEME REGISTRY
# ============================================================================

THEMES: Dict[str, ThemeTokens] = {
    "liquid_glass": LIQUID_GLASS,
    "dark_neon_glass": DARK_NEON_GLASS,
}

DEFAULT_THEME = "liquid_glass"


def get_theme(name: str) -> ThemeTokens:
    """Get theme tokens by name, falling back to default."""
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def list_themes() -> Dict[str, str]:
    """Return dict of theme_name -> display_name."""
    return {name: theme.display_name for name, theme in THEMES.items()}
