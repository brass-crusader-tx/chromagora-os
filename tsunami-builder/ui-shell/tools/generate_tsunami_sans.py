from __future__ import annotations
from pathlib import Path
from shapely.geometry import box, Point, Polygon, MultiPolygon, LineString
from shapely.affinity import scale, translate
from shapely.ops import unary_union
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from PIL import Image, ImageDraw, ImageFont

UPM=1000; ASC=800; DESC=-220; CAP=710; XH=500; FONT_TIMESTAMP=3873139200
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'app/src/main/res/font'
PROOFS=Path(__file__).resolve().parent/'proofs'
OUT.mkdir(parents=True,exist_ok=True); PROOFS.mkdir(parents=True,exist_ok=True)
WEIGHTS=[('Light',300,42),('Regular',400,68),('Medium',500,86),('Semibold',600,102),('Bold',700,120)]

def R(x0,y0,x1,y1): return box(x0,y0,x1,y1)
def E(cx,cy,rx,ry,res=64): return translate(scale(Point(0,0).buffer(1,resolution=res),rx,ry),cx,cy)
def ring(cx,cy,rx,ry,t): return E(cx,cy,rx,ry).difference(E(cx,cy,max(1,rx-t),max(1,ry-t)))
def U(*g): return unary_union([x for x in g if x is not None and not x.is_empty])
def clip(g,x0,y0,x1,y1): return g.intersection(R(x0,y0,x1,y1))
def line(x0,y0,x1,y1,t,cap=2): return LineString([(x0,y0),(x1,y1)]).buffer(t/2,cap_style=cap,join_style=1)
def path(points,t,cap=2): return LineString(points).buffer(t/2,cap_style=cap,join_style=1)
def bezier(p0,p1,p2,p3,n=28):
    out=[]
    for i in range(n+1):
        u=i/n; v=1-u
        x=v**3*p0[0]+3*v*v*u*p1[0]+3*v*u*u*p2[0]+u**3*p3[0]
        y=v**3*p0[1]+3*v*v*u*p1[1]+3*v*u*u*p2[1]+u**3*p3[1]
        out.append((x,y))
    return out

def s_curve(w,h,t):
    pts=bezier((w*.78,h*.88),(w*.52,h*1.02),(w*.18,h*.88),(w*.24,h*.63),n=18)
    pts += bezier((w*.24,h*.63),(w*.28,h*.50),(w*.72,h*.50),(w*.76,h*.36),n=14)[1:]
    pts += bezier((w*.76,h*.36),(w*.84,h*.10),(w*.49,-h*.02),(w*.20,h*.12),n=18)[1:]
    return path(pts,t,cap=2)

def Cshape(w,h,t):
    outer=ring(w/2,h/2,w*.38,h*.49,t)
    cut=R(w*.70,h*.20,w+100,h*.80)
    return outer.difference(cut)

def arc_right(x,cy,rx,ry,t):
    return clip(ring(x,cy,rx,ry,t),x,cy-ry-2,x+rx+2,cy+ry+2)
def arch_top(cx,base,rx,ry,t):
    return clip(ring(cx,base,rx,ry,t),cx-rx-2,base,cx+rx+2,base+ry+2)

