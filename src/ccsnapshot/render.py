"""PNG rendering for CC Snapshot cards."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image, ImageDraw, ImageFont

from .time_stats import format_duration


# Card dimensions (Threads optimal)
WIDTH = 1080
HEIGHT = 1350

# Colors
BG_TOP = (26, 26, 46)       # #1a1a2e
BG_BOTTOM = (22, 33, 62)    # #16213e
CARD_BG = (30, 41, 59)      # #1e293b
ACCENT = (99, 102, 241)     # #6366f1 (indigo)
TEXT_PRIMARY = (255, 255, 255)
TEXT_SECONDARY = (148, 163, 184)  # #94a3b8
BAR_COLOR = (99, 102, 241)  # #6366f1
BAR_EMPTY = (51, 65, 85)    # #334155


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


def create_gradient_background(width: int, height: int) -> Image.Image:
    """Create a vertical gradient background."""
    img = Image.new('RGB', (width, height))
    for y in range(height):
        ratio = y / height
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * ratio)
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
    xy: tuple[int, int, int, int],
    radius: int,
    fill: tuple[int, int, int]
) -> None:
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill)
    draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill)
    draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill)
    draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill)


def render_snapshot(metrics: SnapshotMetrics) -> Image.Image:
    """Render the snapshot card as a PIL Image."""
    # Create gradient background
    img = create_gradient_background(WIDTH, HEIGHT)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = get_font(64)
    font_day = get_font(32)
    font_metric_value = get_font(72)
    font_metric_label = get_font(28)
    font_bar_label = get_font(20)

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
        fill=TEXT_PRIMARY
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
        fill=ACCENT
    )
    draw.text(
        (badge_x + badge_padding, badge_y + 8),
        day_text,
        font=font_day,
        fill=TEXT_PRIMARY
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

        # Card background
        draw_rounded_rect(
            draw,
            (card_margin, card_y, WIDTH - card_margin, card_y + card_height),
            radius=20,
            fill=CARD_BG
        )

        # Value (large)
        value_bbox = draw.textbbox((0, 0), value, font=font_metric_value)
        value_width = value_bbox[2] - value_bbox[0]
        draw.text(
            ((WIDTH - value_width) // 2, card_y + 30),
            value,
            font=font_metric_value,
            fill=TEXT_PRIMARY
        )

        # Label
        label_bbox = draw.textbbox((0, 0), sublabel, font=font_metric_label)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text(
            ((WIDTH - label_width) // 2, card_y + 120),
            sublabel,
            font=font_metric_label,
            fill=TEXT_SECONDARY
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
        fill=TEXT_SECONDARY
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
            fill=BAR_EMPTY
        )

        # Bar fill
        if minutes > 0:
            fill_height = int((minutes / max_minutes) * bar_area_height)
            fill_top = bar_area_top + bar_area_height - fill_height
            draw_rounded_rect(
                draw,
                (bar_x, fill_top, bar_x + bar_width, bar_area_top + bar_area_height),
                radius=10,
                fill=BAR_COLOR
            )

        # Day label
        label_bbox = draw.textbbox((0, 0), day_labels[i], font=font_bar_label)
        label_width = label_bbox[2] - label_bbox[0]
        draw.text(
            (bar_x + (bar_width - label_width) // 2, bar_area_top + bar_area_height + 10),
            day_labels[i],
            font=font_bar_label,
            fill=TEXT_SECONDARY
        )

    # Footer
    footer_text = "Built with Claude Code"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_bar_label)
    footer_width = footer_bbox[2] - footer_bbox[0]
    draw.text(
        ((WIDTH - footer_width) // 2, HEIGHT - 60),
        footer_text,
        font=font_bar_label,
        fill=TEXT_SECONDARY
    )

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
