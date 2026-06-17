from PIL import Image
# Load page 5 and check it's well-formed
img = Image.open('pdf_preview/hires-05.jpg')
print('page5 size:', img.size)
# Sample some regions to confirm content exists (not blank)
import os
print('page5 bytes:', os.path.getsize('pdf_preview/hires-05.jpg')//1024, 'KB')

# Check all 12 pages are non-trivial sizes (real content)
for i in range(1, 13):
    p = 'pdf_preview/hires-{:02d}.jpg'.format(i)
    kb = os.path.getsize(p) // 1024
    im = Image.open(p)
    print('page {:02d}: {}x{} {}KB'.format(i, im.width, im.height, kb))
