"""Regenerates app.ico and logo.png. Dev-only (needs: pip install pillow)."""
import os
from PIL import Image, ImageDraw, ImageFont

S = 1024
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # any bold font works
if os.name == "nt":
    FONT = r"C:\Windows\Fonts\arialbd.ttf"

# Background: rounded square with a vertical blue gradient
grad = Image.new("RGB", (S, S))
top, bottom = (36, 104, 232), (12, 36, 100)
gd = ImageDraw.Draw(grad)
for y in range(S):
    t = y / (S - 1)
    gd.line([(0, y), (S, y)], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1), radius=230, fill=255)
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
img.paste(grad, (0, 0), mask)
d = ImageDraw.Draw(img)

# License plate
d.rounded_rectangle((96, 270, 928, 726), radius=70, fill=(0, 0, 0, 60))            # soft shadow
d.rounded_rectangle((96, 250, 928, 706), radius=70, fill="white")
d.rounded_rectangle((122, 276, 902, 680), radius=48, outline=(12, 36, 100), width=14)
font = ImageFont.truetype(FONT, 215)
d.text((440, 455), "ABC", font=font, fill=(12, 36, 100), anchor="mm")

# Green check badge
cx, cy, r = 790, 770, 185
d.ellipse((cx - r - 30, cy - r - 30, cx + r + 30, cy + r + 30), fill="white")
d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(22, 163, 74))
pts = [(cx - 95, cy + 5), (cx - 25, cy + 80), (cx + 100, cy - 70)]
d.line(pts, fill="white", width=58, joint="curve")
for x, y in (pts[0], pts[-1]):
    d.ellipse((x - 29, y - 29, x + 29, y + 29), fill="white")

sizes = [16, 24, 32, 48, 64, 128, 256]
img.resize((256, 256), Image.LANCZOS).save(
    os.path.join(ROOT, "app.ico"), sizes=[(s, s) for s in sizes])
img.resize((64, 64), Image.LANCZOS).save(os.path.join(ROOT, "logo.png"))
img.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "tools", "icon_preview.png"))
print("done")