def caps(ch,t):
    w=620; h=CAP; m=58; mid=h/2
    if ch=='A': return U(line(m,0,w/2,h,t),line(w-m,0,w/2,h,t),R(w*.23,h*.30,w*.77,h*.30+t)),w
    if ch=='B': return U(R(m,0,m+t,h),arc_right(m+t,h*.73,w-m-(m+t),h*.27,t),arc_right(m+t,h*.27,w-m-(m+t),h*.27,t)),w
    if ch=='C': return Cshape(w,h,t),w
    if ch=='D': return U(R(m,0,m+t,h),arc_right(m+t,h/2,w-m-(m+t),h/2,t)),w
    if ch=='E': return U(R(m,0,m+t,h),R(m,h-t,w-m,h),R(m,mid-t/2,w*.82,mid+t/2),R(m,0,w-m,t)),w
    if ch=='F': return U(R(m,0,m+t,h),R(m,h-t,w-m,h),R(m,mid-t/2,w*.80,mid+t/2)),w
    if ch=='G': return U(Cshape(w,h,t),R(w*.47,mid-t/2,w-m,mid+t/2),R(w-m-t,h*.24,w-m,mid+t/2)),w
    if ch=='H': return U(R(m,0,m+t,h),R(w-m-t,0,w-m,h),R(m,mid-t/2,w-m,mid+t/2)),w
    if ch=='I': return U(R(w/2-t/2,0,w/2+t/2,h),R(w/2-105,h-t,w/2+105,h),R(w/2-105,0,w/2+105,t)),w
    if ch=='J': return U(R(w-m-t,h*.22,w-m,h),clip(ring(w*.52,h*.20,w*.28,h*.22,t),m,-50,w-m,h*.25)),w
    if ch=='K': return U(R(m,0,m+t,h),line(m+t/2,mid,w-m,h,t),line(m+t/2,mid,w-m,0,t)),w
    if ch=='L': return U(R(m,0,m+t,h),R(m,0,w-m,t)),w
    if ch=='M': return U(R(m,0,m+t,h),R(w-m-t,0,w-m,h),line(m+t/2,h,w/2,h*.34,t),line(w/2,h*.34,w-m-t/2,h,t)),w
    if ch=='N': return U(R(m,0,m+t,h),R(w-m-t,0,w-m,h),line(m+t/2,h,w-m-t/2,0,t)),w
    if ch=='O': return ring(w/2,h/2,w*.38,h*.49,t),w
    if ch=='P': return U(R(m,0,m+t,h),arc_right(m+t,h*.72,w-m-(m+t),h*.28,t)),w
    if ch=='Q': return U(ring(w/2,h/2,w*.38,h*.49,t),line(w*.53,h*.19,w*.84,-h*.05,t)),w
    if ch=='R': return U(R(m,0,m+t,h),arc_right(m+t,h*.72,w-m-(m+t),h*.28,t),line(m+t,h*.46,w-m,0,t)),w
    if ch=='S': return s_curve(w,h,t),w
    if ch=='T': return U(R(m,h-t,w-m,h),R(w/2-t/2,0,w/2+t/2,h)),w
    if ch=='U': return U(R(m,h*.20,m+t,h),R(w-m-t,h*.20,w-m,h),clip(ring(w/2,h*.20,w*.36,h*.24,t),m,-60,w-m,h*.24)),w
    if ch=='V': return U(line(m,h,w/2,0,t),line(w-m,h,w/2,0,t)),w
    if ch=='W': return U(line(m,h,w*.21,0,t),line(w*.21,0,w*.5,h*.52,t),line(w*.5,h*.52,w*.79,0,t),line(w*.79,0,w-m,h,t)),700
    if ch=='X': return U(line(m,0,w-m,h,t),line(m,h,w-m,0,t)),w
    if ch=='Y': return U(line(m,h,w/2,h*.47,t),line(w-m,h,w/2,h*.47,t),R(w/2-t/2,0,w/2+t/2,h*.49)),w
    if ch=='Z': return U(R(m,h-t,w-m,h),line(w-m,h,m,0,t),R(m,0,w-m,t)),w
    return ring(w/2,h/2,w*.35,h*.45,t),w

