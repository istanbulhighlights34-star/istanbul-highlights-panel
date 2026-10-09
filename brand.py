"""Site-matched navy/gold editorial frame, no paid services."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
NAVY='#0B0F19'; GOLD='#C5A059'
def font(size,serif=False):
    paths=('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','/System/Library/Fonts/Supplemental/Georgia.ttf') if serif else ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/System/Library/Fonts/Supplemental/Arial.ttf')
    for name in paths:
        if Path(name).is_file(): return ImageFont.truetype(name,size)
    return ImageFont.load_default(size=size)
def logo(size=120):
    image=Image.new('RGBA',(size,size),NAVY);d=ImageDraw.Draw(image)
    d.ellipse((size*.13,size*.13,size*.87,size*.87),outline=GOLD,width=max(1,round(size*.02)))
    f=font(round(size*.33),True);box=d.textbbox((0,0),'IH',font=f)
    d.text(((size-box[2])/2,(size-box[3])/2-box[1]),'IH',font=f,fill=GOLD)
    return image

def render_free_design(source,destination,headline='Istanbul'):
    with Image.open(source) as image:
        photo=ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'),(980,900))
    canvas=Image.new('RGB',(1080,1350),NAVY);canvas.paste(photo,(50,210));d=ImageDraw.Draw(canvas)
    canvas.paste(logo(116),(46,44))
    d.text((192,59),'Istanbul',font=font(53,True),fill='white')
    d.text((194,122),'HIGHLIGHTS',font=font(26),fill=GOLD,stroke_width=0)
    d.rectangle((49,209,1030,1110),outline=GOLD,width=2)
    size=52
    while size>24 and d.textlength(headline,font=font(size,True))>980: size-=2
    title=headline
    if d.textlength(title,font=font(size,True))>980:
        while d.textlength(title+'…',font=font(size,True))>980: title=title[:-1]
        title+='…'
    d.text((50,1143),title,font=font(size,True),fill='white')
    d.line((50,1230,1030,1230),fill=GOLD,width=2)
    d.text((50,1260),'Discover more at',font=font(24),fill='#D1D5DB')
    d.text((300,1254),'istanbulhighlights.com',font=font(34,True),fill=GOLD)
    canvas.save(destination,'JPEG',quality=92)
    return True
