"""
FMS Flyer Generator v2 — Direct Pillow image editing approach.
Uses FundFlyer.png as the base and draws directly on it (no RGBA overlay)
to ensure 100% opaque white-outs that fully cover original text.
Replaces the "YOUR LOGO HERE" box with the FMS logo.
All coordinates derived from pixel analysis of FundFlyer.png (1024x1536).
"""

import os
import io
from PIL import Image, ImageDraw, ImageFont

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
BASE_FLYER = os.path.join(BASE_DIR, "FundFlyer.png")
FMS_LOGO   = os.path.join(BASE_DIR, "FMLogo.png")

# ── Colors (RGB, no alpha — drawing directly on RGB image) ───────────────────
BLACK     = (0, 0, 0)
PINK      = (232, 62, 114)
OFF_WHITE = (253, 251, 249)   # matches flyer background


def load_font(size, bold=False):
    """Load a system font at the given size."""
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def wrap_to_width(draw, text, font, max_w):
    """Wrap text into lines that fit within max_w pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if text_width(draw, test, font) <= max_w:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_flyer(org_name, start_date, end_date, fundraiser_code, output_path=None):
    """
    Generate a fundraiser flyer PNG by drawing directly on FundFlyer.png.
    Returns PNG bytes.
    """
    # ── 1. Open base flyer as RGB (no alpha) — draw directly on it ───────────
    img  = Image.open(BASE_FLYER).convert("RGB")
    W, H = img.size   # 1024 x 1536
    draw = ImageDraw.Draw(img)

    # ── 2. White-out: org name area (full width to cover original text) ───────
    # Original "YOUR ORGANIZATION NAME HERE" text: y=151..191, x=40..856
    # White-out from y=148 to y=196 to fully cover original text
    draw.rectangle([40, 148, 860, 196], fill=OFF_WHITE)

    # ── 3. Draw org name in bold black, auto-sized ────────────────────────────
    # Available area: y=148..196 (height=48), x=42..590 (width=548)
    org_upper = org_name.upper()
    max_w_org = 548   # left column: x=42..590
    area_h    = 48    # y=148..196

    # Find largest font that fits in 1-2 lines within the 48px height
    for size in [44, 38, 32, 28, 24, 20]:
        font_org = load_font(size, bold=True)
        lines    = wrap_to_width(draw, org_upper, font_org, max_w_org)
        line_h   = text_height(draw, "A", font_org) + 4
        if len(lines) <= 2 and len(lines) * line_h <= area_h:
            break

    line_h       = text_height(draw, "A", font_org) + 4
    total_text_h = len(lines) * line_h
    y_org        = 148 + max(0, (area_h - total_text_h) // 2)

    for line in lines[:2]:
        draw.text((42, y_org), line, font=font_org, fill=BLACK)
        y_org += line_h

    # ── 4. Replace "YOUR LOGO HERE" box with FMS logo ────────────────────────
    # Logo box: x=618..1008, y=48..235 (extend to y=235 to cover pink bottom border at y=228-230)
    logo_x1, logo_y1, logo_x2, logo_y2 = 615, 46, 1010, 236
    draw.rectangle([logo_x1, logo_y1, logo_x2, logo_y2], fill=OFF_WHITE)

    try:
        fms_logo = Image.open(FMS_LOGO).convert("RGBA")
        pad      = 16
        max_lw   = (logo_x2 - logo_x1) - pad * 2
        max_lh   = (logo_y2 - logo_y1) - pad * 2
        fms_logo.thumbnail((max_lw, max_lh), Image.LANCZOS)
        lw, lh = fms_logo.size
        lx = logo_x1 + ((logo_x2 - logo_x1) - lw) // 2
        ly = logo_y1 + ((logo_y2 - logo_y1) - lh) // 2
        # Paste with alpha mask onto RGB image
        logo_rgb  = Image.new("RGB", fms_logo.size, OFF_WHITE)
        logo_rgb.paste(fms_logo, mask=fms_logo.split()[3])
        img.paste(logo_rgb, (lx, ly))
    except Exception as e:
        print(f"Logo paste error: {e}")

    # ── 5. Fill Fundraiser Dates ──────────────────────────────────────────────
    # Start date blank area: y=375..422 (above gray line at y=423)
    # End date blank area:   y=435..498 (below TO, above gray line at y=500)
    # Right panel x range:   x=618..1008
    font_date = load_font(26, bold=False)

    # Date text starts at x=673 (aligned with original underline)
    draw.rectangle([618, 375, 1008, 422], fill=OFF_WHITE)
    draw.text((673, 388), start_date, font=font_date, fill=BLACK)

    draw.rectangle([618, 435, 1008, 498], fill=OFF_WHITE)
    draw.text((673, 462), end_date, font=font_date, fill=BLACK)

    # ── 6. Fill Fundraiser Code ───────────────────────────────────────────────
    # Code input box interior: x=618..1008, y=593..618
    font_code  = load_font(30, bold=True)
    code_upper = fundraiser_code.upper()

    draw.rectangle([618, 593, 1008, 618], fill=OFF_WHITE)
    cw = text_width(draw, code_upper, font_code)
    cx = 618 + ((1008 - 618) - cw) // 2
    draw.text((cx, 594), code_upper, font=font_code, fill=PINK)

    # ── 7. Fill "THANK YOU FOR SUPPORTING" org name box ──────────────────────
    # Box: x=872..1015, y=1472..1512
    draw.rectangle([872, 1472, 1015, 1512], fill=OFF_WHITE)
    font_thanks = load_font(15, bold=False)
    ty_lines    = wrap_to_width(draw, org_name, font_thanks, 138)
    ty_y        = 1476
    for tl in ty_lines[:2]:
        draw.text((876, ty_y), tl, font=font_thanks, fill=BLACK)
        ty_y += 18

    # ── 8. Save and return ────────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(150, 150))
    buf.seek(0)
    png_bytes = buf.read()

    if output_path:
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"Saved to {output_path} ({len(png_bytes):,} bytes)")

    return png_bytes


if __name__ == "__main__":
    generate_flyer(
        org_name        = "Lincoln Elementary PTA",
        start_date      = "07/01/2026",
        end_date        = "07/31/2026",
        fundraiser_code = "LINCO",
        output_path     = "/tmp/test_flyer_v4.png"
    )