def lower(ch,t):
    h=XH; w=540; m=54; tl=max(34,t*.95)
    o=lambda: ring(w/2,h/2,w*.39,h*.51,tl)
    if ch=='a': return U(o(),R(w-m-tl,0,w-m,h)),w
    if ch=='b': return U(R(m,0,m+tl,ASC),translate(o(),xoff=18)),w
    if ch=='c': return o().difference(R(w*.66,h*.16,w+80,h*.84)),w
    if ch=='d': return U(R(w-m-tl,0,w-m,ASC),translate(o(),xoff=-18)),w
    if ch=='e':
        bowl=o().difference(R(w*.67,h*.32,w+80,h*.68))
        bar=R(w*.25,h*.46,w*.84,h*.46+tl)
        return U(bowl,bar),w
    if ch=='f':
        top_y=ASC-82
        stem=R(w*.40,0,w*.40+tl,top_y)
        hook=path(bezier((w*.40+tl/2,top_y),(w*.41,ASC-18),(w*.56,ASC+2),(w*.67,ASC-30),n=14),tl,cap=2)
        cross=R(w*.16,h*.66,w*.68,h*.66+tl)
        return U(stem,hook,cross),350
    if ch=='g':
        bowl=o()
        stem=R(w-m-tl,-42,w-m,h*.48)
        hook_pts=bezier((w-m-tl/2,-42),(w*.79,-150),(w*.43,-190),(w*.27,-92),n=18)
        hook=path(hook_pts,tl,cap=2)
        return U(bowl,stem,hook),w
    if ch=='h': return U(R(m,0,m+tl,ASC),arch_top((m+w-m)/2,h*.47,(w-2*m)/2,h*.47,tl),R(w-m-tl,0,w-m,h*.47)),w
    if ch=='i': return U(R(w/2-tl/2,0,w/2+tl/2,h),E(w/2,h+105,tl*.48,tl*.48)),280
    if ch=='j': return U(R(w/2-tl/2,DESC,w/2+tl/2,h),E(w/2,h+105,tl*.48,tl*.48),clip(ring(w*.38,DESC+35,w*.16,70,tl),w*.10,DESC-40,w*.48,DESC+45)),300
    if ch=='k': return U(R(m,0,m+tl,ASC),line(m+tl/2,h*.44,w-m,h,t),line(m+tl/2,h*.44,w-m,0,t)),w
    if ch=='l': return U(R(w/2-tl/2,0,w/2+tl/2,ASC),R(w/2-tl/2,0,w/2+70,tl)),300
    if ch=='m':
        w2=760; left=m; right=w2-m; span=(right-left)/2
        return U(R(left,0,left+tl,h),arch_top(left+span/2,h*.47,span/2,h*.47,tl),arch_top(left+span+span/2,h*.47,span/2,h*.47,tl),R(left+span-tl,0,left+span,h*.47),R(right-tl,0,right,h*.47)),w2
    if ch=='n': return U(R(m,0,m+tl,h),arch_top((m+w-m)/2,h*.47,(w-2*m)/2,h*.47,tl),R(w-m-tl,0,w-m,h*.47)),w
    if ch=='o': return o(),w
    if ch=='p': return U(R(m,DESC,m+tl,h),translate(o(),xoff=18)),w
    if ch=='q': return U(R(w-m-tl,DESC,w-m,h),translate(o(),xoff=-18)),w
    if ch=='r':
        shoulder_pts=bezier((m+tl/2,h*.48),(m+tl/2,h*.88),(m+145,h*.99),(m+245,h*.82),n=16)
        return U(R(m,0,m+tl,h),path(shoulder_pts,tl,cap=2)),350
    if ch=='s': return s_curve(w,h,tl),w
    if ch=='t':
        top_y=XH+105
        stem=R(w*.45,0,w*.45+tl,top_y)
        cross=R(w*.18,h*.64,w*.74,h*.64+tl)
        return U(stem,cross),350
    if ch=='u': return U(R(m,h*.18,m+tl,h),R(w-m-tl,h*.18,w-m,h),clip(ring(w/2,h*.18,w*.37,h*.23,tl),m,-65,w-m,h*.22)),w
    if ch=='v': return U(line(m,h,w/2,0,tl),line(w-m,h,w/2,0,tl)),w
    if ch=='w': return U(line(m,h,w*.21,0,tl),line(w*.21,0,w*.50,h*.46,tl),line(w*.50,h*.46,w*.79,0,tl),line(w*.79,0,w-m,h,tl)),650
    if ch=='x': return U(line(m,0,w-m,h,tl),line(m,h,w-m,0,tl)),w
    if ch=='y': return U(line(m,h,w/2,h*.12,tl),line(w-m,h,w/2,h*.12,tl),line(w/2,h*.12,w*.38,DESC,tl)),w
    if ch=='z': return U(R(m,h-tl,w-m,h),line(w-m,h,m,0,tl),R(m,0,w-m,tl)),w
    return o(),w

