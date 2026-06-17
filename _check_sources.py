import os, sys
from PIL import Image, ExifTags

d = "assets/series_sources"
for f in sorted(os.listdir(d)):
    p = os.path.join(d, f)
    img = Image.open(p)
    size_kb = os.path.getsize(p) // 1024
    print(f)
    print("  size:", img.size, "mode:", img.mode, "bytes:", size_kb, "KB")
    try:
        exif = img._getexif()
        if exif:
            for k, v in exif.items():
                name = ExifTags.TAGS.get(k, k)
                if isinstance(v, bytes):
                    v = v[:80]
                print("  EXIF:", name, "=", v)
        else:
            print("  EXIF: None")
    except Exception as e:
        print("  EXIF error:", e)
    if img.info:
        for k, v in img.info.items():
            print("  INFO:", k, "=", str(v)[:100])
    print()
