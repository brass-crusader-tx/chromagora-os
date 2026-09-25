package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.tsunami.shell.brand.TsunamiMark
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*
import kotlin.math.sin

@Composable fun ExpandedListening(state:ShellState,wide:Boolean,onBack:()->Unit){
    val p=LocalTsunamiPalette.current; val t=state.currentTrack
    if(t==null){Box(Modifier.fillMaxSize().background(p.ground),contentAlignment=Alignment.Center){Text("Nothing playing",style=Type.title.copy(color=p.ink))};return}
    val progress=(state.positionMs.toFloat()/t.durationMs.coerceAtLeast(1L)).coerceIn(0f,1f)
    Column(Modifier.fillMaxSize().background(p.ground).statusBarsPadding().navigationBarsPadding()){
        Row(Modifier.fillMaxWidth().height(64.dp).padding(horizontal=12.dp),verticalAlignment=Alignment.CenterVertically){HitIcon(Glyph.BACK,"Back",onBack);Spacer(Modifier.width(6.dp));Text("LISTENING",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold));Spacer(Modifier.weight(1f));Text(state.output,style=Type.meta.copy(color=p.ink2));HitIcon(Glyph.OUTPUT,"Output",{state.playerMode=PlayerMode.OUTPUT})};Rule()
        if(wide){Row(Modifier.weight(1f).padding(28.dp)){ListeningCore(state,t,progress,Modifier.weight(1f));Spacer(Modifier.width(32.dp));Box(Modifier.width(1.dp).fillMaxHeight().background(p.rule));Spacer(Modifier.width(32.dp));ListeningModePane(state,Modifier.weight(.9f))}}
        else{Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal=20.dp)){ListeningCore(state,t,progress,Modifier.fillMaxWidth());Spacer(Modifier.height(20.dp));Rule();ListeningModePane(state,Modifier.fillMaxWidth().height(360.dp))}}
        CompactTransport(state,t)
    }
}

@Composable private fun ListeningCore(state:ShellState,t:Track,progress:Float,modifier:Modifier){
    val p=LocalTsunamiPalette.current
    Column(modifier){
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.Bottom){
            if(state.showArtworkInPlayer){
                Artwork(t,Modifier.width(if(t.longform)110.dp else 132.dp).height(if(state.squareArtwork)(if(t.longform)110.dp else 132.dp) else (if(t.longform)82.dp else 98.dp)),state.fixture.missingArtwork)
            }else{
                Box(Modifier.size(if(t.longform)110.dp else 132.dp).background(p.groundAlt),contentAlignment=Alignment.Center){TsunamiMark(Modifier.fillMaxSize(.52f))}
            }
            Spacer(Modifier.width(18.dp))
            Column(Modifier.weight(1f)){
                Text(if(t.longform)"LONGFORM" else "NOW PLAYING",style=Type.micro.copy(color=p.ink3))
                Spacer(Modifier.height(4.dp))
                Text(when{!t.available->"UNAVAILABLE";state.buffering->"BUFFERING";state.playing->"PLAYING";else->"PAUSED"},style=Type.micro.copy(color=when{!t.available->p.danger;state.buffering->p.possession;else->p.ink3},fontWeight=FontWeight.SemiBold))
                Spacer(Modifier.height(8.dp))
                Text(t.title,style=(if(state.compactPlayerMetadata)Type.title else Type.display).copy(color=if(t.available)p.ink else p.ink3),maxLines=4,overflow=TextOverflow.Ellipsis)
                Spacer(Modifier.height(4.dp))
                Text(t.artist,style=Type.body.copy(color=p.ink2))
                if(t.longform){Spacer(Modifier.height(4.dp));Text(t.chapter?:"Chapter",style=Type.meta.copy(color=p.possession))}
            }
        }
        Spacer(Modifier.height(26.dp));TimeRuler(progress,state::seekFraction,enabled=t.available);Row(Modifier.fillMaxWidth()){Text(formatTime(state.positionMs),style=Type.numeric.copy(color=p.ink3));Spacer(Modifier.weight(1f));Text("−${formatTime((t.durationMs-state.positionMs).coerceAtLeast(0))}",style=Type.numeric.copy(color=p.ink3))}
        Spacer(Modifier.height(16.dp));Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(t.quality,style=Type.meta.copy(color=p.ink3));Text(if(state.downloads[t.id]==DownloadState.DOWNLOADED)"OFFLINE" else t.provenance.name,style=Type.micro.copy(color=if(state.downloads[t.id]==DownloadState.DOWNLOADED)p.possession else p.ink3))}
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
            TextCommand(if(t.id in state.favourites)"Favourite" else "Favourite",{state.toggleFavourite(t.id)},t.id in state.favourites)
            TextCommand(if(state.downloads[t.id]==DownloadState.DOWNLOADED)"Offline" else "Make offline",{state.toggleDownload(t.id)},state.downloads[t.id]==DownloadState.DOWNLOADED,enabled=t.available)
            TextCommand("Share ${formatTime(state.positionMs)}",{state.shareTimestamp()})
            TextCommand("Queue",{state.playerMode=PlayerMode.QUEUE},state.playerMode==PlayerMode.QUEUE)
        }
        if(t.longform){Spacer(Modifier.height(16.dp));Rule();Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){Text("Bookmark",style=Type.meta.copy(color=p.ink2),modifier=Modifier.weight(1f));Text(state.bookmarks[t.id]?.let{formatTime(it)}?:"None",style=Type.numeric.copy(color=p.ink3));if(state.bookmarks[t.id]!=null)HitIcon(Glyph.CLOSE,"Remove bookmark",{state.bookmarks.remove(t.id);state.banner="Bookmark removed"}) else HitIcon(Glyph.PLUS,"Add bookmark",{state.bookmarks[t.id]=state.positionMs;state.banner="Bookmark added"})}}
    }
}