def digit(ch,t):
    w=540; h=CAP; m=58; tl=t
    if ch=='0': return U(ring(w/2,h/2,w*.34,h*.49,tl),line(w*.36,h*.18,w*.64,h*.82,max(18,tl*.25))),w
    if ch=='1': return U(R(w/2-tl/2,0,w/2+tl/2,h),line(w/2-tl/2,h,w*.30,h*.83,tl),R(w*.28,0,w*.72,tl)),w
    if ch=='2':
        top=path(bezier((m,h*.72),(w*.18,h*.98),(w*.68,h*1.01),(w-m,h*.78),n=20),tl,cap=2)
        sweep=path(bezier((w-m,h*.78),(w*.82,h*.58),(w*.34,h*.32),(m,h*.08),n=20),tl,cap=2)
        base=R(m,0,w-m,tl)
        return U(top,sweep,base),w
    if ch=='3':
        pts=bezier((m,h*.88),(w*.28,h*1.01),(w*.73,h*.98),(w-m,h*.78),n=16)
        pts+=bezier((w-m,h*.78),(w*.80,h*.61),(w*.62,h*.52),(w*.48,h*.50),n=10)[1:]
        pts+=bezier((w*.48,h*.50),(w*.68,h*.49),(w*.83,h*.40),(w-m,h*.25),n=10)[1:]
        pts+=bezier((w-m,h*.25),(w*.72,-h*.02),(w*.28,-h*.02),(m,h*.12),n=16)[1:]
        return path(pts,tl,cap=2),w
    if ch=='4': return U(line(m,h*.30,w*.62,h,tl),R(w*.60-tl/2,0,w*.60+tl/2,h),R(m,h*.31,w-m,h*.31+tl)),w
    if ch=='5':
        top=U(R(m,h-tl,w-m,h),R(m,h*.52,m+tl,h))
        lower=path(bezier((m+tl/2,h*.52),(w*.40,h*.58),(w*.83,h*.56),(w-m,h*.33),n=14)+bezier((w-m,h*.33),(w*.76,h*.02),(w*.36,-h*.03),(m,h*.14),n=18)[1:],tl,cap=2)
        return U(top,lower),w
    if ch=='6':
        bowl=ring(w/2,h*.28,w*.34,h*.27,tl)
        lead=path(bezier((w*.78,h*.88),(w*.56,h*1.00),(w*.24,h*.86),(w*.20,h*.55),n=18),tl,cap=2)
        return U(bowl,lead),w
    if ch=='7': return U(R(m,h-tl,w-m,h),line(w-m,h,w*.30,0,tl)),w
    if ch=='8': return U(ring(w/2,h*.72,w*.31,h*.24,tl),ring(w/2,h*.24,w*.35,h*.26,tl)),w
    if ch=='9':
        bowl=ring(w/2,h*.72,w*.34,h*.27,tl)
        tail=path(bezier((w*.77,h*.70),(w*.82,h*.42),(w*.67,h*.10),(w*.24,h*.08),n=20),tl,cap=2)
        return U(bowl,tail),w
    return None,w

