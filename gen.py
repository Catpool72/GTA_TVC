#!/usr/bin/env python3
"""GRAND THEFT TRABANT VI – BALATON VICE  (TVC 64K paródia-trailer)
Adatgenerátor: font, háttérképek (RLE), sprite-ok, táblák, zene, feliratok -> data.inc
Előnézeti képek: preview_*.png

TVC 16 színű mód: 128x240 képpont, 64 bájt/sor, bájtonként 2 képpont
(bal: b7,b5,b3,b1 ; jobb: b6,b4,b2,b0), szín = I*8+G*4+R*2+B.
"""
import math, random
from PIL import Image, ImageDraw

W, H = 128, 240
SPREAD = [0, 1, 4, 5, 16, 17, 20, 21, 64, 65, 68, 69, 80, 81, 84, 85]
HI, LO = 255, 146
def rgb(c):
    i, g, r, b = (c >> 3) & 1, (c >> 2) & 1, (c >> 1) & 1, c & 1
    v = HI if i else LO
    return (r * v, g * v, b * v)

BLK, BLU, RED, MAG, GRN, CYN, BRN, GRY = range(8)
LBLU, LRED, LMAG, LGRN, LCYN, YEL, WHT = range(9, 16)

def pbyte(l, r):
    return (SPREAD[l] << 1) | SPREAD[r]

# ---------------------------------------------------------------- font
# 3x5 betűk; ékezet: 2 sor (4 képpont széles), a betű 5 sora duplázva -> 12 sor
G = {
 ' ': "... ... ... ... ...", 'A': ".X. X.X XXX X.X X.X", 'B': "XX. X.X XX. X.X XX.",
 'C': ".XX X.. X.. X.. .XX", 'D': "XX. X.X X.X X.X XX.", 'E': "XXX X.. XX. X.. XXX",
 'F': "XXX X.. XX. X.. X..", 'G': ".XX X.. X.X X.X .XX", 'H': "X.X X.X XXX X.X X.X",
 'I': "XXX .X. .X. .X. XXX", 'J': "..X ..X ..X X.X .X.", 'K': "X.X X.X XX. X.X X.X",
 'L': "X.. X.. X.. X.. XXX", 'M': "X.X XXX XXX X.X X.X", 'N': "XX. X.X X.X X.X X.X",
 'O': ".X. X.X X.X X.X .X.", 'P': "XX. X.X XX. X.. X..", 'Q': ".X. X.X X.X XX. .XX",
 'R': "XX. X.X XX. X.X X.X", 'S': ".XX X.. .X. ..X XX.", 'T': "XXX .X. .X. .X. .X.",
 'U': "X.X X.X X.X X.X XXX", 'V': "X.X X.X X.X .X. .X.", 'W': "X.X X.X XXX XXX X.X",
 'X': "X.X X.X .X. X.X X.X", 'Y': "X.X X.X .X. .X. .X.", 'Z': "XXX ..X .X. X.. XXX",
 '0': "XXX X.X X.X X.X XXX", '1': ".X. XX. .X. .X. XXX", '2': "XX. ..X .X. X.. XXX",
 '3': "XX. ..X .X. ..X XX.", '4': "X.X X.X XXX ..X ..X", '5': "XXX X.. XX. ..X XX.",
 '6': ".XX X.. XXX X.X XXX", '7': "XXX ..X .X. .X. .X.", '8': "XXX X.X XXX X.X XXX",
 '9': "XXX X.X XXX ..X XX.", '.': "... ... ... ... .X.", ',': "... ... ... .X. X..",
 ':': "... .X. ... .X. ...", '!': ".X. .X. .X. ... .X.", '?': "XX. ..X .X. ... .X.",
 '-': "... ... XXX ... ...", "'": ".X. .X. ... ... ...", '/': "..X ..X .X. X.. X..",
 '*': "... X.X .X. X.X ...", '+': "... .X. XXX .X. ...", '=': "... XXX ... XXX ...",
 '(': ".X. X.. X.. X.. .X.", ')': ".X. ..X ..X ..X .X.", '"': "X.X X.X ... ... ...",
 '$': ".XX XX. .X. .XX XX.", '#': ".X. XXX .X. X.X ...",   # '#' = csillag (körözés)
}
ACC = {'Á': ('A', "..X. .X.."), 'É': ('E', "..X. .X.."), 'Í': ('I', "..X. .X.."),
       'Ó': ('O', "..X. .X.."), 'Ú': ('U', "..X. .X.."), 'Ö': ('O', ".... X.X."),
       'Ü': ('U', ".... X.X."), 'Ő': ('O', ".X.X X.X."), 'Ű': ('U', ".X.X X.X.")}
CHARS = list(G.keys()) + list(ACC.keys())
CIDX = {c: i for i, c in enumerate(CHARS)}

def glyph_rows(ch):
    """12 sor, soronként 4 bit (b3 = bal)."""
    if ch in ACC:
        base, acc = ACC[ch]
    else:
        base, acc = ch, ".... ...."
    rows = []
    for a in acc.split():
        rows.append(sum(8 >> i for i, c in enumerate(a) if c == 'X'))
    for r in G[base].split():
        v = sum(8 >> i for i, c in enumerate(r) if c == 'X')
        rows += [v, v]
    return rows

