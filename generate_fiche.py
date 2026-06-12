# -*- coding: utf-8 -*-
"""
Génère la fiche Ming Gua personnalisée (9 pages A4) en PDF.
Usage : python3 generate_fiche.py --gua 1 --prenom Marie [--naissance "14 mars 1981"] [--out out/fiche.pdf]

Layout et textes repris fidèlement des maquettes validées d'Aurélie.
Données dynamiques depuis data/{guas,qi,trigrammes}.json.
"""
import argparse, math, datetime, io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import Color
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import fiche_common as F

W, H = A4
ORDRE_FAV   = ['SHENG QI', 'TIAN YI', 'YAN NIAN', 'FU WEI']
ORDRE_DEFAV = ['HUO HAI', 'WU GUI', 'LIU SHA', 'JUE MING']

URL_YOUTUBE   = "https://www.youtube.com/@lestisseusesdharmonies/featured"
URL_PINTEREST = "https://pin.it/3KCCZfEv0"
URL_SITE      = "https://lestisseusesdharmonies.fr"
URL_MAIL      = "mailto:contact@lestisseusesdharmonies.fr"

# --- Offre 1 (page 6) -------------------------------------------------------
# Au lancement : OFFRE1_DISPONIBLE = False -> affiche le placeholder.
# Dès que l'Offre 1 est en ligne : passer à True et renseigner l'URL + le prix.
OFFRE1_DISPONIBLE = False
OFFRE1_URL  = ""            # ex. "https://lestisseusesdharmonies.fr/diagnostic"
OFFRE1_PRIX = ""            # ex. "97 €"

_MOIS = ["janvier","février","mars","avril","mai","juin","juillet","août",
         "septembre","octobre","novembre","décembre"]
def _date_fr(d=None):
    d = d or datetime.date.today()
    return f"{d.day} {_MOIS[d.month-1]} {d.year}"

def signe(n): return ("+" if n > 0 else "") + str(n)

# ============================================================
#  Contexte
# ============================================================
class Ctx:
    def __init__(self, gua, prenom, naissance=None, edition=None, sexe="femme"):
        guas = F.load_guas()
        self.qi = F.load_qi()
        self.trig = F.load_trigrammes()[str(gua)]
        self.g = guas[str(gua)]
        self.prenom = prenom
        self.sexe = sexe
        self.fe = "" if sexe == "homme" else "e"  # accord féminin
        self.gua_num = str(self.g["numero"])
        self.gua_nom = self.g["nom"]
        self.gua_char = self.g["caractere"]
        self.groupe = "GROUPE " + self.g["groupe"].upper()
        self.naissance = naissance
        self.edition = edition or f"Édition du {_date_fr()}"

    def qi_by_score(self, score):
        return next(v for v in self.qi.values() if v["score"] == score)
    def empl_dir(self, score):
        return next(d for d, v in self.g["emplacements"].items() if v["score"] == score)

# ============================================================
#  En-tête / pied communs
# ============================================================
def _bg(c):
    c.setFillColor(F.BEIGE_BG); c.rect(0, 0, W, H, fill=1, stroke=0)

def _header(c, ctx, page_no, logo_small=True):
    if F.LOGO_PATH:
        try:
            logo = ImageReader(F.LOGO_PATH)
            c.drawImage(logo, 50, H - 65, width=35, height=38, mask='auto', preserveAspectRatio=True)
        except Exception: pass
    c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 7.5)
    c.drawRightString(W - 50, H - 45, f"Page {page_no} / 7")
    c.setFillColor(F.SAGE_DARK); c.setFont("SerifBold", 9)
    c.drawRightString(W - 50, H - 58, f"Ming Gua {ctx.gua_num}  ·  {ctx.gua_nom}")

def _footer(c, ctx, with_site_link=True):
    c.setStrokeColor(F.CORAL); c.setLineWidth(0.6); c.line(60, 60, W - 60, 60)
    c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 6.5)
    c.drawString(60, 45, f"© Les Tisseuses d'Harmonies. Document personnel pour {ctx.prenom}. Merci de ne pas en recopier le contenu.")
    site = "lestisseusesdharmonies.fr"
    sw = c.stringWidth(site, "Sans", 6.5); sx = W - 60 - sw
    c.drawString(sx, 45, site)
    if with_site_link:
        c.linkURL(URL_SITE, (sx - 2, 42, W - 58, 53), relative=0)

def _title(c, y, titre, sous_titre):
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 22)
    c.drawCentredString(W/2, y, titre)
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(W/2 - 28, y - 11, W/2 + 28, y - 11)
    c.setFont("SerifItalic", 11); c.setFillColor(F.TEXT_MUTED)
    c.drawCentredString(W/2, y - 26, sous_titre)

# ============================================================
#  PAGE 1 — Couverture
# ============================================================
def page1(c, ctx):
    _bg(c)
    if F.LOGO_PATH:
        try:
            logo = ImageReader(F.LOGO_PATH)
            lw, lh = 60, 65
            c.drawImage(logo, (W - lw)/2, H - 95, width=lw, height=lh, mask='auto', preserveAspectRatio=True)
        except Exception: pass

    card_w, card_h = 320, 230
    card_x = (W - card_w) / 2
    card_y = H - 360
    card_top = card_y + card_h
    c.setFillColor(F.SAGE_DARK)
    c.roundRect(card_x, card_y, card_w, card_h, 12, fill=1, stroke=0)

    c.setFillColor(F.CREAM); c.setFont("Sans", 58)
    c.drawCentredString(W/2, card_top - 70, ctx.gua_num)
    img, iw, ih = F.cjk_image(ctx.gua_char, 70, color=F.color_rgba(F.CREAM))
    disp_h = 50; disp_w = iw * (disp_h / ih)
    c.drawImage(img, W/2 - disp_w/2, card_top - 150, width=disp_w, height=disp_h, mask='auto')
    c.setFillColor(F.CREAM); c.setFont("SerifBold", 17)
    c.drawCentredString(W/2, card_top - 185, ctx.gua_nom)

    c.setFont("Sans", 8)
    bw = c.stringWidth(ctx.groupe, "Sans", 8) + 24
    bx = (W - bw) / 2; by = card_y + 18
    c.setFillColor(F.SAGE_LIGHT); c.roundRect(bx, by, bw, 17, 8.5, fill=1, stroke=0)
    c.setFillColor(F.CREAM); c.drawCentredString(W/2, by + 5, ctx.groupe)

    # Titre verrouillé du lead magnet (sur deux lignes)
    title_y = card_y - 35
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 25)
    c.drawCentredString(W/2, title_y, "Ton énergie et ta maison,")
    c.drawCentredString(W/2, title_y - 28, "est-ce que ça matche ?")
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(W/2 - 28, title_y - 40, W/2 + 28, title_y - 40)
    c.setFont("SerifItalic", 12); c.setFillColor(F.TEXT_DARK)
    c.drawCentredString(W/2, title_y - 56, "Ton profil énergétique spécial habitat")
    c.setFont("Sans", 8); c.setFillColor(F.TEXT_MUTED)
    c.drawCentredString(W/2, title_y - 76, "8  EMPLACEMENTS")

    accueil = (
        f"<font name='SansBold'>Bonjour {ctx.prenom},</font><br/><br/>"
        "Tu tiens entre les mains quelque chose de rare : ta carte d'identité énergétique "
        "dans l'espace. En feng shui traditionnel chinois, ça s'appelle le Ming Gua, "
        "et c'est le socle de tout.<br/><br/>"
        "C'est lui qui détermine où ton corps trouve de l'appui dans ta maison, et où il "
        "s'épuise. Pas une théorie : une grille de lecture millénaire, calculée à partir "
        "de ta date de naissance.<br/><br/>"
        "Dans cette fiche, tu vas découvrir tes 8 emplacements : les 4 qui te portent et "
        "les 4 qui t'épuisent. Prends le temps de la lire tranquillement. "
        "Le feng shui ne se survole pas, il se laisse infuser."
    )
    style = ParagraphStyle("Accueil", fontName="Sans", fontSize=10.5, leading=15.5,
                           textColor=F.TEXT_DARK, alignment=TA_LEFT)
    para = Paragraph(accueil, style)
    text_top = title_y - 102
    _, ah = para.wrap(W - 170, 1000)
    para.drawOn(c, 85, text_top - ah)
    # Signature alignée à droite, comme un courrier
    c.setFont("SerifItalic", 12)
    c.setFillColor(F.TEXT_DARK)
    c.drawRightString(W - 85, text_top - ah - 26, "Aurélie")

    c.setStrokeColor(F.CORAL); c.setLineWidth(0.8); c.line(W/2 - 18, 65, W/2 + 18, 65)
    c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 7.5)
    if ctx.naissance:
        c.drawCentredString(W/2, 52, f"Fiche élaborée à partir de ta date de naissance : {ctx.naissance}")
    c.drawCentredString(W/2, 40, ctx.edition)
    c.showPage()