def punct(ch,t):
    w=330; h=CAP; tl=max(30,t*.8)
    dot=lambda x,y,r=tl*.48:E(x,y,r,r)
    if ch=='.': return dot(w/2,40),w
    if ch==',': return U(dot(w/2,50),line(w/2,35,w*.42,-85,tl*.55)),w
    if ch==':': return U(dot(w/2,210),dot(w/2,500)),w
    if ch==';': return U(dot(w/2,500),dot(w/2,210),line(w/2,195,w*.42,70,tl*.55)),w
    if ch=='!': return U(R(w/2-tl/2,170,w/2+tl/2,h),dot(w/2,45)),w
    if ch=='?': return U(path([(w*.22,h*.76),(w*.35,h*.95),(w*.66,h*.95),(w*.80,h*.76),(w*.73,h*.58),(w*.50,h*.46),(w*.50,h*.29)],tl,cap=2),dot(w/2,45)),w
    if ch in '-‑–−': return R(45,300,w-45,300+tl),w
    if ch=='—': return R(35,300,565,300+tl),600
    if ch=='_': return R(20,-50,w-20,-50+tl),w
    if ch=='+': return U(R(40,305,w-40,305+tl),R(w/2-tl/2,165,w/2+tl/2,475)),w
    if ch=='=': return U(R(45,250,w-45,250+tl),R(45,385,w-45,385+tl)),w
    if ch=='/': return line(55,-30,w-55,h+30,tl),w
    if ch=='\\': return line(55,h+30,w-55,-30,tl),w
    if ch=='|': return R(w/2-tl/2,DESC,w/2+tl/2,ASC),w
    if ch=='[': return U(R(85,-45,85+tl,h+45),R(85,h+45-tl,w-70,h+45),R(85,-45,w-70,-45+tl)),w
    if ch==']': return U(R(w-85-tl,-45,w-85,h+45),R(70,h+45-tl,w-85,h+45),R(70,-45,w-85,-45+tl)),w
    if ch=='{': return U(path([(w*.68,h+35),(w*.48,h*.90),(w*.51,h*.62),(w*.35,h*.50),(w*.51,h*.38),(w*.48,h*.10),(w*.68,-35)],tl*.72,cap=2)),w
    if ch=='}': return U(path([(w*.32,h+35),(w*.52,h*.90),(w*.49,h*.62),(w*.65,h*.50),(w*.49,h*.38),(w*.52,h*.10),(w*.32,-35)],tl*.72,cap=2)),w
    if ch=='<': return U(line(w*.75,h*.70,w*.25,h*.50,tl*.70),line(w*.25,h*.50,w*.75,h*.30,tl*.70)),w
    if ch=='>': return U(line(w*.25,h*.70,w*.75,h*.50,tl*.70),line(w*.75,h*.50,w*.25,h*.30,tl*.70)),w
    if ch=='^': return U(line(w*.25,h*.55,w*.50,h*.78,tl*.70),line(w*.50,h*.78,w*.75,h*.55,tl*.70)),w
    if ch=='~': return path([(w*.12,h*.46),(w*.34,h*.54),(w*.56,h*.46),(w*.82,h*.54)],tl*.55,cap=2),w
    if ch=='(': return clip(ring(w*.68,h/2,160,385,tl),0,-50,w*.59,h+50),w
    if ch==')': return clip(ring(w*.32,h/2,160,385,tl),w*.41,-50,w,h+50),w
    if ch in "'’‘": return line(w/2,h+35,w*.45,h-95,tl*.55),220
    if ch in '"“”': return U(translate(punct("'",t)[0],xoff=-45),translate(punct("'",t)[0],xoff=45)),300
    if ch=='·': return dot(w/2,h*.48,tl*.42),w
    if ch=='•': return dot(w/2,h*.48,tl*.75),w
    if ch=='…': return U(dot(70,40),dot(165,40),dot(260,40)),330
    if ch=='→': return U(R(35,320,260,320+tl*.7),line(240,430,300,320+tl*.35,tl*.55),line(300,320+tl*.35,240,215,tl*.55)),350
    if ch=='#': return U(R(100,0,100+tl,h),R(230,0,230+tl,h),R(35,255,w-35,255+tl),R(35,460,w-35,460+tl)),w
    if ch=='%': return U(ring(90,560,55,70,tl*.55),ring(245,150,55,70,tl*.55),line(70,0,265,h,tl*.55)),w
    if ch=='@': return U(ring(250,350,205,280,tl*.60),ring(245,350,92,125,tl*.60),R(300,260,300+tl*.60,485)),500
    if ch=='&': return U(ring(180,500,110,140,tl*.70),ring(180,180,145,180,tl*.70),line(150,290,330,0,tl*.70)),420
    if ch=='*': return U(line(w/2,240,w/2,520,tl*.55),line(70,285,w-70,475,tl*.55),line(70,475,w-70,285,tl*.55)),w
    if ch=='×': return U(line(70,220,w-70,500,tl*.70),line(70,500,w-70,220,tl*.70)),w
    if ch=='÷': return U(R(55,330,w-55,330+tl*.65),dot(w/2,500,tl*.45),dot(w/2,190,tl*.45)),w
    if ch=='$': return U(s_curve(540,CAP,t),R(270-t*.25,-35,270+t*.25,CAP+35)),540
    if ch=='€': return U(Cshape(560,CAP,t),R(60,260,355,260+tl*.55),R(60,395,355,395+tl*.55)),560
    if ch=='£': return U(R(120,0,120+tl,CAP*.65),arch_top(220,CAP*.70,100,160,tl),R(70,290,430,290+tl*.55),R(70,80,480,80+tl*.7)),520
    if ch=='¥': return U(line(65,CAP,270,CAP*.46,t),line(475,CAP,270,CAP*.46,t),R(270-t/2,0,270+t/2,CAP*.48),R(120,290,420,290+tl*.55),R(140,400,400,400+tl*.55)),540
    return dot(w/2,40),w

