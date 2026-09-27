#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageDraw
root=Path(__file__).resolve().parents[1]/'build/verification'
base=sorted(p for p in root.glob('*.png') if '-mono' not in p.stem and '-squint' not in p.stem and p.stem!='contact-sheet')
thumbs=[]
for p in base:
    im=Image.open(p).convert('RGB')
    gray=ImageOps.grayscale(im).convert('RGB'); gray.save(root/(p.stem+'-mono.png'))
    gray.filter(ImageFilter.GaussianBlur(radius=10)).save(root/(p.stem+'-squint.png'))
    if True:
        tw=320; ratio=tw/im.width; h=max(1,int(im.height*ratio)); t=im.resize((tw,h))
        canvas=Image.new('RGB',(tw,h+32),'white');canvas.paste(t,(0,32));ImageDraw.Draw(canvas).text((8,8),p.name,fill='black');thumbs.append(canvas)
if thumbs:
    cols=4; rows=(len(thumbs)+cols-1)//cols; cell_h=max(i.height for i in thumbs)
    sheet=Image.new('RGB',(cols*320,rows*cell_h),'#d8d8d8')
    for i,t in enumerate(thumbs): sheet.paste(t,((i%cols)*320,(i//cols)*cell_h))
    sheet.save(root/'contact-sheet.png')
print(f'base={len(base)} png_total={len(list(root.glob("*.png")))}')