@Composable private fun ModeSelector(state:ShellState){
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
        listOf(PlayerMode.QUEUE to "Queue",PlayerMode.LYRICS to "Lyrics",PlayerMode.OUTPUT to "Output",PlayerMode.VISUAL to "Visual").forEach{(m,label)->TextCommand(label,{state.playerMode=m},state.playerMode==m)}
        TextCommand(if(state.shuffle)"Shuffle on" else "Shuffle",{state.shuffle=!state.shuffle},state.shuffle)
        TextCommand("Repeat ${state.repeat.name.lowercase()}",{state.cycleRepeat()},state.repeat!=RepeatMode.OFF)
    }
}

@Composable private fun ListeningModePane(state:ShellState,modifier:Modifier){
    Column(modifier){
        ModeSelector(state)
        Rule()
        when(state.playerMode){
            PlayerMode.QUEUE -> LazyColumn(Modifier.fillMaxWidth().weight(1f)){itemsIndexed(state.queue,key={_,t->t.id}){i,t->QueueRow(state,i,t)}}
            PlayerMode.LYRICS -> LyricsPane(state,Modifier.fillMaxWidth().weight(1f))
            PlayerMode.OUTPUT -> OutputPane(state,Modifier.fillMaxWidth().weight(1f))
            PlayerMode.VISUAL -> VisualPane(state,Modifier.fillMaxWidth().weight(1f))
        }
    }
}

@Composable private fun QueueRow(state:ShellState,index:Int,t:Track){
    val p=LocalTsunamiPalette.current; val current=t.id==state.currentTrack?.id
    Row(Modifier.fillMaxWidth().heightIn(min=62.dp).clickable{state.selectTrack(t,true)}.padding(vertical=8.dp),verticalAlignment=Alignment.CenterVertically){
        Text((index+1).toString().padStart(2,'0'),style=Type.numeric.copy(color=if(current)p.selected else p.ink3),modifier=Modifier.width(34.dp));Column(Modifier.weight(1f)){Text(t.title,style=Type.row.copy(color=if(current)p.ink else p.ink2,fontWeight=if(current)FontWeight.SemiBold else FontWeight.Normal),maxLines=1);Text(t.artist,style=Type.meta.copy(color=p.ink3),maxLines=1)}
        if(index>0)HitIcon(Glyph.UP,"Move up",{state.moveQueue(index,index-1)})
        if(index<state.queue.lastIndex)HitIcon(Glyph.DOWN,"Move down",{state.moveQueue(index,index+1)})
        HitIcon(Glyph.CLOSE,"Remove",{state.removeFromQueue(index)})
    };Rule()
}

