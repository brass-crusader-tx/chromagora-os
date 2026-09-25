package com.tsunami.shell.components

import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsPressedAsState
import androidx.compose.foundation.shape.RectangleShape
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.*
import com.tsunami.shell.model.*
import com.tsunami.shell.theme.*
import kotlin.math.roundToInt

@Composable fun Text(text:String,style:TextStyle,modifier:Modifier=Modifier,maxLines:Int=Int.MAX_VALUE,overflow:TextOverflow=TextOverflow.Clip){
    BasicText(text=text,modifier=modifier,style=style,maxLines=maxLines,overflow=overflow)
}

enum class Glyph { PLAY, PAUSE, NEXT, PREVIOUS, STAR, DOWNLOAD, SEARCH, SETTINGS, BACK, SHUFFLE, REPEAT, QUEUE, LYRICS, OUTPUT, MORE, CLOSE, PLUS, MINUS, UP, DOWN }

@Composable fun GlyphIcon(glyph:Glyph,modifier:Modifier=Modifier.size(22.dp),color:Color=LocalTsunamiPalette.current.ink){
    Canvas(modifier){
        val s=size.minDimension; val c=Offset(size.width/2,size.height/2); val sw=s*.09f; val st=Stroke(sw,cap=StrokeCap.Square,join=StrokeJoin.Miter)
        fun line(a:Offset,b:Offset)=drawLine(color,a,b,sw,StrokeCap.Square)
        when(glyph){
            Glyph.PLAY -> drawPath(Path().apply{moveTo(s*.28f,s*.16f);lineTo(s*.78f,s*.5f);lineTo(s*.28f,s*.84f);close()},color)
            Glyph.PAUSE -> { drawRect(color,Offset(s*.25f,s*.18f),androidx.compose.ui.geometry.Size(s*.16f,s*.64f)); drawRect(color,Offset(s*.59f,s*.18f),androidx.compose.ui.geometry.Size(s*.16f,s*.64f)) }
            Glyph.NEXT -> { line(Offset(s*.22f,s*.2f),Offset(s*.64f,s*.5f));line(Offset(s*.64f,s*.5f),Offset(s*.22f,s*.8f));line(Offset(s*.75f,s*.2f),Offset(s*.75f,s*.8f)) }
            Glyph.PREVIOUS -> { line(Offset(s*.78f,s*.2f),Offset(s*.36f,s*.5f));line(Offset(s*.36f,s*.5f),Offset(s*.78f,s*.8f));line(Offset(s*.25f,s*.2f),Offset(s*.25f,s*.8f)) }
            Glyph.SEARCH -> { drawCircle(color,s*.27f,Offset(s*.42f,s*.42f),style=st);line(Offset(s*.61f,s*.61f),Offset(s*.84f,s*.84f)) }
            Glyph.BACK -> {line(Offset(s*.75f,s*.2f),Offset(s*.32f,s*.5f));line(Offset(s*.32f,s*.5f),Offset(s*.75f,s*.8f))}
            Glyph.CLOSE -> {line(Offset(s*.25f,s*.25f),Offset(s*.75f,s*.75f));line(Offset(s*.75f,s*.25f),Offset(s*.25f,s*.75f))}
            Glyph.PLUS -> {line(Offset(s*.18f,s*.5f),Offset(s*.82f,s*.5f));line(Offset(s*.5f,s*.18f),Offset(s*.5f,s*.82f))}
            Glyph.MINUS -> line(Offset(s*.18f,s*.5f),Offset(s*.82f,s*.5f))
            Glyph.UP -> {line(Offset(s*.22f,s*.64f),Offset(s*.5f,s*.34f));line(Offset(s*.5f,s*.34f),Offset(s*.78f,s*.64f))}
            Glyph.DOWN -> {line(Offset(s*.22f,s*.36f),Offset(s*.5f,s*.66f));line(Offset(s*.5f,s*.66f),Offset(s*.78f,s*.36f))}
            Glyph.MORE -> {drawCircle(color,s*.07f,Offset(s*.22f,s*.5f));drawCircle(color,s*.07f,Offset(s*.5f,s*.5f));drawCircle(color,s*.07f,Offset(s*.78f,s*.5f))}
            Glyph.STAR -> {
                val p=Path(); repeat(10){i-> val a=(-Math.PI/2+i*Math.PI/5).toFloat(); val r=if(i%2==0)s*.38f else s*.17f; val pt=Offset(c.x+kotlin.math.cos(a)*r,c.y+kotlin.math.sin(a)*r); if(i==0)p.moveTo(pt.x,pt.y) else p.lineTo(pt.x,pt.y)};p.close();drawPath(p,color,style=st)
            }
            Glyph.DOWNLOAD -> {line(Offset(s*.5f,s*.15f),Offset(s*.5f,s*.65f));line(Offset(s*.28f,s*.48f),Offset(s*.5f,s*.7f));line(Offset(s*.72f,s*.48f),Offset(s*.5f,s*.7f));line(Offset(s*.2f,s*.84f),Offset(s*.8f,s*.84f))}
            Glyph.SHUFFLE -> {line(Offset(s*.12f,s*.27f),Offset(s*.34f,s*.27f));line(Offset(s*.34f,s*.27f),Offset(s*.66f,s*.72f));line(Offset(s*.66f,s*.72f),Offset(s*.88f,s*.72f));line(Offset(s*.72f,s*.58f),Offset(s*.88f,s*.72f));line(Offset(s*.72f,s*.86f),Offset(s*.88f,s*.72f));line(Offset(s*.12f,s*.72f),Offset(s*.34f,s*.72f));line(Offset(s*.34f,s*.72f),Offset(s*.5f,s*.49f));line(Offset(s*.58f,s*.38f),Offset(s*.66f,s*.27f));line(Offset(s*.66f,s*.27f),Offset(s*.88f,s*.27f))}
            Glyph.REPEAT -> {line(Offset(s*.2f,s*.3f),Offset(s*.75f,s*.3f));line(Offset(s*.75f,s*.3f),Offset(s*.88f,s*.43f));line(Offset(s*.88f,s*.43f),Offset(s*.88f,s*.52f));line(Offset(s*.8f,s*.7f),Offset(s*.25f,s*.7f));line(Offset(s*.25f,s*.7f),Offset(s*.12f,s*.57f));line(Offset(s*.12f,s*.57f),Offset(s*.12f,s*.48f))}
            Glyph.QUEUE -> {listOf(.25f,.5f,.75f).forEach{y->line(Offset(s*.18f,s*y),Offset(s*.82f,s*y))}}
            Glyph.LYRICS -> {line(Offset(s*.2f,s*.24f),Offset(s*.8f,s*.24f));line(Offset(s*.2f,s*.5f),Offset(s*.68f,s*.5f));line(Offset(s*.2f,s*.76f),Offset(s*.56f,s*.76f))}
            Glyph.OUTPUT -> {drawCircle(color,s*.08f,c);drawCircle(color,s*.24f,c,style=st);drawCircle(color,s*.4f,c,style=st)}
            Glyph.SETTINGS -> {drawCircle(color,s*.16f,c,style=st); for(i in 0 until 8){ val a=(i*Math.PI/4).toFloat(); line(Offset(c.x+kotlin.math.cos(a)*s*.28f,c.y+kotlin.math.sin(a)*s*.28f),Offset(c.x+kotlin.math.cos(a)*s*.42f,c.y+kotlin.math.sin(a)*s*.42f)) }}
        }
    }
}