# ============================================================
#  PAGE 2 — Le trigramme
# ============================================================
def page2(c, ctx):
    _bg(c); _header(c, ctx, 2)
    title_y = H - 105
    _title(c, title_y, f"Le trigramme {ctx.gua_nom}", "Ce que ton trigramme évoque")

    note = (
        "<font name='SansBold'>Avant d'aller plus loin, un point important.</font> "
        f"Le trigramme qui t'est associé (ici <b>{ctx.gua_nom}</b>) n'est pas une étiquette psychologique. "
        "Ce n'est pas un test de personnalité qui te dit \"tu es comme ça\". "
        "C'est une clef de lecture issue de la pensée chinoise classique, "
        "riche de correspondances symboliques avec la nature, les éléments, les saisons.<br/><br/>"
        "Concrètement, en <b>BaZhai</b> (la branche du feng shui qu'on travaille ici), "
        "c'est surtout ton numéro Gua qui sert : il détermine tes 8 emplacements. "
        "Le reste (l'élément qui t'est associé, le profil évoqué plus bas) "
        "vient d'un système de correspondances plus large issu du <i>Yi Jing</i>. À utiliser avec souplesse.<br/><br/>"
        "<font name='SansItalic'>Prends ce qui résonne. Laisse de côté ce qui ne te parle pas. "
        "Tu n'es pas réductible à quelques mots : personne ne l'est. "
        "Mais ces mots peuvent t'éclairer.</font>"
    )
    note_style = ParagraphStyle("Note", fontName="Sans", fontSize=9.5, leading=13.5,
                                textColor=F.TEXT_DARK, alignment=TA_LEFT)
    note_para = Paragraph(note, note_style)
    _, note_h = note_para.wrap(W - 150, 1000)
    pad_t, pad_b = 10, 8
    box_h = note_h + pad_t + pad_b
    box_top = title_y - 50; box_y = box_top - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.CORAL); c.rect(60, box_y, 3, box_h, fill=1, stroke=0)
    note_para.drawOn(c, 75, box_y + pad_b)

    # Synthèse
    synth_y = box_y - 26
    c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 13)
    c.drawString(60, synth_y, "Ton trigramme en synthèse")
    c.setStrokeColor(F.CORAL); c.setLineWidth(0.6); c.line(60, synth_y - 7, 195, synth_y - 7)

    grid_y = synth_y - 22; cell_w = (W - 120 - 10)/2; cell_h = 44
    t = ctx.trig
    def cell(x, y, w, h, label, value):
        c.setFillColor(F.CARD_BG); c.roundRect(x, y, w, h, 5, fill=1, stroke=0)
        c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 7.5); c.drawString(x + 12, y + h - 14, label.upper())
        c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 11); c.drawString(x + 12, y + 12, value)
    cell(60, grid_y - cell_h, cell_w, cell_h, "Image", t["image"])
    cell(60 + cell_w + 10, grid_y - cell_h, cell_w, cell_h, "Attribut", t["attribut"])
    cell(60, grid_y - 2*cell_h - 8, cell_w, cell_h, "Élément", t["element"])
    cell(60 + cell_w + 10, grid_y - 2*cell_h - 8, cell_w, cell_h, "Couleurs", t["couleurs"])
    cell(60, grid_y - 3*cell_h - 16, W - 120, cell_h, "Relation familiale", t["relation"])

    # Profil énergétique (textes validés par Aurélie, brief 11 juin 2026 — sans ligne d'humilité,
    # portée par le cadre d'intro de la page)
    tend_y = grid_y - 3*cell_h - 40
    c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 13)
    c.drawString(60, tend_y, f"Ton profil énergétique : {t['attribut']}")
    c.setStrokeColor(F.CORAL); c.setLineWidth(0.6); c.line(60, tend_y - 7, 235, tend_y - 7)

    tend = t.get("profil", "").strip() or "[Profil à venir]"
    tend_style = ParagraphStyle("Tend", fontName="Sans", fontSize=9.5, leading=14,
                                textColor=F.TEXT_DARK, alignment=TA_LEFT)
    tend_para = Paragraph(tend, tend_style)
    _, tend_h = tend_para.wrap(W - 120, 1000)
    tend_para.drawOn(c, 60, (tend_y - 18) - tend_h)

    _footer(c, ctx, with_site_link=False)
    c.showPage()

