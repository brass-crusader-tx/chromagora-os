#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
THEME=ROOT/"app/src/main/java/com/tsunami/shell/theme/TsunamiTheme.kt"
SRC=ROOT/"app/src/main/java/com/tsunami/shell"

def srgb_luminance(hex6:str)->float:
    rgb=[int(hex6[i:i+2],16)/255.0 for i in (0,2,4)]
    def channel(v:float)->float:
        return v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4
    r,g,b=(channel(v) for v in rgb)
    return 0.2126*r+0.7152*g+0.0722*b

def contrast(a:str,b:str)->float:
    l1,l2=sorted((srgb_luminance(a),srgb_luminance(b)),reverse=True)
    return (l1+0.05)/(l2+0.05)

def block(src:str,name:str)->str:
    marker=f"{name}="
    start=src.find(marker)
    if start<0:
        raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL missing palette {name}")
    open_at=src.find("(",start)
    depth=0
    for i in range(open_at,len(src)):
        if src[i]=="(": depth+=1
        elif src[i]==")":
            depth-=1
            if depth==0:
                return src[open_at+1:i]
    raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL unterminated palette {name}")

def palette(src:str,name:str)->dict[str,str]:
    body=block(src,name)
    # Compose's named black/white constants are semantically identical to the
    # ARGB literals used by the other roles. Normalize them before parsing so
    # the high-contrast palettes are genuinely verified rather than skipped.
    body=body.replace("Color.White","Color(0xFFFFFFFF)").replace("Color.Black","Color(0xFF000000)")
    values=dict(re.findall(r"(ground|groundAlt|ink|ink2|ink3|rule|selected|possession|danger|inverse)\s*=\s*Color\(0xFF([0-9A-Fa-f]{6})\)",body))
    if "ground" not in values:
        # high-contrast blocks inherit values through copy but always override ground and every text/state role.
        raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL {name} missing ground")
    return values

def main()->int:
    src=THEME.read_text(encoding="utf-8")
    names=("LightPalette","DarkPalette","LightHighContrast","DarkHighContrast")
    palettes={name:palette(src,name) for name in names}
    text_roles=("ink","ink2","ink3","selected","possession","danger")
    for name,p in palettes.items():
        missing=[role for role in text_roles if role not in p]
        if missing:
            raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL {name} missing roles {missing}")
        ratios={role:contrast(p["ground"],p[role]) for role in text_roles}
        failed={role:ratio for role,ratio in ratios.items() if ratio<4.5}
        if failed:
            raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL {name} contrast {failed}")
        print(name+" "+" ".join(f"{role}={ratios[role]:.2f}:1" for role in text_roles))
    for anchor in ("LocalControlTarget=staticCompositionLocalOf<Dp> { 48.dp }","if(largeControls) 56.dp else 48.dp"):
        if anchor not in src:
            raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL missing touch-target anchor: {anchor}")

    semantic_contract={
        "navigation/GenesisShell.kt":(
            'role=Role.Tab',
            'contentDescription="Settings"',
            'semantics { contentDescription = "Open listening environment"; role=Role.Button }',
            '.onFocusChanged{focused=it.isFocused}',
            '.onFocusChanged{settingsFocused=it.isFocused}',
            '.background(if(settingsFocused)p.groundAlt else Color.Transparent)',
            '.onFocusChanged{bannerFocused=it.isFocused}',
            '.border(2.dp,if(bannerFocused)p.selected else Color.Transparent)',
            '.onFocusChanged{spineFocused=it.isFocused}',
            '.border(2.dp,if(spineFocused)p.selected else Color.Transparent)',
        ),
        "components/Primitives.kt":(
            'role=Role.Button',
            'ProgressBarRangeInfo(progress,0f..1f)',
            'setProgress { target ->',
            '.focusable(enabled)',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(selected||focused)p.groundAlt else Color.Transparent)',
            '.onFocusChanged{actionFocused=it.isFocused}',
            '.onFocusChanged{downloadFocused=it.isFocused}',
            '.background(if(downloadFocused&&!unavailable)p.groundAlt else Color.Transparent)',
        ),
        "screens/FindScreen.kt":(
            'contentDescription="$label. ${if(enabled)detail else "Unavailable while offline"}"',
            'if(!enabled)disabled()',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(focused&&enabled)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)',
        ),
        "screens/LibraryScreen.kt":(
            'contentDescription="$name, $type, $meta"',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)',
        ),
        "screens/ExpandedListening.kt":(
            'contentDescription="Queue item ${index+1}: ${t.title}, ${t.artist}"',
            'stateDescription="Current lyric"',
            'stateDescription="Active output"',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)',
            '.onFocusChanged{playFocused=it.isFocused}',
            '.border(2.dp,if(playFocused&&t.available)p.selected else androidx.compose.ui.graphics.Color.Transparent)',
        ),
        "screens/OnboardingScreen.kt":(
            'contentDescription="$title. $detail"',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)',
        ),
        "screens/SettingsScreen.kt":(
            'semantics(mergeDescendants=true){role=Role.Button}',
            'semantics(mergeDescendants=true){role=Role.Switch;stateDescription=state}',
            '.onFocusChanged{focused=it.isFocused}',
            '.background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)',
            'contentDescription="Mini player extra: $action"',
            'contentDescription="Full player action: $action"',
            'contentDescription="Notification action: $action"',
        ),
    }
    for rel,anchors in semantic_contract.items():
        body=(SRC/rel).read_text(encoding="utf-8")
        missing=[anchor for anchor in anchors if anchor not in body]
        if missing:
            raise SystemExit(f"ACCESSIBILITY_VERIFY_FAIL {rel} missing semantic anchors {missing}")

    # Every direct authored clickable surface must expose a visible focus state.
    # Shared primitives already satisfy this through onFocusChanged; this scan
    # prevents ad-hoc clickable rows from silently reintroducing keyboard-only
    # focus with no structural visual indication.
    focus_gaps=[]
    for source in SRC.rglob("*.kt"):
        body=source.read_text(encoding="utf-8")
        for needle in (".clickable", ".combinedClickable"):
            cursor=0
            while True:
                at=body.find(needle,cursor)
                if at<0:
                    break
                line_start=body.rfind("\n",0,at)+1
                line_end=body.find("\n",at)
                if line_end<0:
                    line_end=len(body)
                line=body[line_start:line_end].strip()
                if not line.startswith("import "):
                    prefix=body[max(0,at-700):at]
                    if ".onFocusChanged" not in prefix:
                        focus_gaps.append(f"{source.relative_to(SRC)}:{body.count(chr(10),0,at)+1}:{needle}")
                cursor=at+len(needle)
    if focus_gaps:
        raise SystemExit("ACCESSIBILITY_VERIFY_FAIL clickable surfaces without visible focus: "+", ".join(focus_gaps))
    print("ACCESSIBILITY_DIRECT_CLICKABLE_FOCUS=PASS")
    print("ACCESSIBILITY_SEMANTICS=PASS tabs buttons switches seek disabled-state labels visible-focus navigation-ledgers-settings-listening-header-download-actions-banner-spine-transport")
    print("ACCESSIBILITY_VERIFY=PASS text_contrast>=4.5 touch_targets=48/56dp")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
