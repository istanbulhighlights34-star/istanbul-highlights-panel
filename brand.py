"""Site-matched navy/gold editorial frame, no paid services."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
NAVY='#0B0F19'; GOLD='#C5A059'
def font(size,serif=False,bold=False):
    import base64,io
    name=('PlayfairDisplay-Bold' if bold else 'PlayfairDisplay-Regular') if serif else 'PlusJakartaSans-Regular'
    path=Path(__file__).resolve().parent/'fonts'/(name+'.ttf.b64')
    return ImageFont.truetype(io.BytesIO(base64.b64decode(path.read_text())),size)

def tracked_width(draw,text,face,spacing):
    return sum(draw.textlength(char,font=face) for char in text)+max(0,len(text)-1)*spacing

def tracked_text(draw,text,x,baseline,face,spacing,fill):
    for char in text:
        draw.text((x,baseline),char,font=face,fill=fill,anchor='ls')
        x+=draw.textlength(char,font=face)+spacing
    return x

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
    # Match the site's single-line uppercase, bold/regular serif wordmark.
    size=52
    while True:
        first=font(size,True,True);second=font(size,True);spacing=round(size*.2,2);gap=size*.55
        first_width=tracked_width(d,'ISTANBUL',first,spacing)
        total=first_width+gap+tracked_width(d,'HIGHLIGHTS',second,spacing)
        if total<=980:break
        size-=1
    x=(1080-total)/2
    tracked_text(d,'ISTANBUL',x,97,first,spacing,'white')
    tracked_text(d,'HIGHLIGHTS',x+first_width+gap,97,second,spacing,GOLD)
    subtitle=font(24);label='DISCOVER ISTANBUL';tracking=2.5
    width=tracked_width(d,label,subtitle,tracking)
    tracked_text(d,label,(1080-width)/2,151,subtitle,tracking,'#D1D5DB')
    d.rectangle((49,209,1030,1110),outline=GOLD,width=2)
    size=52
    while size>24 and d.textlength(headline,font=font(size,True))>980: size-=2
    title=headline
    if d.textlength(title,font=font(size,True))>980:
        while d.textlength(title+'…',font=font(size,True))>980: title=title[:-1]
        title+='…'
    d.text((540,1181),title,font=font(size,True),fill='white',anchor='mm')
    d.line((50,1230,1030,1230),fill=GOLD,width=2)
    d.text((50,1260),'Discover more at',font=font(24),fill='#D1D5DB')
    d.text((300,1254),'istanbulhighlights.com',font=font(34,True),fill=GOLD)
    canvas.save(destination,'JPEG',quality=92)
    return True