# ============================================================
#  PAGES 3 & 4 — Emplacements
# ============================================================
def _page_emplacements(c, ctx, page_no, favorable):
    _bg(c); _header(c, ctx, page_no)
    title_y = H - 96
    if favorable:
        _title(c, title_y, "Tes 4 emplacements favorables", "Les secteurs où l'énergie te soutient")
        intro = ("Ces quatre emplacements portent un Qi favorable pour toi : chacun avec sa propre "
                 "couleur énergétique, son intensité, son domaine. <font name='SansBold'>Plus le score est haut, "
                 "plus l'énergie est forte et active. Plus il est bas, plus elle est douce et reposante.</font> "
                 "Aucun n'est meilleur qu'un autre : tout dépend de ce que tu cherches à nourrir dans ta vie.")
        scores = [90, 80, 70, 60]
    else:
        _title(c, title_y, "Tes 4 emplacements défavorables", "Les secteurs où l'énergie te pèse")
        intro = ("Ces quatre emplacements portent un Qi défavorable pour toi : des intensités énergétiques "
                 "mal alignées avec ton trigramme natal, qui peuvent peser quand on s'y expose longtemps. "
                 "<font name='SansBold'>Plus le score est élevé en valeur absolue (de -60 vers -90), "
                 "plus l'énergie est puissante. Il y a un vrai saut de gravité entre les deux premières "
                 "et les deux dernières.</font> Le -60 reste à éviter sans inquiétude particulière. "
                 "Les -80 et -90 sont des énergies vraiment néfastes : à éviter absolument, à transformer "
                 "si elles tombent sur des secteurs importants, ou à fréquenter le moins possible.")
        scores = [-60, -70, -80, -90]

    intro_y = title_y - 48
    intro_style = ParagraphStyle("Intro", fontName="Sans", fontSize=9, leading=12.6,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    intro_para = Paragraph(intro, intro_style)
    _, intro_h = intro_para.wrap(W - 120, 400)
    intro_para.drawOn(c, 60, intro_y - intro_h)

    # Cartes à hauteur DYNAMIQUE : elles s'adaptent au texte -> plus de débordement.
    cards_y_top = intro_y - intro_h - 14
    card_x = 60; card_w = W - 120
    card_gap = 7
    bw = 62                       # médaillon (direction + score)
    content_left = 12 + bw + 16
    header_zone = 48              # hauteur réservée nom + surnom + filet
    pad_bottom = 13
    desc_style = ParagraphStyle("Desc", fontName="Sans", fontSize=8.4, leading=11.5,
                                textColor=F.TEXT_DARK, alignment=TA_LEFT)
    cw = card_w - content_left - 20   # largeur texte avec marge droite confortable

    y_cursor = cards_y_top
    for score in scores:
        qi = ctx.qi_by_score(score)
        direction = ctx.empl_dir(score)
        badge_col = F.SAGE_DARK if favorable else F.score_color(score)

        desc = Paragraph(F.to_rl_markup(qi["description"]), desc_style)
        _, dh = desc.wrap(cw, 1000)
        card_h = max(header_zone + dh + pad_bottom, bw + 24)
        y = y_cursor - card_h

        c.setFillColor(F.CARD_BG); c.roundRect(card_x, y, card_w, card_h, 8, fill=1, stroke=0)

        bx = card_x + 12; by = y + (card_h - bw) / 2
        c.setFillColor(badge_col); c.roundRect(bx, by, bw, bw, 7, fill=1, stroke=0)
        c.setFillColor(F.CREAM); c.setFont("SerifBold", 20)
        c.drawCentredString(bx + bw/2, by + bw/2 + 1, direction)
        c.setFont("Sans", 8.5); c.drawCentredString(bx + bw/2, by + 11, signe(score))

        cx = card_x + content_left
        c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 13.5)
        nom = qi["nom"]; c.drawString(cx, y + card_h - 20, nom)
        nom_w = c.stringWidth(nom, "SerifBold", 13.5)
        ci, ciw, cih = F.cjk_image(qi["caractere"], 26, color=F.color_rgba(F.SAGE_DARK))
        chh = 13; cw2 = ciw * (chh / cih)
        c.drawImage(ci, cx + nom_w + 8, y + card_h - 22, width=cw2, height=chh, mask='auto')
        c.setFont("SerifItalic", 10); c.setFillColor(F.TEXT_MUTED)
        c.drawString(cx, y + card_h - 36, qi["surnom"])
        c.setStrokeColor(F.CORAL); c.setLineWidth(0.5); c.line(cx, y + card_h - 44, cx + 25, y + card_h - 44)
        desc.drawOn(c, cx, (y + card_h - header_zone) - dh)

        y_cursor = y - card_gap

    _footer(c, ctx)
    c.showPage()

def page3(c, ctx): _page_emplacements(c, ctx, 3, True)
def page4(c, ctx): _page_emplacements(c, ctx, 4, False)

# ============================================================
#  PAGES 5 & 6 — Directions
# ============================================================
def _qi_block(c, x, y_top, w, score, badge_color, nom, caractere, mots_cles, directions):
    line_h = 12.5; header_h = 19; pad_top = 9; pad_bottom = 5
    block_h = header_h + len(directions) * line_h + pad_top + pad_bottom
    c.setFillColor(F.CARD_BG); c.roundRect(x, y_top - block_h, w, block_h, 5, fill=1, stroke=0)
    badge_y = y_top - 18
    c.setFillColor(badge_color); c.roundRect(x + 8, badge_y, 36, 14, 3, fill=1, stroke=0)
    c.setFillColor(F.CREAM); c.setFont("SansBold", 8); c.drawCentredString(x + 26, badge_y + 4, score)
    c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 11)
    name_x = x + 52; c.drawString(name_x, badge_y + 3, nom)
    nom_w = c.stringWidth(nom, "SerifBold", 11)
    ci, ciw, cih = F.cjk_image(caractere, 40, color=F.color_rgba(badge_color))
    ch = 13; cw = ciw * (ch / cih)
    c.drawImage(ci, name_x + nom_w + 6, badge_y + 1, width=cw, height=ch, mask='auto')
    c.setFont("SerifItalic", 9); c.setFillColor(F.TEXT_MUTED)
    c.drawRightString(x + w - 10, badge_y + 3, mots_cles)
    c.setStrokeColor(badge_color); c.setLineWidth(0.4); c.line(x + 8, badge_y - 4, x + w - 8, badge_y - 4)

    dir_y = y_top - header_h - pad_top
    for (label, char, romaji, deg1, deg2) in directions:
        c.setFillColor(F.TEXT_DARK); c.setFont("SansBold", 9); c.drawString(x + 18, dir_y - 4, label)
        chi, chw, chh = F.cjk_image(char, 36, color=F.color_rgba(F.TEXT_DARK))
        chd = 12; chwd = chw * (chd / chh)
        c.drawImage(chi, x + 80, dir_y - 5, width=chwd, height=chd, mask='auto')
        c.setFont("Serif", 9); c.setFillColor(F.TEXT_DARK)
        c.drawString(x + 80 + chwd + 6, dir_y - 4, romaji)
        c.setFont("Serif", 9); c.setFillColor(F.TEXT_MUTED)
        c.drawRightString(x + w - 14, dir_y - 4, f"{deg1} – {deg2}")
        dir_y -= line_h
    return block_h

def _dirs_for(ctx, qi_key):
    out = []
    for d in ctx.g["directions24"]:
        if d["qi"] == qi_key:
            parts = [p.strip() for p in d["degres"].split("–")]
            deg1, deg2 = (parts + [""])[:2]
            out.append((d["label"], d["caractere"], d["montagne"], deg1, deg2))
    return out

def _page_directions(c, ctx, page_no, favorable):
    _bg(c); _header(c, ctx, page_no)
    n_fav = sum(1 for d in ctx.g["directions24"] if d["score"] > 0)
    n = n_fav if favorable else 24 - n_fav
    title_y = H - 100
    if favorable:
        _title(c, title_y, f"Tes {n} directions favorables", "Les sous-directions de 15° qui te soutiennent")
        intro = (
            "Tu entres maintenant dans la partie la plus précise — "
            "et probablement la plus précieuse — de cette fiche.<br/><br/>"
            "Le feng shui qu'on rencontre couramment dans les magazines et les blogs "
            "propose souvent des recettes du type « mets ta cuisine au Sud-Est, ta chambre au Nord ». "
            "<font name='SansBold'>Ces recettes sont fausses</font> : elles viennent d'un bagua "
            "occidental qui n'a rien à voir avec le feng shui traditionnel — où c'est ton Ming Gua "
            "qui détermine <font name='SansBold'>tes</font> emplacements favorables, pas une grille universelle.<br/><br/>"
            "Et même avec les emplacements bien travaillés, il reste une dimension qu'il ne faut "
            "surtout pas oublier : <font name='SansBold'>les directions</font>. "
            "Très puissantes, bien combinées aux emplacements, elles deviennent essentielles. "
            "Un exemple parlant : un lit posé dans un excellent emplacement, mais dont la tête est "
            "orientée vers une mauvaise direction — et tout le travail fait en amont est gâché.<br/><br/>"
            "Le système traditionnel chinois découpe chacune des 8 directions cardinales et "
            "intercardinales en 3 sous-directions de 15° chacune, formant la roue des 24 montagnes. "
            "Chaque sous-direction porte une énergie qui lui est propre, qui interagit différemment "
            "avec ton Ming Gua. <font name='SansBold'>Cette précision change tout : "
            "pour un même Ming Gua, deux sous-directions voisines peuvent porter des énergies opposées.</font><br/><br/>"
            "Concrètement : se dire « orienté vers le Sud », ça ne veut rien dire pour un consultant "
            "traditionnel. Le S1, le S2 et le S3 peuvent porter des énergies très différentes pour la "
            "même personne. C'est la lecture fine que seule une boussole précise "
            "(le <font name='SansItalic'>Luo Pan</font>, dans la tradition) permet vraiment d'exploiter "
            "— et que tu trouves ici, calculée spécifiquement pour ton Ming Gua."
        )
        intro_fs, intro_lead = 8.5, 11.8
        ordre = ORDRE_FAV
    else:
        _title(c, title_y, f"Tes {n} directions défavorables", "Les sous-directions de 15° à éviter")
        intro = (
            "Même principe que les directions favorables : "
            "<font name='SansBold'>plus le score est élevé en valeur absolue (de -60 vers -90), "
            "plus l'énergie est puissante.</font> "
            "Le -60 reste à éviter sans inquiétude particulière. "
            "Les -80 et -90 sont des énergies vraiment néfastes — "
            "à éviter absolument, à transformer si elles tombent sur des secteurs importants, "
            "ou à fréquenter le moins possible."
        )
        intro_fs, intro_lead = 9, 12.5
        ordre = ORDRE_DEFAV

    intro_style = ParagraphStyle("Intro", fontName="Sans", fontSize=intro_fs, leading=intro_lead,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    intro_para = Paragraph(intro, intro_style)
    _, intro_h = intro_para.wrap(W - 144, 1000)
    intro_y_top = title_y - 50
    box_pad = 10; box_h = intro_h + 2*box_pad; box_y = intro_y_top - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.CORAL); c.rect(60, box_y, 3, box_h, fill=1, stroke=0)
    intro_para.drawOn(c, 72, box_y + box_pad)

    current_y = box_y - 16; block_x = 60; block_w = W - 120; block_gap = 5
    for qi_key in ordre:
        qi = ctx.qi[qi_key]
        dirs = _dirs_for(ctx, qi_key)
        if not dirs: continue
        color = F.score_color(qi["score"])
        mots = " · ".join(qi["motsCles"])
        h = _qi_block(c, block_x, current_y, block_w, signe(qi["score"]), color,
                      qi["nom"], qi["caractere"], mots, dirs)
        current_y -= (h + block_gap)

    _footer(c, ctx)
    c.showPage()