@Composable fun HitIcon(glyph:Glyph,label:String,onClick:()->Unit,selected:Boolean=false,modifier:Modifier=Modifier,enabled:Boolean=true){
    val p=LocalTsunamiPalette.current
    val target=LocalControlTarget.current
    var focused by remember { mutableStateOf(false) }
    val interactions=remember { MutableInteractionSource() }
    val pressed by interactions.collectIsPressedAsState()
    Box(
        modifier.sizeIn(minWidth=target,minHeight=target)
            .semantics{contentDescription=label;role=Role.Button;if(selected) stateDescription="Selected";if(!enabled) disabled()}
            .onFocusChanged{focused=it.isFocused}
            .focusable(enabled)
            .clickable(interactionSource=interactions,indication=null,enabled=enabled,onClick=onClick),
        contentAlignment=Alignment.Center
    ){
        GlyphIcon(glyph,color=when{!enabled->p.ink3.copy(alpha=.52f);selected||focused||pressed->p.selected;else->p.ink})
        if(focused||pressed) Box(Modifier.align(Alignment.BottomCenter).width(if(focused)20.dp else 14.dp).height(2.dp).background(p.selected))
    }
}

@Composable fun Rule(modifier:Modifier=Modifier,color:Color=LocalTsunamiPalette.current.rule,thickness:Dp=1.dp){ Box(modifier.height(thickness).background(color)) }

