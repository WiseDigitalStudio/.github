"""Generates profile/banner.svg: the night-flight globe from the website (real land dots, amber routes) + the wordmark.
Static SVG with SMIL animation only (GitHub serves README images as <img>: no JS, no external fonts).
usage: python3 tools/make-banner.py <path to wise-website>"""
import json, math, re, sys
site = sys.argv[1]
land = json.load(open(f"{site}/static/data/land-dots.json"))
logo = open(f"{site}/static/images/brand/wise-logo.svg").read()

W, H = 1280, 360
CX, CY, R = 1010, 330, 300          # globe centre near the bottom edge, Europe in frame
LON0, LAT0 = 18, 28                 # camera over Europe / Mediterranean

def proj(lat, lon):
    la, lo = math.radians(lat), math.radians(lon - LON0)
    c0, s0 = math.cos(math.radians(LAT0)), math.sin(math.radians(LAT0))
    x = math.cos(la) * math.sin(lo)
    y = c0 * math.sin(la) - s0 * math.cos(la) * math.cos(lo)
    z = s0 * math.sin(la) + c0 * math.cos(la) * math.cos(lo)
    return CX + x * R, CY - y * R, z

dots = []
for lat, lon in zip(land["lat"], land["lon"]):
    x, y, z = proj(lat, lon)
    if z > 0.02 and -4 < x < W + 4 and -4 < y < H + 4:
        dots.append((round(x, 1), round(y, 1), z))
# bucket by depth so each group shares one fill-opacity
groups = {}
for x, y, z in dots:
    b = min(5, int(z * 6)); groups.setdefault(b, []).append((x, y))

CITIES = {"MXP": (45.63, 8.72), "JFK": (40.64, -73.78), "DXB": (25.25, 55.36), "LIS": (38.77, -9.13),
          "FRA": (50.03, 8.56), "LHR": (51.47, -0.45), "ATH": (37.94, 23.94), "CAI": (30.12, 31.41),
          "MAD": (40.47, -3.56), "FCO": (41.8, 12.25), "IST": (41.26, 28.74), "TLV": (32.01, 34.89)}
ROUTES = [("MXP", "JFK", 0.4), ("FCO", "DXB", 2.0), ("LHR", "ATH", 3.6), ("MAD", "IST", 5.2), ("FRA", "LIS", 6.0), ("MXP", "CAI", 6.4)]

def vec(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return [math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)]
def arc(a, b, n=40):
    va, vb = vec(*CITIES[a]), vec(*CITIES[b])
    om = math.acos(max(-1, min(1, sum(p * q for p, q in zip(va, vb)))))
    pts = []
    for i in range(n + 1):
        t = i / n
        k1, k2 = math.sin((1 - t) * om) / math.sin(om), math.sin(t * om) / math.sin(om)
        v = [k1 * p + k2 * q for p, q in zip(va, vb)]
        h = 1 + math.sin(math.pi * t) * (0.06 + om * 0.1)
        lat = math.degrees(math.asin(v[2] / math.sqrt(sum(c * c for c in v))))
        lon = math.degrees(math.atan2(v[1], v[0]))
        x, y, z = proj(lat, lon)
        # lift: push away from the globe centre
        x, y = CX + (x - CX) * h, CY + (y - CY) * h
        pts.append((x, y, z))
    return pts