def old_page_directions_fav(c, ctx): _page_directions(c, ctx, 5, True)   # hors lead magnet
def old_page_directions_defav(c, ctx): _page_directions(c, ctx, 6, False)  # hors lead magnet

# ============================================================
#  PAGE 5 / 7 — Distinction emplacements / directions
#  (seule page, avec la 6, où le mot « directions » est autorisé)
# ============================================================
def page_distinction(c, ctx):
    _bg(c); _header(c, ctx, 5)
    title_y = H - 96
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 24)
    c.drawCentredString(W/2, title_y, "Emplacements et directions")
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(W/2 - 28, title_y - 11, W/2 + 28, title_y - 11)
    c.setFont("SerifItalic", 12); c.setFillColor(F.TEXT_MUTED)
    c.drawCentredString(W/2, title_y - 26, "La grande distinction à poser une fois pour toutes")

    intro = (
        "Tu as maintenant vu tes 8 emplacements (pages 3-4). "
        "Avant d'aller plus loin, faisons le point sur une distinction essentielle. "
        "<font name='SansBold'>Cette histoire d'emplacements et de directions perturbe beaucoup de gens</font>, "
        "pour deux raisons : la plupart ne connaissent pas la distinction au départ, "
        "et même en la connaissant, on s'en emmêle facilement les pinceaux entre les deux. "
        "C'est pourtant crucial de bien comprendre les deux : ces notions sont "
        "<font name='SansBold'>complètement différentes et en même temps très complémentaires</font>."
    )
    intro_style = ParagraphStyle("Intro", fontName="Sans", fontSize=8.8, leading=12.2,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    intro_para = Paragraph(intro, intro_style)
    _, intro_h = intro_para.wrap(W - 144, 1000)
    intro_y_top = title_y - 46; box_pad = 9; box_h = intro_h + 2*box_pad; box_y = intro_y_top - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.CORAL); c.rect(60, box_y, 3, box_h, fill=1, stroke=0)
    intro_para.drawOn(c, 72, box_y + box_pad)

    table_y = box_y - 16; col_w = (W - 120 - 10)/2
    lx = 60; rx = lx + col_w + 10; header_h = 28
    c.setFillColor(F.SAGE_DARK); c.roundRect(lx, table_y - header_h, col_w, header_h, 5, fill=1, stroke=0)
    c.setFillColor(F.CORAL_DARK); c.roundRect(rx, table_y - header_h, col_w, header_h, 5, fill=1, stroke=0)
    c.setFillColor(F.CREAM); c.setFont("SerifBold", 13)
    c.drawCentredString(lx + col_w/2, table_y - 14, "EMPLACEMENT")
    c.drawCentredString(rx + col_w/2, table_y - 14, "DIRECTION")
    c.setFont("SerifItalic", 9)
    c.drawCentredString(lx + col_w/2, table_y - 25, "« où tu vis »")
    c.drawCentredString(rx + col_w/2, table_y - 25, "« où tu pointes »")

    lignes = [
        ("C'est quoi", "Un secteur de ta maison", "Une orientation, un cap"),
        ("Comment on le détermine", "On découpe le plan en 8 secteurs (la grille Ba Zhai)",
         "On mesure un degré précis d'orientation à la boussole (15° près pour les 24 montagnes)"),
        ("À quoi ça sert", "Savoir comment <b>organiser</b> ta maison : où placer une pièce, une activité",
         "Savoir comment <b>orienter</b> tes meubles (lit, bureau, cuisinière...)"),
    ]
    row_h = 44; row_y = table_y - header_h - 5
    cell_style = ParagraphStyle("Cell", fontName="Sans", fontSize=8.6, leading=11.6,
                                textColor=F.TEXT_DARK, alignment=TA_LEFT)
    for label, vl, vr in lignes:
        c.setFillColor(F.CARD_BG); c.roundRect(lx, row_y - row_h, col_w, row_h, 4, fill=1, stroke=0)
        c.roundRect(rx, row_y - row_h, col_w, row_h, 4, fill=1, stroke=0)
        c.setFillColor(F.TEXT_MUTED); c.setFont("SansBold", 7)
        c.drawString(lx + 10, row_y - 14, label.upper()); c.drawString(rx + 10, row_y - 14, label.upper())
        pl = Paragraph(vl, cell_style); pr = Paragraph(vr, cell_style)
        _, plh = pl.wrap(col_w - 20, 100); _, prh = pr.wrap(col_w - 20, 100)
        pl.drawOn(c, lx + 10, row_y - 18 - plh); pr.drawOn(c, rx + 10, row_y - 18 - prh)
        row_y -= (row_h + 4)
    table_bottom = row_y + 4

    # Pictogrammes
    schema_y = table_bottom - 10; psize = 78; pgap = 60
    plx = (W - (2*psize + pgap))/2
    house_x = plx; house_y = schema_y - psize; cs = psize/3
    c.setFillColor(F.CARD_BG); c.roundRect(house_x, house_y, psize, psize, 4, fill=1, stroke=0)
    c.setStrokeColor(F.SAGE_LIGHT); c.setLineWidth(0.5)
    for i in range(1, 3):
        c.line(house_x + i*cs, house_y, house_x + i*cs, house_y + psize)
        c.line(house_x, house_y + i*cs, house_x + psize, house_y + i*cs)
    labels = [("NO",0,2),("N",1,2),("NE",2,2),("O",0,1),("",1,1),("E",2,1),("SO",0,0),("S",1,0),("SE",2,0)]
    c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 6)
    for lab, col, row in labels:
        if lab:
            c.drawCentredString(house_x + col*cs + cs/2, house_y + row*cs + cs/2 - 2, lab)
    hx = house_x + 1*cs; hy = house_y + 2*cs
    c.setFillColor(Color(0.37, 0.42, 0.31, alpha=0.4)); c.rect(hx + 1, hy + 1, cs - 2, cs - 2, fill=1, stroke=0)
    c.setFillColor(F.CREAM); c.setFont("SansBold", 6); c.drawCentredString(hx + cs/2, hy + cs/2 - 2, "N")
    c.setFillColor(F.CORAL); c.circle(hx + cs/2, hy + cs/2 + 5, 2.2, fill=1, stroke=0)
    c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 9); c.drawCentredString(house_x + psize/2, house_y - 14, "« Je suis »")
    c.setFont("SerifItalic", 8.5); c.setFillColor(F.TEXT_MUTED); c.drawCentredString(house_x + psize/2, house_y - 26, "dans cet emplacement")

    ccx = plx + psize + pgap + psize/2; ccy = house_y + psize/2; cr = psize/2 - 3
    c.setFillColor(F.CARD_BG); c.circle(ccx, ccy, cr + 3, fill=1, stroke=0)
    c.setStrokeColor(F.SAGE_LIGHT); c.setLineWidth(0.8); c.circle(ccx, ccy, cr, fill=0, stroke=1)
    for i in range(24):
        a = math.radians(i*15)
        xo = ccx + cr*math.sin(a); yo = ccy + cr*math.cos(a)
        ir = cr - (4 if i % 3 == 0 else 2.5)
        xi = ccx + ir*math.sin(a); yi = ccy + ir*math.cos(a)
        c.setLineWidth(0.7 if i % 3 == 0 else 0.3); c.line(xo, yo, xi, yi)
    c.setFillColor(F.TEXT_MUTED); c.setFont("Sans", 6.5)
    c.drawCentredString(ccx, ccy + cr + 6, "N"); c.drawCentredString(ccx, ccy - cr - 9, "S")
    c.drawCentredString(ccx + cr + 7, ccy - 2, "E"); c.drawCentredString(ccx - cr - 7, ccy - 2, "O")
    a = math.radians(180); al = cr - 5
    tx = ccx + al*math.sin(a); ty = ccy + al*math.cos(a)
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.6); c.line(ccx, ccy, tx, ty)
    aw = 3.5; px = math.cos(a); py = -math.sin(a)
    bx = tx - 6*math.sin(a); by = ty - 6*math.cos(a)
    c.setFillColor(F.CORAL); path = c.beginPath()
    path.moveTo(tx, ty); path.lineTo(bx + px*aw, by + py*aw); path.lineTo(bx - px*aw, by - py*aw); path.close()
    c.drawPath(path, fill=1, stroke=0)
    c.setFillColor(F.SAGE_DARK); c.circle(ccx, ccy, 1.8, fill=1, stroke=0)
    c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 9); c.drawCentredString(ccx, house_y - 14, "« Je regarde vers »")
    c.setFont("SerifItalic", 8.5); c.setFillColor(F.TEXT_MUTED); c.drawCentredString(ccx, house_y - 26, "cette direction")

    mnemo_y = house_y - 36
    mnemo = (
        "<font name='SansBold' size='11'>« Je suis »</font> "
        "<font name='Sans' size='9'>(emplacement)</font>  "
        "<font name='SansBold' size='11'>vs</font>  "
        "<font name='SansBold' size='11'>« Je regarde vers »</font> "
        "<font name='Sans' size='9'>(direction)</font><br/>"
        "<font name='SansItalic' size='8.5' color='#7A7568'>"
        "Exemple : Je suis dans mon bureau qui est en secteur Nord, "
        "et je regarde vers la direction Sud 2.</font>"
    )
    mnemo_style = ParagraphStyle("Mnemo", fontName="Sans", fontSize=10, leading=14,
                                 textColor=F.TEXT_DARK, alignment=TA_CENTER)
    mnemo_para = Paragraph(mnemo, mnemo_style)
    _, mnemo_h = mnemo_para.wrap(W - 144, 1000)
    box_pad = 10; box_h = mnemo_h + 2*box_pad; box_y = mnemo_y - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.CORAL); c.rect(60, box_y, 3, box_h, fill=1, stroke=0)
    mnemo_para.drawOn(c, 70, box_y + box_pad)

    # Texte de fin (validé) — pont vers la page 6
    final = (
        "Tu as maintenant ta carte : 8 emplacements, et une distinction essentielle entre "
        "« où tu vis » et « où tu pointes ».<br/><br/>"
        "Mais il reste une question, peut-être la plus concrète de toutes : "
        "<font name='SansBold'>est-ce que ton lit, ton bureau, ta porte d'entrée, ta cuisinière "
        "sont orientés vers une direction qui te porte… ou qui t'épuise ?</font><br/><br/>"
        "Parce que tu peux être dans un excellent emplacement, mais avec la tête de lit qui "
        "pointe vers une direction à -80. Et tout le bénéfice s'efface.<br/><br/>"
        "C'est exactement là que la page suivante t'emmène."
    )
    final_style = ParagraphStyle("Final", fontName="Sans", fontSize=8.8, leading=12.2,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    final_para = Paragraph(final, final_style)
    _, final_h = final_para.wrap(W - 144, 1000)
    final_para.drawOn(c, 72, (box_y - 12) - final_h)

    _footer(c, ctx)
    c.showPage()

# ============================================================
#  PAGE 6 / 7 — Et maintenant, chez toi ?  (teasing Offre 1)
# ============================================================
def page_offre(c, ctx):
    _bg(c); _header(c, ctx, 6)
    title_y = H - 96
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 24)
    c.drawCentredString(W/2, title_y, "Et maintenant, chez toi ?")
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(W/2 - 28, title_y - 11, W/2 + 28, title_y - 11)
    c.setFont("SerifItalic", 12); c.setFillColor(F.TEXT_MUTED)
    c.drawCentredString(W/2, title_y - 26, "Ce que ton profil peut te révéler de concret")

    body_style = ParagraphStyle("Body6", fontName="Sans", fontSize=9.5, leading=14,
                                textColor=F.TEXT_DARK, alignment=TA_LEFT)

    texte = (
        "En ce moment, pendant que tu lis cette fiche, ton lit pointe dans une direction "
        "précise. Ton bureau aussi. Ta porte d'entrée laisse entrer l'énergie depuis un "
        "angle précis. Ta cuisinière oriente tes repas (et ton énergie) vers un cap que "
        "tu n'as probablement jamais mesuré.<br/><br/>"
        "Chacune de ces directions active l'un de tes 8 types de Qi. Et selon ton Ming Gua, "
        "ce Qi peut être Sheng Qi (+90), ton meilleur allié, ou Jue Ming (-90), ton pire "
        "frein. Souvent, c'est entre les deux. Mais la nuance change tout.<br/><br/>"
        "Ce que tu as entre les mains aujourd'hui, c'est ta carte d'identité : le "
        "<font name='SansItalic'>qui tu es</font> dans l'espace. C'est le socle.<br/><br/>"
        "<font name='SansBold'>L'étape suivante, c'est la lecture de ce qui se passe chez toi "
        "<font name='SansItalic'>maintenant</font>.</font>"
    )
    p = Paragraph(texte, body_style)
    _, ph = p.wrap(W - 130, 1000)
    text_top = title_y - 52
    p.drawOn(c, 65, text_top - ph)

    # --- Encart Offre 1 (nom verrouillé) ---
    offre = (
        "C'est ce que fait <font name='SansBold'><font name='SansItalic'>Ce que tes directions "
        "disent de ta maison</font></font>, ton diagnostic personnalisé : tu me donnes 5 mesures "
        "à la boussole (lit, bureau, porte, cuisinière, fauteuil), et tu reçois un rapport qui te "
        "dit, pour chaque direction, quel Qi elle active pour toi, et quoi faire avec.<br/><br/>"
        f"Pas de jargon. Pas de grille à interpréter tout{'e' if ctx.fe else ''} seul{ctx.fe}. "
        "Une lecture faite pour toi, avec des recommandations concrètes et hiérarchisées."
    )
    offre_style = ParagraphStyle("Offre", fontName="Sans", fontSize=9.5, leading=14,
                                 textColor=F.CREAM, alignment=TA_LEFT)
    op = Paragraph(offre, offre_style)
    _, oph = op.wrap(W - 154, 1000)
    box_pad = 16
    box_h = oph + 2 * box_pad
    box_top = text_top - ph - 22
    box_y = box_top - box_h
    c.setFillColor(F.SAGE_DARK)
    c.roundRect(60, box_y, W - 120, box_h, 10, fill=1, stroke=0)
    op.drawOn(c, 77, box_y + box_pad)

    # --- Bloc de clôture : placeholder de lancement OU bouton Offre 1 ---
    cl_top = box_y - 24
    if OFFRE1_DISPONIBLE and OFFRE1_URL:
        btn_label = "Découvrir le diagnostic" + (f"  ·  {OFFRE1_PRIX}" if OFFRE1_PRIX else "")
        c.setFont("SansBold", 11)
        bw = c.stringWidth(btn_label, "SansBold", 11) + 44
        bx = (W - bw) / 2; bh = 32; by = cl_top - bh
        c.setFillColor(F.CORAL); c.roundRect(bx, by, bw, bh, 16, fill=1, stroke=0)
        c.setFillColor(F.CREAM); c.drawCentredString(W/2, by + 11, btn_label)
        c.linkURL(OFFRE1_URL, (bx, by, bx + bw, by + bh), relative=0)
        after_y = by - 22
    else:
        c.setFont("SerifItalic", 11.5); c.setFillColor(F.TEXT_DARK)
        c.drawCentredString(W/2, cl_top - 12,
                            "Le diagnostic sera disponible très prochainement.")
        premiere = "la première informée" if ctx.fe else "le premier informé"
        c.drawCentredString(W/2, cl_top - 28, f"Tu seras {premiere} par email.")
        after_y = cl_top - 52

    invite = (
        "En attendant, si cette fiche t'a fait voir ta maison un peu différemment (ou si elle "
        "a soulevé une question), <font name='SansBold'>réponds à ce mail</font>. "
        "Je lis tout, je réponds."
    )
    inv_p = Paragraph(invite, body_style)
    iw, ih = inv_p.wrap(W - 130, 1000)
    inv_p.drawOn(c, 65, after_y - ih)
    c.linkURL(URL_MAIL, (65, after_y - ih - 2, 65 + iw, after_y + 2), relative=0)

    c.setFont("SerifItalic", 12); c.setFillColor(F.CORAL)
    c.drawRightString(W - 65, after_y - ih - 26, "Aurélie")

    _footer(c, ctx)
    c.showPage()