@Composable fun SectionHeader(label:String,action:String?=null,onAction:(()->Unit)?=null){
    val p=LocalTsunamiPalette.current
    val target=LocalControlTarget.current
    var actionFocused by remember(label,action){ mutableStateOf(false) }
    Row(Modifier.fillMaxWidth().padding(top=18.dp,bottom=9.dp),verticalAlignment=Alignment.CenterVertically){
        Text(label,style=Type.meta.copy(color=p.ink2,fontWeight=FontWeight.SemiBold),modifier=Modifier.weight(1f))
        if(action!=null&&onAction!=null){
            Column(
                Modifier
                    .sizeIn(minHeight=target)
                    .semantics{role=Role.Button;contentDescription="$action $label"}
                    .onFocusChanged{actionFocused=it.isFocused}
                    .focusable()
                    .clickable(onClick=onAction)
                    .padding(horizontal=6.dp),
                verticalArrangement=Arrangement.Center
            ){
                Text(action,style=Type.meta.copy(color=if(actionFocused)p.selected else p.ink2,fontWeight=if(actionFocused)FontWeight.SemiBold else FontWeight.Normal))
                Spacer(Modifier.height(4.dp))
                Box(Modifier.width(if(actionFocused)18.dp else 8.dp).height(if(actionFocused)2.dp else 1.dp).background(if(actionFocused)p.selected else Color.Transparent))
            }
        }
    }
    Rule()
}

@Composable fun TextCommand(text:String,onClick:()->Unit,selected:Boolean=false,modifier:Modifier=Modifier,enabled:Boolean=true){
    val p=LocalTsunamiPalette.current
    val target=LocalControlTarget.current
    var focused by remember { mutableStateOf(false) }
    val interactions=remember { MutableInteractionSource() }
    val pressed by interactions.collectIsPressedAsState()
    val textColor=when{
        !enabled->p.ink3.copy(alpha=.56f)
        selected->p.ink
        focused||pressed->p.selected
        else->p.ink2
    }
    Column(
        modifier
            .sizeIn(minHeight=target)
            .semantics{role=Role.Button;contentDescription=text;if(selected) stateDescription="Selected";if(!enabled) disabled()}
            .onFocusChanged{focused=it.isFocused}
            .focusable(enabled)
            .clickable(interactionSource=interactions,indication=null,enabled=enabled,onClick=onClick)
            .padding(horizontal=6.dp),
        verticalArrangement=Arrangement.Center
    ){
        Text(text,style=Type.meta.copy(color=textColor,fontWeight=if(selected||focused||pressed)FontWeight.SemiBold else FontWeight.Normal))
        Spacer(Modifier.height(5.dp))
        Box(
            Modifier
                .width(if(selected)26.dp else if(focused)18.dp else if(pressed)14.dp else 10.dp)
                .height(if(selected||focused||pressed)2.dp else 1.dp)
                .background(if(selected||focused||pressed)p.selected else Color.Transparent)
        )
    }
}

