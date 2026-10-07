"""Genera los iconos de la app (fondo de tormenta, hexágono brillante y una F)."""
import math, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 1024
OUT = os.path.join(os.path.dirname(__file__), "..", "icons")
os.makedirs(OUT, exist_ok=True)

def radial(size, center, radius, inner, outer):
    img = Image.new("RGB", (size, size), outer)
    px = img.load()
    cx, cy = center
    for y in range(size):
        for x in range(size):
            d = min(1.0, math.hypot(x - cx, y - cy) / radius)
            t = d ** 1.4
            px[x, y] = tuple(int(inner[i] * (1 - t) + outer[i] * t) for i in range(3))
    return img

def hexagon(cx, cy, r):
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in range(-90, 270, 60)]

bg = radial(S, (S * .5, S * .42), S * .75, (24, 62, 140), (3, 6, 13))

# rayos tenues de fondo
bolt = Image.new("RGBA", (S, S), (0, 0, 0, 0))
bd = ImageDraw.Draw(bolt)
for pts, w in [([(120, 0), (190, 210), (150, 240), (240, 470)], 10), ([(900, 40), (830, 260), (880, 290), (790, 520)], 8)]:
    bd.line(pts, fill=(140, 220, 255, 150), width=w, joint="curve")
bolt = bolt.filter(ImageFilter.GaussianBlur(6))
bg = Image.alpha_composite(bg.convert("RGBA"), bolt)

# brillo del hexágono
glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.polygon(hexagon(512, 520, 360), outline=(67, 214, 255, 255), width=46)
glow = glow.filter(ImageFilter.GaussianBlur(38))
bg = Image.alpha_composite(bg, glow)

# hexágono: borde + relleno degradado
hexl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
hd = ImageDraw.Draw(hexl)
hd.polygon(hexagon(512, 520, 360), fill=(67, 214, 255, 255))
inner = Image.new("L", (S, S), 0)
ImageDraw.Draw(inner).polygon(hexagon(512, 520, 330), fill=255)
fill = radial(S, (512, 380), 420, (22, 58, 120), (5, 12, 28)).convert("RGBA")
hexl.paste(fill, (0, 0), inner)
bg = Image.alpha_composite(bg, hexl)

# letra F en cursiva gruesa
font = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 470)
txt = Image.new("RGBA", (S, S), (0, 0, 0, 0))
td = ImageDraw.Draw(txt)
bbox = td.textbbox((0, 0), "F", font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
td.text((512 - w / 2 - bbox[0], 520 - h / 2 - bbox[1]), "F", font=font, fill=(255, 255, 255, 255))
shear = .22
txt = txt.transform((S, S), Image.AFFINE, (1, shear, -shear * 520, 0, 1, 0), resample=Image.BICUBIC)
# degradado cian→azul dentro de la letra
grad = Image.new("RGBA", (S, S))
gp = ImageDraw.Draw(grad)
for y in range(S):
    t = min(1, max(0, (y - 300) / 420))
    gp.line([(0, y), (S, y)], fill=(int(150 - 103 * t), int(236 - 113 * t), 255, 255))
letter = Image.new("RGBA", (S, S), (0, 0, 0, 0))
letter.paste(grad, (0, 0), txt.split()[3])
lglow = txt.filter(ImageFilter.GaussianBlur(22))
lglow = Image.merge("RGBA", (*[Image.new("L", (S, S), v) for v in (67, 214, 255)], lglow.split()[3]))
bg = Image.alpha_composite(bg, lglow)
bg = Image.alpha_composite(bg, letter)

final = bg.convert("RGB")
for size, name in [(1024, "icon-1024.png"), (512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")]:
    final.resize((size, size), Image.LANCZOS).save(os.path.join(OUT, name), optimize=True)
print("iconos generados en", os.path.abspath(OUT))