# ============================================================
#  (ancienne page 8 — retirée du lead magnet, conservée pour l'Offre 1)
# ============================================================
def _draw_lit(c, x, y, w, h):
    cx = x + w/2; cy = y + h/2
    lw = w*0.5; lh = h*0.62; lx = cx - lw/2; ly = cy - lh/2 - 5
    c.setStrokeColor(F.SAGE_DARK); c.setFillColor(F.CARD_BG); c.setLineWidth(1.4)
    c.roundRect(lx, ly, lw, lh, 3, fill=1, stroke=1)
    c.setStrokeColor(F.SAGE_DARK); c.setLineWidth(3); c.line(lx, ly + lh, lx + lw, ly + lh)
    c.setFillColor(F.SAGE_LIGHT); c.setStrokeColor(F.SAGE_DARK); c.setLineWidth(0.8)
    c.circle(cx, ly + lh - 9, 5, fill=1, stroke=1)
    bw = 11; bh = lh*0.45; c.roundRect(cx - bw/2, ly + lh*0.18, bw, bh, bw/2, fill=1, stroke=1)
    asx = cx; asy = ly + lh + 1.5; aey = asy + 22
    c.setStrokeColor(F.SAGE_90); c.setLineWidth(1.6); c.line(asx, asy, asx, aey)
    c.line(asx, aey, asx - 3, aey - 4); c.line(asx, aey, asx + 3, aey - 4)
    mcx = asx + 18; mcy = asy + 14; mr = 8
    c.setFillColor(F.CARD_BG); c.setStrokeColor(F.SAGE_70); c.setLineWidth(0.7); c.circle(mcx, mcy, mr, fill=1, stroke=1)
    for ad in [0, 90, 180, 270]:
        a = math.radians(ad)
        c.line(mcx + mr*math.sin(a), mcy + mr*math.cos(a), mcx + (mr-2)*math.sin(a), mcy + (mr-2)*math.cos(a))
    c.setFillColor(F.SAGE_DARK); c.setFont("SansBold", 5.5); c.drawCentredString(mcx, mcy + mr + 2.5, "N")

