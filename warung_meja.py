
import pygame
import random
import math
import sys
import json
import os
import socket
import threading
import hashlib
import time

pygame.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("Warung Meja vs Zombie")
clock = pygame.time.Clock()

W, H = screen.get_size()

# ---- SAVE / LOAD ----
try:
    _BASE = os.path.dirname(os.path.abspath(__file__))
except Exception:
    _BASE = os.getcwd()
SAVE_SOLO = os.path.join(_BASE, "warung_save.json")          # simpanan MAIN SENDIRI
SAVE_MULTI = os.path.join(_BASE, "warung_save_multi.json")   # simpanan MULTIPLAYER
SAVE_PATH = SAVE_SOLO                                        # simpanan mode yang sedang aktif
AUTOSAVE_EVERY = 8.0       # detik: game auto save berkala selama permainan berjalan
DEFAULT_PLAYER_NAME = "Pemain"
NAME_MAX = 12              # panjang maksimal nama player


def _write_json_safe(path, data):
    """Tulis save lewat file sementara, supaya save tidak rusak walau game ditutup saat menulis."""
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

# COLORS
BG = (255, 244, 222)
BROWN = (145, 91, 48)
DARK = (65, 39, 22)
WHITE = (255, 255, 255)
ORANGE = (242, 125, 35)
GREEN = (45, 170, 75)
RED = (220, 55, 55)
BLUE = (55, 135, 220)
YELLOW = (255, 205, 55)
GRAY = (125, 115, 105)
LIGHT = (245, 224, 190)
PURPLE = (140, 80, 180)
SKULL_GOLD = (230, 200, 80)

ITEMS = [
    ("Burger", 15000, (214, 120, 40), 3),
    ("Kentang", 10000, (240, 190, 40), 2.5),
    ("Ayam", 12000, (190, 90, 50), 4),
    ("Pizza", 20000, (210, 60, 60), 5),
    ("Hotdog", 8000, (200, 110, 90), 2),
    ("Minuman", 5000, (60, 140, 210), 1)
]

STATIONS = ["Panggangan", "Penggorengan", "Oven", "Mesin Minum"]
ST_OF = [0, 1, 1, 2, 0, 3]

ROWS = 4
TABLE_COLS = 4
START_MONEY = 50000
TABLE_PRICE = 25000
MAX_CARRY = 3

# ---- hari, senapan, tembok, zombie (silakan ubah angkanya) ----
DAY_LEN = 120                  # 1 hari = 120 detik permainan (survival, tanpa batas total)
COLS = 12                      # 0 dapur | 1-4 meja | 5-7 antre | 8 senapan | 9 tembok | 10-11 jalur zombie
WALK_MAX = 8.9                 # pemain boleh sampai pos senapan

START_AMMO = 25                # peluru awal
AMMO_PRICE = 1000              # 1 peluru = Rp1.000
AMMO_PACKS = [10, 100, 1000, 10000]   # pilihan beli peluru (4 tombol)
FIRE_DELAY = 1.00              # jeda awal senapan (detik)
AK47_MIN_DELAY = 0.10            # batas tercepat: otomatis seperti AK-47
CHEF_COST = 600000               # harga merekrut koki
STATION_UPGRADE_COST = 100000   # harga peningkatan semua alat dapur

WALL_HP = 100
REPAIR_COST = 5000
REPAIR_HP = 20

ZOMBIE_N0 = 2                        # jumlah zombie dasar hari/level pertama
ZOMBIE_HP0, ZOMBIE_HP_STEP = 3, 1    # health zombie hari 1, tambah per hari
ZOMBIE_WAVE_START = 3.0              # zombie pertama muncul (detik sejak hari dimulai)
ZOMBIE_WAVE_END = DAY_LEN - 3.0      # semua zombie hari itu sudah datang sebelum detik ini (< 2 menit)
PIERCE_WIDTH = 0.45                  # lebar jalur peluru tembus (satuan petak)
ZOMBIE_SPEED = .3
ZOMBIE_STOP_X = 10.05
ZOMBIE_DMG = 2
ZOMBIE_HIT_DELAY = 1.0

# ---- pelanggan: naik seiring hari ----
CUSTOMER_BASE = 5              # target pelanggan awal (hari 1)
CUSTOMER_STEP = 1              # naik 1 target pelanggan per hari
QUEUE_SLOTS = 12               # slot antre (kolom 5-7)
RETURN_CD_MIN = 10             # cooldown balik tiap pelanggan (detik) - minimum
RETURN_CD_MAX = 10             # cooldown balik tiap pelanggan (detik) - maksimum
                               # (isi beda, mis. 8 dan 14, biar waktu datangnya acak)

# ---- ponsel: karyawan & tentara ----
HIRE_COST = 300000             # harga 1 karyawan atau 1 tentara
MAX_KARYAWAN = 5
MAX_TENTARA = 5
KARYAWAN_SPEED = 2.2           # kecepatan jalan karyawan
CLEANER_COST = 100000          # harga 1 karyawan pembersih (khusus ambil tip di meja)
MAX_CLEANER = 5
CLEANER_SPEED = 2.2            # kecepatan jalan pembersih
TENTARA_FIRE_DELAY = 0.55      # jeda tembak tentara
# damage peluru = max(1.0, 1 + ammo * 0.01)  → naik 1% per peluru, min 1, tak terbatas

# ---- BULAN MERAH: tiap kelipatan 5 hari, cahaya jadi merah & zombie 2x lipat ----
BLOOD_EVERY = 5                # event tiap 5 hari
BLOOD_MULT = 2                 # jumlah zombie dikali 2
BLOOD_BASE_ALPHA = 70          # kuat cahaya merah normal (0-255)
BLOOD_FLASH_TIME = 1.4         # lama kilatan merah mendadak (detik)

SPEEDS = [1, 4, 8]
SHIRTS = [
    (210, 70, 70), (65, 130, 220),
    (70, 170, 100), (160, 90, 190),
    (230, 150, 50)
]

M = max(5, int(H * 0.015))

RED_LIGHT = pygame.Surface((W, H))
RED_LIGHT.fill((255, 0, 0))
FONT = pygame.font.Font(None, max(18, int(H * 0.045)))
SMALL = pygame.font.Font(None, max(14, int(H * 0.032)))
BIG = pygame.font.Font(None, max(28, int(H * 0.075)))

BAR_H = int(H * 0.10)
CARD_Y = BAR_H + M
CARD_H = int(H * 0.15)
MAP_Y = CARD_Y + CARD_H + int(H * 0.08)
MAP_H = int(H * 0.53)
BOTTOM_Y = MAP_Y + MAP_H + M

CELL_W = (W - 2 * M) / COLS
CELL_H = MAP_H / 4
PS = max(1.0, CELL_H / 90)        # skala orang mengikuti ukuran layar
DOOR_TOP = CARD_Y + CARD_H + 2    # pintu masuk di atas area antre
DOOR_CX = M + 6.5 * CELL_W
DOOR_W = CELL_W * .9

menu_rects = [
    pygame.Rect(
        M + i * ((W - 2 * M) / 6),
        CARD_Y,
        (W - 7 * M) / 6,
        CARD_H
    )
    for i in range(6)
]

speed_rect = pygame.Rect(
    W - int(W * .13), M,
    int(W * .12), BAR_H - M
)

trash_rect = pygame.Rect(
    W - int(W * .16), BOTTOM_Y,
    int(W * .14), int(H * .10)
)

ammo_rect = pygame.Rect(
    trash_rect.x - int(W * .22), BOTTOM_Y,
    int(W * .20), int(H * .10)
)