ACCENTS={'Ñ':('N','tilde'),'ñ':('n','tilde'),'À':('A','grave'),'Á':('A','acute'),'Â':('A','circumflex'),'Ã':('A','tilde'),'Ä':('A','dieresis'),'Å':('A','ring'),'Ç':('C','cedilla'),'È':('E','grave'),'É':('E','acute'),'Ê':('E','circumflex'),'Ë':('E','dieresis'),'Ì':('I','grave'),'Í':('I','acute'),'Î':('I','circumflex'),'Ï':('I','dieresis'),'Ò':('O','grave'),'Ó':('O','acute'),'Ô':('O','circumflex'),'Õ':('O','tilde'),'Ö':('O','dieresis'),'Ù':('U','grave'),'Ú':('U','acute'),'Û':('U','circumflex'),'Ü':('U','dieresis'),'Ý':('Y','acute'),'à':('a','grave'),'á':('a','acute'),'â':('a','circumflex'),'ã':('a','tilde'),'ä':('a','dieresis'),'å':('a','ring'),'ç':('c','cedilla'),'è':('e','grave'),'é':('e','acute'),'ê':('e','circumflex'),'ë':('e','dieresis'),'ì':('i','grave'),'í':('i','acute'),'î':('i','circumflex'),'ï':('i','dieresis'),'ò':('o','grave'),'ó':('o','acute'),'ô':('o','circumflex'),'õ':('o','tilde'),'ö':('o','dieresis'),'ù':('u','grave'),'ú':('u','acute'),'û':('u','circumflex'),'ü':('u','dieresis'),'ý':('y','acute'),'ÿ':('y','dieresis')}
def accent(kind,t,c,top):
    tl=max(26,t*.55)
    if kind=='acute': return line(c-45,top,c+45,top+85,tl)
    if kind=='grave': return line(c-45,top+85,c+45,top,tl)
    if kind=='circumflex': return U(line(c-80,top,c,top+72,tl),line(c,top+72,c+80,top,tl))
    if kind=='dieresis': return U(E(c-58,top+40,tl*.42,tl*.42),E(c+58,top+40,tl*.42,tl*.42))
    if kind=='tilde': return path([(c-90,top+35),(c-30,top+60),(c+30,top+35),(c+90,top+60)],tl*.6,cap=2)
    if kind=='ring': return ring(c,top+38,48,48,tl*.45)
    if kind=='cedilla': return U(line(c,4,c-28,-72,tl*.55),clip(ring(c-8,-86,55,42,tl*.55),c-70,-140,c+55,-60))

def special(ch,t):
    if ch=='Æ':
        w=820; h=CAP; m=50
        shared=360
        return U(
            line(m,0,shared,h,t), line(shared,h,shared+82,0,t),
            R(120,h*.30,shared+45,h*.30+t),
            R(shared,0,shared+t,h),
            R(shared,h-t,w-m,h), R(shared,h*.50-t/2,w-m-35,h*.50+t/2), R(shared,0,w-m,t)
        ),w
    if ch=='æ':
        a,_=lower('a',t); e,_=lower('e',t); w=760
        return U(scale(a,.76,1,origin=(0,0)),translate(scale(e,.76,1,origin=(0,0)),xoff=350)),w
    if ch=='Œ':
        w=820; h=CAP; tl=t
        o=ring(250,h/2,205,h*.49,tl)
        return U(o,R(420,0,420+tl,h),R(420,h-t,w-50,h),R(420,h*.50-t/2,w-80,h*.50+t/2),R(420,0,w-50,t)),w
    if ch=='œ':
        o,_=lower('o',t); e,_=lower('e',t); w=760
        return U(scale(o,.76,1,origin=(0,0)),translate(scale(e,.76,1,origin=(0,0)),xoff=350)),w
    if ch=='Ø':
        o,w=caps('O',t); return U(o,line(w*.23,CAP*.05,w*.77,CAP*.95,max(26,t*.46))),w
    if ch=='ø':
        o,w=lower('o',t); return U(o,line(w*.24,XH*.04,w*.76,XH*.96,max(24,t*.46))),w
    if ch=='Ð':
        d,w=caps('D',t); return U(d,R(18,CAP*.48,w*.52,CAP*.48+max(28,t*.65))),w
    if ch=='ð':
        d,w=lower('d',t); return U(d,line(w*.34,XH*.76,w*.66,ASC*.94,max(24,t*.55))),w
    if ch=='Þ':
        p,w=caps('P',t); return U(p,R(58,-20,58+t,CAP*.76)),w
    if ch=='þ':
        p,w=lower('p',t); return U(p,R(54,DESC,54+max(34,t*.95),ASC)),w
    if ch=='ß':
        w=590; h=ASC; tl=max(34,t*.95); m=55
        top=arc_right(m+tl,h*.66,w-m-(m+tl),h*.24,tl)
        lower_arc=path([(m+tl,h*.44),(w*.72,h*.43),(w*.82,h*.20),(w*.66,h*.04),(w*.42,0)],tl,cap=2)
        return U(R(m,0,m+tl,h*.72),top,lower_arc),w
    return None