def _draw_bureau(c, x, y, w, h):
    cx = x + w/2; cy = y + h/2
    bw = w*0.55; bh = h*0.16; bx = cx - bw/2; by = cy + 6
    c.setStrokeColor(F.SAGE_DARK); c.setFillColor(F.CARD_BG); c.setLineWidth(1.4)
    c.roundRect(bx, by, bw, bh, 2, fill=1, stroke=1)
    chy = by - 11; c.setStrokeColor(F.SAGE_DARK); c.setLineWidth(1.4); c.setFillColor(F.SAGE_60)
    p = c.beginPath()
    p.moveTo(cx - 7, chy + 4.5); p.lineTo(cx + 7, chy + 4.5); p.lineTo(cx + 9, chy - 4.5); p.lineTo(cx - 9, chy - 4.5); p.close()
    c.drawPath(p, fill=1, stroke=1)
    c.setFillColor(F.SAGE_DARK); c.setStrokeColor(F.SAGE_DARK); c.setLineWidth(0.8); c.circle(cx, chy + 1, 4.5, fill=1, stroke=1)
    asx = cx; asy = by + bh + 1.5; aey = asy + 18
    c.setStrokeColor(F.SAGE_90); c.setLineWidth(1.6); c.line(asx, asy, asx, aey)
    c.line(asx, aey, asx - 3, aey - 4); c.line(asx, aey, asx + 3, aey - 4)
    mcx = asx + 18; mcy = asy + 11; mr = 8
    c.setFillColor(F.CARD_BG); c.setStrokeColor(F.SAGE_70); c.setLineWidth(0.7); c.circle(mcx, mcy, mr, fill=1, stroke=1)
    for ad in [0, 90, 180, 270]:
        a = math.radians(ad)
        c.line(mcx + mr*math.sin(a), mcy + mr*math.cos(a), mcx + (mr-2)*math.sin(a), mcy + (mr-2)*math.cos(a))
    c.setFillColor(F.SAGE_DARK); c.setFont("SansBold", 5.5); c.drawCentredString(mcx, mcy + mr + 2.5, "N")

