"""Create a small local JPEG preview without modifying the source."""
import argparse
import io
from pathlib import Path
from PIL import Image, ImageOps

p = argparse.ArgumentParser()
p.add_argument('source')
p.add_argument('output')
a = p.parse_args()
src, dst = Path(a.source), Path(a.output)
if src.resolve() == dst.resolve() or dst.exists():
    p.error('预览必须使用新的文件名，不能覆盖原图或已有文件')
with Image.open(src) as source:
    im = ImageOps.exif_transpose(source).convert('RGBA')
    bg = Image.new('RGBA', im.size, 'white')
    bg.alpha_composite(im)
    im = bg.convert('RGB')
im.thumbnail((960, 960))
while True:
    result = io.BytesIO()
    im.save(result, format='JPEG', quality=75, optimize=True)
    if result.tell() <= 160 * 1024 or max(im.size) <= 160:
        break
    im.thumbnail((int(im.width * .85), int(im.height * .85)))
dst.parent.mkdir(parents=True, exist_ok=True)
with dst.open('xb') as stream:
    stream.write(result.getvalue())
print(str(dst.resolve()), im.size, result.tell(), 'bytes')
