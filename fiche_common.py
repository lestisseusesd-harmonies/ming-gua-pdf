# -*- coding: utf-8 -*-
"""
Module commun pour la génération de la fiche Ming Gua personnalisée.
Polices, palette, rendu CJK (caractères chinois en image), chargement des données.
Compatible macOS (test local) et Linux/conteneur (production).
"""
import io, os, json
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- Palette : source unique = Podia_CSS_Personnalise.css (charte Noriane Mesli) ----------
BEIGE_BG   = HexColor("#F2EBE0")   # --creme
CARD_BG    = HexColor("#F5EFE4")   # --creme-carte
CREAM      = HexColor("#F2EBE0")   # --texte-clair
SAGE_DARK  = HexColor("#4B4D3C")   # --olive
SAGE_LIGHT = HexColor("#8BBAB4")   # --sauge
# Échelle d'intensité des Qi favorables (tons exacts de la charte, du plus dense au plus léger)
SAGE_90    = HexColor("#4B4D3C")   # --olive
SAGE_80    = HexColor("#5C5E4A")   # --olive-clair
SAGE_70    = HexColor("#6EA49E")   # --sauge-fonce
SAGE_60    = HexColor("#8BBAB4")   # --sauge
CORAL      = HexColor("#E5614A")   # --corail
CORAL_DARK = HexColor("#D04F3A")   # --corail-hover (défavorables -80/-90)
TEXT_DARK  = HexColor("#2A2926")   # --texte-fonce
TEXT_MUTED = HexColor("#6E6A60")   # texte atténué (dérivé du texte foncé)

# ---------- Résolution de chemins multi-environnement ----------
def _first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None

# Charte : titres = Cormorant Garamond, corps/UI = Jost. DejaVu = secours.
_FONT_CANDIDATES = {
    "Serif":       [os.path.join(BASE, "fonts/CormorantGaramond-Regular.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSerif.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "SerifItalic": [os.path.join(BASE, "fonts/CormorantGaramond-Italic.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSerif-Italic.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"],
    "SerifBold":   [os.path.join(BASE, "fonts/CormorantGaramond-SemiBold.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSerif-Bold.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "Sans":        [os.path.join(BASE, "fonts/Jost-Regular.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSans.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "SansBold":    [os.path.join(BASE, "fonts/Jost-SemiBold.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSans-Bold.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "SansItalic":  [os.path.join(BASE, "fonts/Jost-Italic.ttf"),
                    os.path.join(BASE, "fonts/DejaVuSans.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}

# Police CJK pour PIL : (chemin, index dans la collection)
# index=3 = Traditional Chinese dans le .ttc combiné Noto (cf. maquettes d'origine).
_CJK_CANDIDATES = [
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 3),   # Debian fonts-noto-cjk (TC)
    ("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc", 0),   # secours si collection à 1 police
    ("/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc", 3),
    ("/usr/share/fonts/opentype/noto/NotoSerifTC-Regular.otf", 0),    # police TC autonome
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),             # macOS (serif, local)
    ("/Library/Fonts/Arial Unicode.ttf", 0),                          # macOS secours
]

_fonts_registered = False
def register_fonts():
    global _fonts_registered
    if _fonts_registered:
        return
    for name, candidates in _FONT_CANDIDATES.items():
        path = _first_existing(candidates)
        if not path:
            raise RuntimeError(f"Police introuvable pour {name} : {candidates}")
        pdfmetrics.registerFont(TTFont(name, path))
    # Familles pour que <b>/<i> fonctionnent dans les Paragraph
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="SansBold",
                                  italic="SansItalic", boldItalic="SansBold")
    pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="SerifBold",
                                  italic="SerifItalic", boldItalic="SerifBold")
    _fonts_registered = True

def _cjk_font_spec():
    for path, idx in _CJK_CANDIDATES:
        if os.path.exists(path):
            return path, idx
    raise RuntimeError("Aucune police CJK trouvée.")

_CJK_PATH, _CJK_INDEX = None, None
def cjk_image(text, size_px, color=(95, 108, 80, 255)):
    """Rend un texte CJK en image PNG transparente. Retourne (ImageReader, w, h)."""
    global _CJK_PATH, _CJK_INDEX
    if _CJK_PATH is None:
        _CJK_PATH, _CJK_INDEX = _cjk_font_spec()
    font = ImageFont.truetype(_CJK_PATH, size_px, index=_CJK_INDEX)
    bbox = font.getbbox(text)
    img_w = bbox[2] - bbox[0] + 4
    img_h = int(size_px * 1.15)
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((-bbox[0] + 2, -bbox[1]), text, font=font, fill=color)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    bio.seek(0)
    return ImageReader(bio), img_w, img_h

def color_rgba(hexcolor):
    return (int(hexcolor.red * 255), int(hexcolor.green * 255), int(hexcolor.blue * 255), 255)

# ---------- Assets ----------
LOGO_PATH = _first_existing([os.path.join(BASE, "assets/logo.png")])
PHOTO_PATH = _first_existing([os.path.join(BASE, "assets/aurelie.png")])

# ---------- Données ----------
_data_cache = {}
def _load(name):
    if name not in _data_cache:
        with open(os.path.join(BASE, "data", name), encoding="utf-8") as f:
            _data_cache[name] = json.load(f)
    return _data_cache[name]

def load_guas():       return _load("guas.json")
def load_qi():         return _load("qi.json")
def load_trigrammes(): return _load("trigrammes.json")

# Conversion markup web -> markup reportlab.
# Corps de texte = Jost (charte) : le gras/italique inline suit la police du corps.
def to_rl_markup(html):
    return (html.replace("<strong>", "<font name='SansBold'>")
                .replace("</strong>", "</font>")
                .replace("<em>", "<font name='SansItalic'>")
                .replace("</em>", "</font>"))

# Score -> couleur de badge
def score_color(score):
    return {90: SAGE_90, 80: SAGE_80, 70: SAGE_70, 60: SAGE_60}.get(
        score, CORAL if score >= -70 else CORAL_DARK)