def shape(ch,t):
    sp=special(ch,t)
    if sp is not None: return sp
    if 'A'<=ch<='Z': return caps(ch,t)
    if 'a'<=ch<='z': return lower(ch,t)
    if ch.isdigit(): return digit(ch,t)
    if ch==' ': return None,270
    if ch in ACCENTS:
        base,kind=ACCENTS[ch]; sh,w=shape(base,t); top=(XH+45 if base.islower() else CAP+35); return U(sh,accent(kind,t,w/2,top)),w
    return punct(ch,t)

def glyph(shape):
    pen=TTGlyphPen(None)
    if shape is None or shape.is_empty: return pen.glyph()
    geoms=shape.geoms if isinstance(shape,MultiPolygon) else [shape]
    for p in geoms:
        if not isinstance(p,Polygon): continue
        ext=list(p.exterior.coords)
        pen.moveTo(ext[0]); [pen.lineTo(q) for q in ext[1:-1]]; pen.closePath()
        for hole in p.interiors:
            pts=list(hole.coords)
            pen.moveTo(pts[0]); [pen.lineTo(q) for q in pts[1:-1]]; pen.closePath()
    return pen.glyph()

PUNCT='.,:;!?-_+=/\\|()[]{}<>^~\'’‘"“”#%&@*·•…‑–—−→×÷$€£¥'
SPECIALS='ÆæŒœØøÐðÞþß'
CHARS=' '+''.join(chr(i) for i in range(65,91))+''.join(chr(i) for i in range(97,123))+'0123456789'+PUNCT+''.join(ACCENTS)+SPECIALS

def build(style,weight,t):
    order=['.notdef']; glyphs={'.notdef':glyph(U(R(80,0,520,690).difference(R(140,60,460,630)),line(120,80,480,610,max(32,t*.55))))}; metrics={'.notdef':(600,0)}; cmap={}
    seen=set()
    for ch in CHARS:
        if ch in seen: continue
        seen.add(ch); name=f'u{ord(ch):04X}'; sh,w=shape(ch,t); side=max(24,int(34-(weight-300)*.010))
        if sh is not None and not sh.is_empty:
            minx,miny,maxx,maxy=sh.bounds; sh=translate(sh,xoff=side-minx); adv=int(max(w,maxx-minx)+2*side)
        else: adv=w
        order.append(name); glyphs[name]=glyph(sh); metrics[name]=(adv,0); cmap[ord(ch)]=name
    fb=FontBuilder(UPM,isTTF=True); fb.font['head'].created=FONT_TIMESTAMP; fb.font['head'].modified=FONT_TIMESTAMP; fb.setupGlyphOrder(order); fb.setupCharacterMap(cmap); fb.setupGlyf(glyphs); fb.setupHorizontalMetrics(metrics); fb.setupHorizontalHeader(ascent=ASC,descent=DESC,lineGap=110)
    fb.setupOS2(sTypoAscender=ASC,sTypoDescender=DESC,sTypoLineGap=110,usWinAscent=940,usWinDescent=260,usWeightClass=weight,fsSelection=(1<<6 if weight==400 else 0),sxHeight=XH,sCapHeight=CAP,achVendID='TSNM')
    fb.setupNameTable({'familyName':'TSUNAMI Sans','styleName':style,'uniqueFontIdentifier':f'TSUNAMI Sans {style} 4.5','fullName':f'TSUNAMI Sans {style}','psName':f'TSUNAMISans-{style}','version':'Version 4.500'}); fb.setupPost(); fb.setupMaxp()
    kern_pairs=[('A','V',-40),('A','W',-34),('A','Y',-42),('V','A',-40),('W','A',-30),('Y','A',-44),('T','A',-28),('T','o',-34),('T','e',-34),('T','a',-30),('T','y',-24),('F','o',-22),('F','a',-18),('L','T',-20),('L','Y',-28),('Y','o',-36),('Y','e',-36),('P','a',-18),('r','y',-12)]
    feature_lines=[]
    for left,right,value in kern_pairs:
        if ord(left) in cmap and ord(right) in cmap:
            feature_lines.append(f"pos {cmap[ord(left)]} {cmap[ord(right)]} {value};")
    if feature_lines:
        addOpenTypeFeaturesFromString(fb.font,'feature kern {\n'+'\n'.join(feature_lines)+'\n} kern;')
    out=OUT/f'tsunami_sans_{style.lower()}.ttf'; fb.save(out); return out