def old_page_regarder(c, ctx):  # hors lead magnet (contenu Offre 1)
    _bg(c); _header(c, ctx, 8)
    title_y = H - 100
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 21)
    c.drawCentredString(W/2, title_y, "Ce que tu peux déjà regarder chez toi")
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(W/2 - 28, title_y - 11, W/2 + 28, title_y - 11)

    chapeau = (
        "<font name='SansItalic'>En Ba Zhai, il y a beaucoup de combinaisons possibles entre "
        "emplacements et directions, et tout un ordre de priorité dans la lecture. "
        "C'est ce qu'on explore quand on va plus loin.<br/><br/>"
        "Mais déjà, avec ce que tu as entre les mains — ton Ming Gua et tes directions — "
        "il y a <font name='SansBold'>deux choses très concrètes</font> que tu peux observer chez toi "
        "dès maintenant.</font>"
    )
    chapeau_style = ParagraphStyle("Chapeau", fontName="Sans", fontSize=9.2, leading=13,
                                   textColor=F.TEXT_DARK, alignment=TA_LEFT)
    chapeau_para = Paragraph(chapeau, chapeau_style)
    _, chapeau_h = chapeau_para.wrap(W - 144, 1000)
    chapeau_y_top = title_y - 30; box_pad = 10; box_h = chapeau_h + 2*box_pad; box_y = chapeau_y_top - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.SAGE_70); c.rect(60, box_y, 3, box_h, fill=1, stroke=0)
    chapeau_para.drawOn(c, 70, box_y + box_pad)

    fe = ctx.fe
    cartes = [
        {"numero": "1", "titre": "La direction de ton lit",
         "soustitre": "vers où pointe le haut de ta tête de lit — milieu de la tête de lit",
         "texte": (f"Quand tu es allongé{fe} dans ton lit, vers quelle direction pointe le haut de "
                   "ta tête ? On prend la mesure au milieu de la tête de lit. "
                   "Cette direction active <font name='SansBold'>un des 8 types de Qi</font> "
                   "pour toi — l'un de tes quatre favorables (Sheng Qi, Tian Yi, Yan Nian, Fu Wei) "
                   "ou l'un de tes quatre défavorables (Huo Hai, Wu Gui, Liu Sha, Jue Ming)."),
         "schema": "lit"},
        {"numero": "2", "titre": "La direction de ton poste de travail",
         "soustitre": f"ou de tout endroit où tu passes beaucoup de temps assis{fe}",
         "texte": (f"Quand tu es assis{fe} à ton bureau, vers quelle direction pointe ton regard ? "
                   "Pour mesurer en vrai : tu poses ta boussole sur la tranche avant du bureau, "
                   "alignée dans le sens où tu regardes. C'est ça, ta direction de travail.<br/><br/>"
                   "Et ça vaut pour tout endroit où tu passes des heures dans une orientation "
                   "stable : ton bureau chez toi, ton poste au travail, le fauteuil où tu lis "
                   "tous les soirs... À chaque fois, c'est la direction que tu "
                   "<font name='SansBold'>occupes</font> pendant ces longues heures qui compte. "
                   "Même logique : un des 8 Qi se met en mouvement pendant tout ce temps."),
         "schema": "bureau"},
    ]
    cartes_y_top = box_y - 16; carte_x = 60; carte_w = W - 120; carte_gap = 8
    texte_style = ParagraphStyle("Texte", fontName="Sans", fontSize=9, leading=12.8,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    current_y = cartes_y_top
    for carte in cartes:
        p_texte = Paragraph(carte["texte"], texte_style)
        schema_w = 130; text_w = carte_w - schema_w - 30
        _, pt_h = p_texte.wrap(text_w, 500)
        carte_h = max(pt_h + 56, 130); y_bot = current_y - carte_h
        c.setFillColor(F.CARD_BG); c.roundRect(carte_x, y_bot, carte_w, carte_h, 6, fill=1, stroke=0)
        c.setFillColor(F.SAGE_70); c.rect(carte_x, y_bot, 4, carte_h, fill=1, stroke=0)
        num_cx = carte_x + 24; num_cy = current_y - 22
        c.setFillColor(F.SAGE_90); c.circle(num_cx, num_cy, 11, fill=1, stroke=0)
        c.setFillColor(F.CREAM); c.setFont("SerifBold", 13); c.drawCentredString(num_cx, num_cy - 4, carte["numero"])
        titre_x = num_cx + 18
        c.setFillColor(F.TEXT_DARK); c.setFont("SerifBold", 13.5); c.drawString(titre_x, current_y - 19, carte["titre"])
        c.setFont("SerifItalic", 9); c.setFillColor(F.TEXT_MUTED); c.drawString(titre_x, current_y - 33, carte["soustitre"])
        p_texte.drawOn(c, carte_x + 18, (current_y - 50) - pt_h)
        sx = carte_x + carte_w - schema_w - 12; sy = y_bot + 8; sh = carte_h - 16
        if carte["schema"] == "lit": _draw_lit(c, sx, sy, schema_w, sh)
        else: _draw_bureau(c, sx, sy, schema_w, sh)
        current_y = y_bot - carte_gap

    concl_y = current_y - 4
    c.setStrokeColor(F.SAGE_70); c.setLineWidth(0.7); c.line(W/2 - 50, concl_y, W/2 + 50, concl_y)
    concl_y -= 12
    conclusion = (
        "Ces deux directions, tu peux les vérifier <font name='SansBold'>dès maintenant</font>. "
        "Et souvent, ça suffit déjà à éclairer des choses — pourquoi tel sommeil, pourquoi telle "
        "ambiance dans tes heures concentrées, pourquoi ça avance ou pas.<br/><br/>"
        "<font name='SansItalic'>Mais c'est vraiment le début du chemin. En Ba Zhai, il y a bien "
        "plus à lire : dans quel secteur de ta maison se trouve ta chambre, ton entrée, ta cuisine "
        "— ce qui demande de poser la grille Ba Zhai sur ton plan. Comment les énergies se "
        "répartissent pièce par pièce. Ce qui se joue pour chacun des membres de la famille. "
        "Les priorités, les compensations possibles, les harmonies à tisser entre tous ces fils.</font><br/><br/>"
        "C'est ce parcours-là que je suis en train de préparer pour toi, et je t'en reparlerai "
        "très bientôt.<br/><br/>"
        "En attendant, si tu veux qu'on garde le fil ensemble, "
        "<font name='SansBold'>réponds à ce mail</font> : raconte-moi ce que tu as découvert en "
        "lisant ta fiche, ou pose-moi la question qui te trotte dans la tête. Je lis tout, je réponds."
    )
    concl_style = ParagraphStyle("Concl", fontName="Sans", fontSize=9, leading=12.8,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    concl_para = Paragraph(conclusion, concl_style)
    cw, ch = concl_para.wrap(W - 130, 1000)
    concl_para.drawOn(c, 65, concl_y - ch)
    c.linkURL(URL_MAIL, (65, concl_y - ch - 1, 65 + cw, concl_y - ch + 40), relative=0)
    c.setFont("SerifItalic", 11); c.setFillColor(F.CORAL); c.drawString(65, concl_y - ch - 12, "Aurélie")

    _footer(c, ctx)
    c.showPage()

# ============================================================
#  PAGE 9 — Qui suis-je
# ============================================================
def page_bio(c, ctx):
    _bg(c); _header(c, ctx, 7)
    photo_size = 105; photo_x = 60; photo_y_top = H - 100; photo_y = photo_y_top - photo_size
    if F.PHOTO_PATH:
        try:
            photo = ImageReader(F.PHOTO_PATH)
            c.drawImage(photo, photo_x, photo_y, width=photo_size, height=photo_size, mask='auto', preserveAspectRatio=True)
        except Exception: pass
    c.setStrokeColor(F.SAGE_70); c.setLineWidth(1.2)
    c.circle(photo_x + photo_size/2, photo_y + photo_size/2, photo_size/2 + 1, fill=0, stroke=1)

    text_x = photo_x + photo_size + 25; text_top = photo_y_top - 8
    c.setFillColor(F.TEXT_MUTED); c.setFont("SerifItalic", 11); c.drawString(text_x, text_top, "Qui suis-je")
    c.setStrokeColor(F.CORAL); c.setLineWidth(1.2); c.line(text_x, text_top - 7, text_x + 26, text_top - 7)
    c.setFillColor(F.SAGE_DARK); c.setFont("Serif", 36); c.drawString(text_x, text_top - 48, "Aurélie")
    tagline = ("<font name='SansItalic' color='#5F6C50'>Tisseuse d'harmonies<br/>"
               "feng shui traditionnel &amp; accompagnement par l'habitat</font>")
    tagline_style = ParagraphStyle("Tagline", fontName="SerifItalic", fontSize=10.5, leading=14,
                                   textColor=F.SAGE_DARK, alignment=TA_LEFT)
    tagline_para = Paragraph(tagline, tagline_style)
    _, tag_h = tagline_para.wrap(W - text_x - 60, 1000)
    tagline_para.drawOn(c, text_x, text_top - 48 - 12 - tag_h)
    identite_bot = min(photo_y, text_top - 48 - 12 - tag_h) - 4

    recit = (
        "J'ai cherché longtemps. Méthodes énergétiques, développement personnel, "
        "feng shui new age, thérapies… J'ai essayé beaucoup de choses avant d'arriver "
        "là où je suis aujourd'hui. Et ce qui ne marchait pas, je l'ai compris après : "
        "c'était trop superficiel, trop décoratif, trop « astuces ».<br/><br/>"
        "En 2015, à bout, j'ai croisé la route du <font name='SansBold'>feng shui "
        "traditionnel chinois</font> : celui d'avant l'occidentalisation, celui qui lit "
        "la maison avec ses montagnes, ses orientations, ses énergies, ses temps. "
        "Ça a été le coup de cœur immédiat. Une cohérence enfin. Quelque chose qui se tient.<br/><br/>"
        "Je me suis formée pendant deux ans. J'ai d'abord pratiqué dans ma propre maison "
        "(mon terrain d'expérimentation) avant d'accompagner d'autres femmes. "
        "Et j'ai vu, encore et encore, le lien profond que nous entretenons avec notre "
        "habitation. Pas par magie : par lecture juste, par actions ciblées, par alignement "
        "entre ce que la maison disait et ce qu'elles traversaient.<br/><br/>"
        "Aujourd'hui je transmets. Pas en oracle qui aurait toutes les réponses, mais "
        "en <font name='SansBold'>tisseuse qui aide à relier les fils</font>. "
        "Parce qu'au fond, ta maison te parle déjà. Mon métier, c'est de t'aider à l'écouter."
    )
    recit_style = ParagraphStyle("Recit", fontName="Sans", fontSize=10, leading=14,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    recit_para = Paragraph(recit, recit_style)
    _, recit_h = recit_para.wrap(W - 120, 1000)
    recit_y_top = identite_bot - 16; recit_para.drawOn(c, 60, recit_y_top - recit_h)
    recit_bot = recit_y_top - recit_h

    carte_y_top = recit_bot - 16
    carte = (
        "<font name='SansBold' color='#7A8B6D' size='7.5'>MA FAÇON DE TRAVAILLER</font><br/><br/>"
        "Je travaille en feng shui traditionnel chinois : sans bagua occidental, sans "
        "« secteur amour », sans astuces déco. Et j'allie cette lecture à un accompagnement "
        "de la personne qui habite : <font name='SansBold'>parce que la maison ouvre des "
        "portes, mais c'est toi qui les franchis</font>."
    )
    carte_style = ParagraphStyle("Carte", fontName="Sans", fontSize=9.5, leading=13.5,
                                 textColor=F.TEXT_DARK, alignment=TA_LEFT)
    carte_para = Paragraph(carte, carte_style)
    _, carte_h = carte_para.wrap(W - 140, 1000)
    box_pad = 12; box_h = carte_h + 2*box_pad; box_y = carte_y_top - box_h
    c.setFillColor(F.CARD_BG); c.roundRect(60, box_y, W - 120, box_h, 6, fill=1, stroke=0)
    c.setFillColor(F.SAGE_70); c.rect(60, box_y, 4, box_h, fill=1, stroke=0)
    carte_para.drawOn(c, 75, box_y + box_pad)
    carte_bot = box_y

    lien_y = carte_bot - 22
    c.setFillColor(F.CORAL); c.setFont("SerifItalic", 14); c.drawString(60, lien_y, "Restons en lien")
    intro_y = lien_y - 20
    c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 9.5)
    c.drawString(60, intro_y, "Pendant que je prépare mes diagnostics, voici où me retrouver :")
    def puce(x, y, main, sec, url):
        c.setFillColor(F.SAGE_70); c.circle(x, y + 3, 2, fill=1, stroke=0)
        tx = x + 8; c.setFillColor(F.TEXT_DARK); c.setFont("Serif", 9.5)
        full = f"{main} : {sec}"; c.drawString(tx, y, full)
        tw = c.stringWidth(full, "Serif", 9.5); c.linkURL(url, (tx - 2, y - 3, tx + tw + 2, y + 11), relative=0)
    px = 70; py = intro_y - 18; lh = 16
    puce(px, py, "YouTube", "@lestisseusesdharmonies", URL_YOUTUBE)
    puce(px, py - lh, "Pinterest", "@lestisseusesdharmonies", URL_PINTEREST)
    puce(px, py - 2*lh, "Site", "lestisseusesdharmonies.fr (en cours de refonte)", URL_SITE)
    rappel_y = py - 2*lh - 24
    rappel = ("<font name='SansItalic'>Et n'oublie pas : tu peux toujours "
              "<font name='SansBold'>répondre à ce mail</font>. Je lis tout, je réponds.</font>")
    rappel_style = ParagraphStyle("Rappel", fontName="Sans", fontSize=9.5, leading=13,
                                  textColor=F.TEXT_DARK, alignment=TA_LEFT)
    rappel_para = Paragraph(rappel, rappel_style)
    rw, rh = rappel_para.wrap(W - 130, 1000)
    rappel_para.drawOn(c, 60, rappel_y - rh)
    c.linkURL(URL_MAIL, (60, rappel_y - rh - 1, 60 + rw, rappel_y + 2), relative=0)

    _footer(c, ctx)
    c.showPage()

# ============================================================
#  Orchestration
# ============================================================
# Lead magnet = 7 pages. Les anciennes pages « directions » (24 montagnes) et
# « ce que tu peux déjà regarder » sont retirées du PDF gratuit (contenu Offre 1) ;
# leurs fonctions restent dans le fichier pour réutilisation future.
_PAGES = (page1, page2, page3, page4, page_distinction, page_offre, page_bio)

def _render(target, gua, prenom, naissance, sexe):
    F.register_fonts()
    ctx = Ctx(gua, prenom, naissance, sexe=sexe)
    c = canvas.Canvas(target, pagesize=A4)
    for fn in _PAGES:
        fn(c, ctx)
    c.save()

def generer(gua, prenom, naissance=None, out="out/fiche.pdf", sexe="femme"):
    _render(out, gua, prenom, naissance, sexe)
    return out

def generer_bytes(gua, prenom, naissance=None, sexe="femme"):
    """Renvoie le PDF en mémoire (pour le service web)."""
    buf = io.BytesIO()
    _render(buf, gua, prenom, naissance, sexe)
    return buf.getvalue()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gua", type=int, required=True, choices=[1,2,3,4,6,7,8,9])
    ap.add_argument("--prenom", required=True)
    ap.add_argument("--naissance", default=None)
    ap.add_argument("--sexe", default="femme", choices=["femme", "homme"])
    ap.add_argument("--out", default="out/fiche.pdf")
    a = ap.parse_args()
    path = generer(a.gua, a.prenom, a.naissance, a.out, sexe=a.sexe)
    print(f"OK : {path}")

if __name__ == "__main__":
    main()
