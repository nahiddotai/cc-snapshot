"""PNG rendering for CC Snapshot cards."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .theme import DEFAULT_THEME, ThemeTokens, get_theme
from .time_stats import format_duration


# Card dimensions (Threads optimal)
WIDTH = 1080
HEIGHT = 1350


@dataclass
class SnapshotMetrics:
    """Metrics to display on the snapshot card."""
    streak: int
    total_minutes: int
    files_changed: int
    daily_minutes: dict[str, int]  # YYYY-MM-DD -> minutes
    day_number: int
    title: str = "CC Snapshot"
    project_name: str = ""


def create_gradient_background(
    width: int, height: int, theme: ThemeTokens
) -> Image.Image:
    """Create a vertical gradient background using theme colors."""
    img = Image.new('RGB', (width, height))
    top = theme.bg_gradient_top
    bottom = theme.bg_gradient_bottom
    for y in range(height):
        ratio = y / height
        r = int(top[0] + (bottom[0] - top[0]) * ratio)
        g = int(top[1] + (bottom[1] - top[1]) * ratio)
        b = int(top[2] + (bottom[2] - top[2]) * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get a font at the specified size, with fallback."""
    # Try common system fonts
    font_paths = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Fallback to default
    return ImageFont.load_default()


def draw_rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill: Union[Tuple[int, int, int], Tuple[int, int, int, int]]
) -> None:
    """Draw a rounded rectangle (supports RGB or RGBA fill)."""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill)


def draw_rounded_rect_outline(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    outline: Tuple[int, int, int, int],
    width: int = 2
) -> None:
    """Draw a rounded rectangle outline (border only)."""
    x1, y1, x2, y2 = xy
    # Top edge
    draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
    # Bottom edge
    draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
    # Left edge
    draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
    # Right edge
    draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)
    # Corner arcs (using ellipse outline)
    draw.arc([x1, y1, x1 + radius * 2, y1 + radius * 2], 180, 270, fill=outline, width=width)
    draw.arc([x2 - radius * 2, y1, x2, y1 + radius * 2], 270, 360, fill=outline, width=width)
    draw.arc([x1, y2 - radius * 2, x1 + radius * 2, y2], 90, 180, fill=outline, width=width)
    draw.arc([x2 - radius * 2, y2 - radius * 2, x2, y2], 0, 90, fill=outline, width=width)


def apply_glow(
    base_img: Image.Image,
    xy: Tuple[int, int, int, int],
    radius: int,
    glow_color: Tuple[int, int, int, int],
    blur_radius: int,
    strength: float
) -> Image.Image:
    """Apply a soft glow effect around a rounded rectangle area."""
    # Create glow layer
    glow_layer = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # Draw slightly larger shape for glow
    x1, y1, x2, y2 = xy
    expand = blur_radius
    glow_xy = (x1 - expand, y1 - expand, x2 + expand, y2 + expand)
    draw_rounded_rect(glow_draw, glow_xy, radius + expand // 2, glow_color)

    # Apply blur
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(blur_radius))

    # Adjust strength by modifying alpha
    if strength < 1.0:
        r, g, b, a = glow_layer.split()
        a = a.point(lambda x: int(x * strength))
        glow_layer = Image.merge('RGBA', (r, g, b, a))

    # Composite glow under content
    result = Image.new('RGBA', base_img.size, (0, 0, 0, 0))
    result.paste(glow_layer, (0, 0))

    # Convert base to RGBA if needed and composite on top
    if base_img.mode != 'RGBA':
        base_rgba = base_img.convert('RGBA')
    else:
        base_rgba = base_img
    result = Image.alpha_composite(result, base_rgba)

    return result