def proof(fonts):
    W,H=1700,1510; im=Image.new('RGB',(W,H),'#F4F1EA'); d=ImageDraw.Draw(im)
    def F(wt,size): return ImageFont.truetype(str(fonts[wt]),size)
    d.text((70,45),'TSUNAMI Sans — Genesis Proof v4.5',font=F('Semibold',54),fill='#111216')
    d.text((70,118),'H O n o  ·  optical control glyphs',font=F('Regular',34),fill='#44464C')
    y=185
    samples=[('ABCDEFGHIJKLM','Regular',56),('NOPQRSTUVWXYZ','Regular',56),('abcdefghijklm','Regular',48),('nopqrstuvwxyz','Regular',48),('0123456789  01:42 / 04:19','Medium',46),('S s  G R  a e g r t k y  2 3 5 6 8','Regular',44),('I l 1   O 0   rn m   c e   v y','Regular',42),('S s  G C  R  a e g r t k y   & ? @   [] {}','Regular',36),('Æ æ  Œ œ  Ø ø  Ð ð  Þ þ  ß  Ñ ñ','Regular',34),('ÀÁÂÃÄÅ Ç ÈÉÊË Ï Ö Ü  àáâä ç éêë ï ö ü','Regular',36),('“Afterglow at the edge of the city”','Semibold',46),('Mira Sol · Refractions / Deluxe Edition','Medium',34),('FLAC 24-bit · 96 kHz   OFFLINE   QUEUED','Regular',28)]
    for txt,wt,size in samples: d.text((70,y),txt,font=F(wt,size),fill='#111216'); y+=80 if size>=46 else 66
    x=1060; y=190
    for wt in ['Light','Regular','Medium','Semibold','Bold']:
        d.text((x,y),f'{wt}  Aa 128',font=F(wt,48),fill='#111216'); y+=86
    d.line((1000,155,1000,1390),fill='#BDB8AE',width=2)
    im.save(PROOFS/'tsunami-sans-proof.png')

    ui=Image.new('RGB',(1280,1260),'#F4F1EA'); u=ImageDraw.Draw(ui)
    u.text((64,42),'TSUNAMI Sans — UI-size proof',font=F('Semibold',38),fill='#111216')
    y=118
    ui_samples=[
        (12,'Regular','12 px metadata · FLAC 24-bit · 96 kHz · OFFLINE'),
        (14,'Regular','14 px body · Mira Sol — Refractions · 04:19 remaining'),
        (16,'Medium','16 px row · Afterglow at the Edge of the City'),
        (18,'Medium','18 px command · Play next · Shuffle next · Output'),
        (22,'Semibold','22 px title · Library / Listening / Signal'),
        (34,'Medium','34 px display · Your listening line'),
    ]
    for size,wt,txt in ui_samples:
        u.text((64,y),txt,font=F(wt,size),fill='#111216')
        y+=108
    u.text((64,790),'Control pairs: I l 1   O 0   rn m   S s   G C   e c',font=F('Regular',18),fill='#44464C')
    u.text((64,850),'LONG ALBUM TITLE',font=F('Semibold',12),fill='#44464C')
    u.text((64,880),'A Very Long Album Title About Motion, Memory, Distance,',font=F('Medium',22),fill='#111216')
    u.text((64,912),'and the Places We Return To',font=F('Medium',22),fill='#111216')
    u.text((64,970),'MIXED-WEIGHT HIERARCHY',font=F('Semibold',12),fill='#44464C')
    u.text((64,1000),'Afterglow at the Edge of the City',font=F('Semibold',24),fill='#111216')
    u.text((64,1035),'Mira Sol · Refractions',font=F('Regular',16),fill='#44464C')
    u.text((64,1065),'1:34 / 4:19   FLAC · 24 / 96   OWNED',font=F('Medium',13),fill='#66686E')
    u.text((64,1125),'Accents: déjà vu · São Paulo · Ångström · façade · naïve · cœur · Straße',font=F('Regular',17),fill='#111216')
    u.text((64,1165),'Punctuation: ! ? — – … “ ” ‘ ’ ( ) [ ] { } / \\ & @ # % + = × ÷ →',font=F('Regular',16),fill='#44464C')
    ui.save(PROOFS/'tsunami-sans-ui-proof.png')

if __name__=='__main__':
    fonts={wt:build(wt,w,t) for wt,w,t in WEIGHTS}; proof(fonts); print('\n'.join(map(str,fonts.values())))