def glyph_pixels(ch):
    """5x3 (+ékezet) képpontok a képekre rajzoláshoz: (x, y) lista, y: -2..4"""
    pts = []
    base, acc = ACC.get(ch, (ch, ".... ...."))
    for y, a in enumerate(acc.split()):
        for x, c in enumerate(a):
            if c == 'X':
                pts.append((x, y - 2))
    for y, r in enumerate(G[base].split()):
        for x, c in enumerate(r):
            if c == 'X':
                pts.append((x, y))
    return pts

def enc(s):
    return [CIDX[c] for c in s] + [0xFF]

# ---------------------------------------------------------------- vászon
class Canvas:
    def __init__(self, bg=0):
        self.img = Image.new('L', (W, H), bg)
        self.d = ImageDraw.Draw(self.img)
    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.img.putpixel((x, y), c)
    def get(self, x, y):
        return self.img.getpixel((x, y))
    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle((x0, y0, x1, y1), fill=c)
    def poly(self, pts, c):
        self.d.polygon(pts, fill=c)
    def ell(self, cx, cy, rx, ry, c):
        self.d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=c)
    def line(self, pts, c, w=1):
        self.d.line(pts, fill=c, width=w)
    def hdither(self, y0, y1, a, b, x0=0, x1=W - 1):
        """sakktábla-keverés két színből (soronként egyforma bájt)"""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, a if (x + y) % 2 == 0 else b)
    def text(self, s, x, y, c, sx=1, sy=2, shadow=None):
        for i, ch in enumerate(s):
            for (gx, gy) in glyph_pixels(ch):
                for k in ([(1, 1, shadow)] if shadow is not None else []) + [(0, 0, c)]:
                    ox, oy, col = k
                    if col is None:
                        continue
                    self.rect(x + i * 4 * sx + gx * sx + ox, y + gy * sy + oy,
                              x + i * 4 * sx + gx * sx + sx - 1 + ox, y + gy * sy + sy - 1 + oy, col)
    def to_bytes(self):
        out = bytearray()
        for y in range(H):
            for xb in range(64):
                out.append(pbyte(self.get(xb * 2, y), self.get(xb * 2 + 1, y)))
        return out
    def png(self, name):
        im = Image.new('RGB', (W, H))
        im.putdata([rgb(v) for v in self.img.getdata()])
        im.resize((W * 4, H * 2), Image.NEAREST).save(name)

def rowbyte(cv, y, xb):
    return pbyte(cv.get(xb * 2, y), cv.get(xb * 2 + 1, y))

def rle(data):
    """bájt-RLE: 0..127 = n+1 nyers bájt; 128..255 = (n-125) ismétlés (3..130)"""
    out = bytearray(); i = 0; lit = bytearray()
    def flush():
        nonlocal lit
        while lit:
            chunk = lit[:128]; lit = lit[128:]
            out.append(len(chunk) - 1); out.extend(chunk)
    while i < len(data):
        j = i
        while j < len(data) and data[j] == data[i] and j - i < 130:
            j += 1
        if j - i >= 3:
            flush(); out.append(j - i + 125); out.append(data[i]); i = j
        else:
            lit.append(data[i]); i += 1
    flush()
    return out

def unrle_check(src, n):
    out = bytearray(); i = 0
    while len(out) < n:
        b = src[i]; i += 1
        if b < 128:
            out += src[i:i + b + 1]; i += b + 1
        else:
            out += bytes([src[i]]) * (b - 125); i += 1
    return out

random.seed(6)
CAP_Y = 222              # feliratsor
HORIZON = 130

# ================================================================ 1. NAPLEMENTE
def sky_sunset(cv):
    bands = [(0, 25, BLU, BLU), (26, 37, BLU, MAG), (38, 55, MAG, MAG), (56, 67, MAG, LMAG),
             (68, 85, LMAG, LMAG), (86, 97, LMAG, LRED), (98, 111, LRED, LRED),
             (112, 121, LRED, YEL), (122, 129, YEL, YEL)]
    for y0, y1, a, b in bands:
        cv.hdither(y0, y1, a, b)
sun = Canvas()
sky_sunset(sun)
SKYROW = [rowbyte(sun, y, 30) for y in range(HORIZON)]
for _ in range(30):                               # csillagok (a nap oszlopain kívül)
    x = random.choice(list(range(2, 44)) + list(range(86, 126))); y = random.randint(2, 30)
    sun.px(x, y, WHT if random.random() < .5 else LBLU)
# távoli part: Badacsony-forma balra, lankák jobbra (sötét)
sun.poly([(0, 130), (0, 116), (6, 113), (14, 106), (30, 106), (38, 113), (44, 124), (46, 130)], BLU)
sun.poly([(84, 130), (92, 124), (104, 121), (116, 118), (127, 121), (127, 130)], BLU)
sun.rect(0, 129, 47, 130, BLU); sun.rect(84, 129, 127, 130, BLU)
# víz
wbands = [(131, 136, LMAG, MAG), (137, 150, MAG, MAG), (151, 165, MAG, BLU), (166, 199, BLU, BLU)]
for y0, y1, a, b in wbands:
    sun.hdither(y0, y1, a, b)