@Composable private fun LyricsPane(state:ShellState,modifier:Modifier){
    val p=LocalTsunamiPalette.current
    if(state.fixture.missingLyrics){
        Column(modifier.padding(vertical=24.dp)){
            Text("No timed lyrics",style=Type.title.copy(color=p.ink))
            Spacer(Modifier.height(8.dp))
            Text("TSUNAMI does not fabricate a karaoke layer. The listening environment remains complete without it.",style=Type.body.copy(color=p.ink2))
            Spacer(Modifier.height(12.dp))
            if(state.missingLyricsFallback) Text("Try metadata fallback",style=Type.meta.copy(color=p.selected),modifier=Modifier.heightIn(min=48.dp).clickable{state.banner="Mock lyric fallback checked"}.wrapContentHeight())
            else Text("Fallback disabled",style=Type.meta.copy(color=p.ink3))
        }
        return
    }
    val lines=listOf("Streetlights fold into the rain","Every window keeps a name","I was counting all the distance","You were listening for the change","Afterglow at the edge of the city","Hold the line until it fades","Nothing leaves without a shadow","Nothing stays the way it came")
    val delayed=(state.positionMs+state.lyricsGlobalDelayMs).coerceAtLeast(0L)
    val active=if(state.lyricsFollowPlayback)((delayed/32_000L).toInt()).coerceIn(0,lines.lastIndex) else 0
    Column(modifier){
        Row(Modifier.fillMaxWidth().heightIn(min=42.dp),verticalAlignment=Alignment.CenterVertically){
            Text(if(state.lyricsWordTiming)"WORD TIMING" else "LINE TIMING",style=Type.micro.copy(color=p.ink3),modifier=Modifier.weight(1f))
            Text(if(state.lyricsGlobalDelayMs==0)"0 ms" else "${state.lyricsGlobalDelayMs} ms",style=Type.numeric.copy(color=p.ink3))
        }
        Rule()
        if(state.visualizerBehindLyrics){
            Canvas(Modifier.fillMaxWidth().height(36.dp)){
                val n=22;val gap=size.width/n
                for(i in 0 until n){val amp=.25f+.55f*((sin((i*.71+state.positionMs/3600f).toDouble()).toFloat()+1f)/2f);drawLine(p.ink3,androidx.compose.ui.geometry.Offset(i*gap,size.height/2-size.height*amp/2),androidx.compose.ui.geometry.Offset(i*gap,size.height/2+size.height*amp/2),1.dp.toPx())}
            }
        }
        LazyColumn(Modifier.fillMaxWidth().weight(1f)){
            itemsIndexed(lines){i,line->
                val activeStyle=if(i==active)Type.title else Type.body
                val shown=if(i==active && state.lyricsWordTiming) line.split(" ").joinToString(" · ") else line
                Text(shown,style=activeStyle.copy(color=when{i==active->p.ink;i<active->p.ink3;else->p.ink2}),modifier=Modifier.fillMaxWidth().heightIn(min=58.dp).clickable{state.positionMs=(i*32_000L-state.lyricsGlobalDelayMs).coerceAtLeast(0L)}.wrapContentHeight(Alignment.CenterVertically))
            }
        }
    }
}
@Composable private fun OutputPane(state:ShellState,modifier:Modifier){
    val p=LocalTsunamiPalette.current
    Column(modifier){listOf("This device" to "AudioTrack · 96 kHz", "Sony WH-1000X" to "Bluetooth · connected", "Living room" to "Cast · available").forEach{(name,detail)->val active=state.output==name;Row(Modifier.fillMaxWidth().heightIn(min=70.dp).clickable{state.output=name;state.banner="Output: $name"}.padding(vertical=10.dp),verticalAlignment=Alignment.CenterVertically){Box(Modifier.width(if(active)3.dp else 1.dp).height(26.dp).background(if(active)p.selected else p.rule));Spacer(Modifier.width(12.dp));Column(Modifier.weight(1f)){Text(name,style=Type.row.copy(color=p.ink));Text(detail,style=Type.meta.copy(color=p.ink3))};Text(if(active)"ACTIVE" else "",style=Type.micro.copy(color=p.selected))};Rule()}}
}