def draw_glass_panel(
    img: Image.Image,
    xy: Tuple[int, int, int, int],
    radius: int,
    theme: ThemeTokens
) -> Image.Image:
    """Draw a glass panel with optional border and highlight (liquid glass style)."""
    # Convert to RGBA for transparency support
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create panel layer
    panel_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_layer)

    # Draw panel fill
    draw_rounded_rect(panel_draw, xy, radius, theme.panel_fill)

    # Composite panel onto image
    img = Image.alpha_composite(img, panel_layer)

    # Draw border if specified
    if theme.panel_border_width > 0 and theme.panel_border[3] > 0:
        border_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_layer)
        draw_rounded_rect_outline(
            border_draw, xy, radius, theme.panel_border, theme.panel_border_width
        )
        img = Image.alpha_composite(img, border_layer)

    # Draw highlight streak if specified (top edge)
    if theme.panel_highlight is not None:
        highlight_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        highlight_draw = ImageDraw.Draw(highlight_layer)
        x1, y1, x2, y2 = xy
        # Thin highlight line near top
        highlight_draw.line(
            [(x1 + radius, y1 + 4), (x2 - radius, y1 + 4)],
            fill=theme.panel_highlight,
            width=2
        )
        img = Image.alpha_composite(img, highlight_layer)

    return img


def draw_neon_glass_panel(
    img: Image.Image,
    xy: Tuple[int, int, int, int],
    radius: int,
    theme: ThemeTokens
) -> Image.Image:
    """Draw a dark glass panel with neon border and glow effect."""
    # Apply glow first (behind everything)
    if theme.glow.enabled:
        img = apply_glow(
            img, xy, radius,
            theme.glow.color,
            theme.glow.blur_radius,
            theme.glow.strength
        )

    # Convert to RGBA for transparency support
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Create panel layer
    panel_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    panel_draw = ImageDraw.Draw(panel_layer)

    # Draw panel fill
    draw_rounded_rect(panel_draw, xy, radius, theme.panel_fill)

    # Composite panel onto image
    img = Image.alpha_composite(img, panel_layer)

    # Draw neon border
    if theme.panel_border_width > 0 and theme.panel_border[3] > 0:
        border_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border_layer)
        draw_rounded_rect_outline(
            border_draw, xy, radius, theme.panel_border, theme.panel_border_width
        )
        img = Image.alpha_composite(img, border_layer)

    return img


def draw_themed_panel(
    img: Image.Image,
    xy: Tuple[int, int, int, int],
    radius: int,
    theme: ThemeTokens
) -> Image.Image:
    """Draw a themed panel - routes to appropriate style based on theme."""
    if theme.glow.enabled:
        return draw_neon_glass_panel(img, xy, radius, theme)
    else:
        return draw_glass_panel(img, xy, radius, theme)