# 4 tombol beli peluru (grid 2x2 di dalam ammo_rect)
ammo_rects = []
for _i in range(len(AMMO_PACKS)):
    _w = (ammo_rect.w - 4) // 2
    _h = (ammo_rect.h - 4) // 2
    ammo_rects.append(pygame.Rect(
        ammo_rect.x + (_i % 2) * (_w + 4),
        ammo_rect.y + (_i // 2) * (_h + 4),
        _w, _h))

def fmt_short(n):
    # harga singkat: Rp10rb, Rp1jt, dst.
    if n >= 1000000 and n % 1000000 == 0:
        return "Rp%djt" % (n // 1000000)
    if n >= 1000 and n % 1000 == 0:
        return "Rp%drb" % (n // 1000)
    return "Rp%d" % n

phone_rect = pygame.Rect(
    ammo_rect.x - int(W * .16), BOTTOM_Y,
    int(W * .15), int(H * .10)
)

# tombol ponsel juga di header (lebih gampang diklik)
phone_top_rect = pygame.Rect(
    int(W * .33), M,
    int(W * .12), BAR_H - M
)

# tombol MENU di header (sebelah judul WARUNG MEJA)
menu_btn_rect = pygame.Rect(
    int(W * .20), M,
    int(W * .09), BAR_H - M
)

# Tombol SIMPAN di sebelah tombol MENU
save_btn_rect = pygame.Rect(
    int(W * .295), M,
    int(W * .09), BAR_H - M
)

def fmt(n):
    return "Rp" + "{:,}".format(int(n)).replace(",", ".")

def draw_text(txt, font, color, x, y, center=True):
    img = font.render(str(txt), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    screen.blit(img, rect)

def button(rect, color, label, font=FONT):
    pygame.draw.rect(screen, color, rect, border_radius=12)
    pygame.draw.rect(screen, WHITE, rect, 2, border_radius=12)
    draw_text(label, font, WHITE, rect.centerx, rect.centery)

def cell_pos(r, c):
    return (
        M + c * CELL_W + CELL_W / 2,
        MAP_Y + r * CELL_H + CELL_H / 2
    )

def R(x, y, w, h):
    return pygame.Rect(int(x), int(y), max(1, int(w)), max(1, int(h)))

def P(x, y):
    return (int(x), int(y))

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)

# ---------- WAJAH ----------
SKINS = [
    (255, 214, 165), (241, 194, 145), (224, 172, 120),
    (198, 134, 86), (141, 92, 60)
]
HAIRS = [
    (30, 25, 25), (70, 45, 25), (120, 75, 35),
    (205, 165, 65), (150, 150, 155), (150, 40, 30)
]
STYLES = ["short", "long", "bun", "cap", "curly",
          "bald", "peci", "hijab", "spiky"]
ACCENTS = [
    (210, 70, 70), (65, 130, 220), (70, 170, 100),
    (160, 90, 190), (230, 150, 50), (240, 240, 240), (35, 35, 40)
]

def random_face():
    style = random.choice(STYLES)
    cowok = style in ("short", "cap", "curly", "bald", "peci", "spiky")
    return {
        "skin": random.choice(SKINS),
        "hair": random.choice(HAIRS),
        "style": style,
        "accent": random.choice(ACCENTS),
        "eyes": random.randrange(3),
        "mouth": random.randrange(3),
        "glasses": random.random() < .25,
        "mustache": cowok and random.random() < .2,
        "blush": random.random() < .3,
    }

# Wajah pemain: topi koki putih + celemek, supaya beda dari pelanggan
PLAYER_FACE_DEFAULT = {
    "skin": (232, 180, 128),
    "hair": (30, 25, 25),
    "style": "chef",
    "accent": WHITE,
    "eyes": 1,
    "mouth": 1,
    "glasses": False,
    "mustache": False,
    "blush": True,
}
PLAYER_FACE = dict(PLAYER_FACE_DEFAULT)

# ---- SKIN SHOP (mata uang tengkorak) ----
# 1 tengkorak = tiap 10 zombie dibunuh
SKIN_STYLES = ["chef", "short", "long", "bun", "cap", "curly",
               "bald", "peci", "hijab", "spiky"]
SKIN_PRICES = {
    "skin": 1,       # ganti warna kulit
    "hair": 1,       # ganti warna rambut
    "style": 2,      # ganti gaya rambut / topi
    "accent": 1,     # warna aksen (topi/hijab)
    "eyes": 1,       # bentuk mata
    "mouth": 1,      # bentuk mulut
    "glasses": 2,    # kacamata on/off
    "mustache": 2,   # kumis on/off
    "blush": 1,      # blush on/off
}

def copy_face(f):
    return {
        "skin": tuple(f["skin"]),
        "hair": tuple(f["hair"]),
        "style": f["style"],
        "accent": tuple(f["accent"]),
        "eyes": int(f["eyes"]),
        "mouth": int(f["mouth"]),
        "glasses": bool(f["glasses"]),
        "mustache": bool(f["mustache"]),
        "blush": bool(f["blush"]),
    }

def draw_person(x, y, shirt, scale=1, face=None, mood=0, apron=False):
    # mood: 0 senang, 1 biasa saja, 2 marah
    s = scale
    f = face or PLAYER_FACE
    x, y = int(x), int(y)
    skin, hair, st, acc = f["skin"], f["hair"], f["style"], f["accent"]
    hy = y - 11 * s
    lw = max(1, int(1.4 * s))

    # bayangan, kaki, sepatu
    pygame.draw.ellipse(screen, (175, 135, 90),
                        R(x - 14*s, y + 28*s, 28*s, 8*s))
    pants = (55, 55, 85)
    pygame.draw.rect(screen, pants, R(x - 9*s, y + 18*s, 7*s, 12*s),
                     border_radius=2)
    pygame.draw.rect(screen, pants, R(x + 2*s, y + 18*s, 7*s, 12*s),
                     border_radius=2)
    pygame.draw.ellipse(screen, DARK, R(x - 10*s, y + 28*s, 9*s, 5*s))
    pygame.draw.ellipse(screen, DARK, R(x + 1*s, y + 28*s, 9*s, 5*s))

    # lengan + tangan
    armc = shade(shirt, .85)
    for sx in (-1, 1):
        pygame.draw.rect(screen, armc,
                         R(x + sx*14*s - 3*s, y + 1*s, 6*s, 15*s),
                         border_radius=int(3*s))
        pygame.draw.circle(screen, skin, P(x + sx*14*s, y + 17*s),
                           max(2, int(3*s)))

    # badan
    pygame.draw.rect(screen, shirt, R(x - 12*s, y, 24*s, 22*s),
                     border_radius=int(5*s))
    if apron:
        pygame.draw.polygon(screen, WHITE, [
            P(x - 8*s, y + 5*s), P(x + 8*s, y + 5*s),
            P(x + 10*s, y + 22*s), P(x - 10*s, y + 22*s)])
        pygame.draw.rect(screen, (215, 215, 215),
                         R(x - 4*s, y + 13*s, 8*s, 5*s), 1)

    # rambut belakang / jilbab
    if st != "hijab":
        pygame.draw.rect(screen, shade(skin, .92), R(x - 3*s, y - 4*s, 6*s, 6*s))
    if st == "long":
        pygame.draw.rect(screen, hair, R(x - 12*s, hy - 3*s, 24*s, 24*s),
                         border_radius=int(7*s))
    elif st == "curly":
        for ddx, ddy, r in ((-9, -5, 7), (9, -5, 7), (0, -11, 8),
                            (-11, 2, 5), (11, 2, 5)):
            pygame.draw.circle(screen, hair, P(x + ddx*s, hy + ddy*s),
                               max(2, int(r*s)))
    elif st == "hijab":
        pygame.draw.circle(screen, acc, P(x, hy), int(14*s))
        pygame.draw.rect(screen, acc, R(x - 14*s, hy, 28*s, 19*s),
                         border_radius=int(8*s))
    else:
        for sx in (-1, 1):  # telinga
            pygame.draw.circle(screen, shade(skin, .95),
                               P(x + sx*11*s, hy + 1*s), max(2, int(2.6*s)))

    # kepala
    if st == "hijab":
        pygame.draw.ellipse(screen, skin, R(x - 9*s, hy - 10*s, 18*s, 21*s))
    else:
        pygame.draw.circle(screen, skin, P(x, hy), int(11*s))

    # rambut depan / topi
    if st in ("short", "long", "bun"):
        pygame.draw.ellipse(screen, hair, R(x - 11.5*s, hy - 12.5*s, 23*s, 11*s))
        if st == "bun":
            pygame.draw.circle(screen, hair, P(x, hy - 14*s), max(2, int(5*s)))
    elif st == "curly":
        pygame.draw.ellipse(screen, hair, R(x - 10*s, hy - 12*s, 20*s, 8*s))
    elif st == "spiky":
        pygame.draw.polygon(screen, hair, [
            P(x - 11*s, hy - 2*s), P(x - 11*s, hy - 12*s),
            P(x - 7*s, hy - 8*s), P(x - 4*s, hy - 17*s),
            P(x, hy - 10*s), P(x + 4*s, hy - 17*s),
            P(x + 7*s, hy - 8*s), P(x + 11*s, hy - 12*s),
            P(x + 11*s, hy - 2*s)])
    elif st == "cap":
        pygame.draw.ellipse(screen, acc, R(x - 12*s, hy - 14*s, 24*s, 14*s))
        pygame.draw.rect(screen, shade(acc, .75), R(x - 12*s, hy - 4*s, 24*s, 4*s),
                         border_radius=2)
    elif st == "peci":
        pygame.draw.polygon(screen, (28, 28, 28), [
            P(x - 9*s, hy - 7*s), P(x + 9*s, hy - 7*s),
            P(x + 8*s, hy - 17*s), P(x - 8*s, hy - 17*s)])
        pygame.draw.line(screen, (200, 170, 60),
                         P(x - 9*s, hy - 8*s), P(x + 9*s, hy - 8*s), lw)
    elif st == "chef":
        pygame.draw.ellipse(screen, hair, R(x - 11*s, hy - 9*s, 22*s, 7*s))
        puffs = ((-6, -17, 6), (0, -20, 6.5), (6, -17, 6))
        gray = (205, 205, 205)
        for ddx, ddy, r in puffs:
            pygame.draw.circle(screen, gray, P(x + ddx*s, hy + ddy*s),
                               int((r + 1)*s))
        pygame.draw.rect(screen, gray, R(x - 10*s, hy - 15*s, 20*s, 9*s),
                         border_radius=int(2*s))
        for ddx, ddy, r in puffs:
            pygame.draw.circle(screen, WHITE, P(x + ddx*s, hy + ddy*s),
                               int(r*s))
        pygame.draw.rect(screen, WHITE, R(x - 9*s, hy - 14*s, 18*s, 7*s))

    # ---------- fitur wajah ----------
    ex, ey = 4.2 * s, hy + 1 * s

    if f["blush"]:
        for sx in (-1, 1):
            pygame.draw.circle(screen, (245, 150, 140),
                               P(x + sx*7*s, ey + 4*s), max(2, int(2.4*s)))

    et = f["eyes"]
    if mood and et == 2:
        et = 0
    if mood == 2:
        et = 0
    for sx in (-1, 1):
        cx = x + sx * ex
        if et == 0:
            pygame.draw.circle(screen, DARK, P(cx, ey), max(1, int(1.8*s)))
        elif et == 1:
            pygame.draw.circle(screen, WHITE, P(cx, ey), max(2, int(3*s)))
            pygame.draw.circle(screen, DARK, P(cx, ey), max(1, int(1.6*s)))
        else:  # mata senyum
            pygame.draw.lines(screen, DARK, False, [
                P(cx - 2.5*s, ey + 1*s), P(cx, ey - 1.5*s),
                P(cx + 2.5*s, ey + 1*s)], lw)

    if mood == 2:  # alis marah
        pygame.draw.line(screen, DARK, P(x - ex - 3*s, ey - 5*s),
                         P(x - ex + 3*s, ey - 2.5*s), lw)
        pygame.draw.line(screen, DARK, P(x + ex + 3*s, ey - 5*s),
                         P(x + ex - 3*s, ey - 2.5*s), lw)

    if f["glasses"]:
        for sx in (-1, 1):
            pygame.draw.circle(screen, DARK, P(x + sx*ex, ey),
                               max(3, int(3.7*s)), 1)
        pygame.draw.line(screen, DARK, P(x - ex + 3.5*s, ey),
                         P(x + ex - 3.5*s, ey), 1)

    my = hy + 6.5 * s
    if f["mustache"]:
        pygame.draw.ellipse(screen, hair, R(x - 4*s, my - 2.5*s, 8*s, 2.6*s))

    if mood == 2:  # cemberut
        pygame.draw.lines(screen, DARK, False, [
            P(x - 3*s, my + 1.5*s), P(x, my - .5*s),
            P(x + 3*s, my + 1.5*s)], lw)
    elif mood == 1:  # datar
        pygame.draw.line(screen, DARK, P(x - 2.5*s, my + .5*s),
                         P(x + 2.5*s, my + .5*s), lw)
    else:
        mt = f["mouth"]
        if mt == 0:  # senyum
            pygame.draw.lines(screen, DARK, False, [
                P(x - 3*s, my - 1*s), P(x - 1.5*s, my + 1*s),
                P(x + 1.5*s, my + 1*s), P(x + 3*s, my - 1*s)], lw)
        elif mt == 1:  # senyum lebar
            pygame.draw.ellipse(screen, (150, 40, 40),
                                R(x - 3*s, my - 1.5*s, 6*s, 4*s))
        else:  # senyum miring
            pygame.draw.lines(screen, DARK, False, [
                P(x - 2*s, my + .5*s), P(x + 1*s, my + 1*s),
                P(x + 3*s, my - .5*s)], lw)

# ---------- GAMBAR MAKANAN ----------
def draw_food(i, x, y, size=18, plate=False):
    x, y = int(x), int(y)
    u = size / 18.0

    def q(a, b):
        return (int(x + a*u), int(y + b*u))

    def rr(a, b, w, h):
        return R(x + a*u, y + b*u, w*u, h*u)

    lw = max(1, int(1.6*u))

    if plate:
        pygame.draw.circle(screen, WHITE, (x, y), int(size*1.2))
        pygame.draw.circle(screen, ITEMS[i][2], (x, y), int(size*1.2), 2)

    if i == 0:  # BURGER
        bun = (226, 150, 62)
        pygame.draw.rect(screen, bun, rr(-15, 12, 30, 7), border_radius=int(3*u))
        pygame.draw.rect(screen, (110, 58, 30), rr(-16, 6, 32, 7),
                         border_radius=int(3*u))
        pygame.draw.rect(screen, (255, 205, 55), rr(-15, 4, 30, 5))
        pygame.draw.ellipse(screen, (90, 180, 70), rr(-17, 0, 34, 6))
        pygame.draw.ellipse(screen, bun, rr(-16, -17, 32, 20))
        for a, b in ((-7, -11), (1, -13), (8, -9), (-1, -7)):
            pygame.draw.ellipse(screen, (255, 238, 195), rr(a, b, 4, 2.4))

    elif i == 1:  # KENTANG GORENG
        for px, top in ((-9, -9), (-4.5, -15), (0, -11), (4.5, -16), (9, -10)):
            pygame.draw.rect(screen, (250, 205, 60), rr(px - 2, top, 4, 20),
                             border_radius=int(1*u))
            pygame.draw.rect(screen, (225, 165, 40), rr(px - 2, top, 4, 20), 1,
                             border_radius=int(1*u))
        pygame.draw.polygon(screen, (215, 50, 50),
                            [q(-12, 2), q(12, 2), q(9, 18), q(-9, 18)])
        pygame.draw.circle(screen, (255, 205, 55), q(0, 10), max(2, int(3*u)))

    elif i == 2:  # AYAM GORENG
        bone = (245, 235, 215)
        pygame.draw.line(screen, bone, q(2, 2), q(12, 13), max(2, int(4*u)))
        pygame.draw.circle(screen, bone, q(11, 15), max(2, int(3*u)))
        pygame.draw.circle(screen, bone, q(14, 12), max(2, int(3*u)))
        pygame.draw.ellipse(screen, (200, 105, 40), rr(-16, -16, 26, 23))
        pygame.draw.ellipse(screen, (225, 145, 65), rr(-13, -13, 12, 8))
        for a, b in ((-3, -3), (2, 0), (-8, 2), (1, -8), (-9, -8)):
            pygame.draw.circle(screen, (165, 80, 30), q(a, b), max(1, int(1.4*u)))

    elif i == 3:  # PIZZA
        tri = [q(-15, -11), q(15, -11), q(0, 17)]
        pygame.draw.polygon(screen, (252, 200, 70), tri)
        pygame.draw.polygon(screen, (205, 140, 40), tri, lw)
        pygame.draw.rect(screen, (205, 135, 65), rr(-16, -16, 32, 7),
                         border_radius=int(3*u))
        for a, b, r in ((-5, -3, 3.5), (5, -2, 3), (0, 7, 3)):
            pygame.draw.circle(screen, (200, 50, 50), q(a, b), max(2, int(r*u)))
        pygame.draw.circle(screen, (70, 150, 60), q(-1, 1), max(1, int(1.3*u)))

    elif i == 4:  # HOTDOG
        pygame.draw.rect(screen, (225, 165, 85), rr(-15, -8, 30, 18),
                         border_radius=int(8*u))
        pygame.draw.rect(screen, (190, 65, 45), rr(-18, -5, 36, 9),
                         border_radius=int(4*u))
        pygame.draw.rect(screen, (210, 145, 65), rr(-15, 0, 30, 11),
                         border_radius=int(5*u))
        pygame.draw.lines(screen, (255, 205, 55), False,
                          [q(-12, -2), q(-8, -4.5), q(-4, -2), q(0, -4.5),
                           q(4, -2), q(8, -4.5), q(12, -2)], lw)

    else:  # MINUMAN
        straw = (220, 50, 50)
        pygame.draw.line(screen, straw, q(2, -9), q(6, -17), max(2, int(2*u)))
        pygame.draw.line(screen, straw, q(6, -17), q(11, -17), max(2, int(2*u)))
        pygame.draw.polygon(screen, (245, 245, 250),
                            [q(-9, -6), q(9, -6), q(7, 17), q(-7, 17)])
        pygame.draw.polygon(screen, (60, 140, 210),
                            [q(-8.4, -1), q(8.4, -1), q(7, 17), q(-7, 17)])
        pygame.draw.rect(screen, (225, 240, 255), rr(-5, 2, 5, 5), border_radius=2)
        pygame.draw.rect(screen, (225, 240, 255), rr(1, 8, 5, 5), border_radius=2)
        pygame.draw.polygon(screen, (190, 190, 205),
                            [q(-9, -6), q(9, -6), q(7, 17), q(-7, 17)], 1)
        pygame.draw.rect(screen, WHITE, rr(-11, -10, 22, 4),
                         border_radius=int(2*u))
        pygame.draw.rect(screen, (190, 190, 205), rr(-11, -10, 22, 4), 1,
                         border_radius=int(2*u))


# ---------- JAM MASAK, SENAPAN, TEMBOK, ZOMBIE ----------
def draw_heart(x, y, size, color=(225, 45, 70)):
    x, y = int(x), int(y)
    r = max(2, int(size * .55))
    pygame.draw.circle(screen, color,
                       (x - int(size * .5), y - int(size * .3)), r)
    pygame.draw.circle(screen, color,
                       (x + int(size * .5), y - int(size * .3)), r)
    pygame.draw.polygon(screen, color, [
        (x - int(size * 1.04), y - int(size * .05)),
        (x + int(size * 1.04), y - int(size * .05)),
        (x, y + int(size * 1.05))])
    pygame.draw.circle(screen, (255, 190, 200),
                       (x - int(size * .6), y - int(size * .45)),
                       max(1, int(size * .2)))

def draw_skull(x, y, size):
    """Ikon tengkorak sederhana untuk mata uang skin."""
    x, y = int(x), int(y)
    s = max(4, int(size))
    # kepala
    pygame.draw.ellipse(screen, (240, 235, 220),
                        R(x - s * .55, y - s * .6, s * 1.1, s * 1.05))
    pygame.draw.ellipse(screen, (90, 80, 70),
                        R(x - s * .55, y - s * .6, s * 1.1, s * 1.05), 1)
    # mata
    for sx in (-1, 1):
        pygame.draw.ellipse(screen, (30, 25, 25),
                            R(x + sx * s * .22 - s * .14, y - s * .25,
                              s * .28, s * .32))
    # hidung
    pygame.draw.polygon(screen, (50, 40, 35), [
        P(x, y + s * .05), P(x - s * .1, y + s * .22),
        P(x + s * .1, y + s * .22)])
    # gigi
    pygame.draw.rect(screen, (240, 235, 220),
                     R(x - s * .28, y + s * .28, s * .56, s * .22),
                     border_radius=2)
    for gx in (-.18, -.06, .06, .18):
        pygame.draw.line(screen, (90, 80, 70),
                         P(x + gx * s, y + s * .28),
                         P(x + gx * s, y + s * .48), 1)

def draw_bullet(x, y, size):
    s = size
    pygame.draw.rect(screen, (235, 190, 70),
                     R(x - .45*s, y - .1*s, .9*s, 1.1*s), border_radius=2)
    pygame.draw.polygon(screen, (190, 110, 50), [
        P(x - .45*s, y - .1*s), P(x + .45*s, y - .1*s), P(x, y - 1.1*s)])
    pygame.draw.line(screen, (170, 130, 40),
                     P(x - .45*s, y + .75*s), P(x + .45*s, y + .75*s), 1)

def draw_clock(x, y, r, frac, label=None):
    # jam: bagian oranye = sisa waktu memasak
    x, y, r = int(x), int(y), max(4, int(r))
    frac = max(0.0, min(1.0, frac))
    pygame.draw.circle(screen, WHITE, (x, y), r)
    if frac > 0:
        n = max(3, int(30 * frac) + 1)
        pts = [(x, y)]
        for k in range(n + 1):
            a = -math.pi / 2 + 2 * math.pi * frac * k / n
            pts.append((int(x + math.cos(a) * (r - 2)),
                        int(y + math.sin(a) * (r - 2))))
        pygame.draw.polygon(screen, ORANGE, pts)
    pygame.draw.circle(screen, BROWN, (x, y), r, 2)
    pygame.draw.line(screen, DARK, (x, y - r), (x, y - r + 3), 2)
    if label is not None and r >= 10:
        draw_text(label, SMALL, DARK, x, y)

def draw_station(r, rect):
    st = game.stations[r]
    panel = rect.inflate(-CELL_W * .10, -CELL_H * .14)
    pygame.draw.rect(screen, (110, 110, 120), panel, border_radius=8)
    label = STATIONS[r] + (" +" if st["level"] else "")
    img = SMALL.render(label, True, WHITE)
    if img.get_width() > panel.w - 6:
        k = (panel.w - 6) / img.get_width()
        img = pygame.transform.smoothscale(
            img, (max(1, int(img.get_width() * k)),
                  max(1, int(img.get_height() * k))))
    screen.blit(img, img.get_rect(center=(panel.centerx, int(panel.y + panel.h * .15))))

    isz = max(6, int(panel.h * .11))
    cooks = st["cooks"]
    for idx, ck in enumerate(cooks):
        cr = max(6, int(panel.h * .13))
        cx = panel.centerx + (idx - (len(cooks)-1)/2) * cr * 2.7
        cy = panel.y + panel.h * .48
        draw_clock(cx - cr, cy, cr, ck["left"] / ck["total"],
                   str(int(math.ceil(ck["left"]))))
        draw_food(ck["item"], cx + cr, cy, isz)

    n = len(st["ready"])
    gap = isz * 2.7
    for k, item in enumerate(st["ready"]):
        draw_food(item, panel.centerx + (k - (n - 1) / 2) * gap,
                  panel.y + panel.h * .84, isz, True)

def draw_gun_post(r, rect):
    pygame.draw.rect(screen, (205, 170, 120), rect.inflate(-2, -2))
    u = CELL_W * .0075
    ox = rect.x + CELL_W * .38
    oy = rect.centery + CELL_H * .12

    # karung pasir
    for k in range(3):
        bag = R(ox - 28*u + k*20*u, oy + 8*u, 22*u, 11*u)
        pygame.draw.ellipse(screen, (190, 160, 95), bag)
        pygame.draw.ellipse(screen, (145, 115, 65), bag, 1)

    # senapan
    pygame.draw.polygon(screen, (120, 75, 40), [
        P(ox - 26*u, oy - 1*u), P(ox - 10*u, oy - 3*u),
        P(ox - 10*u, oy + 5*u), P(ox - 22*u, oy + 9*u)])
    pygame.draw.rect(screen, (70, 70, 78),
                     R(ox - 10*u, oy - 4*u, 22*u, 8*u), border_radius=2)
    pygame.draw.rect(screen, (45, 45, 52), R(ox + 12*u, oy - 2*u, 26*u, 4*u))
    pygame.draw.rect(screen, (30, 30, 35), R(ox + 36*u, oy - 3*u, 4*u, 6*u))
    pygame.draw.rect(screen, (35, 35, 40),
                     R(ox - 2*u, oy - 9*u, 12*u, 4*u), border_radius=2)
    pygame.draw.circle(screen, (90, 160, 230),
                       P(ox + 10*u, oy - 7*u), max(1, int(2*u)))
    pygame.draw.rect(screen, (60, 60, 66), R(ox + 1*u, oy + 4*u, 6*u, 10*u))

    # kilatan moncong saat menembak
    p = game.player
    if game.flash > 0 and p["x"] >= 8.0 and int(p["y"]) == r:
        fx = ox + 40*u
        pygame.draw.polygon(screen, (255, 225, 90), [
            P(fx, oy), P(fx + 9*u, oy - 6*u), P(fx + 6*u, oy),
            P(fx + 12*u, oy + 1*u), P(fx + 6*u, oy + 3*u),
            P(fx + 9*u, oy + 8*u)])

CRACKS = [
    [(.15, .05), (.5, .09), (.35, .15)],
    [(.6, .22), (.3, .28), (.55, .34), (.4, .4)],
    [(.2, .45), (.55, .5), (.45, .58)],
    [(.7, .62), (.4, .66), (.6, .74)],
    [(.25, .78), (.6, .82), (.4, .9)],
    [(.5, .12), (.7, .2), (.55, .26)],
    [(.3, .52), (.15, .6), (.35, .68)],
    [(.65, .88), (.35, .94), (.5, .99)],
]

def draw_wall():
    ww = CELL_W * .8
    rect = R(M + 9 * CELL_W + CELL_W * .1, MAP_Y, ww, MAP_H)
    frac = max(0.0, game.wall / WALL_HP)
    base = (180, 120, 110) if game.wall_hit > 0 else (150, 140, 130)
    pygame.draw.rect(screen, base, rect, border_radius=6)

    # susunan bata
    bh = max(8, int(CELL_H / 4))
    k = 0
    yy = MAP_Y
    while yy < MAP_Y + MAP_H:
        y2 = min(MAP_Y + MAP_H, yy + bh)
        pygame.draw.line(screen, (105, 95, 88),
                         (rect.x, yy), (rect.right - 1, yy), 1)
        xs = (.5,) if k % 2 == 0 else (.25, .75)
        for fx in xs:
            pygame.draw.line(screen, (105, 95, 88),
                             (int(rect.x + ww * fx), yy),
                             (int(rect.x + ww * fx), y2), 1)
        yy += bh
        k += 1

    # retakan makin banyak saat health turun
    if frac < 1:
        n = min(len(CRACKS), int((1 - frac) * len(CRACKS) + .999))
        for cr in CRACKS[:n]:
            pts = [(int(rect.x + px * ww), int(MAP_Y + py * MAP_H))
                   for px, py in cr]
            pygame.draw.lines(screen, (55, 45, 40), False, pts, 2)

    pygame.draw.rect(screen, (80, 70, 65), rect, 3, border_radius=6)

def draw_zone_hud():
    # peluru (di atas pos senapan) & health tembok (di atas tembok)
    gh = MAP_Y - DOOR_TOP
    cy = DOOR_TOP + gh // 2
    x8 = M + 8 * CELL_W
    x9 = M + 9 * CELL_W

    bs = max(5, int(gh * .26))
    for k in range(2):
        draw_bullet(x8 + CELL_W * (.12 + k * .1), cy, bs)
    draw_text("x" + str(game.ammo), SMALL,
              RED if game.ammo <= 5 else DARK, x8 + CELL_W * .62, cy)

    draw_heart(x9 + CELL_W * .14, cy - gh * .05, max(5, int(gh * .22)))
    bar = R(x9 + CELL_W * .30, cy - gh * .2, CELL_W * .64, gh * .4)
    frac = max(0.0, game.wall / WALL_HP)
    col = GREEN if frac > .5 else (ORANGE if frac > .25 else RED)
    pygame.draw.rect(screen, (70, 30, 30), bar, border_radius=6)
    pygame.draw.rect(screen, col, R(bar.x, bar.y, bar.w * frac, bar.h),
                     border_radius=6)
    pygame.draw.rect(screen, WHITE, bar, 2, border_radius=6)
    draw_text(str(int(game.wall)), SMALL, WHITE, bar.centerx, bar.centery)

def draw_zombie(x, y, s, phase, hpf):
    x, y = int(x), int(y)
    y = int(y + math.sin(phase * 2) * 1.5 * s)
    sw = math.sin(phase) * 3 * s
    skin = (126, 172, 104)
    hy = y - 11 * s

    pygame.draw.ellipse(screen, (130, 140, 105),
                        R(x - 14*s, y + 28*s, 28*s, 8*s))
    pants = (70, 68, 58)
    pygame.draw.rect(screen, pants, R(x - 9*s + sw, y + 18*s, 7*s, 12*s),
                     border_radius=2)
    pygame.draw.rect(screen, pants, R(x + 2*s - sw, y + 18*s, 7*s, 12*s),
                     border_radius=2)
    pygame.draw.ellipse(screen, DARK, R(x - 10*s + sw, y + 28*s, 9*s, 5*s))
    pygame.draw.ellipse(screen, DARK, R(x + 1*s - sw, y + 28*s, 9*s, 5*s))

    # lengan terjulur ke arah tembok (kiri)
    for ay in (3, 9):
        pygame.draw.rect(screen, skin, R(x - 27*s, y + ay*s, 18*s, 5*s),
                         border_radius=int(2*s))
        pygame.draw.circle(screen, shade(skin, .85),
                           P(x - 27*s, y + (ay + 2.5)*s), max(2, int(3*s)))

    # badan sobek + noda darah
    pygame.draw.rect(screen, (95, 105, 135), R(x - 12*s, y, 24*s, 22*s),
                     border_radius=int(4*s))
    pygame.draw.rect(screen, (70, 78, 105), R(x - 12*s, y + 17*s, 24*s, 5*s),
                     border_radius=int(2*s))
    for bx, by in ((4, 7), (-6, 12), (7, 15)):
        pygame.draw.circle(screen, (150, 30, 30),
                           P(x + bx*s, y + by*s), max(1, int(2.2*s)))

    # kepala
    pygame.draw.circle(screen, skin, P(x, hy), int(11*s))
    pygame.draw.polygon(screen, (50, 45, 35), [
        P(x - 9*s, hy - 6*s), P(x - 7*s, hy - 14*s), P(x - 3*s, hy - 9*s),
        P(x + 1*s, hy - 15*s), P(x + 4*s, hy - 9*s), P(x + 9*s, hy - 12*s),
        P(x + 9*s, hy - 4*s)])
    for ex in (-6, -.5):
        pygame.draw.circle(screen, WHITE, P(x + ex*s, hy), max(2, int(2.7*s)))
        pygame.draw.circle(screen, (200, 30, 30),
                           P(x + (ex - .8)*s, hy), max(1, int(1.4*s)))
    lw = max(1, int(1.5*s))
    pygame.draw.line(screen, DARK, P(x - 10*s, hy - 5*s),
                     P(x - 3*s, hy - 2.5*s), lw)
    pygame.draw.line(screen, DARK, P(x - 1*s, hy - 3*s),
                     P(x + 4*s, hy - 4*s), lw)
    pygame.draw.ellipse(screen, (60, 15, 15), R(x - 9*s, hy + 4*s, 9*s, 5*s))
    pygame.draw.rect(screen, WHITE, R(x - 8*s, hy + 4*s, 2*s, 2*s))
    pygame.draw.rect(screen, WHITE, R(x - 4*s, hy + 4*s, 2*s, 2*s))
    pygame.draw.line(screen, (150, 30, 30), P(x + 3*s, hy - 6*s),
                     P(x + 7*s, hy - 1*s), lw)

    # bar health zombie
    bw = int(30*s)
    bh = max(4, int(4*s))
    bx, by = x - bw // 2, int(hy - 20*s)
    pygame.draw.rect(screen, (60, 20, 20), (bx, by, bw, bh))
    pygame.draw.rect(screen, GREEN, (bx, by, int(bw * max(0, hpf)), bh))
    pygame.draw.rect(screen, WHITE, (bx, by, bw, bh), 1)


def phone_layout():
    pw, ph = int(W * .62), int(H * .58)
    px = (W - pw) // 2
    py = (H - ph) // 2
    bw3 = int(pw * .28)
    bh = int(ph * .18)
    return {
        "panel": pygame.Rect(px, py, pw, ph),
        # baris 1: karyawan | tentara | pembersih
        "k": pygame.Rect(px + int(pw * .06), py + int(ph * .30), bw3, bh),
        "t": pygame.Rect(px + int(pw * .36), py + int(ph * .30), bw3, bh),
        "cleaner": pygame.Rect(px + int(pw * .66), py + int(ph * .30), bw3, bh),
        # baris 2: koki | upgrade
        "chef": pygame.Rect(px + int(pw * .06), py + int(ph * .53),
                            int(pw * .42), bh),
        "upgrade": pygame.Rect(px + int(pw * .52), py + int(ph * .53),
                               int(pw * .42), bh),
        "x": pygame.Rect(px + pw - int(W * .07), py + int(H * .015),
                         int(W * .055), int(H * .055)),
    }


def main_menu_layout():
    """Layout layar menu utama: INFO kiri | MAIN/SKIN/KELUAR tengah | REKOR kanan."""
    bw = int(W * .32)
    bh = int(H * .09)
    cx = W // 2
    top = int(H * .38)
    gap = int(H * .025)
    # tombol INFO di kiri
    info_w = int(W * .12)
    info_h = int(H * .10)
    # area rekor di kanan
    rec_w = int(W * .22)
    rec_h = int(H * .16)
    return {
        "play": pygame.Rect(cx - bw // 2, top, bw, bh),
        "skin": pygame.Rect(cx - bw // 2, top + bh + gap, bw, bh),
        "quit": pygame.Rect(cx - bw // 2, top + 2 * (bh + gap), bw, bh),
        "info": pygame.Rect(int(W * .06), top + bh, info_w, info_h),
        "record": pygame.Rect(W - int(W * .06) - rec_w, top + int(bh * 0.5), rec_w, rec_h),
    }


def skin_layout():
    """Layout panel kustomisasi skin."""
    pw, ph = int(W * .78), int(H * .78)
    px = (W - pw) // 2
    py = (H - ph) // 2
    # tombol opsi di sisi kanan panel
    opts = {}
    labels = [
        ("skin", "Kulit"),
        ("hair", "Rambut"),
        ("style", "Gaya"),
        ("accent", "Aksen"),
        ("eyes", "Mata"),
        ("mouth", "Mulut"),
        ("glasses", "Kacamata"),
        ("mustache", "Kumis"),
        ("blush", "Blush"),
    ]
    ox = px + int(pw * .42)
    oy = py + int(ph * .22)
    ow = int(pw * .24)
    oh = int(ph * .065)
    og = int(ph * .012)
    for i, (key, lab) in enumerate(labels):
        row = i
        opts[key] = pygame.Rect(ox, oy + row * (oh + og), ow, oh)
        opts[key + "_next"] = pygame.Rect(ox + ow + 6, oy + row * (oh + og),
                                          int(ow * .55), oh)
    return {
        "panel": pygame.Rect(px, py, pw, ph),
        "back": pygame.Rect(px + int(pw * .04), py + int(ph * .88),
                            int(pw * .22), int(ph * .08)),
        "reset": pygame.Rect(px + int(pw * .30), py + int(ph * .88),
                             int(pw * .22), int(ph * .08)),
        "opts": opts,
        "labels": labels,
        "preview_x": px + int(pw * .20),
        "preview_y": py + int(ph * .42),
        # kolom NAMA tepat di bawah karakter preview
        "name": pygame.Rect(px + int(pw * .20) - int(pw * .17),
                            py + int(ph * .42) + int(80 * PS) + int(ph * .05),
                            int(pw * .34), int(ph * .085)),
    }


def wrap_text(txt, font, maxw):
    """Pecah teks jadi beberapa baris sesuai lebar maksimum."""
    words = str(txt).split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w) if cur else w
        if not cur or font.size(test)[0] <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def info_layout():
    """Layout panel informasi: judul di kiri (bisa diklik) | detail di kanan."""
    pw, ph = int(W * .86), int(H * .86)
    px = (W - pw) // 2
    py = (H - ph) // 2
    n = len(INFO_TOPICS)
    per_col = (n + 1) // 2
    colw = int(pw * .215)
    gx = int(pw * .015)
    rh = int(ph * .075)
    gap = int(ph * .012)
    top = py + int(ph * .12)
    x0 = px + int(pw * .03)
    rows = []
    for i in range(n):
        c, r = i // per_col, i % per_col
        rows.append(pygame.Rect(x0 + c * (colw + gx), top + r * (rh + gap), colw, rh))
    dx = x0 + 2 * (colw + gx) + gx
    detail = pygame.Rect(dx, top, px + pw - int(pw * .03) - dx,
                         per_col * (rh + gap) - gap)
    return {
        "panel": pygame.Rect(px, py, pw, ph),
        "rows": rows,
        "detail": detail,
        "back": pygame.Rect(px + int(pw * .35), py + int(ph * .90),
                            int(pw * .30), int(ph * .07)),
    }


# Isi informasi: (judul, warna, [penjelasan spesifik ...]) — klik judul di panel INFO
INFO_TOPICS = [
    ("TUJUAN", ORANGE, [
        "Bertahan selama mungkin. Game over hanya jika tembok hancur.",
        "Timer bertahan naik terus. Waktu terlama jadi REKOR di menu utama.",
        "Uang didapat dari pelanggan yang dilayani, tip di meja, dan zombie yang dibunuh (+%s tiap zombie)." % fmt(500),
    ]),
    ("HARI", BLUE, [
        "1 hari = %d detik permainan." % DAY_LEN,
        "Target pelanggan hari 1 = %d, lalu naik %d tiap hari." % (CUSTOMER_BASE, CUSTOMER_STEP),
        "Jumlah zombie per hari = hari x (hari + 1) - 2. Hari 1 = 2, hari 2 = 4, hari 3 = 10, hari 4 = 18, dst.",
        "Health zombie naik 1 tiap hari. Semua zombie hari itu datang dalam kurang dari 2 menit.",
        "Tombol kecepatan di header: 1x, 4x, 8x.",
    ]),
    ("BULAN MERAH", RED, [
        "Terjadi tiap kelipatan %d hari (5, 10, 15, ...)." % BLOOD_EVERY,
        "Cahaya mendadak jadi merah dan jumlah zombie hari itu %d kali lipat." % BLOOD_MULT,
        "Lagu latar berganti jadi lagu tegang dengan volume naik 25%.",
    ]),
    ("DAPUR", (200, 140, 60), [
        "Klik kartu menu makanan di atas untuk mulai memasak.",
        "Burger & Hotdog dimasak di Panggangan, Kentang & Ayam di Penggorengan, Pizza di Oven, Minuman di Mesin Minum.",
        "Ketuk alat untuk mengambil makanan matang. Pengambilan sistem borong: semua yang matang terambil sampai tangan penuh (maks %d)." % MAX_CARRY,
        "Hanya kamu yang bisa salah masak / salah ambil. Buang sendiri ke SAMPAH.",
    ]),
    ("MEJA", GREEN, [
        "Beli meja (%s) agar pelanggan bisa duduk & makan di tempat." % fmt(TABLE_PRICE),
        "Pelanggan datang dari pintu di atas area antre dan berbaris.",
        "Pelanggan bisa meninggalkan tip (koin) di meja. Ambil sendiri atau pakai karyawan pembersih.",
    ]),
    ("SENAPAN", (90, 90, 110), [
        "Berdiri di pos senapan (kolom 8) untuk menembak otomatis.",
        "Jeda tembak awal %.1f detik. Tiap 100 peluru yang pernah dimiliki mempercepat 0,05 detik, sampai batas %.1f detik." % (FIRE_DELAY, AK47_MIN_DELAY),
        "Peluru menembus: kalau damage lebih besar dari health zombie, sisanya diteruskan ke zombie di belakang.",
    ]),
    ("PELURU", YELLOW, [
        "1 peluru = %s. Peluru awal %d." % (fmt(AMMO_PRICE), START_AMMO),
        "Beli di tombol +PELURU: paket 10, 100, 1.000, atau 10.000.",
        "Damage peluru = 1 + 1% dari jumlah peluru yang kamu punya (minimal 1). Makin banyak peluru, makin kuat.",
    ]),
    ("TEMBOK", (150, 100, 90), [
        "Kekuatan tembok awal %d HP. Zombie yang sampai di tembok akan memukulnya." % WALL_HP,
        "Perbaiki di kolom tembok (kolom 9): %s untuk +%d HP." % (fmt(REPAIR_COST), REPAIR_HP),
        "Tembok hancur = GAME OVER.",
    ]),
    ("PONSEL", (50, 140, 200), [
        "Tombol PONSEL (di header atau bawah) membuka menu rekrut.",
        "Isinya: Karyawan, Pembersih, Tentara, Koki, dan peningkatan alat dapur.",
        "Harga: Karyawan & Tentara %s, Pembersih %s, Koki %s." % (fmt(HIRE_COST), fmt(CLEANER_COST), fmt(CHEF_COST)),
    ]),
    ("KARYAWAN", (70, 170, 100), [
        "Otomatis mengantar makanan ke pelanggan (maks %d)." % MAX_KARYAWAN,
        "Harga %s per orang." % fmt(HIRE_COST),
        "Karyawan hanya mengantar. Memasak dilakukan kamu atau koki.",
    ]),
    ("PEMBERSIH", (40, 150, 150), [
        "Khusus mengambil tip/koin di meja (maks %d)." % MAX_CLEANER,
        "Harga %s per orang." % fmt(CLEANER_COST),
    ]),
    ("TENTARA", (90, 90, 120), [
        "Otomatis menembak zombie (maks %d)." % MAX_TENTARA,
        "Memakai peluru yang sama dengan senapan kamu.",
        "Harga %s per orang." % fmt(HIRE_COST),
    ]),
    ("KOKI", (190, 125, 45), [
        "Otomatis memasak sesuai pesanan pelanggan (maks 10).",
        "Harga %s per orang." % fmt(CHEF_COST),
        "Koki hanya memasak yang dipesan, jadi tidak pernah salah masak.",
    ]),
    ("TENGKORAK", SKULL_GOLD, [
        "Kamu dapat 1 tengkorak tiap membunuh 10 zombie.",
        "Dipakai di menu SKIN untuk mengganti penampilan pemainmu.",
        "Harga tiap bagian skin berbeda, lihat angka di tombolnya.",
    ]),
    ("REKOR", YELLOW, [
        "Waktu bertahan terlama tersimpan otomatis dan tampil di menu utama.",
        "Rekor, tengkorak, dan skin tersimpan terpisah untuk MAIN SENDIRI dan MULTIPLAYER.",
    ]),
    ("MULTIPLAYER", (80, 150, 210), [
        "Menu MAIN punya 2 pilihan: MAIN SENDIRI dan MULTIPLAYER, masing-masing punya simpanan sendiri.",
        "BUAT SERVER: tulis nama dan sandi server. JOIN SERVER: tulis nama dan sandi yang sama.",
        "Pemain harus satu Wi-Fi atau hotspot yang sama. Maksimal 4 pemain.",
    ]),
]


def mode_layout():
    """Layar pilih mode: MAIN SENDIRI | MULTIPLAYER."""
    bw, bh = int(W * .42), int(H * .17)
    x = (W - bw) // 2
    return {
        "solo": pygame.Rect(x, int(H * .28), bw, bh),
        "multi": pygame.Rect(x, int(H * .28) + bh + int(H * .03), bw, bh),
        "back": pygame.Rect((W - int(W * .22)) // 2, int(H * .76), int(W * .22), int(H * .09)),
    }


def multi_layout():
    """Menu multiplayer: BUAT SERVER | JOIN SERVER."""
    bw, bh = int(W * .40), int(H * .15)
    x = (W - bw) // 2
    return {
        "host": pygame.Rect(x, int(H * .30), bw, bh),
        "join": pygame.Rect(x, int(H * .30) + bh + int(H * .03), bw, bh),
        "back": pygame.Rect((W - int(W * .22)) // 2, int(H * .76), int(W * .22), int(H * .09)),
    }


def form_layout():
    """Form nama + sandi server (dibuat di bagian atas supaya tidak tertutup keyboard)."""
    fx, fw, fh = int(W * .07), int(W * .50), int(H * .11)
    pw_w = fw - int(W * .125)
    pw_r = pygame.Rect(fx, int(H * .42), pw_w, fh)
    return {
        "name": pygame.Rect(fx, int(H * .24), fw, fh),
        "pw": pw_r,
        "show": pygame.Rect(pw_r.right + int(W * .01), pw_r.y, int(W * .115), fh),
        "ok": pygame.Rect(int(W * .66), int(H * .24), int(W * .27), fh),
        "back": pygame.Rect(int(W * .66), int(H * .42), int(W * .27), fh),
    }


def lobby_layout():
    bw = int(W * .30)
    x = (W - bw) // 2
    return {
        "start": pygame.Rect(x, int(H * .62), bw, int(H * .11)),
        "back": pygame.Rect(x, int(H * .76), bw, int(H * .11)),
    }


# =====================================================================
# SUARA (dibuat sendiri lewat kode, tanpa file audio / tanpa numpy)
# =====================================================================
ZOMBIE_REWARD = 500            # uang tiap zombie yang terbunuh

# ---- MUSIK LATAR ----
MUSIC_VOL_CALM = 0.30                    # hari normal: pelan
MUSIC_VOL_BLOOD = MUSIC_VOL_CALM * 1.25  # hari bulan merah: naik 25%
MUSIC_RMS = 4800                         # kekerasan dasar kedua lagu sama

_SR = 22050


def _sfx_resonator(f, bw):
    r = math.exp(-math.pi * bw / _SR)
    return (2 * r * math.cos(2 * math.pi * f / _SR), -r * r, 1 - r)


def _sfx_voice(dur, f0_fn, form_fn, amp_fn, noise_fn=None, seed=1):
    """Suara mirip manusia: gelombang gigi gergaji lewat filter formant."""
    rnd = random.Random(seed)
    n = int(dur * _SR)
    out = [0.0] * n
    ph = 0.0
    coef = None
    nf = 0
    y1 = [0.0] * 4
    y2 = [0.0] * 4
    for i in range(n):
        t = i / _SR
        if i % 40 == 0:
            form = form_fn(t)
            nf = len(form)
            coef = [(_sfx_resonator(f, bw), g) for (f, bw, g) in form]
        ph += f0_fn(t) / _SR
        if ph >= 1.0:
            ph -= 1.0
        x = 2 * ph - 1
        if noise_fn is not None:
            nz = noise_fn(t)
            x = x * (1 - nz) + (rnd.random() * 2 - 1) * nz
        s = 0.0
        for k in range(nf):
            (b1, b2, a), g = coef[k]
            yk = a * x + b1 * y1[k] + b2 * y2[k]
            y2[k] = y1[k]
            y1[k] = yk
            s += yk * g
        out[i] = s * amp_fn(t)
    return out


def _sfx_lerp(a, b, u):
    u = 0 if u < 0 else (1 if u > 1 else u)
    return a + (b - a) * u


def synth_hai(f0=190, seed=1):
    """'Hai!' : h (desah) -> a -> i"""
    dur = 0.46
    A = [(750, 110, 1.0), (1150, 130, .7), (2500, 160, .35)]
    I = [(300, 80, 1.0), (2300, 140, .8), (3000, 170, .4)]

    def form(t):
        u = (t - 0.22) / 0.16
        return [(_sfx_lerp(A[k][0], I[k][0], u),
                 _sfx_lerp(A[k][1], I[k][1], u),
                 A[k][2]) for k in range(3)]

    def f0_fn(t):
        return f0 * (1 + 0.14 * max(0, (t - 0.12)) / 0.34) \
            * (1 + .012 * math.sin(2 * math.pi * 5.5 * t))

    def amp(t):
        if t < .07:                          # "h"
            return 0.55 * (t / .07)
        if t < .10:
            return 0.55 + 0.45 * ((t - .07) / .03)
        env = 1.0
        if t > .30:
            env = max(0.0, 1 - (t - .30) / .16)
        return env

    def noise(t):
        if t < .07:
            return .9
        if t < .12:
            return .9 - .8 * ((t - .07) / .05)
        return .08

    return _sfx_voice(dur, f0_fn, form, amp, noise, seed)


def synth_crowd(seed=7):
    """Keramaian seperti di mall: beberapa orang ngobrol bersamaan."""
    rnd = random.Random(seed)
    dur = 1.3
    n = int(dur * _SR)
    mix = [0.0] * n
    vowels = [
        [(730, 120, 1.0), (1090, 140, .6)],    # a
        [(530, 100, 1.0), (1840, 150, .5)],    # e
        [(300, 90, 1.0), (2300, 150, .6)],     # i
        [(570, 100, 1.0), (840, 120, .7)],     # o
        [(300, 90, 1.0), (870, 120, .5)],      # u
    ]
    for v in range(4):
        base = rnd.uniform(105, 250)
        drift = rnd.uniform(0, 6.28)
        # susunan "suku kata": kapan bicara, kapan jeda
        segs = []
        t = rnd.uniform(0, .15)
        while t < dur:
            ln = rnd.uniform(.09, .26)
            segs.append((t, t + ln, rnd.choice(vowels), rnd.choice(vowels),
                         rnd.uniform(.6, 1.0)))
            t += ln + rnd.uniform(.03, .2)

        def seg_at(t, segs=segs):
            for s in segs:
                if s[0] <= t < s[1]:
                    return s
            return None

        def f0_fn(t, base=base, drift=drift):
            return base * (1 + .07 * math.sin(2 * math.pi * 3.1 * t + drift))

        def form(t, seg_at=seg_at, vowels=vowels):
            s = seg_at(t)
            if s is None:
                return vowels[0]
            u = (t - s[0]) / (s[1] - s[0])
            return [(_sfx_lerp(s[2][k][0], s[3][k][0], u),
                     _sfx_lerp(s[2][k][1], s[3][k][1], u),
                     s[2][k][2]) for k in range(2)]

        def amp(t, seg_at=seg_at):
            s = seg_at(t)
            if s is None:
                return 0.0
            u = (t - s[0]) / (s[1] - s[0])
            return s[4] * math.sin(math.pi * u) ** .7

        voice = _sfx_voice(dur, f0_fn, form, amp, lambda t: .25, seed + v)
        for i in range(n):
            mix[i] += voice[i]

    # desis latar belakang (gema ruangan)
    lp = 0.0
    for i in range(n):
        lp += ((rnd.random() * 2 - 1) - lp) * .12
        mix[i] += lp * 0.5 * .35
    # fade in / out
    fi, fo = int(.12 * _SR), int(.4 * _SR)
    for i in range(n):
        g = 1.0
        if i < fi:
            g = i / fi
        elif i > n - fo:
            g = (n - i) / fo
        mix[i] *= g
    return mix


def synth_shot():
    rnd = random.Random(3)
    dur = .32
    n = int(dur * _SR)
    out = [0.0] * n
    lp = 0.0
    for i in range(n):
        t = i / _SR
        noise = rnd.random() * 2 - 1
        k = max(.06, .95 * math.exp(-t * 28))
        lp += (noise - lp) * k
        s = lp * math.exp(-t * 22) * 1.2
        if t < .006:
            s += noise * (1 - t / .006)         # "tak!" awal
        boom = math.sin(2 * math.pi * (55 + 130 * math.exp(-t * 35)) * t)
        s += boom * math.exp(-t * 14) * .9
        out[i] = s
    return out


def synth_zombie():
    """Geraman zombie: 'grooaaarh'."""
    rnd = random.Random(11)
    dur = .85
    jit = [0.0]

    def f0_fn(t):
        jit[0] += (rnd.random() - .5) * .9
        jit[0] *= .97
        return (95 - 38 * (t / dur)) * (1 + .03 * jit[0]) \
            * (1 + .05 * math.sin(2 * math.pi * 7 * t))

    def form(t):
        u = t / dur
        return [(_sfx_lerp(480, 720, u), 120, 1.0),
                (_sfx_lerp(850, 1150, u), 160, .7),
                (1900, 250, .25)]

    def amp(t):
        a = min(1, t / .09)
        if t > .55:
            a *= max(0.0, 1 - (t - .55) / .3)
        rattle = .65 + .35 * math.sin(2 * math.pi * 26 * t)
        return a * rattle

    return _sfx_voice(dur, f0_fn, form, amp, lambda t: .35, 5)


def _sfx_bell_strike(out, start, f, amp, decay=4.0):
    parts = [(1.0, 1.0, 1.0), (2.01, .55, 1.3), (2.76, .45, 1.7),
             (4.07, .25, 2.4), (5.43, .15, 3.2)]
    s0 = int(start * _SR)
    n = len(out)
    for i in range(s0, n):
        t = (i - s0) / _SR
        v = 0.0
        for ratio, a, d in parts:
            v += a * math.exp(-t * decay * d) * math.sin(
                2 * math.pi * f * ratio * t)
        if t < .003:
            v *= t / .003
        out[i] += v * amp


def synth_bell():
    """Lonceng makanan matang: 'ting-ting!'"""
    out = [0.0] * int(1.1 * _SR)
    _sfx_bell_strike(out, 0.0, 1760, 1.0, 3.2)
    _sfx_bell_strike(out, 0.17, 1760, .85, 3.0)
    return out


def synth_money():
    """Lonceng uang (mesin kasir): 'ka-ching' + denting koin."""
    rnd = random.Random(9)
    out = [0.0] * int(.95 * _SR)
    # "ka" : klik mekanis singkat
    prev = 0.0
    for i in range(int(.05 * _SR)):
        t = i / _SR
        x = rnd.random() * 2 - 1
        out[i] += (x - prev) * math.exp(-t * 90) * .8
        prev = x
    _sfx_bell_strike(out, .045, 2637, 1.0, 3.4)         # "ching"
    _sfx_bell_strike(out, .045, 3951, .45, 4.5)
    for k, f in enumerate((3136, 3951, 4699)):           # koin jatuh
        _sfx_bell_strike(out, .30 + k * .075, f, .28, 7.0)
    return out


def _kf(keys, t):
    """Nilai di waktu t dari daftar titik (waktu, nilai), diinterpolasi."""
    if t <= keys[0][0]:
        return keys[0][1]
    for j in range(1, len(keys)):
        if t <= keys[j][0]:
            t0, v0 = keys[j - 1]
            t1, v1 = keys[j]
            return v0 + (v1 - v0) * (t - t0) / max(1e-9, t1 - t0)
    return keys[-1][1]


def synth_doorbell():
    """Lonceng pintu toko: 'ding-dong'."""
    out = [0.0] * int(1.6 * _SR)
    _sfx_bell_strike(out, 0.0, 988, 1.0, 1.7)      # ding (nada tinggi)
    _sfx_bell_strike(out, 0.42, 784, 1.0, 1.5)     # dong (nada lebih rendah)
    n = len(out)
    fo = int(.25 * _SR)
    for i in range(n - fo, n):
        out[i] *= (n - i) / fo
    return out


def synth_thankyou(f0=190, seed=1):
    """Suara 'thank you': th - a - ng - k - y - u (sintesis formant)."""
    dur = 0.8
    AE = [(700, 110, 1.0), (1700, 130, .7), (2500, 160, .3)]
    NG = [(260, 80, 1.0), (1000, 200, .25), (2400, 220, .12)]
    KB = [(1800, 300, .8), (3000, 320, .5), (1200, 300, .5)]
    YI = [(300, 80, 1.0), (2300, 140, .8), (3000, 170, .4)]
    UU = [(320, 90, 1.0), (870, 120, .5), (2250, 150, .15)]
    form_keys = [(0.00, AE), (0.20, AE), (0.25, NG), (0.30, NG),
                 (0.36, KB), (0.40, YI), (0.46, YI), (0.52, UU), (0.80, UU)]
    amp_keys = [(0, 0), (.01, .25), (.07, .3), (.10, 1.0), (.21, 1.0),
                (.25, .55), (.30, .5), (.31, 0), (.35, 0), (.355, .7),
                (.385, .4), (.40, .8), (.46, .8), (.52, 1.0), (.66, .9),
                (.80, 0)]
    noise_keys = [(0, .95), (.07, .9), (.11, .06), (.30, .06), (.34, .9),
                  (.385, .9), (.40, .05), (.80, .05)]
    f0_keys = [(0, 1.0), (.12, 1.1), (.30, .92), (.46, 1.0), (.80, .8)]

    def form(t):
        for j in range(1, len(form_keys)):
            if t <= form_keys[j][0]:
                t0, a = form_keys[j - 1]
                t1, b = form_keys[j]
                u = (t - t0) / max(1e-9, t1 - t0)
                return [(_sfx_lerp(a[k][0], b[k][0], u),
                         _sfx_lerp(a[k][1], b[k][1], u),
                         _sfx_lerp(a[k][2], b[k][2], u)) for k in range(3)]
        return form_keys[-1][1]

    return _sfx_voice(dur,
                      lambda t: f0 * _kf(f0_keys, t),
                      form,
                      lambda t: _kf(amp_keys, t),
                      lambda t: _kf(noise_keys, t), seed)



# ---------------------------------------------------------------------
# MUSIK LATAR (dirender setengah laju sampel supaya cepat dimuat)
# ---------------------------------------------------------------------
def _mus_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _mus_pluck(buf, sr, start, f, amp, tau, dur, harm=0.0):
    """Nada petik/piano listrik: sinus yang meredup (resonator)."""
    s0 = int(start * sr)
    for (ratio, a, tt) in ((1, 1.0, tau), (2, harm, tau * .45)):
        if a <= 0:
            continue
        n = min(int(min(dur, 4.2 * tt) * sr), len(buf) - s0)
        if n <= 0:
            continue
        w = 2 * math.pi * f * ratio / sr
        r = math.exp(-1.0 / (tt * sr))
        a1 = 2 * r * math.cos(w)
        a2 = r * r
        y2 = 0.0
        y1 = a * amp * r * math.sin(w)
        j = s0
        for _ in range(n):
            buf[j] += y1
            y = a1 * y1 - a2 * y2
            y2 = y1
            y1 = y
            j += 1


def _mus_drone(buf, sr, f, amp, loop_s):
    """Sinus terus-menerus; frekuensi dibulatkan agar loop mulus."""
    f = round(f * loop_s) / loop_s
    w = 2 * math.pi * f / sr
    c = 2 * math.cos(w)
    y2 = 0.0
    y1 = amp * math.sin(w)
    for j in range(len(buf)):
        buf[j] += y1
        y = c * y1 - y2
        y2 = y1
        y1 = y


def _mus_noise(buf, sr, start, dur, amp, seed, hp=True):
    rnd = random.Random(seed)
    s0 = int(start * sr)
    n = min(int(dur * sr), len(buf) - s0)
    prev = 0.0
    for i in range(n):
        x = rnd.random() * 2 - 1
        v = (x - prev) if hp else x
        prev = x
        buf[s0 + i] += v * amp * (1 - i / n) ** 2


def _mus_finish(buf, n, echo_s, fb, sr):
    """Lipat ekor nada ke awal (loop mulus), beri gema, ubah ke laju penuh."""
    for i in range(len(buf) - n):
        buf[i] += buf[n + i]
    del buf[n:]
    d = int(echo_s * sr)
    for i in range(n):
        buf[i] += buf[i - d] * fb
    # naikkan ke laju penuh (interpolasi linear)
    out = [0.0] * (n * 2)
    for i in range(n):
        a = buf[i]
        b = buf[i + 1] if i + 1 < n else buf[0]
        out[2 * i] = a
        out[2 * i + 1] = (a + b) * .5
    return out


def synth_music_calm():
    """Lagu santai ala lo-fi, 8 birama, ~70 bpm."""
    sr = _SR // 2
    bpm = 70.0
    beat = 60.0 / bpm
    bars = 8
    loop_s = beat * 4 * bars
    n = int(loop_s * sr)
    buf = [0.0] * (n + int(3.0 * sr))
    # akor (bass, [nada akor]) per birama
    prog = [
        (36, [60, 64, 71]),    # Cmaj7
        (33, [60, 64, 67]),    # Am7
        (38, [62, 65, 72]),    # Dm7
        (31, [59, 62, 65]),    # G7
        (36, [60, 64, 71]),    # Cmaj7
        (40, [59, 62, 67]),    # Em7
        (41, [60, 64, 69]),    # Fmaj7
        (31, [59, 62, 65]),    # G7
    ]
    # melodi pentatonik C yang jarang-jarang: (birama, ketukan, nada, panjang)
    mel = [
        (0, 1.5, 76, 2), (0, 3.0, 72, 1.5),
        (1, 0.5, 69, 1.5), (1, 2.5, 72, 2),
        (2, 1.0, 74, 1.5), (2, 3.0, 69, 1.5),
        (3, 0.5, 67, 2.5),
        (4, 1.5, 79, 2), (4, 3.0, 76, 1.5),
        (5, 0.5, 74, 1.5), (5, 2.5, 71, 2),
        (6, 1.0, 72, 1.5), (6, 3.0, 69, 1.5),
        (7, 1.0, 67, 1.5), (7, 3.0, 71, 1.0),
    ]
    for b, (bass, chord) in enumerate(prog):
        t0 = b * 4 * beat
        for k, m in enumerate(chord):
            # akor dipetik pelan (arpeggio tipis)
            _mus_pluck(buf, sr, t0 + k * .035, _mus_hz(m), .55, .75, 2.6, .3)
        # ulang akor ringan di ketukan 2.5 (syncopation)
        for k, m in enumerate(chord[:2]):
            _mus_pluck(buf, sr, t0 + 2.5 * beat + k * .03, _mus_hz(m), .28,
                       .5, 1.6, .2)
        _mus_pluck(buf, sr, t0, _mus_hz(bass), .9, .9, 2.4, .0)
        _mus_pluck(buf, sr, t0 + 2 * beat, _mus_hz(bass + 7), .55, .6, 1.6, .0)
        # kick halus + hat lembut
        _mus_pluck(buf, sr, t0, 55.0, .9, .09, .35, .0)
        _mus_pluck(buf, sr, t0 + 2 * beat, 55.0, .7, .09, .35, .0)
        for q in range(4):
            _mus_noise(buf, sr, t0 + q * beat + beat * .5, .05, .05, b * 4 + q)
    for (b, bt, m, ln) in mel:
        _mus_pluck(buf, sr, (b * 4 + bt) * beat, _mus_hz(m), .5, .55,
                   ln, .45)
    return _mus_finish(buf, n, beat * .75, .3, sr)


def synth_music_tense():
    """Lagu tegang: bass berdenyut, jantung berdebar, dentuman, tangga naik."""
    sr = _SR // 2
    bpm = 128.0
    beat = 60.0 / bpm
    bars = 8
    loop_s = beat * 4 * bars
    n = int(loop_s * sr)
    buf = [0.0] * (n + int(3.0 * sr))
    _mus_drone(buf, sr, 55.0, .30, loop_s)       # A1
    _mus_drone(buf, sr, 55.7, .22, loop_s)       # sedikit sumbang -> bergetar
    _mus_drone(buf, sr, 466.2, .035, loop_s)     # Bb4 (sumbang)
    _mus_drone(buf, sr, 440.0, .035, loop_s)     # A4
    bass_line = [33, 33, 34, 33, 33, 36, 34, 33]   # A, A, Bb, A ...
    for b in range(bars):
        t0 = b * 4 * beat
        root = bass_line[b]
        for q in range(8):                       # bass 8th berdenyut
            note = root + (12 if q % 4 == 3 else 0)
            _mus_pluck(buf, sr, t0 + q * beat * .5, _mus_hz(note), .75, .16,
                       .5, .6)
        for q in range(4):                       # detak jantung "dug-dug"
            _mus_pluck(buf, sr, t0 + q * beat, 50.0, 1.0, .08, .3, .0)
            _mus_pluck(buf, sr, t0 + q * beat + .17, 50.0, .6, .07, .25, .0)
        for q in range(8):                       # hat yang berdetak cepat
            _mus_noise(buf, sr, t0 + q * beat * .5 + beat * .25, .04, .09,
                       b * 8 + q)
        if b % 2 == 1:                           # sengatan sumbang
            _mus_pluck(buf, sr, t0 + 3 * beat, _mus_hz(81), .35, .9, 2.5, .5)
            _mus_pluck(buf, sr, t0 + 3 * beat, _mus_hz(82), .35, .9, 2.5, .5)
    # motif melodi menegangkan
    motif = [(0, 0, 69, .5), (0, .5, 70, .5), (0, 1, 69, .5), (0, 1.5, 68, 1),
             (2, 0, 69, .5), (2, .5, 70, .5), (2, 1, 73, .5), (2, 1.5, 72, 1),
             (4, 0, 69, .5), (4, .5, 70, .5), (4, 1, 69, .5), (4, 1.5, 68, 1),
             (6, 0, 76, .5), (6, .5, 75, .5), (6, 1, 74, .5), (6, 1.5, 70, 1.5)]
    for (b, bt, m, ln) in motif:
        _mus_pluck(buf, sr, (b * 4 + bt) * beat, _mus_hz(m + 12), .35, .3,
                   ln * beat + .3, .6)
    # tangga naik di 2 birama terakhir
    s0 = int(6 * 4 * beat * sr)
    cnt = n - s0
    ph = 0.0
    for i in range(cnt):
        u = i / cnt
        ph += (220.0 * 4 ** u) / sr
        buf[s0 + i] += math.sin(2 * math.pi * ph) * .12 * u
    return _mus_finish(buf, n, beat * .5, .22, sr)


class Sfx:
    def __init__(self):
        self.ok = False
        self.pending = []
        self.last = {}
        self.hai_free = 0
        self.snd = {}
        self.music_ok = False
        self.music_mode = None
        self.music_ch = None
        try:
            global _SR
            try:
                pygame.mixer.quit()
            except Exception:
                pass
            pygame.mixer.init(22050, -16, 1, 512)
            info = pygame.mixer.get_init()
            if not info:
                return
            _SR = info[0]
            self.channels = info[2]
            pygame.mixer.set_num_channels(16)
            pygame.mixer.set_reserved(1)      # kanal 0 khusus musik latar
            self.music_ch = pygame.mixer.Channel(0)

            # layar "memuat" sebentar karena suara dibuat lewat kode
            screen.fill(BG)
            draw_text("Memuat suara dan musik...", FONT, DARK, W / 2, H / 2)
            pygame.display.flip()

            self.snd["shot"] = self._make(synth_shot(), .75)
            self.snd["shot_soft"] = self._make(synth_shot(), .35)
            self.snd["zombie"] = self._make(synth_zombie(), .9)
            self.snd["bell"] = self._make(synth_bell(), .7)
            self.snd["money"] = self._make(synth_money(), .75)
            self.snd["doorbell"] = self._make(synth_doorbell(), .8)
            self.snd["thanks"] = [
                self._make(synth_thankyou(150, 1), .9),
                self._make(synth_thankyou(190, 2), .9),
                self._make(synth_thankyou(240, 3), .9),
            ]
            self.ok = True
            try:
                self.snd["calm"] = self._make_music(
                    synth_music_calm(), MUSIC_VOL_CALM)
                self.snd["blood"] = self._make_music(
                    synth_music_tense(), MUSIC_VOL_BLOOD)
                self.music_ok = True
            except Exception as e2:      # musik gagal -> efek suara tetap jalan
                print("Musik dimatikan:", e2)
        except Exception as e:           # kalau gagal, game tetap jalan
            print("Suara dimatikan:", e)
            self.ok = False

    def _make(self, samples, volume):
        import array
        peak = max(1e-9, max(abs(s) for s in samples))
        sc = 30000.0 / peak
        arr = array.array("h")
        for s in samples:
            v = int(s * sc)
            for _ in range(self.channels):
                arr.append(v)
        snd = pygame.mixer.Sound(buffer=arr.tobytes())
        snd.set_volume(volume)
        return snd

    def play(self, name, gap=0):
        """gap = jeda minimal (ms) antar suara yang sama."""
        if not self.ok:
            return
        now = pygame.time.get_ticks()
        if now - self.last.get(name, -99999) < gap:
            return
        self.last[name] = now
        try:
            self.snd[name].play()
        except Exception:
            pass

    def _make_music(self, samples, volume):
        """Musik: kekerasan dasar (RMS) sama untuk kedua lagu; beda lewat volume."""
        import array
        rms = math.sqrt(sum(s * s for s in samples) / len(samples))
        sc = MUSIC_RMS / max(1e-9, rms)
        arr = array.array("h")
        for s in samples:
            v = int(s * sc)
            if v > 32000:
                v = 32000
            elif v < -32000:
                v = -32000
            for _ in range(self.channels):
                arr.append(v)
        snd = pygame.mixer.Sound(buffer=arr.tobytes())
        snd.set_volume(volume)
        return snd

    def doorbell(self):
        """Lonceng pintu saat pelanggan masuk; kalau datang bersamaan, bergantian."""
        if not self.ok:
            return
        now = pygame.time.get_ticks()
        t = max(now, self.hai_free)
        if t - now > 1500:
            return
        self.hai_free = t + 700
        snd = self.snd["doorbell"]
        if t <= now:
            snd.play()
        else:
            self.pending.append((t, snd))

    def thanks(self):
        """Pelanggan bilang 'thank you' saat menerima makanan."""
        if not self.ok:
            return
        now = pygame.time.get_ticks()
        if now - self.last.get("thanks", -99999) < 250:
            return
        self.last["thanks"] = now
        try:
            random.choice(self.snd["thanks"]).play()
        except Exception:
            pass

    def music(self, blood):
        """Putar lagu santai (hari normal) atau lagu tegang (bulan merah)."""
        if not (self.ok and self.music_ok):
            return
        mode = "blood" if blood else "calm"
        try:
            if mode == self.music_mode and self.music_ch.get_busy():
                return
            self.music_mode = mode
            self.music_ch.play(self.snd[mode], loops=-1, fade_ms=900)
        except Exception:
            pass

    def music_stop(self):
        if not (self.ok and self.music_ok):
            return
        try:
            self.music_ch.fadeout(1200)
        except Exception:
            pass
        self.music_mode = None

    def update(self):
        if not self.pending:
            return
        now = pygame.time.get_ticks()
        for item in self.pending[:]:
            if item[0] <= now:
                self.pending.remove(item)
                try:
                    item[1].play()
                except Exception:
                    pass


sfx = Sfx()


# =====================================================================
# MULTIPLAYER (jaringan lokal: satu Wi-Fi / hotspot)
#  - BUAT SERVER : nama + sandi -> server aktif, menunggu pemain
#  - JOIN SERVER : nama + sandi -> mencari server dengan nama itu lewat Wi-Fi
# =====================================================================
NET_TCP = 50555
NET_UDP = 50556
NET_MAX = 4          # maksimal pemain (termasuk host)


def _local_ip():
    try:
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sk.connect(("10.255.255.255", 1))
        ip = sk.getsockname()[0]
        sk.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _pw_hash(name, pw):
    raw = "wm|%s|%s" % (name.strip().lower(), pw)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class _Lines:
    """Pembaca pesan JSON per baris dari socket TCP."""
    def __init__(self, sk):
        self.sk = sk
        self.buf = b""

    def read(self):
        # None = belum ada pesan (timeout), {} = pesan rusak, error = koneksi putus
        while b"\n" not in self.buf:
            try:
                d = self.sk.recv(4096)
            except socket.timeout:
                return None
            if not d:
                raise ConnectionError("putus")
            self.buf += d
            if len(self.buf) > 65536:
                raise ConnectionError("terlalu besar")
        line, self.buf = self.buf.split(b"\n", 1)
        try:
            msg = json.loads(line.decode("utf-8"))
            return msg if isinstance(msg, dict) else {}
        except Exception:
            return {}


def _send(sk, obj):
    try:
        sk.sendall((json.dumps(obj) + "\n").encode("utf-8"))
        return True
    except Exception:
        return False


class Net:
    def __init__(self):
        self.lock = threading.Lock()
        self._reset()

    def _reset(self):
        self.role = None          # None | "host" | "client"
        self.name = ""
        self.pwh = ""
        self.status = ""
        self.error = ""
        self.alive = False
        self.connected = False    # client: sudah diterima server
        self.started = False
        self.lost = False
        self.count = 1            # jumlah pemain terhubung
        self.my_id = 0
        self.remote = {}          # id pemain lain -> [x, y]
        self.faces = {}
        self.clients = {}         # host: id -> socket
        self.next_id = 1
        self.tcp = None
        self.udp = None
        self.sock = None
        self.send_t = 0.0

    # ---------------- HOST ----------------
    def start_host(self, name, pw):
        self.close()
        self.role = "host"
        self.name = name
        self.pwh = _pw_hash(name, pw)
        self.alive = True
        try:
            self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp.bind(("", NET_TCP))
            self.tcp.listen(8)
            self.tcp.settimeout(0.5)
            self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.udp.bind(("", NET_UDP))
            self.udp.settimeout(0.5)
        except Exception:
            self.close()
            self.error = "Gagal membuat server (port sedang dipakai / tidak ada jaringan)"
            return False
        self.status = "Server aktif. Menunggu pemain bergabung..."
        threading.Thread(target=self._udp_loop, daemon=True).start()
        threading.Thread(target=self._accept_loop, daemon=True).start()
        return True

    def _udp_loop(self):
        udp = self.udp
        while self.alive and udp is self.udp:
            try:
                data, addr = udp.recvfrom(256)
            except socket.timeout:
                continue
            except Exception:
                break
            try:
                p = data.decode("utf-8", "ignore").split("|")
                if len(p) == 2 and p[0] == "WMQ" and \
                        p[1].strip().lower() == self.name.strip().lower():
                    udp.sendto(("WMR|%s|%d" % (self.name, NET_TCP)).encode("utf-8"), addr)
            except Exception:
                pass

    def _accept_loop(self):
        tcp = self.tcp
        while self.alive and tcp is self.tcp:
            try:
                conn, _addr = tcp.accept()
            except socket.timeout:
                continue
            except Exception:
                break
            threading.Thread(target=self._client_loop, args=(conn,), daemon=True).start()

    def _client_loop(self, conn):
        rd = _Lines(conn)
        cid = None
        try:
            conn.settimeout(5.0)
            try:
                conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass
            msg = rd.read()
            if not msg or msg.get("t") != "join":
                return
            if msg.get("pw") != self.pwh or \
                    str(msg.get("name", "")).strip().lower() != self.name.strip().lower():
                _send(conn, {"t": "no", "why": "Sandi salah"})
                return
            if self.started:
                _send(conn, {"t": "no", "why": "Permainan sudah dimulai"})
                return
            with self.lock:
                if len(self.clients) + 1 >= NET_MAX:
                    full = True
                else:
                    full = False
                    cid = self.next_id
                    self.next_id += 1
                    self.clients[cid] = conn
                    self.count = 1 + len(self.clients)
            if full:
                _send(conn, {"t": "no", "why": "Server penuh"})
                return
            _send(conn, {"t": "ok", "id": cid})
            self._broadcast({"t": "count", "n": self.count})
            conn.settimeout(1.0)
            while self.alive:
                msg = rd.read()
                if msg is None:
                    continue
                if msg.get("t") == "pos":
                    self.remote[cid] = [float(msg.get("x", 0)), float(msg.get("y", 0))]
        except Exception:
            pass
        finally:
            if cid is not None:
                with self.lock:
                    self.clients.pop(cid, None)
                    self.remote.pop(cid, None)
                    self.count = 1 + len(self.clients)
                if self.alive:
                    self._broadcast({"t": "count", "n": self.count})
            try:
                conn.close()
            except Exception:
                pass

    def _broadcast(self, obj):
        for _cid, c in list(self.clients.items()):
            _send(c, obj)

    def start_game(self):
        self.started = True
        self._broadcast({"t": "start"})

    # ---------------- CLIENT ----------------
    def start_join(self, name, pw):
        self.close()
        self.role = "client"
        self.name = name
        self.pwh = _pw_hash(name, pw)
        self.alive = True
        self.status = "Mencari server..."
        threading.Thread(target=self._join_thread, daemon=True).start()

    def _join_thread(self):
        host, port = None, NET_TCP
        try:
            u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            u.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            u.settimeout(0.4)
            ip = _local_ip()
            targets = ["255.255.255.255"]
            if ip.count(".") == 3:
                base = ip.rsplit(".", 1)[0]
                targets += [base + ".255", base + ".1"]
            q = ("WMQ|%s" % self.name).encode("utf-8")
            t_end = time.time() + 4.0
            while self.alive and host is None and time.time() < t_end:
                for t in targets:
                    try:
                        u.sendto(q, (t, NET_UDP))
                    except Exception:
                        pass
                t2 = time.time() + 0.8
                while self.alive and host is None and time.time() < t2:
                    try:
                        data, addr = u.recvfrom(256)
                    except socket.timeout:
                        continue
                    except Exception:
                        break
                    p = data.decode("utf-8", "ignore").split("|")
                    if len(p) == 3 and p[0] == "WMR" and \
                            p[1].strip().lower() == self.name.strip().lower():
                        host, port = addr[0], int(p[2])
            u.close()
        except Exception:
            pass
        if not self.alive:
            return
        if host is None:
            self.error = "Server tidak ditemukan. Cek nama server dan pastikan satu Wi-Fi/hotspot."
            return
        self.status = "Menyambung ke server..."
        sk = None
        try:
            sk = socket.create_connection((host, port), timeout=4.0)
            try:
                sk.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except Exception:
                pass
            sk.settimeout(1.0)
            _send(sk, {"t": "join", "name": self.name, "pw": self.pwh})
            rd = _Lines(sk)
            msg = None
            t_end = time.time() + 5.0
            while msg is None and self.alive and time.time() < t_end:
                msg = rd.read()
            if not msg or msg.get("t") != "ok":
                self.error = str(msg.get("why", "Ditolak server")) if msg else "Server tidak merespons"
                sk.close()
                return
            self.my_id = int(msg.get("id", 1))
            self.sock = sk
            self.connected = True
            self.status = "Terhubung! Menunggu host memulai permainan..."
            while self.alive:
                msg = rd.read()
                if msg is None:
                    continue
                t = msg.get("t")
                if t == "count":
                    self.count = int(msg.get("n", 1))
                elif t == "start":
                    self.started = True
                elif t == "snap":
                    snap = {}
                    for k, v in dict(msg.get("p", {})).items():
                        if int(k) != self.my_id:
                            snap[int(k)] = v
                    self.remote = snap
                elif t == "bye":
                    raise ConnectionError("host keluar")
        except Exception:
            if self.alive:
                if self.connected:
                    self.connected = False
                    self.remote = {}
                    self.lost = True
                    self.error = "Koneksi ke host terputus"
                elif not self.error:
                    self.error = "Gagal tersambung ke server"
        finally:
            if not self.connected and sk is not None and sk is not self.sock:
                try:
                    sk.close()
                except Exception:
                    pass

    # ---------------- UMUM ----------------
    def tick(self, px, py, dt):
        """Kirim posisi pemain ~10x per detik."""
        if not self.role or not self.alive or not self.started:
            return
        self.send_t += dt
        if self.send_t < 0.1:
            return
        self.send_t = 0.0
        if self.role == "host":
            snap = {str(k): v for k, v in list(self.remote.items())}
            snap["0"] = [px, py]
            self._broadcast({"t": "snap", "p": snap})
        elif self.role == "client" and self.connected and self.sock:
            _send(self.sock, {"t": "pos", "x": px, "y": py})

    def close(self):
        was_host = (self.role == "host")
        self.alive = False
        if was_host:
            self._broadcast({"t": "bye"})
        for sk in [self.tcp, self.udp, self.sock] + list(self.clients.values()):
            try:
                if sk:
                    sk.close()
            except Exception:
                pass
        self._reset()


net = Net()


class Game:
    def __init__(self):
        # state: "menu" | "mode" | "multi" | "host_form" | "join_form" | "lobby"
        #        | "playing" | "skin" | "info"
        self.state = "menu"
        self.autosave_t = 0.0        # penghitung auto save berkala
        self.player_name = DEFAULT_PLAYER_NAME
        self.mode = "solo"           # "solo" | "multi" — tiap mode punya file save sendiri
        self.info_sel = None         # topik INFO yang sedang dibuka
        self.form = {"name": "", "pw": "", "focus": 0, "show": False, "err": ""}
        self.load_meta()
        self.reset(from_menu=True)

    def load_meta(self):
        """Muat data menu (tengkorak, skin, rekor) dari save mode yang aktif."""
        global PLAYER_FACE
        self.has_save = os.path.isfile(SAVE_PATH)
        self.skulls = 0
        self.kills_for_skull = 0   # counter menuju 10
        self.player_face = copy_face(PLAYER_FACE_DEFAULT)
        PLAYER_FACE = self.player_face
        self.player_name = DEFAULT_PLAYER_NAME
        self.kills = 0
        self.best_survive = 0.0    # rekor waktu bertahan (detik)
        if self.has_save:
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.skulls = int(data.get("skulls", 0))
                self.kills_for_skull = int(data.get("kills_for_skull", 0))
                self.kills = int(data.get("kills", 0))
                self.best_survive = float(data.get("best_survive", 0))
                nm = str(data.get("player_name", "")).strip()[:NAME_MAX]
                if nm:
                    self.player_name = nm
                face = data.get("player_face")
                if face:
                    self.player_face = copy_face(face)
                    PLAYER_FACE = self.player_face
            except Exception:
                pass

    def set_mode(self, mode):
        """Pindah mode (solo / multi): ganti file save lalu muat data menunya."""
        global SAVE_PATH
        if mode == self.mode:
            return
        self.mode = mode
        SAVE_PATH = SAVE_MULTI if mode == "multi" else SAVE_SOLO
        self.load_meta()
        self.reset(from_menu=True)

    # ---------- MULTIPLAYER: form & lobi ----------
    def open_form(self, which):
        self.form = {"name": "", "pw": "", "focus": 0, "show": False, "err": ""}
        self.state = which

    def open_name_form(self):
        cur = self.player_name if self.player_name != DEFAULT_PLAYER_NAME else ""
        self.form = {"name": cur, "pw": "", "focus": 0, "show": False, "err": ""}
        self.state = "name_form"

    def submit_name(self):
        name = " ".join(self.form["name"].split())[:NAME_MAX]
        if not name:
            self.form["err"] = "Nama belum diisi"
            return
        self.player_name = name
        self.save_skin_only()
        self.say("Nama player disimpan: " + name, GREEN)
        self.state = "skin"

    def type_text(self, txt):
        f = self.form
        key = "name" if f["focus"] == 0 else "pw"
        limit = NAME_MAX if self.state == "name_form" else 20
        for ch in txt:
            if not ch.isprintable() or ch in "\r\n\t":
                continue
            if key == "name" and ch == "|":
                continue
            if len(f[key]) >= limit:
                break
            f[key] += ch
        f["err"] = ""

    def form_backspace(self):
        f = self.form
        key = "name" if f["focus"] == 0 else "pw"
        f[key] = f[key][:-1]
        f["err"] = ""

    def form_enter(self):
        if self.state == "name_form":
            self.submit_name()
            return
        if self.form["focus"] == 0:
            self.form["focus"] = 1
        else:
            self.form_submit()

    def form_submit(self):
        f = self.form
        name = f["name"].strip()
        pw = f["pw"]
        if not name:
            f["err"] = "Nama server belum diisi"
            f["focus"] = 0
            return
        if not pw:
            f["err"] = "Sandi server belum diisi"
            f["focus"] = 1
            return
        f["name"] = name
        if self.state == "host_form":
            if net.start_host(name, pw):
                self.state = "lobby"
            else:
                f["err"] = net.error or "Gagal membuat server"
        else:
            net.start_join(name, pw)
            self.state = "lobby"

    def leave_lobby(self):
        net.close()
        self.state = "multi"

    def reset(self, from_menu=False):
        self.money = START_MONEY
        self.survive = 0.0          # timer bertahan (detik) — naik terus
        self.speed = 0
        self.tables = [
            [{"state": "none", "coin": 0}
             for _ in range(TABLE_COLS)]
            for _ in range(ROWS)
        ]

        self.stations = [
            {"cooks": [], "ready": [], "level": 0}
            for _ in STATIONS
        ]

        self.customers = []
        self.returns = []           # cooldown balik per pelanggan yang pergi
        self.carry = []

        self.player = {
            "x": 0.5,
            "y": 2.0,
            "tx": None,
            "ty": None,
            "action": None
        }

        self.served = 0
        self.message = "Beli meja untuk menerima pelanggan"
        self.msg_color = DARK
        self.spawn_timer = 2.0  # pelanggan pertama datang setelah 2 detik
        self.over = False
        self.over_reason = "TEMBOK HANCUR"
        self.ammo = START_AMMO
        self.wall = WALL_HP
        self.wall_hit = 0
        self.zombies = []
        self.tracers = []
        self.fire_cd = 0
        self.ammo_earned = START_AMMO
        self.flash = 0
        self.kills = 0
        self.z_left = 0
        self.z_sched = []           # jadwal muncul zombie hari ini (detik sejak awal hari)
        self.z_hp = ZOMBIE_HP0
        self.day_n = 0
        self.banner_t = 0
        self.day = 0
        self.blood_moon = False
        self.moon_flash = 0
        self.cust_target = CUSTOMER_BASE   # target jumlah pelanggan aktif
        # ponsel & pekerja
        self.phone_open = False
        self.karyawan = []          # list of worker dicts
        self.tentara = []           # list of soldier dicts
        self.n_karyawan = 0
        self.n_tentara = 0
        self.cleaners = []          # karyawan pembersih (ambil tip di meja)
        self.n_cleaner = 0
        self.koki = []
        self.n_koki = 0
        # tengkorak & skin tetap (tidak di-reset kecuali game baru penuh)
        if not from_menu:
            self.skulls = 0
            self.kills_for_skull = 0
            self.player_name = DEFAULT_PLAYER_NAME
            self.player_face = copy_face(PLAYER_FACE_DEFAULT)
            global PLAYER_FACE
            PLAYER_FACE = self.player_face
        self.start_day(1)

    def say(self, msg, color=GREEN):
        self.message = msg
        self.msg_color = color

    # ---------- SAVE / LOAD ----------
    def update_best_survive(self):
        """Update rekor bertahan jika waktu saat ini lebih lama."""
        if self.survive > self.best_survive:
            self.best_survive = self.survive

    def save(self):
        """Auto-save progress saat kembali ke menu."""
        self.update_best_survive()
        data = {
            "money": self.money,
            "survive": self.survive,
            "speed": self.speed,
            "tables": self.tables,
            "stations": [
                {"cooks": [], "ready": list(s["ready"]), "level": s["level"]}
                for s in self.stations
            ],
            "ammo": self.ammo,
            "ammo_earned": self.ammo_earned,
            "wall": self.wall,
            "kills": self.kills,
            "served": self.served,
            "day": self.day,
            "skulls": self.skulls,
            "kills_for_skull": self.kills_for_skull,
            "player_face": copy_face(self.player_face),
            "player_name": self.player_name,
            "n_karyawan": self.n_karyawan,
            "n_tentara": self.n_tentara,
            "n_cleaner": self.n_cleaner,
            "n_koki": self.n_koki,
            "carry": list(self.carry),
            "best_survive": self.best_survive,
        }
        try:
            _write_json_safe(SAVE_PATH, data)
            self.has_save = True
        except Exception as e:
            print("Gagal simpan:", e)

    def load(self):
        """Muat progress dari file save."""
        if not os.path.isfile(SAVE_PATH):
            return False
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.money = data.get("money", START_MONEY)
            self.survive = float(data.get("survive", 0))
            self.speed = int(data.get("speed", 0))
            self.tables = data.get("tables", self.tables)
            st = data.get("stations")
            if st and len(st) == len(self.stations):
                for i, s in enumerate(st):
                    self.stations[i]["level"] = s.get("level", 0)
                    self.stations[i]["ready"] = list(s.get("ready", []))
                    self.stations[i]["cooks"] = []
            self.ammo = int(data.get("ammo", START_AMMO))
            self.ammo_earned = int(data.get("ammo_earned", self.ammo))
            self.wall = float(data.get("wall", WALL_HP))
            self.kills = int(data.get("kills", 0))
            self.served = int(data.get("served", 0))
            self.day = int(data.get("day", 1))
            self.skulls = int(data.get("skulls", 0))
            self.kills_for_skull = int(data.get("kills_for_skull", 0))
            self.best_survive = float(data.get("best_survive", self.best_survive))
            nm = str(data.get("player_name", "")).strip()[:NAME_MAX]
            if nm:
                self.player_name = nm
            face = data.get("player_face")
            if face:
                self.player_face = copy_face(face)
                global PLAYER_FACE
                PLAYER_FACE = self.player_face
            self.n_karyawan = 0
            self.n_tentara = 0
            self.n_cleaner = 0
            self.n_koki = 0
            self.karyawan = []
            self.tentara = []
            self.cleaners = []
            self.koki = []
            # re-hire workers up to saved counts (cheap recreate)
            for _ in range(int(data.get("n_karyawan", 0))):
                self.n_karyawan += 1
                row = (self.n_karyawan - 1) % ROWS
                self.karyawan.append({
                    "x": 0.4, "y": row + 0.5, "tx": None, "ty": None,
                    "state": "idle", "item": None, "target_cu": None,
                    "station": None, "face": random_face(),
                    "shirt": (70, 170, 100),
                })
            for _ in range(int(data.get("n_tentara", 0))):
                self.n_tentara += 1
                row = (self.n_tentara - 1) % ROWS
                self.tentara.append({
                    "x": 8.3, "y": row + 0.5,
                    "fire_cd": random.uniform(0, TENTARA_FIRE_DELAY),
                    "face": random_face(), "shirt": (90, 90, 110),
                })
            for _ in range(int(data.get("n_cleaner", 0))):
                self.n_cleaner += 1
                row = (self.n_cleaner - 1) % ROWS
                self.cleaners.append({
                    "x": 0.25, "y": row + 0.5, "tx": None, "ty": None,
                    "state": "idle", "tip_table": None,
                    "face": random_face(), "shirt": (70, 190, 190),
                })
            for _ in range(int(data.get("n_koki", 0))):
                self.n_koki += 1
                self.koki.append({
                    "id": self.n_koki, "x": 0.5,
                    "y": (self.n_koki - 1) % ROWS + 0.5,
                    "state": "idle", "item": None, "station": None,
                    "face": random_face(), "shirt": (235, 235, 245),
                })
            self.carry = list(data.get("carry", []))
            self.customers = []
            self.returns = []
            self.zombies = []
            self.tracers = []
            self.z_sched = []
            self.over = False
            self.phone_open = False
            self.player = {
                "x": 0.5, "y": 2.0, "tx": None, "ty": None, "action": None
            }
            # lanjut hari sesuai progress
            d = max(1, self.day)
            self.start_day(d)
            self.has_save = True
            self.say("Progress dimuat! Lanjut bertahan.", GREEN)
            return True
        except Exception as e:
            print("Gagal muat save:", e)
            return False

    def autosave_tick(self, dt):
        """Auto save berkala selama game berjalan (tiap mode punya file save sendiri)."""
        if self.state != "playing" or self.over:
            return
        self.autosave_t += dt
        if self.autosave_t >= AUTOSAVE_EVERY:
            self.autosave_t = 0.0
            self.save()

    def flush_save(self):
        """Simpan sekarang juga (dipanggil saat keluar aplikasi / app ke latar belakang)."""
        if self.state == "playing":
            if self.over:
                self.update_best_survive()
                self.save_skin_only()
            else:
                self.save()

    def go_to_menu(self):
        """Dari permainan kembali ke menu — auto-save dulu."""
        if self.state == "playing":
            self.update_best_survive()
            if not self.over:
                self.save()
                self.say("Game tersimpan otomatis!", GREEN)
            else:
                # game over: simpan rekor saja
                self.save_skin_only()
        self.phone_open = False
        if net.role:
            net.close()      # keluar dari sesi multiplayer
        self.state = "menu"
        sfx.music(False)   # musik latar hari normal di menu

    def start_playing(self, new_game=False):
        """Mulai / lanjut permainan dari menu."""
        if new_game or not self.has_save:
            self.reset(from_menu=True)
            # keep skulls & skin from previous sessions if any
            if self.has_save:
                # load only skulls/skin from save for new game? No — new game keeps current skulls/skin in memory
                pass
        else:
            if not self.load():
                self.reset(from_menu=True)
        self.state = "playing"
        self.autosave_t = 0.0
        sfx.music(self.blood_moon)

    def cycle_skin(self, key):
        """Ganti satu bagian skin, bayar tengkorak."""
        price = SKIN_PRICES.get(key, 1)
        if self.skulls < price:
            self.say("Tengkorak tidak cukup! Butuh %d" % price, RED)
            return
        f = self.player_face
        if key == "skin":
            idx = SKINS.index(tuple(f["skin"])) if tuple(f["skin"]) in SKINS else 0
            f["skin"] = SKINS[(idx + 1) % len(SKINS)]
        elif key == "hair":
            idx = HAIRS.index(tuple(f["hair"])) if tuple(f["hair"]) in HAIRS else 0
            f["hair"] = HAIRS[(idx + 1) % len(HAIRS)]
        elif key == "style":
            idx = SKIN_STYLES.index(f["style"]) if f["style"] in SKIN_STYLES else 0
            f["style"] = SKIN_STYLES[(idx + 1) % len(SKIN_STYLES)]
        elif key == "accent":
            idx = ACCENTS.index(tuple(f["accent"])) if tuple(f["accent"]) in ACCENTS else 0
            f["accent"] = ACCENTS[(idx + 1) % len(ACCENTS)]
        elif key == "eyes":
            f["eyes"] = (f["eyes"] + 1) % 3
        elif key == "mouth":
            f["mouth"] = (f["mouth"] + 1) % 3
        elif key == "glasses":
            f["glasses"] = not f["glasses"]
        elif key == "mustache":
            f["mustache"] = not f["mustache"]
        elif key == "blush":
            f["blush"] = not f["blush"]
        else:
            return
        self.skulls -= price
        global PLAYER_FACE
        PLAYER_FACE = self.player_face
        self.say("Skin diubah! -%d tengkorak" % price, GREEN)
        # auto-save skin progress
        self.save_skin_only()

    def save_skin_only(self):
        """Simpan hanya skulls + face (juga dipanggil dari cycle)."""
        data = {}
        if os.path.isfile(SAVE_PATH):
            try:
                with open(SAVE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data["skulls"] = self.skulls
        data["kills_for_skull"] = self.kills_for_skull
        data["player_face"] = copy_face(self.player_face)
        data["player_name"] = self.player_name
        data["kills"] = self.kills
        data["best_survive"] = self.best_survive
        try:
            _write_json_safe(SAVE_PATH, data)
            self.has_save = True
        except Exception:
            pass

    def reset_skin(self):
        self.player_face = copy_face(PLAYER_FACE_DEFAULT)
        global PLAYER_FACE
        PLAYER_FACE = self.player_face
        self.say("Skin dikembalikan ke default", ORANGE)
        self.save_skin_only()

    def buy_table(self, r, c):
        t = self.tables[r][c]

        if t["state"] != "none":
            return

        if self.money < TABLE_PRICE:
            self.say("Uang tidak cukup!", RED)
            return

        self.money -= TABLE_PRICE
        t["state"] = "free"
        self.say("Meja berhasil dibeli!", GREEN)

    # ---------- PESANAN & STOK (masak hanya yang dipesan) ----------
    def unassigned_demand(self, item):
        """Jumlah pelanggan yang memesan item ini dan belum dijemput karyawan."""
        taken = [k.get("target_cu") for k in self.karyawan
                 if k.get("target_cu") is not None]
        return sum(1 for cu in self.customers
                   if cu["state"] in ("wait", "take")
                   and cu["fav"] == item and cu not in taken)

    def reserved_count(self, item):
        """Makanan di alat yang sudah akan diambil karyawan (jangan dihitung stok bebas)."""
        return sum(1 for k in self.karyawan
                   if k.get("state") == "to_station" and k.get("item") == item)

    def free_supply(self, item):
        """Stok bebas: matang + sedang dimasak + dibawa pemain - yang sudah dipesan karyawan."""
        st = self.stations[ST_OF[item]]
        return (st["ready"].count(item)
                + sum(1 for v in st["cooks"] if v["item"] == item)
                + self.carry.count(item)
                - self.reserved_count(item))

    def need_to_cook(self, item):
        """Berapa lagi item ini perlu dimasak supaya pas dengan pesanan."""
        return self.unassigned_demand(item) - self.free_supply(item)

    def ensure_storage_space(self, st_idx):
        """Cek ruang simpan. Makanan salah TIDAK dibuang otomatis:
        pemain harus mengambilnya lalu membuangnya sendiri ke SAMPAH."""
        s = self.stations[st_idx]
        return len(s["ready"]) < 3 + s["level"]

    def start_cook(self, i):
        k = ST_OF[i]
        s = self.stations[k]
        cook_capacity = 1 + s["level"]

        if len(s["cooks"]) >= cook_capacity:
            self.say("Slot masak alat dapur penuh!", RED)
            return
        salah = self.need_to_cook(i) <= 0   # tidak ada yang memesan
        if not self.ensure_storage_space(k):
            self.say("Penyimpanan penuh! Ambil dan buang makanan yang salah ke SAMPAH.", RED)
            return

        s["cooks"].append({
            "item": i,
            "left": ITEMS[i][3],
            "total": ITEMS[i][3],
            "chef_id": None
        })
        if salah:
            self.say("Salah masak! %s tidak dipesan, nanti buang ke SAMPAH" %
                     ITEMS[i][0], RED)
        else:
            self.say("Memasak " + ITEMS[i][0], ORANGE)

    def max_customers(self):
        """Batas maksimal = meja yang sudah dibeli + slot antre yang kosong."""
        free_tables = sum(
            1 for row in self.tables for t in row if t["state"] == "free"
        )
        # pelanggan yang sedang di meja (wait/eat) sudah mengisi meja
        # antre + enter + take memakai slot antre
        used_queue = sum(
            1 for cu in self.customers
            if cu["state"] in ("enter", "take")
        )
        free_queue = max(0, QUEUE_SLOTS - used_queue)
        # total kapasitas saat ini
        return free_tables + free_queue + sum(
            1 for cu in self.customers
            if cu["state"] in ("wait", "eat", "go")
        )

    def can_spawn(self):
        """Bisa spawn jika masih di bawah target hari DAN ada tempat (meja/antre)."""
        if len(self.customers) >= self.cust_target:
            return False
        # cek slot antre kosong (untuk masuk dulu)
        used = {cu["slot"] for cu in self.customers
                if cu["state"] in ("enter", "take")}
        free_slots = [i for i in range(QUEUE_SLOTS) if i not in used]
        if not free_slots:
            return False
        # cek apakah ada meja free ATAU masih ada yang mau take-away
        free_tables = any(t["state"] == "free" for row in self.tables for t in row)
        # selalu boleh spawn selama ada slot antre (nanti bisa take-away)
        return True

    def spawn(self):
        if not self.can_spawn():
            return False

        used = {cu["slot"] for cu in self.customers
                if cu["state"] in ("enter", "take")}
        free_slots = [i for i in range(QUEUE_SLOTS) if i not in used]
        if not free_slots:
            return False
        slot = random.choice(free_slots)

        fav = random.randrange(len(ITEMS))
        dine = random.random() > .35

        self.customers.append({
            "x": 6.5,
            "y": -0.3,
            "slot": slot,
            "qx": 5 + slot % 3 + .5,
            "qy": slot // 3 + .5,
            "fav": fav,
            "state": "enter",
            "patience": random.uniform(120, 300),
            "maxpat": 300,
            "shirt": random.choice(SHIRTS),
            "face": random_face(),
            "dine": dine,
            "r": 0,
            "c": 0,
            "eat": 0
        })
        sfx.doorbell()                 # lonceng pintu saat pelanggan masuk
        return True

    def customer_left(self):
        """Pelanggan pergi -> mulai cooldown balik miliknya sendiri."""
        self.returns.append(random.uniform(RETURN_CD_MIN, RETURN_CD_MAX))

    def try_spawn_now(self):
        """Coba spawn segera (dipanggil saat pelanggan pergi)."""
        if self.can_spawn():
            self.spawn()

    def go(self, x, y, action=None):
        p = self.player
        p["tx"] = max(.1, min(WALK_MAX, x))
        p["ty"] = max(.1, min(3.9, y))
        p["action"] = action

    def fill_customers_now(self):
        """Datangkan pelanggan secepatnya sampai target hari atau kapasitas antre penuh."""
        while len(self.customers) < self.cust_target and self.spawn():
            pass
        # Kedatangan berikutnya tetap mengikuti jeda normal 10 detik.
        self.spawn_timer = 10.0

    def start_day(self, d):
        self.day = d
        self.z_hp = ZOMBIE_HP0 + (d - 1) * ZOMBIE_HP_STEP
        # Jumlah zombie bertambah bertingkat setiap naik level.
        # Level 1 = 2, level 2 = 4, level 3 = 10, level 4 = 18, dst.
        self.day_n = d * (d + 1) - 2
        event_day = (d % BLOOD_EVERY == 0)
        if event_day:
            self.day_n *= BLOOD_MULT
        self.blood_moon = event_day
        self.moon_flash = BLOOD_FLASH_TIME if event_day else 0
        sfx.music(event_day)           # lagu santai / lagu tegang (bulan merah)
        # sisa zombie hari sebelumnya (jika ada, mis. kecepatan game tinggi) langsung muncul
        for _ in range(len(self.z_sched)):
            self.spawn_zombie()
        # SEMUA zombie hari ini dijadwalkan datang dalam 2 menit (satu hari)
        span = max(1.0, ZOMBIE_WAVE_END - ZOMBIE_WAVE_START)
        n = max(1, self.day_n)
        self.z_sched = [ZOMBIE_WAVE_START + (i + random.random()) * span / n
                        for i in range(self.day_n)]
        self.z_left = len(self.z_sched)
        self.banner_t = 3.5
        self.cust_target = CUSTOMER_BASE + (d - 1) * CUSTOMER_STEP
        # Saat mulai bermain atau naik hari, langsung penuhi target pelanggan.
        self.fill_customers_now()
        if event_day:
            self.say("BULAN MERAH HARI %d! ZOMBIE %d KALI LIPAT: %d zombie!" %
                     (d, BLOOD_MULT, self.day_n), RED)
        elif d > 1:
            self.say("Hari %d: %d zombie (HP %d), target pelanggan %d" %
                     (d, self.day_n, self.z_hp, self.cust_target), ORANGE)
        else:
            self.say("Hari 1: target %d pelanggan. Bertahan selama mungkin!" %
                     self.cust_target, GREEN)

    def spawn_zombie(self):
        self.zombies.append({
            "x": 12.3,
            "y": random.randrange(ROWS) + .5 + random.uniform(-.1, .1),
            "hp": self.z_hp,
            "maxhp": self.z_hp,
            "atk": .5,
            "seed": random.uniform(0, 6.28)
        })

    def buy_ammo(self, pack=10):
        cost = pack * AMMO_PRICE
        if self.money < cost:
            self.say("Uang tidak cukup untuk %d peluru!" % pack, RED)
            return
        self.money -= cost
        self.ammo += pack
        self.ammo_earned += pack
        self.say("Beli %d peluru (-%s)" % (pack, fmt(cost)), ORANGE)

    def bullet_damage(self):
        # Damage mengikuti jumlah peluru yang sedang dimiliki.
        return max(1.0, 1.0 + self.ammo * 0.01)

    def rifle_delay(self):
        # Setiap total 100 peluru yang pernah dimiliki mengurangi jeda 0,05 dtk.
        steps = self.ammo_earned // 100
        return max(AK47_MIN_DELAY, 1.0 - steps * 0.05)

    def hire_chef(self):
        if self.n_koki >= 10:
            self.say("Jumlah koki maksimal 10!", RED)
            return
        if self.money < CHEF_COST:
            self.say("Uang tidak cukup! Butuh %s" % fmt(CHEF_COST), RED)
            return
        self.money -= CHEF_COST
        self.n_koki += 1
        self.koki.append({
            "id": self.n_koki,
            "x": 0.5,
            "y": (self.n_koki - 1) % ROWS + 0.5,
            "state": "idle",
            "item": None,
            "station": None,
            "face": random_face(),
            "shirt": (235, 235, 245)
        })
        self.say("Koki direkrut! Koki akan memasak pesanan pelanggan.", GREEN)

    def upgrade_stations(self):
        if all(s["level"] >= 1 for s in self.stations):
            self.say("Semua alat dapur sudah ditingkatkan!", GRAY)
            return
        if self.money < STATION_UPGRADE_COST:
            self.say("Uang tidak cukup! Butuh %s" % fmt(STATION_UPGRADE_COST), RED)
            return
        self.money -= STATION_UPGRADE_COST
        for s in self.stations:
            s["level"] = 1
        self.say("Semua alat dapur ditingkatkan: kapasitas masak dan simpan +1!", GREEN)

    def update_chefs(self):
        """Koki otomatis memasak jenis dan jumlah makanan sesuai pesanan."""
        for chef in self.koki:
            if chef["state"] == "cooking":
                continue

            # Pilih pesanan yang belum tertutup oleh stok matang / sedang dimasak.
            choices = []
            for item in range(len(ITEMS)):
                need = self.need_to_cook(item)
                if need <= 0:
                    continue
                station = self.stations[ST_OF[item]]
                if len(station["cooks"]) >= 1 + station["level"]:
                    continue
                if not self.ensure_storage_space(ST_OF[item]):
                    continue
                choices.append((need, item))

            if not choices:
                continue
            choices.sort(reverse=True)
            item = choices[0][1]
            st_idx = ST_OF[item]
            station = self.stations[st_idx]
            station["cooks"].append({
                "item": item,
                "left": ITEMS[item][3],
                "total": ITEMS[item][3],
                "chef_id": chef["id"]
            })
            chef["item"] = item
            chef["station"] = st_idx
            chef["state"] = "cooking"
            chef["x"] = 0.5
            chef["y"] = st_idx + 0.5

    def hire_karyawan(self):
        if self.n_karyawan >= MAX_KARYAWAN:
            self.say("Karyawan sudah maksimal (%d)!" % MAX_KARYAWAN, RED)
            return
        if self.money < HIRE_COST:
            self.say("Uang tidak cukup! Butuh %s" % fmt(HIRE_COST), RED)
            return
        self.money -= HIRE_COST
        self.n_karyawan += 1
        row = (self.n_karyawan - 1) % ROWS
        self.karyawan.append({
            "x": 0.4,
            "y": row + 0.5,
            "tx": None,
            "ty": None,
            "state": "idle",      # idle | to_station | to_customer | returning
            "item": None,
            "target_cu": None,
            "station": None,
            "face": random_face(),
            "shirt": (70, 170, 100),
        })
        self.say("Karyawan dipekerjakan! (%d/%d)" % (self.n_karyawan, MAX_KARYAWAN), GREEN)
        self.phone_open = False

    def hire_cleaner(self):
        if self.n_cleaner >= MAX_CLEANER:
            self.say("Pembersih sudah maksimal (%d)!" % MAX_CLEANER, RED)
            return
        if self.money < CLEANER_COST:
            self.say("Uang tidak cukup! Butuh %s" % fmt(CLEANER_COST), RED)
            return
        self.money -= CLEANER_COST
        self.n_cleaner += 1
        row = (self.n_cleaner - 1) % ROWS
        self.cleaners.append({
            "x": 0.25,
            "y": row + 0.5,
            "tx": None,
            "ty": None,
            "state": "idle",      # idle | to_tip
            "tip_table": None,
            "face": random_face(),
            "shirt": (70, 190, 190),
        })
        self.say("Pembersih dipekerjakan! Ia mengambil tip di meja (%d/%d)" %
                 (self.n_cleaner, MAX_CLEANER), GREEN)
        self.phone_open = False

    def update_cleaners(self, dt):
        """Pembersih khusus mengambil tip (koin) di meja, menggantikan karyawan."""
        for cl in self.cleaners:
            if cl["tx"] is not None:
                dx = cl["tx"] - cl["x"]
                dy = cl["ty"] - cl["y"]
                dist = math.hypot(dx, dy)
                step = CLEANER_SPEED * dt
                if dist > step and dist:
                    cl["x"] += dx / dist * step
                    cl["y"] += dy / dist * step
                    continue

                cl["x"], cl["y"] = cl["tx"], cl["ty"]
                cl["tx"] = cl["ty"] = None

                if cl["state"] == "to_tip" and cl["tip_table"]:
                    r, c = cl["tip_table"]
                    table = self.tables[r][c]
                    if table["state"] == "coin":
                        tip = table["coin"]
                        self.money += tip
                        table["coin"] = 0
                        table["state"] = "free"
                        sfx.play("money", 120)     # lonceng uang
                        self.say("Pembersih mengambil tip %s!" % fmt(tip), YELLOW)
                    cl["tip_table"] = None
                    cl["state"] = "idle"
                continue

            if cl["state"] != "idle":
                continue

            # meja bertip yang belum dituju pembersih lain
            taken = [o["tip_table"] for o in self.cleaners
                     if o is not cl and o["tip_table"] is not None]
            best = None
            best_d = None
            for r in range(ROWS):
                for c in range(TABLE_COLS):
                    table = self.tables[r][c]
                    if table["state"] != "coin" or table["coin"] <= 0:
                        continue
                    if (r, c) in taken:
                        continue
                    d = math.hypot(c + 1.5 - cl["x"], r + 0.5 - cl["y"])
                    if best is None or d < best_d:
                        best, best_d = (r, c), d
            if best:
                r, c = best
                cl["tip_table"] = best
                cl["state"] = "to_tip"
                cl["tx"] = c + 1.5
                cl["ty"] = r + 0.5

    def hire_tentara(self):
        if self.n_tentara >= MAX_TENTARA:
            self.say("Tentara sudah maksimal (%d)!" % MAX_TENTARA, RED)
            return
        if self.money < HIRE_COST:
            self.say("Uang tidak cukup! Butuh %s" % fmt(HIRE_COST), RED)
            return
        self.money -= HIRE_COST
        self.n_tentara += 1
        row = (self.n_tentara - 1) % ROWS
        self.tentara.append({
            "x": 8.3,
            "y": row + 0.5,
            "fire_cd": random.uniform(0, TENTARA_FIRE_DELAY),
            "face": random_face(),
            "shirt": (90, 90, 110),
        })
        self.say("Tentara dipekerjakan! (%d/%d)" % (self.n_tentara, MAX_TENTARA), GREEN)
        self.phone_open = False

    def repair_wall(self):
        if self.wall >= WALL_HP:
            self.say("Tembok masih kuat", GRAY)
            return
        if self.money < REPAIR_COST:
            self.say("Uang tidak cukup!", RED)
            return
        self.money -= REPAIR_COST
        self.wall = min(WALL_HP, self.wall + REPAIR_HP)
        self.say("Tembok diperbaiki +%d" % REPAIR_HP, GREEN)

    def zombie_killed(self):
        """Tiap zombie terbunuh: +Rp500, suara zombie, dan tengkorak tiap 10 kill."""
        self.kills += 1
        self.money += ZOMBIE_REWARD
        sfx.play("zombie", 150)
        self.kills_for_skull += 1
        if self.kills_for_skull >= 10:
            self.kills_for_skull = 0
            self.skulls += 1
            self.say("Dapat 1 tengkorak! (total %d)" % self.skulls, YELLOW)

    def fire_piercing(self, sx, sy, tgt, dmg):
        """Peluru tembus. Kena zombie target dulu; kalau damage > health zombie,
        zombie mati dan SISA damage (damage - health) diteruskan ke zombie lain
        di belakangnya (searah tembakan). Berhenti kalau sisa damage tidak
        cukup membunuh (zombie itu hanya terluka). Return jumlah zombie mati."""
        dx, dy = tgt["x"] - sx, tgt["y"] - sy
        ln = math.hypot(dx, dy) or 1.0
        dx, dy = dx / ln, dy / ln
        line = []
        for z in self.zombies:
            vx, vy = z["x"] - sx, z["y"] - sy
            along = vx * dx + vy * dy
            perp = abs(vx * dy - vy * dx)
            if z is tgt:
                line.append((0.0, z))        # target selalu urutan pertama
            elif along > ln - 0.01 and perp <= PIERCE_WIDTH:
                line.append((along, z))
        line.sort(key=lambda a: a[0])
        left = dmg
        killed = 0
        end = tgt
        for _, z in line:
            end = z
            if left >= z["hp"]:
                left -= z["hp"]              # sisa damage = damage - health zombie
                z["hp"] = 0
                self.zombies.remove(z)
                self.zombie_killed()
                killed += 1
                if left <= 0:
                    break
            else:
                z["hp"] -= left              # damage kurang -> tidak tembus lagi
                break
        self.tracers.append([sx, sy, end["x"], end["y"], .08])
        return killed

    def update_zombies(self, dt):
        self.banner_t = max(0, self.banner_t - dt)
        self.wall_hit = max(0, self.wall_hit - dt)
        self.flash = max(0, self.flash - dt)
        self.moon_flash = max(0, self.moon_flash - dt)
        self.fire_cd -= dt

        # hari naik berdasarkan waktu bertahan
        day = int(self.survive // DAY_LEN) + 1
        if day != self.day:
            self.start_day(day)

        # zombie datang dari ujung kanan
        day_t = self.survive - (self.day - 1) * DAY_LEN
        while self.z_sched and self.z_sched[0] <= day_t:
            self.z_sched.pop(0)
            self.spawn_zombie()
        self.z_left = len(self.z_sched)

        # zombie berjalan ke tembok lalu menyerang
        for z in self.zombies:
            if z["x"] > ZOMBIE_STOP_X:
                z["x"] = max(ZOMBIE_STOP_X, z["x"] - ZOMBIE_SPEED * dt)
            else:
                z["atk"] -= dt
                if z["atk"] <= 0:
                    z["atk"] = ZOMBIE_HIT_DELAY
                    self.wall -= ZOMBIE_DMG
                    self.wall_hit = .2
                    self.say("Tembok diserang zombie!", RED)

        if self.wall <= 0:
            self.wall = 0
            self.over = True
            self.over_reason = "TEMBOK HANCUR"
            self.update_best_survive()
            self.save_skin_only()   # simpan rekor & tengkorak
            sfx.music_stop()
            return

        # garis tembakan
        for t in self.tracers[:]:
            t[4] -= dt
            if t[4] <= 0:
                self.tracers.remove(t)

        # pemain berdiri di pos senapan = menembak otomatis
        p = self.player
        manning = p["x"] >= 8.0 and p["tx"] is None
        targets = [z for z in self.zombies if z["x"] < 11.9]
        if manning and targets and self.ammo > 0 and self.fire_cd <= 0:
            tgt = min(targets, key=lambda z: z["x"])
            dmg = self.bullet_damage()
            self.ammo -= 1
            sfx.play("shot", 50)               # suara tembakan
            self.fire_cd = self.rifle_delay()
            self.flash = .12
            row = min(ROWS - 1, int(p["y"]))
            killed = self.fire_piercing(8.68, row + .62, tgt, dmg)
            if killed:
                self.say("%d zombie tumbang! +%s (dmg %.1f)" %
                         (killed, fmt(ZOMBIE_REWARD * killed), dmg), GREEN)

            if self.ammo == 0:
                self.say("Peluru habis! Beli peluru lewat tombol +PELURU", RED)

        # tentara otomatis menembak
        for tnt in self.tentara:
            tnt["fire_cd"] -= dt
            if tnt["fire_cd"] > 0 or self.ammo <= 0:
                continue
            targets = [z for z in self.zombies if z["x"] < 11.9]
            if not targets:
                continue
            # pilih zombie terdekat di baris yang sama dulu, atau terdekat
            same_row = [z for z in targets if abs(z["y"] - tnt["y"]) < 0.7]
            pool = same_row if same_row else targets
            tgt = min(pool, key=lambda z: z["x"])
            dmg = self.bullet_damage()
            self.ammo -= 1
            sfx.play("shot_soft", 50)
            tnt["fire_cd"] = TENTARA_FIRE_DELAY
            killed = self.fire_piercing(8.5, tnt["y"], tgt, dmg)
            if killed:
                self.say("Tentara menumbangkan %d zombie! +%s" %
                         (killed, fmt(ZOMBIE_REWARD * killed)), GREEN)
            if self.ammo == 0:
                self.say("Peluru habis!", RED)

    def update_karyawan(self, dt):
        """Karyawan hanya mengantar makanan sesuai pesanan (tip diambil pembersih)."""
        for k in self.karyawan:
            if k["tx"] is not None:
                dx = k["tx"] - k["x"]
                dy = k["ty"] - k["y"]
                dist = math.hypot(dx, dy)
                step = KARYAWAN_SPEED * dt
                if dist > step and dist:
                    k["x"] += dx / dist * step
                    k["y"] += dy / dist * step
                    continue

                k["x"], k["y"] = k["tx"], k["ty"]
                k["tx"] = k["ty"] = None

                if k["state"] == "to_station":
                    st = self.stations[k["station"]]
                    item = k["item"]
                    if item in st["ready"]:
                        st["ready"].remove(item)
                        cu = k["target_cu"]
                        if cu and cu in self.customers and cu["state"] in ("wait", "take"):
                            k["state"] = "to_customer"
                            if cu["state"] == "wait":
                                k["tx"] = cu["c"] + 1.5
                                k["ty"] = cu["r"] + 0.5
                            else:
                                k["tx"] = cu["x"]
                                k["ty"] = cu["y"]
                        else:
                            k["item"] = None
                            k["target_cu"] = None
                            k["state"] = "idle"
                    else:
                        k["item"] = None
                        k["target_cu"] = None
                        k["state"] = "idle"

                elif k["state"] == "to_customer":
                    cu = k["target_cu"]
                    if cu and cu in self.customers and cu["state"] in ("wait", "take"):
                        if k["item"] == cu["fav"]:
                            self.money += ITEMS[k["item"]][1]
                            sfx.thanks()               # "thank you"
                            if cu["dine"]:
                                cu["state"] = "eat"
                                cu["eat"] = random.uniform(15, 30)
                            else:
                                cu["state"] = "done"
                                cu["eat"] = 3
                            self.say("Karyawan mengantar %s sesuai pesanan!" %
                                     ITEMS[k["item"]][0], GREEN)
                    k["item"] = None
                    k["target_cu"] = None
                    k["state"] = "idle"

                continue

            if k["state"] != "idle":
                continue

            # Cari makanan yang tepat untuk pelanggan yang belum dilayani.
            waiting = [cu for cu in self.customers
                       if cu["state"] in ("wait", "take")]
            assigned = [other.get("target_cu") for other in self.karyawan
                        if other is not k and other.get("target_cu") is not None]
            task = None
            for cu in waiting:
                if cu in assigned:
                    continue
                item = cu["fav"]
                station_idx = ST_OF[item]
                if item in self.stations[station_idx]["ready"]:
                    task = (cu, item, station_idx)
                    break

            if task:
                cu, item, station_idx = task
                k["item"] = item
                k["target_cu"] = cu
                k["station"] = station_idx
                k["state"] = "to_station"
                k["tx"] = 0.5
                k["ty"] = station_idx + 0.5

    def seated(self, r, c):
        for cu in self.customers:
            if cu["state"] in ("wait", "eat"):
                if cu["r"] == r and cu["c"] == c:
                    return cu
        return None

    def serve(self, cu):
        i = cu["fav"]
        if i not in self.carry:
            return False

        self.carry.remove(i)
        self.money += ITEMS[i][1]
        sfx.thanks()                   # pelanggan bilang "thank you"

        if cu["dine"]:
            cu["state"] = "eat"
            cu["eat"] = random.uniform(15, 30)
        else:
            cu["state"] = "done"
            cu["eat"] = 3

        return True

    def take_food(self, k):
        """Sistem BORONG: pemain mengambil semua makanan matang di alat, urut dari
        yang pertama, sampai tangan penuh (MAX_CARRY = 3). Tidak dipilih sesuai
        pesanan, jadi pemain bisa salah ambil dan harus bertanggung jawab
        membuangnya sendiri ke SAMPAH."""
        s = self.stations[k]
        n = 0
        salah = 0

        for item in list(s["ready"]):
            if len(self.carry) >= MAX_CARRY:
                break
            # sisakan yang sudah dipesan karyawan (supaya karyawan tidak kosong)
            if s["ready"].count(item) <= self.reserved_count(item):
                continue
            # hitung makanan yang tidak dipesan siapa pun (salah ambil)
            if self.carry.count(item) >= self.unassigned_demand(item):
                salah += 1
            s["ready"].remove(item)
            self.carry.append(item)
            n += 1

        if n:
            if salah:
                self.say("Memborong %d makanan, %d tidak dipesan! Buang ke SAMPAH" %
                         (n, salah), ORANGE)
            else:
                self.say("Memborong %d makanan" % n, GREEN)
        elif len(self.carry) >= MAX_CARRY:
            self.say("Tangan penuh! Antar atau buang dulu ke SAMPAH", RED)
        else:
            self.say("Belum ada makanan matang", RED)

    def arrive(self):
        p = self.player
        action = p["action"]
        p["tx"] = None
        p["ty"] = None
        p["action"] = None

        if not action:
            return

        if action[0] == "pick":
            self.take_food(action[1])
            return

        if action[0] == "trash":
            n = len(self.carry)
            rugi = sum(ITEMS[v][1] for v in self.carry)
            self.carry.clear()
            if n:
                self.say("Bertanggung jawab! Membuang %d makanan (rugi %s)" %
                         (n, fmt(rugi)), ORANGE)
            else:
                self.say("Tidak ada yang dibuang", GRAY)
            return

        if action[0] == "repair":
            self.repair_wall()
            return

        if action[0] == "gun":
            self.say("Senapan siap! Berdiri di sini untuk menembak", ORANGE)
            return

        if action[0] == "table":
            r, c = action[1], action[2]
            t = self.tables[r][c]

            if t["state"] == "coin":
                self.money += t["coin"]
                t["coin"] = 0
                t["state"] = "free"
                sfx.play("money", 120)         # lonceng uang
                self.say("Mengambil koin!", GREEN)
                return

            cu = self.seated(r, c)
            if cu and cu["state"] == "wait":
                if self.serve(cu):
                    self.say("Makanan berhasil disajikan!", GREEN)
                else:
                    self.say("Makanan tidak cocok!", RED)
            else:
                self.say("Tidak ada pelanggan menunggu", GRAY)

    def update(self, dt):
        if self.over:
            return

        dt *= SPEEDS[self.speed]
        self.survive += dt          # timer bertahan naik terus

        # Memasak: koki dan pemain dapat memakai slot alat dapur yang tersedia.
        for s in self.stations:
            for ck in s["cooks"][:]:
                ck["left"] -= dt
                if ck["left"] <= 0:
                    s["ready"].append(ck["item"])
                    s["cooks"].remove(ck)
                    sfx.play("bell", 150)      # lonceng masakan matang
                    if ck.get("chef_id") is not None:
                        for chef in self.koki:
                            if chef["id"] == ck["chef_id"]:
                                chef["state"] = "idle"
                                chef["item"] = None
                                chef["station"] = None
                                break
                    self.say("Makanan matang: %s!" % ITEMS[ck["item"]][0], GREEN)

        self.update_chefs()

        # Gerakan pemain
        p = self.player
        if p["tx"] is not None:
            dx = p["tx"] - p["x"]
            dy = p["ty"] - p["y"]
            dist = math.hypot(dx, dy)

            move = 2.5 * dt

            if dist <= move:
                p["x"] = p["tx"]
                p["y"] = p["ty"]
                self.arrive()
            elif dist:
                p["x"] += dx / dist * move
                p["y"] += dy / dist * move

        # Zombie, senapan, tembok, tentara
        self.update_zombies(dt)
        if self.over:
            return

        # Karyawan antarkan makanan
        self.update_karyawan(dt)
        # Pembersih ambil tip di meja
        self.update_cleaners(dt)

        # Tiap pelanggan yang pergi punya cooldown sendiri-sendiri,
        # jadi mereka datang lagi bergantian (tidak sekaligus).
        for i in range(len(self.returns) - 1, -1, -1):
            self.returns[i] -= dt
            if self.returns[i] <= 0:
                if self.spawn():
                    del self.returns[i]
                else:
                    self.returns[i] = 1.0  # antrean penuh, coba lagi 1 detik

        # Pengaman: kalau jumlah pelanggan + yang akan balik masih di bawah target
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = 10.0
            if len(self.customers) + len(self.returns) < self.cust_target:
                self.spawn()

        # Antrean pelanggan
        for cu in self.customers[:]:
            if cu["state"] == "enter":
                dx = cu["qx"] - cu["x"]
                dy = cu["qy"] - cu["y"]
                d = math.hypot(dx, dy)
                step = 1.5 * dt

                if d > step:
                    cu["x"] += dx / d * step
                    cu["y"] += dy / d * step
                else:
                    cu["x"], cu["y"] = cu["qx"], cu["qy"]
                    if cu["dine"]:
                        free = [
                            (r, c)
                            for r in range(ROWS)
                            for c in range(TABLE_COLS)
                            if self.tables[r][c]["state"] == "free"
                        ]

                        if free:
                            r, c = random.choice(free)
                            cu["r"], cu["c"] = r, c
                            self.tables[r][c]["state"] = "busy"
                            cu["state"] = "go"
                        else:
                            cu["dine"] = False
                            cu["state"] = "take"
                    else:
                        cu["state"] = "take"

            elif cu["state"] == "go":
                tx = cu["c"] + 1.5
                ty = cu["r"] + .5
                dx, dy = tx-cu["x"], ty-cu["y"]
                d = math.hypot(dx, dy)

                if d < .1:
                    cu["state"] = "wait"
                elif d:
                    cu["x"] += dx/d * 1.5 * dt
                    cu["y"] += dy/d * 1.5 * dt

            elif cu["state"] in ("wait", "take"):
                if cu["fav"] in self.carry:
                    distance = math.hypot(
                        (cu["x"]-p["x"]),
                        (cu["y"]-p["y"])
                    )
                    if distance < .8:
                        self.serve(cu)
                if cu["state"] in ("wait", "take"):
                    cu["patience"] -= dt
                    if cu["patience"] <= 0:
                        if cu["state"] == "wait":
                            self.tables[cu["r"]][cu["c"]]["state"] = "free"
                        self.customers.remove(cu)
                        self.say("Pelanggan kecewa!", RED)
                        self.customer_left()

            elif cu["state"] == "eat":
                cu["eat"] -= dt
                if cu["eat"] <= 0:
                    t = self.tables[cu["r"]][cu["c"]]
                    t["state"] = "coin"
                    t["coin"] = random.randrange(1000, 5001, 500)
                    self.customers.remove(cu)
                    self.served += 1
                    self.say("Pelanggan selesai makan!", GREEN)
                    self.customer_left()

            elif cu["state"] == "done":
                cu["eat"] -= dt
                if cu["eat"] <= 0:
                    self.customers.remove(cu)
                    self.served += 1
                    self.customer_left()

        # Ambil otomatis makanan untuk pelanggan yang cocok
        if self.carry:
            for cu in self.customers[:]:
                if cu["state"] in ("wait", "take"):
                    if cu["fav"] in self.carry:
                        if math.hypot(
                            cu["x"]-p["x"],
                            cu["y"]-p["y"]
                        ) < .8:
                            self.serve(cu)

    def click(self, pos):
        # ---- MENU UTAMA ----
        if self.state == "menu":
            L = main_menu_layout()
            if L["play"].collidepoint(pos):
                # MAIN -> pilih mode (Main Sendiri / Multiplayer)
                self.state = "mode"
                return
            if L["skin"].collidepoint(pos):
                self.state = "skin"
                return
            if L["quit"].collidepoint(pos):
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                return
            if L["info"].collidepoint(pos):
                self.state = "info"
                return
            return

        # ---- INFO SISTEM ----
        if self.state == "info":
            L = info_layout()
            if L["back"].collidepoint(pos):
                self.state = "menu"
                return
            for i, r in enumerate(L["rows"]):
                if r.collidepoint(pos):
                    self.info_sel = i      # tampilkan info spesifik topik ini
                    return
            return

        # ---- PILIH MODE ----
        if self.state == "mode":
            L = mode_layout()
            if L["solo"].collidepoint(pos):
                self.set_mode("solo")
                self.start_playing(new_game=not self.has_save)
                return
            if L["multi"].collidepoint(pos):
                self.set_mode("multi")
                self.state = "multi"
                return
            if L["back"].collidepoint(pos):
                self.state = "menu"
            return

        # ---- MENU MULTIPLAYER ----
        if self.state == "multi":
            L = multi_layout()
            if L["host"].collidepoint(pos):
                self.open_form("host_form")
                return
            if L["join"].collidepoint(pos):
                self.open_form("join_form")
                return
            if L["back"].collidepoint(pos):
                self.state = "mode"
            return

        # ---- FORM NAMA PLAYER ----
        if self.state == "name_form":
            L = form_layout()
            if L["ok"].collidepoint(pos):
                self.submit_name()
                return
            if L["back"].collidepoint(pos):
                self.state = "skin"
                return
            self.form["focus"] = 0
            try:
                pygame.key.start_text_input()   # munculkan keyboard HP
            except Exception:
                pass
            return

        # ---- FORM BUAT SERVER / JOIN SERVER ----
        if self.state in ("host_form", "join_form"):
            L = form_layout()
            f = self.form
            if L["name"].collidepoint(pos):
                f["focus"] = 0
            elif L["pw"].collidepoint(pos):
                f["focus"] = 1
            elif L["show"].collidepoint(pos):
                f["show"] = not f["show"]
            elif L["ok"].collidepoint(pos):
                self.form_submit()
                return
            elif L["back"].collidepoint(pos):
                self.state = "multi"
                return
            try:
                pygame.key.start_text_input()   # munculkan keyboard HP
            except Exception:
                pass
            return

        # ---- LOBI MULTIPLAYER ----
        if self.state == "lobby":
            L = lobby_layout()
            if net.role == "host" and L["start"].collidepoint(pos):
                net.start_game()
                self.start_playing(new_game=not self.has_save)
                return
            if L["back"].collidepoint(pos):
                self.leave_lobby()
            return

        # ---- SKIN SHOP ----
        if self.state == "skin":
            L = skin_layout()
            if L["back"].collidepoint(pos):
                self.state = "menu"
                return
            if L["reset"].collidepoint(pos):
                self.reset_skin()
                return
            if L["name"].collidepoint(pos):
                self.open_name_form()
                return
            opts = L["opts"]
            for key, lab in L["labels"]:
                if opts[key].collidepoint(pos) or opts[key + "_next"].collidepoint(pos):
                    self.cycle_skin(key)
                    return
            return

        # ---- GAME OVER ----
        if self.over:
            if again.collidepoint(pos):
                self.update_best_survive()
                self.reset(from_menu=True)
                self.state = "playing"
                sfx.music(False)
            return

        # tombol SIMPAN di header → simpan progress tanpa keluar dari permainan
        if save_btn_rect.collidepoint(pos):
            self.save()
            self.say("Progress berhasil disimpan! Bisa dilanjutkan nanti.", GREEN)
            return

        # tombol MENU di header → auto-save & kembali
        if menu_btn_rect.collidepoint(pos):
            self.go_to_menu()
            return

        # panel ponsel terbuka
        if self.phone_open:
            # tutup jika klik di luar panel
            L = phone_layout()
            panel = L["panel"]
            if not panel.collidepoint(pos):
                self.phone_open = False
                return
            btn_k, btn_t, btn_cl = L["k"], L["t"], L["cleaner"]
            btn_chef, btn_upgrade, btn_x = L["chef"], L["upgrade"], L["x"]
            if btn_x.collidepoint(pos):
                self.phone_open = False
                return
            if btn_k.collidepoint(pos):
                self.hire_karyawan()
                return
            if btn_t.collidepoint(pos):
                self.hire_tentara()
                return
            if btn_cl.collidepoint(pos):
                self.hire_cleaner()
                return
            if btn_chef.collidepoint(pos):
                self.hire_chef()
                return
            if btn_upgrade.collidepoint(pos):
                self.upgrade_stations()
                return
            return

        if speed_rect.collidepoint(pos):
            self.speed = (self.speed + 1) % 3
            return

        for i, rect in enumerate(menu_rects):
            if rect.collidepoint(pos):
                self.start_cook(i)
                return

        if trash_rect.collidepoint(pos):
            self.go(7.4, 3.5, ("trash",))
            return

        for _k, _r in enumerate(ammo_rects):
            if _r.collidepoint(pos):
                self.buy_ammo(AMMO_PACKS[_k])
                return

        if phone_rect.collidepoint(pos):
            self.phone_open = True
            return

        x, y = pos
        if MAP_Y <= y <= MAP_Y + MAP_H:
            c = int((x-M)/CELL_W)
            r = int((y-MAP_Y)/CELL_H)

            if not (0 <= r < ROWS and 0 <= c < COLS):
                return

            if c == 0:
                self.go(.5, r+.5, ("pick", r))
                # Dapur stasiun dipilih berdasarkan baris
                return

            if 1 <= c <= 4:
                self.buy_table(r, c-1)
                if self.tables[r][c-1]["state"] != "none":
                    self.go(c+.5, r+.5, ("table", r, c-1))
                return

            if c == 8:
                self.go(8.5, r+.5, ("gun",))
                return

            if c == 9:
                self.go(8.5, r+.5, ("repair",))
                return

            if c >= 10:
                return

            self.go(c+.5, r+.5)

game = Game()
sfx.music(False)   # musik hari normal di menu utama

def draw_main_menu():
    """Layar menu utama."""
    screen.fill(BG)
    # dekorasi atas
    pygame.draw.rect(screen, BROWN, (0, 0, W, int(H * .18)))
    draw_text("WARUNG MEJA VS ZOMBIE", BIG, YELLOW, W // 2, int(H * .10))
    draw_text("Bertahan dari zombie sambil melayani pelanggan!",
              SMALL, WHITE, W // 2, int(H * .155))

    # preview pemain di tengah atas area tombol
    draw_person(W // 2, int(H * .28), BLUE, 1.6 * PS, game.player_face, 0, True)

    L = main_menu_layout()
    button(L["play"], GREEN, "MAIN", FONT)
    button(L["skin"], PURPLE, "SKIN", FONT)
    button(L["quit"], RED, "KELUAR", FONT)

    # ---- TOMBOL INFO (kiri) ----
    info_r = L["info"]
    pygame.draw.rect(screen, (55, 120, 180), info_r, border_radius=14)
    pygame.draw.rect(screen, WHITE, info_r, 2, border_radius=14)
    # lingkaran "i"
    icx, icy = info_r.centerx, info_r.centery - int(info_r.h * .12)
    ir = max(10, int(info_r.h * .22))
    pygame.draw.circle(screen, WHITE, (icx, icy), ir)
    draw_text("i", FONT, (55, 120, 180), icx, icy)
    draw_text("INFO", SMALL, WHITE, info_r.centerx, info_r.centery + int(info_r.h * .28))

    # ---- REKOR BERTAHAN (kanan) ----
    rec_r = L["record"]
    pygame.draw.rect(screen, (50, 45, 40), rec_r, border_radius=14)
    pygame.draw.rect(screen, YELLOW, rec_r, 2, border_radius=14)
    draw_text("REKOR", SMALL, YELLOW, rec_r.centerx, rec_r.y + int(rec_r.h * .22))
    bs = int(game.best_survive)
    if bs <= 0:
        draw_text("--:--", FONT, WHITE, rec_r.centerx, rec_r.centery + int(rec_r.h * .08))
        draw_text("Belum ada", SMALL, GRAY, rec_r.centerx, rec_r.y + int(rec_r.h * .78))
    else:
        m, s = bs // 60, bs % 60
        draw_text("%d:%02d" % (m, s), FONT, WHITE, rec_r.centerx, rec_r.centery + int(rec_r.h * .02))
        draw_text("%d mnt %d dtk" % (m, s), SMALL, (220, 210, 180),
                  rec_r.centerx, rec_r.y + int(rec_r.h * .78))

    # info tengkorak & save
    draw_skull(W // 2 - 40, int(H * .78), 18)
    draw_text("x %d" % game.skulls, FONT, SKULL_GOLD, W // 2 + 20, int(H * .78))
    draw_text("Data: " + ("MULTIPLAYER" if game.mode == "multi" else "MAIN SENDIRI") +
              "  |  tekan MAIN untuk memilih mode", SMALL, DARK,
              W // 2, int(H * .86))
    draw_text("1 tengkorak = 10 zombie dibunuh  |  pakai di menu SKIN",
              SMALL, GRAY, W // 2, int(H * .92))


def draw_skin_menu():
    """Layar kustomisasi skin."""
    screen.fill((40, 35, 45))
    L = skin_layout()
    panel = L["panel"]
    pygame.draw.rect(screen, (55, 50, 65), panel, border_radius=18)
    pygame.draw.rect(screen, PURPLE, panel, 3, border_radius=18)

    draw_text("KUSTOMISASI SKIN", FONT, WHITE,
              panel.centerx, panel.y + int(panel.h * .06))
    # tengkorak
    draw_skull(panel.x + int(panel.w * .12), panel.y + int(panel.h * .07), 16)
    draw_text("%d" % game.skulls, FONT, SKULL_GOLD,
              panel.x + int(panel.w * .20), panel.y + int(panel.h * .07))

    # preview besar
    px, py = L["preview_x"], L["preview_y"]
    pygame.draw.circle(screen, (70, 65, 80), (px, py), int(80 * PS))
    draw_person(px, py, BLUE, 2.2 * PS, game.player_face, 0, True)
    draw_text("PREVIEW", SMALL, (200, 200, 210), px, py + int(55 * PS))

    # kolom NAMA di bawah karakter (ketuk untuk mengubah)
    nr = L["name"]
    pygame.draw.rect(screen, (245, 240, 230), nr, border_radius=10)
    pygame.draw.rect(screen, ORANGE, nr, 3, border_radius=10)
    draw_text("NAMA", SMALL, (200, 200, 210), nr.centerx, nr.y - int(SMALL.get_height() * .75))
    draw_text(game.player_name, FONT, DARK, nr.centerx, nr.centery)

    # opsi
    opts = L["opts"]
    for key, lab in L["labels"]:
        price = SKIN_PRICES[key]
        r = opts[key]
        col = (90, 80, 110) if game.skulls >= price else (70, 50, 50)
        button(r, col, "%s  (%d)" % (lab, price), SMALL)
        button(opts[key + "_next"], ORANGE, "GANTI", SMALL)

    button(L["back"], GRAY, "KEMBALI", SMALL)
    button(L["reset"], RED, "RESET", SMALL)
    draw_text("Harga per ganti (tengkorak). Klik GANTI untuk cycle opsi.",
              SMALL, (180, 180, 190), panel.centerx, panel.y + int(panel.h * .84))


def draw_info_menu():
    """Layar informasi: judul di kiri bisa diklik -> penjelasan spesifik di kanan."""
    screen.fill((35, 32, 42))
    L = info_layout()
    panel = L["panel"]
    pygame.draw.rect(screen, (48, 44, 58), panel, border_radius=18)
    pygame.draw.rect(screen, (80, 150, 210), panel, 3, border_radius=18)

    draw_text("INFORMASI SISTEM PERMAINAN", FONT, WHITE,
              panel.centerx, panel.y + int(panel.h * .05))

    sel = game.info_sel
    for i, (title, col, _d) in enumerate(INFO_TOPICS):
        r = L["rows"][i]
        on = (i == sel)
        pygame.draw.rect(screen, col if on else shade(col, .38), r, border_radius=10)
        pygame.draw.rect(screen, col, r, 2, border_radius=10)
        draw_text(title, SMALL, WHITE if on else (230, 225, 215), r.centerx, r.centery)

    d = L["detail"]
    pygame.draw.rect(screen, (38, 35, 48), d, border_radius=12)
    pygame.draw.rect(screen, (90, 85, 105), d, 2, border_radius=12)
    pad = int(d.w * .045)
    screen.set_clip(d.inflate(-4, -4))
    if sel is None:
        draw_text("Klik salah satu judul di kiri", SMALL, (210, 205, 195),
                  d.centerx, d.y + int(d.h * .15))
        draw_text("untuk melihat informasi lebih spesifik.", SMALL, (210, 205, 195),
                  d.centerx, d.y + int(d.h * .15) + SMALL.get_linesize() + 2)
        # mini peta sederhana
        map_x = d.x + int(d.w * .05)
        map_y = d.y + int(d.h * .45)
        map_w = int(d.w * .90)
        map_h = int(d.h * .25)
        pygame.draw.rect(screen, (60, 55, 70), (map_x, map_y, map_w, map_h), border_radius=8)
        zones = [
            (0.00, 0.08, (110, 110, 120)),   # dapur
            (0.08, 0.32, (145, 91, 48)),     # meja
            (0.32, 0.50, (180, 150, 100)),   # antre
            (0.50, 0.58, (120, 100, 70)),    # senapan
            (0.58, 0.68, (150, 140, 130)),   # tembok
            (0.68, 1.00, (126, 172, 104)),   # zombie
        ]
        for za, zb, zc in zones:
            pygame.draw.rect(screen, zc,
                             (map_x + int(map_w * za) + 2, map_y + 4,
                              max(2, int(map_w * (zb - za)) - 2), map_h - 8),
                             border_radius=3)
        draw_text("Peta: Dapur | Meja | Antre | Senapan | Tembok | Zombie",
                  SMALL, (180, 180, 190), map_x + map_w // 2,
                  map_y + map_h + int(d.h * .08))
    else:
        title, col, details = INFO_TOPICS[sel]
        draw_text(title, FONT, col, d.x + pad, d.y + int(pad * .8), center=False)
        y = d.y + int(pad * .8) + FONT.get_linesize() + 6
        lh = SMALL.get_linesize() + 2
        for para in details:
            for j, ln in enumerate(wrap_text(para, SMALL, d.w - 2 * pad - 14)):
                if j == 0:
                    draw_text("-", SMALL, col, d.x + pad, y, center=False)
                draw_text(ln, SMALL, (215, 210, 200), d.x + pad + 14, y, center=False)
                y += lh
            y += 5
    screen.set_clip(None)

    button(L["back"], (80, 150, 210), "KEMBALI", FONT)


def _menu_header(title):
    screen.fill(BG)
    pygame.draw.rect(screen, BROWN, (0, 0, W, int(H * .18)))
    draw_text(title, BIG, YELLOW, W // 2, int(H * .09))


def draw_mode_menu():
    """Pilih mode: MAIN SENDIRI atau MULTIPLAYER (simpanan masing-masing)."""
    _menu_header("PILIH MODE")
    L = mode_layout()
    for key, col, label, path in (("solo", GREEN, "MAIN SENDIRI", SAVE_SOLO),
                                  ("multi", BLUE, "MULTIPLAYER", SAVE_MULTI)):
        r = L[key]
        pygame.draw.rect(screen, col, r, border_radius=14)
        pygame.draw.rect(screen, WHITE, r, 2, border_radius=14)
        draw_text(label, FONT, WHITE, r.centerx, r.y + int(r.h * .36))
        st = "Ada save - bisa lanjut" if os.path.isfile(path) else "Belum ada save"
        draw_text(st + " (simpanan sendiri)", SMALL, WHITE, r.centerx, r.y + int(r.h * .76))
    button(L["back"], GRAY, "KEMBALI", FONT)


def draw_multi_menu():
    """Menu multiplayer: BUAT SERVER | JOIN SERVER."""
    _menu_header("MULTIPLAYER")
    draw_text("Main bareng teman lewat Wi-Fi / hotspot yang sama (maks %d pemain)" % NET_MAX,
              SMALL, DARK, W // 2, int(H * .23))
    L = multi_layout()
    for key, col, label, sub in (
            ("host", ORANGE, "BUAT SERVER", "Tulis nama dan sandi server baru"),
            ("join", BLUE, "JOIN SERVER", "Tulis nama dan sandi server temanmu")):
        r = L[key]
        pygame.draw.rect(screen, col, r, border_radius=14)
        pygame.draw.rect(screen, WHITE, r, 2, border_radius=14)
        draw_text(label, FONT, WHITE, r.centerx, r.y + int(r.h * .38))
        draw_text(sub, SMALL, WHITE, r.centerx, r.y + int(r.h * .74))
    button(L["back"], GRAY, "KEMBALI", FONT)


def draw_form():
    """Form nama server + sandi server (dipakai BUAT SERVER dan JOIN SERVER)."""
    host = (game.state == "host_form")
    _menu_header("BUAT SERVER" if host else "JOIN SERVER")
    L = form_layout()
    f = game.form
    blink = (pygame.time.get_ticks() // 500) % 2 == 0
    for idx, key, label in ((0, "name", "NAMA SERVER"), (1, "pw", "SANDI SERVER")):
        r = L[key]
        draw_text(label, SMALL, DARK, r.x, r.y - int(H * .035), center=False)
        pygame.draw.rect(screen, WHITE, r, border_radius=10)
        pygame.draw.rect(screen, ORANGE if f["focus"] == idx else GRAY, r,
                         3 if f["focus"] == idx else 2, border_radius=10)
        val = f[key]
        if key == "pw" and not f["show"]:
            val = "*" * len(val)
        if f["focus"] == idx and blink:
            val += "|"
        while len(val) > 1 and FONT.size(val)[0] > r.w - 20:
            val = val[1:]            # tampilkan ujung kanan bila kepanjangan
        draw_text(val, FONT, DARK, r.x + 10, r.y + (r.h - FONT.get_height()) // 2,
                  center=False)
    button(L["show"], PURPLE, "TUTUP" if f["show"] else "LIHAT", SMALL)
    button(L["ok"], GREEN, "BUAT" if host else "GABUNG", FONT)
    button(L["back"], GRAY, "KEMBALI", FONT)
    y = int(H * .60)
    if f["err"]:
        for ln in wrap_text(f["err"], SMALL, int(W * .86)):
            draw_text(ln, SMALL, RED, L["name"].x, y, center=False)
            y += SMALL.get_linesize() + 2
    hint = ("Teman bergabung dengan nama & sandi yang sama (satu Wi-Fi / hotspot)."
            if host else
            "Isi nama & sandi server temanmu. Harus satu Wi-Fi / hotspot dengannya.")
    draw_text(hint, SMALL, GRAY, L["name"].x, int(H * .74), center=False)


def draw_name_form():
    """Layar mengetik nama player (dibuka dari kolom NAMA di menu SKIN)."""
    _menu_header("NAMA PLAYER")
    L = form_layout()
    f = game.form
    r = L["name"]
    blink = (pygame.time.get_ticks() // 500) % 2 == 0
    draw_text("NAMA PLAYER", SMALL, DARK, r.x, r.y - int(H * .035), center=False)
    pygame.draw.rect(screen, WHITE, r, border_radius=10)
    pygame.draw.rect(screen, ORANGE, r, 3, border_radius=10)
    val = f["name"] + ("|" if blink else "")
    while len(val) > 1 and FONT.size(val)[0] > r.w - 20:
        val = val[1:]
    draw_text(val, FONT, DARK, r.x + 10, r.y + (r.h - FONT.get_height()) // 2,
              center=False)
    button(L["ok"], GREEN, "SIMPAN", FONT)
    button(L["back"], GRAY, "KEMBALI", FONT)
    if f["err"]:
        draw_text(f["err"], SMALL, RED, r.x, int(H * .60), center=False)
    draw_text("Maksimal %d huruf. Nama tampil di bawah karakter dan di dalam game." % NAME_MAX,
              SMALL, GRAY, r.x, int(H * .74), center=False)


def draw_lobby():
    """Ruang tunggu multiplayer."""
    _menu_header("RUANG TUNGGU")
    L = lobby_layout()
    draw_text("Server: " + net.name, FONT, DARK, W // 2, int(H * .26))
    draw_text("Kamu HOST" if net.role == "host" else "Kamu bergabung sebagai teman",
              SMALL, GRAY, W // 2, int(H * .33))
    draw_text("Pemain terhubung: %d / %d" % (net.count, NET_MAX), FONT, GREEN,
              W // 2, int(H * .43))
    y = int(H * .52)
    for ln in wrap_text(net.status, SMALL, int(W * .8)):
        draw_text(ln, SMALL, DARK, W // 2, y)
        y += SMALL.get_linesize() + 2
    if net.role == "host":
        button(L["start"], GREEN, "MULAI", FONT)
    button(L["back"], RED, "KELUAR", FONT)


def draw():
    if game.state == "menu":
        draw_main_menu()
        return
    if game.state == "skin":
        draw_skin_menu()
        return
    if game.state == "info":
        draw_info_menu()
        return
    if game.state == "mode":
        draw_mode_menu()
        return
    if game.state == "multi":
        draw_multi_menu()
        return
    if game.state in ("host_form", "join_form"):
        draw_form()
        return
    if game.state == "name_form":
        draw_name_form()
        return
    if game.state == "lobby":
        draw_lobby()
        return

    screen.fill(BG)

    # HEADER
    pygame.draw.rect(screen, BROWN, (0, 0, W, BAR_H))
    draw_text(
        "WARUNG MEJA V6",
        FONT, WHITE, M+10, BAR_H//2
    , False)

    # Tombol MENU dan SIMPAN di header
    button(menu_btn_rect, (180, 90, 40), "MENU", SMALL)
    button(save_btn_rect, (45, 145, 75), "SIMPAN", SMALL)

    draw_text(
        fmt(game.money),
        FONT, YELLOW, W*.49, BAR_H//2
    )

    # Timer bertahan (bukan countdown)
    surv = int(game.survive)
    draw_text(
        "Hari %d  |  Bertahan %d:%02d  |  Pelanggan %d/%d" % (
            game.day, surv // 60, surv % 60,
            len(game.customers), game.cust_target),
        SMALL, WHITE, W*.72, BAR_H//2
    )

    button(
        speed_rect, BLUE,
        "x"+str(SPEEDS[game.speed]), SMALL
    )

    # MENU
    for i, rect in enumerate(menu_rects):
        pygame.draw.rect(screen, WHITE, rect, border_radius=10)
        pygame.draw.rect(screen, ITEMS[i][2], rect, 3, border_radius=10)
        draw_food(i, rect.centerx, rect.y + rect.h*.36,
                  max(9, int(rect.h*.19)))
        draw_text(ITEMS[i][0], SMALL, DARK,
                  rect.centerx, rect.y+rect.h*.70)
        draw_text(str(ITEMS[i][3])+"s", SMALL, GRAY,
                  rect.centerx, rect.y+rect.h*.90)

    # MAP
    pygame.draw.rect(
        screen, (220, 185, 135),
        (M, MAP_Y, W-2*M, MAP_H),
        border_radius=10
    )

    for r in range(ROWS):
        for c in range(COLS):
            x = M+c*CELL_W
            y = MAP_Y+r*CELL_H
            rect = pygame.Rect(
                int(x), int(y),
                int(CELL_W), int(CELL_H)
            )

            pygame.draw.rect(screen, LIGHT, rect, 1)

            if c == 0:
                draw_station(r, rect)

            elif 1 <= c <= 4:
                t = game.tables[r][c-1]
                if t["state"] == "none":
                    pygame.draw.rect(
                        screen, (180, 130, 85),
                        rect.inflate(-10, -10),
                        border_radius=8
                    )
                    draw_text(
                        "BELI", SMALL, WHITE,
                        rect.centerx, rect.centery
                    )
                    draw_text(
                        "25rb", SMALL, YELLOW,
                        rect.centerx, rect.centery+15
                    )
                else:
                    color = BROWN if t["state"] == "busy" else GREEN
                    if t["state"] == "coin":
                        color = YELLOW

                    pygame.draw.rect(
                        screen, color,
                        rect.inflate(-12, -12),
                        border_radius=10
                    )

                    if t["state"] == "coin":
                        draw_text(
                            "Rp"+str(t["coin"]),
                            SMALL, DARK,
                            rect.centerx, rect.centery
                        )
                    else:
                        draw_text(
                            "MEJA", SMALL, WHITE,
                            rect.centerx, rect.centery
                        )

            elif c == 8:
                draw_gun_post(r, rect)

            elif c >= 10:
                pygame.draw.rect(
                    screen, (190, 200, 165),
                    rect.inflate(-2, -2)
                )

    # TEMBOK, PELURU & HEALTH
    draw_wall()
    draw_zone_hud()
    draw_text("ZOMBIE", SMALL, (110, 140, 90),
              M + 11 * CELL_W, MAP_Y + MAP_H - int(H * .02))

    # PINTU MASUK (di atas area antre)
    door_w = int(DOOR_W)
    door_h = MAP_Y - DOOR_TOP
    dx0 = int(DOOR_CX - door_w / 2)
    frame = (105, 66, 36)
    inner = (55, 32, 18)
    rad = max(3, int(door_h * .35))
    pygame.draw.rect(screen, frame,
                     (dx0 - 6, DOOR_TOP, door_w + 12, door_h),
                     border_radius=rad)
    pygame.draw.rect(screen, frame,
                     (dx0 - 6, DOOR_TOP + door_h // 2,
                      door_w + 12, door_h - door_h // 2))
    pygame.draw.rect(screen, inner,
                     (dx0, DOOR_TOP + 5, door_w, door_h - 5),
                     border_radius=rad)
    pygame.draw.rect(screen, inner,
                     (dx0, DOOR_TOP + door_h // 2,
                      door_w, door_h - door_h // 2))
    pygame.draw.rect(screen, (170, 60, 50),
                     (dx0 + door_w * .1, MAP_Y + 2,
                      door_w * .8, max(5, int(CELL_H * .09))),
                     border_radius=4)
    sign = SMALL.render("PINTU MASUK >", True, BROWN)
    screen.blit(sign, sign.get_rect(
        midright=(dx0 - 14, DOOR_TOP + door_h // 2)))
    draw_text("ANTRE", SMALL, (190, 145, 95),
              DOOR_CX, MAP_Y + MAP_H - int(H * .02))

    # PELANGGAN
    screen.set_clip(pygame.Rect(0, DOOR_TOP, W, H - DOOR_TOP))
    for cu in sorted(game.customers, key=lambda c: c["y"]):
        x = M + cu["x"]*CELL_W
        y = MAP_Y + cu["y"]*CELL_H

        mood = 0
        if cu["state"] in ("wait", "take"):
            if cu["patience"] < 45:
                mood = 2
            elif cu["patience"] < 90:
                mood = 1

        draw_person(x, y, cu["shirt"], .8*PS, cu["face"], mood)

        if cu["state"] in ("wait", "take"):
            draw_food(cu["fav"], x, y - 44*PS, 13*PS, True)
            frac = max(0, cu["patience"]/cu["maxpat"])
            bw = int(36*PS)
            by = y + 36*PS
            pygame.draw.rect(screen, RED, (x - bw/2, by, bw, 5))
            pygame.draw.rect(screen, GREEN, (x - bw/2, by, bw*frac, 5))
        elif cu["state"] == "eat":
            draw_food(cu["fav"], x + 20*PS, y + 22*PS, 9*PS, True)
    screen.set_clip(None)

    # ZOMBIE (muncul dari ujung kanan)
    screen.set_clip(pygame.Rect(0, MAP_Y, W - M, MAP_H))
    now = pygame.time.get_ticks() / 180.0
    for z in sorted(game.zombies, key=lambda z: z["y"]):
        draw_zombie(
            M + z["x"]*CELL_W, MAP_Y + z["y"]*CELL_H,
            PS, now + z["seed"], z["hp"] / z["maxhp"]
        )
    screen.set_clip(None)

    # PLAYER
    px = M + game.player["x"]*CELL_W
    py = MAP_Y + game.player["y"]*CELL_H
    draw_person(px, py, BLUE, 1.05*PS, PLAYER_FACE, 0, True)
    draw_text(game.player_name, SMALL, WHITE, px, py + 44*PS)

    # pemain lain (multiplayer)
    if game.mode == "multi" and net.role:
        for pid, pos in list(net.remote.items()):
            try:
                qx = M + float(pos[0])*CELL_W
                qy = MAP_Y + float(pos[1])*CELL_H
                if pid not in net.faces:
                    net.faces[pid] = random_face()
                draw_person(qx, qy, ORANGE, 1.05*PS, net.faces[pid], 0, True)
                draw_text("HOST" if pid == 0 else "TEMAN %d" % pid,
                          SMALL, WHITE, qx, qy + 44*PS)
            except Exception:
                pass

    for t in game.tracers:
        a = P(M + t[0]*CELL_W, MAP_Y + t[1]*CELL_H)
        b = P(M + t[2]*CELL_W, MAP_Y + t[3]*CELL_H)
        pygame.draw.line(screen, (255, 230, 120), a, b,
                         max(2, int(2*PS)))
        pygame.draw.circle(screen, (255, 90, 60), b,
                           max(2, int(4*PS)))

    # CAHAYA BULAN MERAH (tiba-tiba menyala saat hari kelipatan 5)
    if game.blood_moon:
        t = pygame.time.get_ticks() / 1000.0
        a = BLOOD_BASE_ALPHA + 20 * math.sin(t * 2.0)
        if game.moon_flash > 0:
            a += 150 * (game.moon_flash / BLOOD_FLASH_TIME)
        RED_LIGHT.set_alpha(int(max(0, min(255, a))))
        screen.blit(RED_LIGHT, (0, 0))
        mr = max(10, int(H * .028))
        mx = int(W * .93)
        my = CARD_Y + CARD_H + int(H * .04)
        pygame.draw.circle(screen, (140, 20, 20), (mx, my), int(mr * 1.6))
        pygame.draw.circle(screen, (225, 45, 45), (mx, my), mr)
        pygame.draw.circle(screen, (170, 25, 25),
                           (mx - int(mr*.3), my - int(mr*.2)), max(2, int(mr*.25)))

    if game.banner_t > 0 and not game.over:
        brect = pygame.Rect(0, 0, int(W*.46), int(MAP_H*.38))
        brect.center = (W//2, MAP_Y + MAP_H//2)
        pygame.draw.rect(screen, (45, 25, 20), brect,
                         border_radius=16)
        pygame.draw.rect(screen, ORANGE, brect, 3,
                         border_radius=16)
        draw_text("HARI "+str(game.day), BIG, YELLOW,
                  brect.centerx, brect.y + brect.h*.32)
        if game.blood_moon:
            draw_text("BULAN MERAH! Zombie %dx lipat" % BLOOD_MULT, SMALL,
                      (255, 120, 120), brect.centerx, brect.y + brect.h*.52)
        draw_text("Zombie: %d   HP zombie: %d" %
                  (game.day_n, game.z_hp), FONT, WHITE,
                  brect.centerx, brect.y + brect.h*.72)

    # BOTTOM
    draw_text(
        game.message, SMALL,
        game.msg_color, W*.42, BOTTOM_Y+10
    )

    bs = max(10, int(H * .024))
    by = BOTTOM_Y + int(H * .052)
    draw_text(
        "BAWAAN:",
        SMALL, DARK, M+10, by - SMALL.get_height()//2, False
    )

    bx = M + 10 + SMALL.size("BAWAAN:")[0] + int(bs * 1.6)
    for i, item in enumerate(game.carry):
        draw_food(item, bx + i*int(bs * 2.8), by, bs, True)

    button(trash_rect, RED, "SAMPAH", SMALL)
    for _k, _r in enumerate(ammo_rects):
        _n = AMMO_PACKS[_k]
        button(_r, (90, 90, 105),
               "+{:,} {}".format(_n, fmt_short(_n * AMMO_PRICE)).replace(",", "."),
               SMALL)
    button(phone_rect, (50, 140, 200), "PONSEL", SMALL)

    # Info pekerja dihapus dari header agar tidak menimpa tulisan rekening pemain.
    # Jumlah pekerja tetap bisa dilihat melalui menu PONSEL.
    # ikon tengkorak + jumlah
    skx = int(W * .58)
    draw_skull(skx, BAR_H // 2, max(8, int(BAR_H * .28)))
    draw_text("x%d" % game.skulls, SMALL, SKULL_GOLD, skx + int(W * .03), BAR_H // 2)

    # gambar karyawan
    for k in game.karyawan:
        kx = M + k["x"] * CELL_W
        ky = MAP_Y + k["y"] * CELL_H
        draw_person(kx, ky, k["shirt"], 0.85 * PS, k["face"], 0, True)
        draw_text("KARYAWAN", SMALL, GREEN, kx, ky + 40 * PS)
        if k["item"] is not None:
            draw_food(k["item"], kx + 18 * PS, ky - 10 * PS, 10 * PS, True)

    # gambar pembersih (bawa sapu kecil)
    for cl in game.cleaners:
        cx = M + cl["x"] * CELL_W
        cy = MAP_Y + cl["y"] * CELL_H
        draw_person(cx, cy, cl["shirt"], 0.85 * PS, cl["face"], 0, False)
        draw_text("PEMBERSIH", SMALL, (30, 130, 130), cx, cy + 40 * PS)
        # sapu
        pygame.draw.line(screen, DARK, (int(cx + 16 * PS), int(cy - 14 * PS)),
                         (int(cx + 16 * PS), int(cy + 26 * PS)), max(2, int(2 * PS)))
        pygame.draw.polygon(screen, YELLOW, [
            (int(cx + 10 * PS), int(cy + 34 * PS)),
            (int(cx + 22 * PS), int(cy + 34 * PS)),
            (int(cx + 19 * PS), int(cy + 24 * PS)),
            (int(cx + 13 * PS), int(cy + 24 * PS))])

    # gambar koki
    for chef in game.koki:
        chx = M + chef["x"] * CELL_W
        chy = MAP_Y + chef["y"] * CELL_H
        draw_person(chx, chy, chef["shirt"], 0.88 * PS, chef["face"], 0, True)
        draw_text("KOKI", SMALL, (150, 90, 35), chx, chy + 40 * PS)
        if chef["item"] is not None:
            draw_food(chef["item"], chx + 18 * PS, chy - 10 * PS, 10 * PS, True)

    # gambar tentara
    for tnt in game.tentara:
        tx = M + tnt["x"] * CELL_W
        ty = MAP_Y + tnt["y"] * CELL_H
        draw_person(tx, ty, tnt["shirt"], 0.9 * PS, tnt["face"], 0, False)
        draw_text("TENTARA", SMALL, (70, 70, 100), tx, ty + 40 * PS)

    # PANEL PONSEL
    if game.phone_open and not game.over:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        L = phone_layout()
        panel = L["panel"]
        px, py, pw, ph = panel.x, panel.y, panel.w, panel.h
        pygame.draw.rect(screen, (40, 45, 55), panel, border_radius=18)
        pygame.draw.rect(screen, (80, 160, 220), panel, 3, border_radius=18)

        draw_text("PONSEL WARUNG", FONT, WHITE, panel.centerx, py + int(ph * .10))
        draw_text("Karyawan/tentara: %s | Pembersih: %s | Koki: %s" %
                  (fmt(HIRE_COST), fmt(CLEANER_COST), fmt(CHEF_COST)),
                  SMALL, (200, 200, 210), panel.centerx, py + int(ph * .22))

        btn_k, btn_t, btn_cl = L["k"], L["t"], L["cleaner"]
        btn_chef, btn_upgrade, btn_x = L["chef"], L["upgrade"], L["x"]

        button(btn_k, GREEN,
               "KARYAWAN %d/%d" % (game.n_karyawan, MAX_KARYAWAN), SMALL)
        button(btn_t, (90, 90, 120),
               "TENTARA %d/%d" % (game.n_tentara, MAX_TENTARA), SMALL)
        button(btn_cl, (40, 150, 150),
               "PEMBERSIH %d/%d" % (game.n_cleaner, MAX_CLEANER), SMALL)
        button(btn_chef, (190, 125, 45),
               "REKRUT KOKI %d/10" % game.n_koki, SMALL)
        button(btn_upgrade, BLUE, "UPGRADE DAPUR", SMALL)
        button(btn_x, RED, "X", SMALL)

        levels = sum(1 for st in game.stations if st["level"] >= 1)
        draw_text("Karyawan hanya antar makanan | Pembersih ambil tip di meja",
                  SMALL, (220, 220, 200), panel.centerx, py + int(ph * .79))
        draw_text("Upgrade %s: semua alat +1 slot masak dan +1 simpan" %
                  fmt(STATION_UPGRADE_COST),
                  SMALL, YELLOW, panel.centerx, py + int(ph * .88))
        draw_text("Dapur ditingkatkan: %d/%d | Jeda senapan: %.2fs | Peluru terkumpul: %d" %
                  (levels, len(game.stations), game.rifle_delay(), game.ammo_earned),
                  SMALL, (220, 220, 220), panel.centerx, py + int(ph * .96))

    if game.over:
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen, WHITE, box,
            border_radius=20
        )

        draw_text(
            game.over_reason,
            BIG, RED,
            box.centerx, box.y+box.h*.18
        )

        surv = int(game.survive)
        draw_text(
            "Bertahan: %d menit %d detik" % (surv // 60, surv % 60),
            FONT, ORANGE,
            box.centerx, box.y+box.h*.32
        )

        draw_text(
            "Hari tercapai: "+str(game.day),
            FONT, DARK,
            box.centerx, box.y+box.h*.42
        )

        draw_text(
            "Uang: "+fmt(game.money),
            FONT, DARK,
            box.centerx, box.y+box.h*.52
        )

        draw_text(
            "Pelanggan dilayani: "+str(game.served)+"   Zombie: "+str(game.kills),
            FONT, DARK,
            box.centerx, box.y+box.h*.58
        )

        bs = int(game.best_survive)
        bm, bsec = bs // 60, bs % 60
        is_new = int(game.survive) >= bs and bs > 0
        rec_col = GREEN if is_new else DARK
        draw_text(
            ("REKOR BARU! " if is_new else "Rekor: ") + "%d mnt %d dtk" % (bm, bsec),
            FONT, rec_col,
            box.centerx, box.y+box.h*.68
        )

        button(again, GREEN, "MAIN LAGI")

# GAME OVER BOX
box = pygame.Rect(
    W*.2, H*.2, W*.6, H*.6
)
again = pygame.Rect(
    W*.35, H*.65, W*.3, H*.12
)

running = True
last_tap = -1000
kb_on = False            # keyboard layar sedang aktif (form multiplayer)
got_textinput = False    # perangkat mengirim event TEXTINPUT
pending_kd = []          # huruf dari KEYDOWN yang menunggu pasangan TEXTINPUT
FORM_STATES = ("host_form", "join_form", "name_form")
_EV_BG = getattr(pygame, "APP_WILLENTERBACKGROUND", -1)    # Android: app ke latar belakang
_EV_FG = getattr(pygame, "APP_DIDENTERFOREGROUND", -1)
app_bg = False           # app sedang di latar belakang -> game berhenti

while running:
    dt = min(clock.tick(60)/1000, .1)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game.flush_save()         # keluar dari app: simpan dulu
            running = False

        elif event.type == _EV_BG:
            game.flush_save()         # app ditinggal: simpan, game berhenti
            app_bg = True

        elif event.type == _EV_FG:
            app_bg = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game.state == "playing":
                    game.go_to_menu()
                elif game.state in ("skin", "info", "mode"):
                    game.state = "menu"
                elif game.state == "name_form":
                    game.state = "skin"
                elif game.state == "multi":
                    game.state = "mode"
                elif game.state in FORM_STATES:
                    game.state = "multi"
                elif game.state == "lobby":
                    game.leave_lobby()
                else:
                    running = False
            elif game.state in FORM_STATES:
                if event.key == pygame.K_BACKSPACE:
                    game.form_backspace()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    game.form_enter()
                elif event.key == pygame.K_TAB and game.state != "name_form":
                    game.form["focus"] = 1 - game.form["focus"]
                elif event.unicode and not got_textinput:
                    # cadangan bila perangkat tidak mengirim TEXTINPUT
                    game.type_text(event.unicode)
                    pending_kd.append((event.unicode, pygame.time.get_ticks()))

        elif event.type == getattr(pygame, "TEXTINPUT", -1):
            if game.state in FORM_STATES:
                got_textinput = True
                now_t = pygame.time.get_ticks()
                pending_kd[:] = [p for p in pending_kd if now_t - p[1] < 500]
                dup = [p for p in pending_kd if p[0] == event.text]
                if dup:
                    pending_kd.remove(dup[0])     # sudah diketik lewat KEYDOWN
                else:
                    game.type_text(event.text)

        elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
            # Di Android satu ketukan dikirim 2x (mouse + jari).
            # Abaikan ketukan kedua supaya masak tidak otomatis penuh.
            now = pygame.time.get_ticks()
            if now - last_tap < 300:
                continue
            last_tap = now
            if event.type == pygame.MOUSEBUTTONDOWN:
                game.click(event.pos)
            else:
                game.click((
                    int(event.x*W),
                    int(event.y*H)
                ))

    # ---- keyboard layar & multiplayer ----
    want_kb = game.state in FORM_STATES
    if want_kb != kb_on:
        kb_on = want_kb
        try:
            if want_kb:
                pygame.key.start_text_input()
            else:
                pygame.key.stop_text_input()
        except Exception:
            pass
    if game.state == "lobby" and net.role == "client":
        if net.connected and net.started:
            game.start_playing(new_game=not game.has_save)
        elif net.error and not net.connected:
            err = net.error
            net.close()
            game.state = "join_form"
            game.form["err"] = err
    if game.state == "playing" and game.mode == "multi" and net.role:
        net.tick(game.player["x"], game.player["y"], dt)
        if net.lost:
            net.lost = False
            game.say("Koneksi ke host terputus. Kamu lanjut main sendiri.", RED)

    sfx.update()
    if game.state == "playing" and not app_bg:
        game.update(dt)
        game.autosave_tick(dt)     # auto save berkala walau game sedang berjalan
    draw()
    pygame.display.flip()

game.flush_save()      # jaga-jaga: simpan terakhir sebelum program berhenti
pygame.quit()
sys.exit()
