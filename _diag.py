from PIL import Image, ImageChops

pairs = [
    ("submission/works/01_春晓.jpg", "review/refined_01_春晓.jpg"),
    ("submission/works/05_夜雨寄北.jpg", "review/refined_05_夜雨寄北.jpg"),
    ("submission/works/02_枫桥夜泊.jpg", "review/refined_02_枫桥夜泊.jpg"),
]
for ap, bp in pairs:
    a = Image.open(ap).convert("RGB")
    b = Image.open(bp).convert("RGB")
    d = ImageChops.difference(a, b)
    print(ap.split("/")[-1], "extrema:", d.getextrema())
    pxa = list(a.getdata())
    pxb = list(b.getdata())
    s = 0
    c = 0
    for pa, pb in zip(pxa[::200], pxb[::200]):
        for x, y in zip(pa, pb):
            s += abs(x - y)
            c += 1
    print("   mean abs diff (sampled):", round(s / c, 2), "/255  (~", round(s / c / 255 * 100, 1), "%)")