def render_snapshot(
    metrics: SnapshotMetrics, theme_name: Optional[str] = None
) -> Image.Image:
    """Render the snapshot card as a PIL Image.

    Args:
        metrics: Snapshot metrics to display
        theme_name: Theme name (liquid_glass or dark_neon_glass). Defaults to liquid_glass.
    """
    # Load theme
    theme = get_theme(theme_name or DEFAULT_THEME)

    # Create gradient background
    img = create_gradient_background(WIDTH, HEIGHT, theme)

    # Fonts
    font_title = get_font(64)
    font_day = get_font(32)
    font_metric_value = get_font(72)
    font_metric_label = get_font(28)
    font_bar_label = get_font(20)

    # Convert to RGBA for transparency support
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Title - "Building [project_name]" or just title
    if metrics.project_name:
        title_text = f"Building {metrics.project_name}"
    else:
        title_text = metrics.title
    title_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(
        ((WIDTH - title_width) // 2, 80),
        title_text,
        font=font_title,
        fill=theme.title_text
    )

    # Day badge
    day_text = f"Day {metrics.day_number}"
    day_bbox = draw.textbbox((0, 0), day_text, font=font_day)
    day_width = day_bbox[2] - day_bbox[0]
    badge_padding = 24
    badge_x = (WIDTH - day_width - badge_padding * 2) // 2
    badge_y = 170

    draw_rounded_rect(
        draw,
        (badge_x, badge_y, badge_x + day_width + badge_padding * 2, badge_y + 50),
        radius=25,
        fill=theme.accent_color
    )
    # Badge text is always white/light for contrast on accent
    badge_text_color = (255, 255, 255) if sum(theme.accent_color) < 500 else (30, 30, 30)
    draw.text(
        (badge_x + badge_padding, badge_y + 8),
        day_text,
        font=font_day,
        fill=badge_text_color
    )

    # Metric cards
    card_margin = 60
    card_width = WIDTH - (card_margin * 2)
    card_height = 180
    card_spacing = 30
    card_start_y = 280

    metrics_data = [
        ("Streak", str(metrics.streak), "Consecutive days coding"),
        ("Build Time", format_duration(metrics.total_minutes), "Total time building"),
        ("Files Changed", str(metrics.files_changed), "Files changed this week"),
    ]

    for i, (label, value, sublabel) in enumerate(metrics_data):
        card_y = card_start_y + (card_height + card_spacing) * i
        card_xy = (card_margin, card_y, WIDTH - card_margin, card_y + card_height)

        # Draw themed panel (glass effect with optional glow)
        img = draw_themed_panel(img, card_xy, 20, theme)
        draw = ImageDraw.Draw(img)  # Refresh draw object after image modification

        # Value (large)
        value_bbox = draw.textbbox((0, 0), value, font=font_metric_value)
        value_width = value_bbox[2] - value_bbox[0]
        draw.text(
            ((WIDTH - value_width) // 2, card_y + 30),
            value,
            font=font_metric_value,
            fill=theme.primary_text
        )

        # Label
        label_bbox = draw.textbbox((0, 0), sublabel, font=font_metric_label)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text(
            ((WIDTH - label_width) // 2, card_y + 120),
            sublabel,
            font=font_metric_label,
            fill=theme.secondary_text
        )

    # Mini bar chart
    chart_y = 920
    chart_height = 280
    bar_width = 100
    bar_spacing = 20
    total_bars_width = (bar_width * 7) + (bar_spacing * 6)
    chart_x = (WIDTH - total_bars_width) // 2

    # Chart title
    chart_title = "This Week"
    chart_title_bbox = draw.textbbox((0, 0), chart_title, font=font_metric_label)
    chart_title_width = chart_title_bbox[2] - chart_title_bbox[0]
    draw.text(
        ((WIDTH - chart_title_width) // 2, chart_y),
        chart_title,
        font=font_metric_label,
        fill=theme.secondary_text
    )

    # Build week starting from Monday
    today = datetime.now().date()
    days_since_monday = today.weekday()  # Monday = 0
    monday = today - timedelta(days=days_since_monday)

    # Create week days Mon-Sun
    week_days = []
    for i in range(7):
        day = monday + timedelta(days=i)
        day_str = day.isoformat()
        minutes = metrics.daily_minutes.get(day_str, 0)
        week_days.append((day, minutes))

    max_minutes = max(m for _, m in week_days) if week_days else 1
    max_minutes = max(max_minutes, 1)  # Avoid division by zero

    bar_area_top = chart_y + 50
    bar_area_height = chart_height - 80

    day_labels = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    for i, (day, minutes) in enumerate(week_days):
        bar_x = chart_x + (bar_width + bar_spacing) * i

        # Bar background (empty)
        draw_rounded_rect(
            draw,
            (bar_x, bar_area_top, bar_x + bar_width, bar_area_top + bar_area_height),
            radius=10,
            fill=theme.chart_bar_empty
        )

        # Bar fill
        if minutes > 0:
            fill_height = int((minutes / max_minutes) * bar_area_height)
            fill_top = bar_area_top + bar_area_height - fill_height
            draw_rounded_rect(
                draw,
                (bar_x, fill_top, bar_x + bar_width, bar_area_top + bar_area_height),
                radius=10,
                fill=theme.chart_bar_fill
            )

        # Day label
        label_bbox = draw.textbbox((0, 0), day_labels[i], font=font_bar_label)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text(
            (bar_x + (bar_width - label_width) // 2, bar_area_top + bar_area_height + 10),
            day_labels[i],
            font=font_bar_label,
            fill=theme.secondary_text
        )

    # Footer
    footer_text = "Built with Claude Code"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_bar_label)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((WIDTH - footer_width) // 2, HEIGHT - 60),
        footer_text,
        font=font_bar_label,
        fill=theme.secondary_text
    )

    # Convert back to RGB for PNG saving
    if img.mode == 'RGBA':
        # Create white background for liquid glass, dark for neon
        bg_color = theme.bg_gradient_bottom
        background = Image.new('RGB', img.size, bg_color)
        background.paste(img, mask=img.split()[3])
        img = background

    return img


def save_snapshot(img: Image.Image, output_dir: Union[str, Path]) -> Path:
    """Save the snapshot image to the output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = output_path / f"{today}.png"

    img.save(filename, "PNG")
    return filename


def get_image_bytes(img: Image.Image) -> bytes:
    """Convert PIL Image to bytes for Streamlit display."""
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