for _ in range(70):                               # hullámfodrok (a tükröződés sávján kívül)
    y = random.randint(133, 196); x = random.choice(list(range(0, 28)) + list(range(100, 124)))
    ln = random.randint(2, 5)
    for k in range(ln):
        sun.px(x + k, y, LBLU if y > 150 else LMAG)
# homokos part
sun.hdither(200, 213, BRN, BLK)
sun.hdither(200, 202, BRN, YEL)
REFL_ROWS = [133 + 3 * k for k in range(21)]
WATROW = []
for y in REFL_ROWS:
    b = rowbyte(sun, y, 30)
    for xb in range(16, 49):
        sun.px(xb * 2, y, sun.get(60, y)); sun.px(xb * 2 + 1, y, sun.get(61, y))
    WATROW.append(rowbyte(sun, y, 30))
# pálmafa balra (Balaton Vice!)
trunk = [(10, 213), (11, 190), (13, 170), (16, 150), (20, 132), (23, 118)]
for i in range(len(trunk) - 1):
    sun.line([trunk[i], trunk[i + 1]], BLK, 3)
for (dx, dy, ex, ey) in [(-20, 6, -26, 18), (-16, -10, -24, -4), (2, -14, 8, -22), (14, -8, 24, -2), (16, 6, 22, 18), (-6, 10, -10, 22)]:
    cx, cy = 23, 116
    sun.line([(cx, cy), (cx + dx // 2, cy + dy // 2 - 3), (cx + dx, cy + dy), (cx + ex, cy + ey)], BLK, 2)
sun.ell(23, 116, 3, 4, BLK)
# lángossütő büfé jobbra
sun.rect(98, 168, 127, 213, BRN)
sun.rect(100, 176, 125, 190, BLK)                 # pult-ablak
sun.rect(98, 190, 127, 192, YEL)
for x in range(98, 128, 4):                       # csíkos előtető
    sun.rect(x, 162, x + 1, 167, LRED); sun.rect(x + 2, 162, x + 3, 167, WHT)
sun.rect(96, 150, 127, 161, BLK)                  # cégtábla háttere
sun.text("3000 FT", 100, 196, YEL, 1, 1)
# árus a pultban
sun.ell(112, 181, 3, 4, BRN); sun.rect(108, 185, 116, 190, WHT)
SIGN_X, SIGN_Y, SIGN_W, SIGN_H = 48, 151, 16, 10  # bájt / sor
def sign_block(on):
    c = Canvas()
    c.rect(96, 150, 127, 161, BLK)
    c.text("LÁNGOS", 101, 153, LMAG if on else MAG, 1, 1)
    if on:
        for x in range(97, 127):
            c.px(x, 150, LMAG if x % 2 else BLK); c.px(x, 161, LMAG if x % 2 == 0 else BLK)
    return bytes(rowbyte(c, SIGN_Y + r, SIGN_X + xb) for r in range(SIGN_H) for xb in range(SIGN_W))
SIGN_ON, SIGN_OFF = sign_block(True), sign_block(False)
for r in range(SIGN_H):
    for xb in range(SIGN_W):
        pass
# a háttérbe a kikapcsolt tábla kerül
sun_bytes = bytearray(sun.to_bytes())
for r in range(SIGN_H):
    for xb in range(SIGN_W):
        sun_bytes[(SIGN_Y + r) * 64 + SIGN_X + xb] = SIGN_OFF[r * SIGN_W + xb]
for y in range(214, 240):
    for xb in range(64):
        sun_bytes[y * 64 + xb] = 0
# nap: R=30 sor, 15 képpont sugár; bájthatáros sávok a 64. képpont körül
SUN_R = 30
SUNTAB = [(0, 0, 0)]                               # 0. = csak takarítás
for dy in range(-SUN_R, SUN_R + 1):
    hw = 15 * math.sqrt(max(0, 1 - (dy / (SUN_R + .5)) ** 2))
    nb = int(round(hw / 2))                        # félszélesség bájtban
    t = (dy + SUN_R) / (2 * SUN_R)
    if t < .3: col = pbyte(YEL, YEL)
    elif t < .45: col = pbyte(YEL, LRED) if dy % 2 else pbyte(LRED, YEL)
    elif t < .65: col = pbyte(LRED, LRED)
    elif t < .8: col = pbyte(LRED, LMAG) if dy % 2 else pbyte(LMAG, LRED)
    else: col = pbyte(LMAG, LMAG)
    gap = False
    if dy > 2:                                     # retró csíkok az alsó félben
        k = dy - 2
        period = 8; gw = 1 + k // 9
        gap = (k % period) < gw
    if nb == 0 or gap:
        SUNTAB.append((0, 0, 0))
    else:
        SUNTAB.append((8 - nb, 2 * nb, col))       # oszlop 24..40, közép = 8. bájt
assert len(SUNTAB) == 62
# tükröződés: f = 0..8 (mennyi látszik a napból), k = sor
REFW = []
for f in range(9):
    for k in range(21):
        base = 3 + k * 0.55
        REFW.append(int(round(base * f / 8)))
FLEV = []
for sy in range(256):
    vis = HORIZON - (sy - SUN_R)
    vis = max(0, min(2 * SUN_R, vis))
    FLEV.append(int(round(vis * 8 / (2 * SUN_R))))
REFB = [pbyte(YEL, LRED) if k < 6 else pbyte(LRED, LMAG) if k < 13 else pbyte(LMAG, MAG) for k in range(21)]
WOB = [0, 1, 1, 2, 1, 1, 0, 0, -1, -1, -2, -1, -1, 0, 0, 1]
WOB = [w & 0xFF for w in WOB]

# ================================================================ 2. ÜLDÖZÉS
ch = Canvas()
cbands = [(0, 33, BLU, BLU), (34, 49, BLU, MAG), (50, 75, MAG, MAG), (76, 89, MAG, LMAG), (90, 127, LMAG, LMAG)]
for y0, y1, a, b in cbands:
    ch.hdither(y0, y1, a, b)
ch.rect(0, 0, 127, 29, BLU)                       # HUD-sáv: tiszta sötétkék
ch.ell(18, 44, 5, 9, WHT); ch.ell(20, 42, 4, 8, BLU)   # holdsarló
for _ in range(25):
    x = random.randint(30, 126); y = random.randint(31, 60)
    ch.px(x, y, WHT if random.random() < .4 else LBLU)
# városkép (Siófok-szerű szállodák) 70..127 sor; ez forog
SKY0, SKY1 = 74, 127
x = 0
while x < 128:
    w = random.choice([10, 12, 14, 16, 18]); h = random.randint(18, 50)
    if x + w > 124: w = 128 - x
    top = 127 - h
    col = random.choice([BLK, BLU, BLK])
    ch.rect(x, top, x + w - 2, 127, col)
    for wy in range(top + 3, 125, 4):
        for wx in range(x + 2, x + w - 3, 3):
            if random.random() < .45:
                ch.rect(wx, wy, wx, wy + 1, random.choice([YEL, YEL, BRN, LCYN]))
    if random.random() < .35 and w >= 14 and h > 30:   # neon felirat a tetőn
        ch.rect(x + 1, top - 3, x + w - 3, top - 2, random.choice([LCYN, LMAG]))
    x += w
for px_ in (8, 40, 70, 104):                         # pálmák a szállodák előtt
    ch.line([(px_, 127), (px_ + 1, 108)], BLK, 2)
    for dx, dy in [(-6, 3), (-5, -3), (5, -3), (6, 3), (0, -5)]:
        ch.line([(px_ + 1, 106), (px_ + 1 + dx, 106 + dy)], BLK, 2)
ch.rect(0, 128, 127, 131, BLK)
ch.rect(0, 132, 127, 133, GRY)                        # szalagkorlát
POST_Y0, POST_N = 134, 6
ch.rect(0, 134, 127, 141, BLK)
ROAD0, ROAD1 = 142, 205
for y in range(ROAD0, ROAD1 + 1):
    for x in range(W):
        ch.px(x, y, BLU if (x + y) % 2 == 0 else BLK)
ch.rect(0, 144, 127, 145, WHT)
ch.rect(0, 202, 127, 203, WHT)
DASH_Y0, DASH_N = 168, 3
ch.hdither(206, 213, BLU, LBLU)                       # a tó csillogása
ASPH = [rowbyte(ch, y, 0) for y in range(240)]
def pattern_line(period, on_bytes, on_byte, off_byte):
    one = [on_byte if i < on_bytes else off_byte for i in range(period)]
    return bytes((one * (80 // period + 2))[:64 + period])
POSTLINE = pattern_line(16, 1, pbyte(GRY, WHT), pbyte(BLK, BLK))
DASHLINE = [pattern_line(32, 10, pbyte(WHT, WHT), ASPH[DASH_Y0 + r]) for r in range(DASH_N)]
ch_bytes = bytearray(ch.to_bytes())
for r in range(POST_N):
    ch_bytes[(POST_Y0 + r) * 64:(POST_Y0 + r) * 64 + 64] = POSTLINE[:64]
for r in range(DASH_N):
    ch_bytes[(DASH_Y0 + r) * 64:(DASH_Y0 + r) * 64 + 64] = DASHLINE[r][:64]
for y in range(214, 240):
    for xb in range(64):
        ch_bytes[y * 64 + xb] = 0

# autók: oldalnézet, jobbra haladnak; a sprite átlátszatlan, az út mintájával
CAR_Y, CAR_H = 178, 23
def car_sprite(kind, frame, wbytes):
    c = Canvas()
    for y in range(CAR_Y, CAR_Y + CAR_H):
        for x in range(W):
            c.px(x, y, ch.get(x, y))
    ox = 2; oy = CAR_Y + (1 if frame == 1 and kind == 'trabi' else 0)
    if kind == 'trabi':
        L = 26
        c.rect(ox + 1, oy + 9, ox + L - 1, oy + 17, LCYN)        # karosszéria
        c.rect(ox, oy + 11, ox, oy + 16, LCYN)
        c.poly([(ox + 6, oy + 9), (ox + 9, oy + 2), (ox + 19, oy + 2), (ox + 22, oy + 9)], WHT)  # tető
        c.poly([(ox + 8, oy + 9), (ox + 10, oy + 4), (ox + 13, oy + 4), (ox + 13, oy + 9)], BLU)   # ablakok
        c.poly([(ox + 15, oy + 9), (ox + 15, oy + 4), (ox + 18, oy + 4), (ox + 20, oy + 9)], BLU)
        c.rect(ox + 11, oy + 5, ox + 12, oy + 8, YEL)            # Lujza (szőke)
        c.rect(ox + 16, oy + 5, ox + 17, oy + 8, BRN)            # Jani
        c.rect(ox + L - 2, oy + 11, ox + L - 1, oy + 12, YEL)    # fényszóró
        c.rect(ox + 1, oy + 11, ox + 1, oy + 12, LRED)           # hátsó lámpa
        c.rect(ox + 1, oy + 15, ox + L - 1, oy + 15, CYN)
        for wx in (ox + 6, ox + 20):
            c.ell(wx, CAR_Y + 19, 2, 3, BLK); c.px(wx, CAR_Y + 19, GRY)
    else:   # rendőrautó (Lada-forma), villogó tetőfény
        L = 28
        c.rect(ox, oy + 9, ox + L - 1, oy + 17, WHT)
        c.poly([(ox + 7, oy + 9), (ox + 9, oy + 3), (ox + 20, oy + 3), (ox + 23, oy + 9)], WHT)
        c.poly([(ox + 9, oy + 9), (ox + 10, oy + 5), (ox + 14, oy + 5), (ox + 14, oy + 9)], BLU)
        c.poly([(ox + 16, oy + 9), (ox + 16, oy + 5), (ox + 20, oy + 5), (ox + 21, oy + 9)], BLU)
        c.rect(ox, oy + 12, ox + L - 1, oy + 13, LBLU)           # kék csík
        c.rect(ox + L - 2, oy + 10, ox + L - 1, oy + 11, YEL)
        lc1, lc2 = (LBLU, LRED) if frame == 0 else (LRED, LBLU)
        c.rect(ox + 11, oy + 1, ox + 13, oy + 2, lc1); c.rect(ox + 15, oy + 1, ox + 17, oy + 2, lc2)
        for wx in (ox + 6, ox + 22):
            c.ell(wx, CAR_Y + 19, 2, 3, BLK); c.px(wx, CAR_Y + 19, GRY)
    return bytes(rowbyte(c, CAR_Y + r, xb) for r in range(CAR_H) for xb in range(wbytes)), c
TRABI_W, POLICE_W = 16, 17
TRABI = [car_sprite('trabi', f, TRABI_W)[0] for f in (0, 1)]
POLICE = [car_sprite('police', f, POLICE_W)[0] for f in (0, 1)]
# füst: két-ütemű kékes füstpamacs (3 fázis), 2 bájt x 4 sor
PUFF_Y = 192

# ================================================================ 3. CÍMKÉP
tc = Canvas()
for y0, y1, a, b in [(0, 59, BLK, BLK), (60, 79, BLK, BLU), (80, 119, BLU, BLU), (120, 139, BLU, MAG),
                     (140, 175, MAG, MAG), (176, 189, MAG, LMAG), (190, 213, LMAG, LMAG)]:
    tc.hdither(y0, y1, a, b)
for _ in range(30):
    tc.px(random.randint(0, 127), random.randint(0, 110), random.choice([WHT, LBLU, GRY]))
# retró-nap a háttérben, csíkokkal
tc.ell(64, 196, 26, 40, LRED)
for y in range(150, 214):
    t = (y - 150)
    if y < 172: tc.hdither(y, y, YEL, LRED, 0, 127) if False else None
for y in range(140, 214):
    for x in range(38, 91):
        if tc.get(x, y) == LRED:
            if y < 160: tc.px(x, y, YEL)
            elif y < 170: tc.px(x, y, YEL if (x + y) % 2 else LRED)
            if y > 176 and (y - 176) % 7 < 1 + (y - 176) // 12:
                tc.px(x, y, tc.get(0, y))
# vízszint és pálmák
tc.rect(0, 205, 127, 213, BLU)
for x in range(0, 128):
    if (x * 7) % 5 == 0: tc.px(x, 206 + (x % 3) * 2, LBLU)
for px_, h in ((8, 70), (118, 60)):
    tc.line([(px_, 213), (px_ + 3, 213 - h)], BLK, 3)
    for dx, dy in [(-12, 6), (-10, -4), (11, -4), (12, 6), (0, -8), (-5, 10), (6, 10)]:
        tc.line([(px_ + 3, 211 - h), (px_ + 3 + dx, 211 - h + dy)], BLK, 2)
tc.text("GRAND THEFT", 20, 8, WHT, 2, 3, shadow=GRY)
tc.text("TRABANT", 22, 30, YEL, 3, 5, shadow=LRED)
# hatalmas VI: kitöltés színátmenettel, ciánkék körvonal
VI_X, VI_Y, VSX, VSY = 36, 64, 7, 13
mask = Canvas()
VH = 5 * VSY
mask.poly([(VI_X, VI_Y), (VI_X + 7, VI_Y), (VI_X + 10, VI_Y + VH * 0.62), (VI_X + 13, VI_Y),
           (VI_X + 20, VI_Y), (VI_X + 14, VI_Y + VH - 1), (VI_X + 6, VI_Y + VH - 1)], 1)
mask.text("I", VI_X + 4 * VSX, VI_Y, 1, VSX, VSY)
for y in range(H):
    for x in range(W):
        if mask.get(x, y):
            for (ddx, ddy) in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1), (2, 0), (-2, 0)):
                xx, yy = x + ddx, y + ddy
                if 0 <= xx < W and 0 <= yy < H and not mask.get(xx, yy):
                    tc.px(xx, yy, LCYN)
for y in range(H):
    for x in range(W):
        if mask.get(x, y):
            t = (y - VI_Y) / (5 * VSY)
            if t < .25: c = WHT if t < .08 else YEL
            elif t < .4: c = YEL if (x + y) % 2 else LRED
            elif t < .6: c = LRED
            elif t < .75: c = LRED if (x + y) % 2 else LMAG
            else: c = LMAG
            tc.px(x, y, c)
SUB_Y = 138
SUB_TXT = "BALATON VICE"
tcb = bytearray(tc.to_bytes())
def sub_block(on):
    c = Canvas()
    for y in range(SUB_Y - 1, SUB_Y + 12):
        for x in range(W):
            c.px(x, y, tc.get(x, y))
    if on:
        c.text(SUB_TXT, 16, SUB_Y, LCYN, 2, 2, shadow=BLU)
    return bytes(rowbyte(c, SUB_Y - 1 + r, xb) for r in range(13) for xb in range(64))
SUB_ON, SUB_OFF = sub_block(True), sub_block(False)
for r in range(13):
    tcb[(SUB_Y - 1 + r) * 64:(SUB_Y + r) * 64] = SUB_ON[r * 64:(r + 1) * 64]
for y in range(214, 240):
    for xb in range(64):
        tcb[y * 64 + xb] = 0
title_c = tc

# ================================================================ előnézetek
def save_preview(b, name):
    im = Image.new('RGB', (W, H))
    pix = []
    for y in range(H):
        for xb in range(64):
            v = b[y * 64 + xb]
            l = ((v >> 7) & 1) << 3 | ((v >> 5) & 1) << 2 | ((v >> 3) & 1) << 1 | ((v >> 1) & 1)
            r = ((v >> 6) & 1) << 3 | ((v >> 4) & 1) << 2 | ((v >> 2) & 1) << 1 | (v & 1)
            pix += [rgb(l), rgb(r)]
    im.putdata(pix)
    im.resize((W * 4, H * 2), Image.NEAREST).save(name)
save_preview(sun_bytes, "preview_sunset.png")
save_preview(ch_bytes, "preview_chase.png")
save_preview(tcb, "preview_title.png")

# ================================================================ zene
def pitch(f):
    return max(0, min(4095, int(round(4096 - 195312.5 / f))))
def note(n):        # MIDI
    return 440 * 2 ** ((n - 69) / 12)
def ev(frames, f, vol):
    if f is None:
        return [frames, 0xFF, 0x0F, 0]
    p = pitch(f)
    return [frames, p & 0xFF, p >> 8, vol]
A2, C3, D3, E3, F2, G2 = 45, 48, 50, 52, 41, 43
mus = []
chords = [(57, [0, 3, 7, 12, 15, 12, 7, 3]),      # Am
          (53, [0, 4, 7, 12, 16, 12, 7, 4]),      # F
          (48, [0, 4, 7, 12, 16, 19, 16, 12]),    # C
          (55, [0, 4, 7, 11, 14, 11, 7, 4])]      # G
for root, arp in chords:
    for bar in range(2):
        for i, iv in enumerate(arp):
            n = root + iv + (12 if bar == 1 and i in (3, 4, 5) else 0)
            mus += ev(4, note(n), 13) + ev(3, note(n), 5)
MUSIC = bytes(mus + [0])
siren = []
for _ in range(1):
    for k in range(10):
        siren += ev(2, 620 + k * 30, 12)
    for k in range(10):
        siren += ev(2, 920 - k * 30, 12)
SIREN = bytes(siren + [0])
fan = []
for n, d in [(57, 6), (60, 6), (64, 6), (69, 10), (64, 4), (69, 24)]:
    fan += ev(d - 2, note(n + 12), 15) + ev(2, note(n + 12), 6)
fan += ev(20, None, 0)
FANFARE = bytes(fan + [0])
BLIP = bytes(ev(3, 1200, 14) + ev(3, 600, 10) + [0])
STRIKE = bytes(ev(4, 160, 15) + ev(6, 110, 12) + [0])
TADA = bytes(ev(5, note(76), 15) + ev(5, note(79), 15) + ev(5, note(84), 15) + ev(20, note(88), 15) + ev(10, note(88), 6) + [0])

# ================================================================ szövegek, idővonalak
def cx(s, big=False):
    w = len(s) * (4 if big else 2)
    return (64 - w) // 2
def capaddr(s, y=CAP_Y):
    return 0x8000 + y * 64 + cx(s)

out = []
def db(name, data, per=24):
    out.append(f"{name}:")
    data = list(data)
    for i in range(0, len(data), per):
        out.append("        db " + ",".join(str(v & 0xFF) for v in data[i:i + per]))
def dw(name, data, per=12):
    out.append(f"{name}:")
    for i in range(0, len(data), per):
        out.append("        dw " + ",".join(str(v) for v in data[i:i + per]))

# font
fontb = []
for chh in CHARS:
    fontb += [v * 2 for v in glyph_rows(chh)]     # *2: közvetlen index a NIB-táblába
db("FONT", fontb)
# NIB-táblák: 16 x (2 bájt) a 4 bites sorhoz (normál), BIG: 16 x 4 bájt
COLS = {}
def nib(ink, paper):
    name = f"NIB_{ink}_{paper}"
    if name not in COLS:
        t = []
        for v in range(16):
            px4 = [ink if v & (8 >> i) else paper for i in range(4)]
            t += [pbyte(px4[0], px4[1]), pbyte(px4[2], px4[3])]
        COLS[name] = t
    return name
BIGS = {}
def big(ink, paper):
    name = f"BIG_{ink}_{paper}"
    if name not in BIGS:
        t = []
        for v in range(16):
            px4 = [ink if v & (8 >> i) else paper for i in range(4)]
            t += [pbyte(c, c) for c in px4]
        BIGS[name] = t
    return name

strings = {}
def S(s):
    if s not in strings:
        strings[s] = f"str{len(strings)}"
    return strings[s]

def timeline(name, items):
    rows = []
    for fr, s, col in items:
        rows += [fr, S(s), capaddr(s), nib(col, 0)]
    rows += [0xFFFF]
    dw(name, rows, 4)

timeline("CAP_SUNSET", [
    (60, "BALATONIA ÁLLAM, 2026 NYARA.", WHT),
    (230, "AZ ÁLMOK ORSZÁGA.", LCYN),
    (380, "AHOL A LÁNGOS 3000 FORINT.", YEL),
    (560, "ÉS A SZÉP ÁLMOK IS DRÁGÁK.", LMAG),
    (740, "", WHT),
])
timeline("CAP_CHASE", [
    (20, "LUJZA ÉS JANI.", WHT),
    (150, "EGY TRABANT. NULLA TERV.", LCYN),
    (330, "SEMMI SEM MEHET FÉLRE...", YEL),
    (480, "...MÁR A RENDŐRSÉG IS KERES!", LRED),
    (700, "", WHT),
])
timeline("CAP_TITLE", [
    (40, "HAMAROSAN* A VIDEOTON TVC-N", WHT),
    (400, "", WHT),
])
nib(WHT, BLU); nib(YEL, BLU); nib(GRY, BLU); nib(LGRN, BLU)
nib(WHT, 0); nib(LRED, 0); nib(YEL, 0); nib(LCYN, 0); nib(GRY, 0); nib(LMAG, 0); nib(LGRN, 0)
for c in (BLU, LBLU, CYN, LCYN, WHT, GRY, LMAG, YEL, LRED, LGRN):
    big(c, 0)

# bemutató (fade)
FADE = [BLU, LBLU, LCYN, WHT, WHT, WHT, WHT, WHT, WHT, LCYN, LBLU, BLU, BLK]
dw("SPLASH_FADE", [big(c, 0) for c in FADE], 13)
out.append(f"SPLASH_FADE_N equ {len(FADE)}")
for s, y, nm in (("KŐSZTÁR GAMES", 96, "SPL1"), ("BEMUTATJA", 132, "SPL2")):
    out.append(f"{nm}_ADDR equ {0x8000 + y * 64 + cx(s, True)}")
    out.append(f"{nm}_STR equ {S(s)}")
# csúszás-poén sorai: (y, szöveg, nagy?, szín, áthúzás?)
DELAY = [
    (16, "MEGJELENÉS:", True, WHT, False),
    (52, "2025 ŐSZ", True, LCYN, True),
    (80, "2026 MÁJUS 26.", True, LCYN, True),
    (108, "2026 NOV. 19.", True, LCYN, False),
    (134, "...DE CSAK KONZOLRA.", False, GRY, False),
    (152, "PC: MAJD EGYSZER...", False, GRY, False),
    (178, "VIDEOTON TVC:", True, YEL, False),
    (204, "MÁR MOST!*", True, LGRN, False),
]
rows = []
for y, s, bg_, col, strike in DELAY:
    addr = 0x8000 + y * 64 + cx(s, bg_)
    w = len(s) * (4 if bg_ else 2)
    rows += [S(s), addr, (1 if bg_ else 0) | (2 if strike else 0), big(col, 0) if bg_ else nib(col, 0),
             addr + (13 * 64 if bg_ else 6 * 64), w]
dw("DELAY_TAB", rows, 6)
out.append(f"DELAY_N equ {len(DELAY)}")
out.append(f"FOOT1_STR equ {S('*CSAK EZ A DEMÓ. BOCS.')}")
out.append(f"FOOT1_ADDR equ {capaddr('*CSAK EZ A DEMÓ. BOCS.', 226)}")
out.append(f"FOOT2_STR equ {S('SZÓKÖZ: ÚJRA   ESC: KILÉPÉS')}")
out.append(f"FOOT2_ADDR equ {capaddr('SZÓKÖZ: ÚJRA   ESC: KILÉPÉS', 226)}")
out.append(f"HUD_TIME_STR equ {S('21:47')}")
out.append(f"HUD_TIME_ADDR equ {0x8000 + 6 * 64 + 2}")
out.append(f"HUD_FT_ADDR equ {0x8000 + 18 * 64 + 64 - 2 * 10 - 2}")
out.append(f"HUD_STAR_ADDR equ {0x8000 + 6 * 64 + 64 - 2 * 5 - 2}")
out.append(f"G_STAR equ {CIDX['#']}")
out.append(f"G_0 equ {CIDX['0']}")
out.append(f"G_F equ {CIDX['F']}")
out.append(f"G_T equ {CIDX['T']}")
out.append(f"G_SPACE equ {CIDX[' ']}")
for s, nm in strings.items():
    db(nm, enc(s))
for name, t in COLS.items():
    db(name, t, 32)
for name, t in BIGS.items():
    db(name, t, 32)

# képek
for nm, b in (("IMG_SUNSET", sun_bytes), ("IMG_CHASE", ch_bytes), ("IMG_TITLE", tcb)):
    r = rle(b[:214 * 64])
    assert unrle_check(r, 214 * 64) == b[:214 * 64]
    db(nm, r, 32)
    out.append(f"; {nm}: {len(r)} bájt")
out.append(f"IMG_LEN equ {214 * 64}")
# naplemente táblák
db("SKYROW", SKYROW)
db("SUNTAB", [v for t in SUNTAB for v in t])
db("WATROW", WATROW)
db("REFW", REFW, 21)
db("FLEV", FLEV, 32)
db("REFB", REFB)
db("WOB", WOB)
db("SIGN_ON", SIGN_ON, 16); db("SIGN_OFF", SIGN_OFF, 16)
blink = [1] * 20 + [0, 1, 0, 1, 1, 1, 0, 0, 1, 1] + [1] * 24 + [0, 0, 0, 1, 0, 1, 1, 1, 1, 1]
db("BLINK", blink + [1] * (64 - len(blink)))
out += [f"SKY_SUNCOL equ 24", f"HORIZON equ {HORIZON}", f"SUN_R equ {SUN_R}",
        f"SIGN_ADDR equ {0x8000 + SIGN_Y * 64 + SIGN_X}", f"SIGN_W equ {SIGN_W}", f"SIGN_H equ {SIGN_H}",
        f"REFL_Y0 equ {REFL_ROWS[0]}", f"REFL_N equ {len(REFL_ROWS)}"]
# üldözés táblák
db("POSTLINE", POSTLINE, 16)
for r in range(DASH_N):
    db(f"DASHLINE{r}", DASHLINE[r], 32)
db("TRABI0", TRABI[0], TRABI_W); db("TRABI1", TRABI[1], TRABI_W)
db("POLICE0", POLICE[0], POLICE_W); db("POLICE1", POLICE[1], POLICE_W)
db("ASPH", ASPH[CAR_Y:CAR_Y + CAR_H])
out += [f"SKY0 equ {SKY0}", f"SKY1 equ {SKY1}", f"POST_Y0 equ {POST_Y0}", f"POST_N equ {POST_N}",
        f"DASH_Y0 equ {DASH_Y0}", f"DASH_N equ {DASH_N}", f"CAR_Y equ {CAR_Y}", f"CAR_H equ {CAR_H}",
        f"TRABI_W equ {TRABI_W}", f"POLICE_W equ {POLICE_W}", f"PUFF_Y equ {PUFF_Y}",
        f"PUFF_B equ {pbyte(GRY, LBLU)}", f"PUFF_B2 equ {pbyte(LBLU, GRY)}"]
# rendőrautó útja: x (előjeles bájt) 4 képkockánként
pol = []
for i in range(256):
    t = i
    if t < 40: x = -18
    elif t < 70: x = -18 + (t - 40) * 30 // 30
    else: x = 12 + int(round(5 * math.sin((t - 70) / 9.0)))
    pol.append(x & 0xFF)
db("POLPATH", pol, 32)
# címkép
db("SUB_ON", SUB_ON, 32); db("SUB_OFF", SUB_OFF, 32)
out.append(f"SUB_ADDR equ {0x8000 + (SUB_Y - 1) * 64}")
# zene
db("MUSIC", MUSIC); db("SIREN", SIREN); db("FANFARE", FANFARE); db("BLIP", BLIP); db("STRIKE", STRIKE); db("TADA", TADA)
out.append(f"CAP_Y equ {CAP_Y}")
out.append(f"STRIKE_B equ {pbyte(LRED, LRED)}")
out.append(f"TRABI_X equ 38")
open("data.inc", "w").write("\n".join(out) + "\n")
print("data.inc kész;", sum(len(l) for l in out), "karakter")