@Composable private fun VisualPane(state:ShellState,modifier:Modifier){
    val p=LocalTsunamiPalette.current
    val signalColor=if(state.visualizerMonochrome)p.ink else p.selected
    Column(modifier.padding(vertical=18.dp)){
        Text("${state.visualizerMode} · ${state.visualizerSensitivity}× sensitivity · ${if(state.reducedMotion)"motion held" else "playback motion"}",style=Type.meta.copy(color=p.ink3))
        Spacer(Modifier.height(18.dp))
        Canvas(Modifier.fillMaxWidth().height(180.dp)){
            val phaseOffset=if(state.reducedMotion)0f else state.positionMs/2800f
            when(state.visualizerMode){
                "Line" -> {
                    val n=36
                    val gap=size.width/(n-1)
                    var last=androidx.compose.ui.geometry.Offset(0f,size.height/2)
                    for(i in 0 until n){
                        val phase=i*.47f+phaseOffset
                        val raw=(sin(phase.toDouble()).toFloat()+1f)/2f
                        val amp=((raw-.5f)*state.visualizerSensitivity).coerceIn(-.5f,.5f)
                        val point=androidx.compose.ui.geometry.Offset(i*gap,size.height/2-amp*size.height*.78f)
                        if(i>0)drawLine(signalColor,last,point,2.dp.toPx(),StrokeCap.Square)
                        last=point
                    }
                }
                "Field" -> {
                    val n=18
                    val gap=size.width/n
                    for(i in 0 until n){
                        val phase=i*.68f+phaseOffset
                        val raw=(sin(phase.toDouble()).toFloat()+1f)/2f
                        val amp=(.14f+raw*.62f*state.visualizerSensitivity).coerceIn(.12f,.92f)
                        val h=size.height*amp
                        val x=i*gap+gap/2
                        drawLine(if(i%4==0)signalColor else p.ink2,androidx.compose.ui.geometry.Offset(x,size.height-h),androidx.compose.ui.geometry.Offset(x,size.height),gap*.34f,StrokeCap.Square)
                    }
                }
                else -> {
                    val n=28
                    val gap=size.width/n
                    for(i in 0 until n){
                        val phase=i*.55f+phaseOffset
                        val raw=(sin(phase.toDouble()).toFloat()+1f)/2f
                        val amp=(.16f+.62f*raw*state.visualizerSensitivity).coerceIn(.12f,.94f)
                        val h=size.height*amp
                        drawLine(if(i%5==0)signalColor else p.ink2,androidx.compose.ui.geometry.Offset(i*gap+gap/2,size.height/2-h/2),androidx.compose.ui.geometry.Offset(i*gap+gap/2,size.height/2+h/2),gap*.28f,StrokeCap.Square)
                    }
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        Text("Generated from deterministic mock state · not signal telemetry",style=Type.micro.copy(color=p.ink3))
    }
}

@Composable private fun CompactTransport(state:ShellState,t:Track){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxWidth().background(p.groundAlt)){
        Rule()
        Row(
            Modifier.fillMaxWidth().heightIn(min=78.dp).padding(horizontal=14.dp),
            verticalAlignment=Alignment.CenterVertically,
            horizontalArrangement=if(state.oneHandedNowPlaying) Arrangement.End else Arrangement.SpaceBetween
        ){
            if(!state.oneHandedNowPlaying) HitIcon(Glyph.SHUFFLE,if(state.shuffle)"Shuffle on" else "Shuffle off",{state.shuffle=!state.shuffle},state.shuffle)
            HitIcon(Glyph.PREVIOUS,"Previous",state::previous)
            Box(
                Modifier.size(58.dp)
                    .semantics{role=androidx.compose.ui.semantics.Role.Button;contentDescription=when{state.buffering->"Finish mock buffering";!t.available->"${t.title} unavailable";state.playing->"Pause";else->"Play"};if(!t.available)disabled()}
                    .clickable(enabled=t.available,onClick=state::togglePlayback),
                contentAlignment=Alignment.Center
            ){GlyphIcon(if(state.playing && !state.buffering)Glyph.PAUSE else Glyph.PLAY,Modifier.size(31.dp),if(t.available)p.ink else p.ink3)}
            HitIcon(Glyph.NEXT,"Next",state::next)
            HitIcon(Glyph.REPEAT,"Repeat ${state.repeat.name.lowercase()}",state::cycleRepeat,state.repeat!=RepeatMode.OFF)
            if(state.oneHandedNowPlaying) HitIcon(Glyph.SHUFFLE,"Shuffle",{state.shuffle=!state.shuffle},state.shuffle)
        }
        if(state.quickActions.isNotEmpty()){
            Rule()
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal=10.dp)){
                state.quickActions.forEach{label->
                    TextCommand(label,{invokeQuickAction(state,label,t)},quickActionSelected(state,label,t))
                }
                TextCommand(if(state.sleepMinutes==0)"Sleep" else "${state.sleepMinutes} min",{state.cycleSleep()},state.sleepMinutes>0)
            }
        }
    }
}

private fun invokeQuickAction(state:ShellState,label:String,t:Track){
    when(label){
        "Favourite" -> state.toggleFavourite(t.id)
        "Lyrics" -> state.playerMode=PlayerMode.LYRICS
        "Output" -> state.playerMode=PlayerMode.OUTPUT
        "Sleep timer" -> state.cycleSleep()
        "Bookmark" -> if(t.longform){
            if(state.bookmarks[t.id]!=null) state.bookmarks.remove(t.id) else state.bookmarks[t.id]=state.positionMs
            state.banner=if(state.bookmarks[t.id]!=null)"Bookmark added" else "Bookmark removed"
        } else state.banner="Bookmarks are available for longform"
        "Shuffle" -> state.shuffle=!state.shuffle
        else -> state.banner="$label ready"
    }
}

private fun quickActionSelected(state:ShellState,label:String,t:Track)=when(label){
    "Favourite" -> t.id in state.favourites
    "Lyrics" -> state.playerMode==PlayerMode.LYRICS
    "Output" -> state.playerMode==PlayerMode.OUTPUT
    "Sleep timer" -> state.sleepMinutes>0
    "Bookmark" -> state.bookmarks[t.id]!=null
    "Shuffle" -> state.shuffle
    else -> false
}