@Composable fun Artwork(track:Track?,modifier:Modifier=Modifier,forceMissing:Boolean=false){
    val p=LocalTsunamiPalette.current
    val seed=track?.artworkSeed
    Box(modifier.clip(RectangleShape).background(p.groundAlt),contentAlignment=Alignment.Center){
        if(seed!=null&&!forceMissing){
            Canvas(Modifier.fillMaxSize()){
                val k=(seed%7)+1
                drawRect(p.ink.copy(alpha=.09f*k),size=size)
                drawLine(p.ink2.copy(alpha=.45f),Offset(0f,size.height*(.15f+.07f*k)),Offset(size.width,size.height*(.80f-.04f*k)),size.minDimension*.045f)
                drawCircle(p.selected.copy(alpha=.20f+.05f*(k%3)),size.minDimension*(.16f+.02f*k),Offset(size.width*(.25f+.06f*(k%5)),size.height*(.35f+.05f*(k%4))))
            }
        } else {
            // Deliberately neutral: the no-artwork verification must not smuggle brand identity
            // back into the content slot. TSUNAMI's hierarchy has to survive this plain field.
            Canvas(Modifier.fillMaxSize()){
                val sw=1.dp.toPx()
                drawRect(p.rule,style=Stroke(width=sw))
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable fun TrackLedgerRow(track:Track,stateLabel:String,onOpen:()->Unit,onPlay:()->Unit,onFavourite:()->Unit,onDownload:()->Unit,compact:Boolean=false,forceMissing:Boolean=false,onPlayNext:(()->Unit)?=null,onShuffleNext:(()->Unit)?=null,onAddToPlaylist:(()->Unit)?=null,selected:Boolean=false,selectionMode:Boolean=false,secondaryLabel:String?=null,downloadState:DownloadState=DownloadState.REMOTE){
    val p=LocalTsunamiPalette.current
    val unavailable=!track.available
    val effectiveState=if(unavailable)"UNAVAILABLE · $stateLabel" else stateLabel
    var showActions by remember(track.id){mutableStateOf(false)}
    var focused by remember(track.id){mutableStateOf(false)}
    var downloadFocused by remember(track.id){mutableStateOf(false)}
    Column(
        Modifier.fillMaxWidth()
            .semantics{
                role=Role.Button
                contentDescription="${track.title}, ${track.artist}, ${track.album}. $effectiveState"
                if(selected) stateDescription="Selected"
            }
            .onFocusChanged{focused=it.isFocused}
            .combinedClickable(onClick=onOpen,onLongClick={if(!selectionMode)showActions=true})
            .background(if(selected||focused)p.groundAlt else Color.Transparent)
            .padding(vertical=if(compact)8.dp else 12.dp)
    ){
        Row(verticalAlignment=Alignment.CenterVertically){
            Box(Modifier.width(if(selected||focused)3.dp else 1.dp).height(if(compact)24.dp else 32.dp).background(if(selected||focused)p.selected else Color.Transparent))
            Spacer(Modifier.width(if(selected)7.dp else 0.dp))
            Artwork(track,Modifier.size(if(compact)42.dp else 52.dp),forceMissing)
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f)){
                Text(track.title,style=Type.row.copy(color=if(unavailable)p.ink3 else p.ink),maxLines=if(compact)1 else 2,overflow=TextOverflow.Ellipsis)
                Spacer(Modifier.height(2.dp))
                Text(secondaryLabel ?: "${track.artist}  ·  ${track.album}",style=Type.meta.copy(color=p.ink2),maxLines=1,overflow=TextOverflow.Ellipsis)
                if(!compact){ Spacer(Modifier.height(3.dp)); Text(effectiveState,style=Type.micro.copy(color=if(unavailable)p.danger else p.ink3),maxLines=1,overflow=TextOverflow.Ellipsis) }
            }
            if(selectionMode){
                Text(if(selected)"SELECTED" else "SELECT",style=Type.micro.copy(color=if(selected)p.selected else p.ink3,fontWeight=if(selected)FontWeight.SemiBold else FontWeight.Normal),modifier=Modifier.padding(horizontal=8.dp))
            }else{
                when(downloadState){
                    DownloadState.DOWNLOADING -> Text("…",style=Type.meta.copy(color=p.selected),modifier=Modifier.width(38.dp))
                    DownloadState.DOWNLOADED -> Text("LOCAL",style=Type.micro.copy(color=p.possession,fontWeight=FontWeight.SemiBold),modifier=Modifier.width(42.dp))
                    DownloadState.REMOTE -> Unit
                }
                HitIcon(Glyph.PLAY,if(unavailable)"${track.title} unavailable" else "Play ${track.title}",onPlay,enabled=!unavailable)
                HitIcon(Glyph.MORE,if(showActions)"Close track actions" else "Track actions",{showActions=!showActions},showActions)
            }
        }
        if(!compact){ 
            Spacer(Modifier.height(8.dp))
            Row(Modifier.padding(start=64.dp),verticalAlignment=Alignment.CenterVertically){
                Text(track.quality,style=Type.micro.copy(color=p.ink3)); Spacer(Modifier.weight(1f)); Text(effectiveState,style=Type.micro.copy(color=if(unavailable)p.danger else p.ink3)); Spacer(Modifier.width(8.dp))
                Box(
                    Modifier
                        .sizeIn(minWidth=64.dp,minHeight=LocalControlTarget.current)
                        .semantics{
                            role=Role.Button
                            contentDescription=when(downloadState){
                                DownloadState.REMOTE->"Make ${track.title} available offline"
                                DownloadState.DOWNLOADING->"Complete download for ${track.title}"
                                DownloadState.DOWNLOADED->"Remove offline copy of ${track.title}"
                            }
                            if(unavailable) disabled()
                        }
                        .onFocusChanged{downloadFocused=it.isFocused}
                        .focusable(!unavailable)
                        .background(if(downloadFocused&&!unavailable)p.groundAlt else Color.Transparent)
                        .clickable(enabled=!unavailable,onClick=onDownload),
                    contentAlignment=Alignment.Center
                ){
                    when(downloadState){
                        DownloadState.REMOTE -> GlyphIcon(Glyph.DOWNLOAD,Modifier.size(17.dp),if(downloadFocused)p.selected else p.ink3)
                        DownloadState.DOWNLOADING -> Text("DOWNLOADING",style=Type.micro.copy(color=p.selected,fontWeight=if(downloadFocused)FontWeight.SemiBold else FontWeight.Medium))
                        DownloadState.DOWNLOADED -> Text("LOCAL",style=Type.micro.copy(color=if(downloadFocused)p.selected else p.possession,fontWeight=FontWeight.SemiBold))
                    }
                    if(downloadFocused&&!unavailable) Box(Modifier.align(Alignment.BottomCenter).width(20.dp).height(2.dp).background(p.selected))
                }
            }
        }
        if(showActions && !selectionMode){
            Row(Modifier.padding(start=64.dp).fillMaxWidth().horizontalScroll(rememberScrollState()),verticalAlignment=Alignment.CenterVertically){
                TextCommand("Favourite",onFavourite)
                TextCommand(when(downloadState){DownloadState.REMOTE->"Make offline";DownloadState.DOWNLOADING->"Finish download";DownloadState.DOWNLOADED->"Remove offline"},onDownload,downloadState==DownloadState.DOWNLOADED,enabled=!unavailable)
                onPlayNext?.let{ TextCommand("Play next",it,enabled=!unavailable) }
                onShuffleNext?.let{ TextCommand("Shuffle next",it,enabled=!unavailable) }
                onAddToPlaylist?.let{ TextCommand("Add to playlist",it) }
            }
        }
    }
    Rule()
}

@Composable fun UnderlineSearch(value:String,onValueChange:(String)->Unit,placeholder:String){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxWidth()){
        Row(Modifier.fillMaxWidth().heightIn(min=56.dp),verticalAlignment=Alignment.CenterVertically){
            GlyphIcon(Glyph.SEARCH,Modifier.size(24.dp),p.ink2); Spacer(Modifier.width(14.dp))
            BasicTextField(value,onValueChange,textStyle=Type.title.copy(color=p.ink),singleLine=true,modifier=Modifier.weight(1f).semantics { contentDescription = "Search music" },decorationBox={inner->Box{if(value.isEmpty())Text(placeholder,style=Type.title.copy(color=p.ink3));inner()}})
            if(value.isNotEmpty()) HitIcon(Glyph.CLOSE,"Clear search",{onValueChange("")})
        }
        Rule(color=p.ink,thickness=2.dp)
    }
}

@Composable fun TimeRuler(progress:Float,onSeek:(Float)->Unit,modifier:Modifier=Modifier,enabled:Boolean=true){
    val p=LocalTsunamiPalette.current
    val target=LocalControlTarget.current
    var focused by remember { mutableStateOf(false) }
    val gestures=if(enabled) Modifier
        .pointerInput(Unit){ detectTapGestures{ o->onSeek((o.x/size.width).coerceIn(0f,1f)) } }
        .pointerInput(Unit){ detectDragGestures(
            onDragStart={ o->onSeek((o.x/size.width).coerceIn(0f,1f)) },
            onDrag={ change,_->onSeek((change.position.x/size.width).coerceIn(0f,1f));change.consume() }
        ) } else Modifier
    Canvas(modifier.height(target).fillMaxWidth()
        .onFocusChanged{focused=it.isFocused}
        .focusable(enabled)
        .semantics{
            progressBarRangeInfo=ProgressBarRangeInfo(progress,0f..1f)
            if(enabled) setProgress { target -> onSeek(target.coerceIn(0f,1f)); true } else disabled()
        }
        .then(gestures)){
        val y=size.height*.5f
        drawLine(if(focused)p.selected else p.rule,Offset(0f,y),Offset(size.width,y),(if(focused)3.dp else 2.dp).toPx())
        drawLine(if(enabled)p.ink else p.ink3,Offset(0f,y),Offset(size.width*progress.coerceIn(0f,1f),y),(if(focused)4.dp else 3.dp).toPx())
        val px=size.width*progress.coerceIn(0f,1f)
        drawLine(if(enabled)p.selected else p.ink3,Offset(px,y-(if(focused)14.dp else 10.dp).toPx()),Offset(px,y+(if(focused)14.dp else 10.dp).toPx()),(if(focused)3.dp else 2.dp).toPx())
    }
}