out = []
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Wise Digital Studio: travel technology">')
out.append('''<defs>
<radialGradient id="glow" cx="78%" cy="115%" r="70%"><stop offset="0" stop-color="#4a5be6" stop-opacity=".45"/><stop offset="1" stop-color="#4a5be6" stop-opacity="0"/></radialGradient>
<radialGradient id="body" cx="40%" cy="20%" r="80%"><stop offset="0" stop-color="#1c2470"/><stop offset="1" stop-color="#060928"/></radialGradient>
<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="#050824"/><stop offset=".42" stop-color="#050824" stop-opacity=".9"/><stop offset=".62" stop-color="#050824" stop-opacity="0"/></linearGradient>
<clipPath id="routes"><rect x="480" y="0" width="800" height="360"/></clipPath>
<radialGradient id="head"><stop offset="0" stop-color="#ffe6be"/><stop offset="1" stop-color="#ffb547" stop-opacity="0"/></radialGradient>
</defs>''')
out.append(f'<rect width="{W}" height="{H}" rx="16" fill="#050824"/>')
out.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#glow)"/>')
out.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#body)" stroke="#9aa5ff" stroke-opacity=".35"/>')
for b in sorted(groups):
    op = 0.18 + b * 0.13
    d = "".join(f"M{x} {y}h1.6" for x, y in groups[b])
    out.append(f'<path d="{d}" stroke="#aab4ff" stroke-opacity="{op:.2f}" stroke-width="1.6" stroke-linecap="round"/>')
# city lights
for k, (lat, lon) in CITIES.items():
    x, y, z = proj(lat, lon)
    if z > 0.05:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#ffb547"><animate attributeName="opacity" values="1;.45;1" dur="{3 + (len(k) + ord(k[0])) % 3}s" repeatCount="indefinite"/></circle>')
# routes: each draws in, holds, fades; a light travels along it
CYCLE = 9.6
out.append('<g clip-path="url(#routes)">')   # lights travel only over the globe; clips any pre-animation speck at (0,0)
for a, b, delay in ROUTES:
    pts = arc(a, b)
    vis = [(x, y) for x, y, z in pts if z > -0.1]
    if len(vis) < 3: continue
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in vis)
    L = sum(math.dist(vis[i], vis[i + 1]) for i in range(len(vis) - 1))
    t0 = delay / CYCLE; t1 = (delay + 2.2) / CYCLE; t2 = (delay + 3.4) / CYCLE
    kt = f"0;{t0:.3f};{t1:.3f};{t2:.3f};1"
    out.append(f'<path d="{d}" fill="none" stroke="#ffb547" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="{L:.0f}" stroke-dashoffset="{L:.0f}" opacity="0">'
               f'<animate attributeName="stroke-dashoffset" values="{L:.0f};{L:.0f};0;0;0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="0;.9;.9;0;0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/></path>')
    out.append(f'<circle r="0" fill="url(#head)" opacity="0"><animateMotion path="{d}" keyPoints="0;0;1;1;1" keyTimes="{kt}" calcMode="linear" dur="{CYCLE}s" repeatCount="indefinite"/>'
               f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;{t0:.3f};{(t1 - 0.005):.3f};{t1:.3f};1" dur="{CYCLE}s" repeatCount="indefinite"/>'
               f'<animate attributeName="r" values="0;7;7;0;0" keyTimes="0;{t0:.3f};{(t1 - 0.005):.3f};{t1:.3f};1" dur="{CYCLE}s" repeatCount="indefinite"/></circle>')
    # r starts at 0: before SMIL positions the light it sits at (0,0), where an <img> render could show a speck
out.append('</g>')
out.append(f'<rect width="{W}" height="{H}" rx="16" fill="url(#fade)"/>')
# letterbox hairlines
out.append(f'<rect width="{W}" height="{H}" rx="16" fill="none" stroke="#9aa5ff" stroke-opacity=".18"/>')
# wordmark (the site logo, inlined)
inner = re.search(r"<svg[^>]*>(.*)</svg>", logo, re.S).group(1)
vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', logo).group(1).split()]
lw = 430; sc = lw / vb[2]
out.append(f'<g transform="translate(72 {H/2 - vb[3]*sc/2:.1f}) scale({sc:.4f}) translate({-vb[0]} {-vb[1]})" fill="#eef0ff" stroke="#eef0ff">{inner}</g>')
out.append('</svg>')
svg = "\n".join(out).replace('class="wm-thin" fill="none" stroke-width="14"', 'class="wm-thin" fill="none" stroke-width="13"')
open("profile/banner.svg", "w").write(svg)
print(len(dots), "dots,", round(len(svg) / 1024), "KB")
