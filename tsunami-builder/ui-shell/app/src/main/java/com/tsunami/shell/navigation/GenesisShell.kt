package com.tsunami.shell.navigation

import androidx.activity.compose.BackHandler
import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.tsunami.shell.brand.TsunamiMark
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.screens.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun GenesisShell(state:ShellState,scenario:String){
    val p=LocalTsunamiPalette.current
    BackHandler(enabled=state.primary==PrimarySpace.LIBRARY && state.focusedObject!=null){ state.focusedObject=null }
    BackHandler(enabled=state.primary==PrimarySpace.FIND && state.findFocusedObject!=null){ state.findFocusedObject=null }
    BackHandler(enabled=state.expandedPlayer){ state.expandedPlayer=false }
    BackHandler(enabled=state.settingsExpanded!=null){ if(state.settingsExpanded=="root")state.settingsExpanded=null else state.settingsExpanded="root" }
    BoxWithConstraints(Modifier.fillMaxSize().background(p.ground)){
        val expanded=maxWidth>=840.dp && maxHeight>=600.dp
        val medium=maxWidth>=600.dp && maxHeight>=480.dp
        if(state.expandedPlayer){ ExpandedListening(state,expanded) { state.expandedPlayer=false }; return@BoxWithConstraints }
        if(scenario=="onboarding" && !state.onboardingComplete){ OnboardingScreen(state); return@BoxWithConstraints }
        if(expanded){
            Row(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()){
                IndexRail(state,Modifier.width(138.dp).fillMaxHeight())
                Box(Modifier.width(1.dp).fillMaxHeight().background(p.rule))
                Workspace(state,scenario,Modifier.weight(1f).fillMaxHeight(),wide=true)
                Box(Modifier.width(1.dp).fillMaxHeight().background(p.rule))
                ListeningSpine(state,Modifier.width(296.dp).fillMaxHeight(),vertical=true)
            }
        }else if(medium){
            Row(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()){
                IndexRail(state,Modifier.width(124.dp).fillMaxHeight())
                Box(Modifier.width(1.dp).fillMaxHeight().background(p.rule))
                Column(Modifier.weight(1f).fillMaxHeight()){
                    Workspace(state,scenario,Modifier.weight(1f),wide=true)
                    ListeningSpine(state,Modifier.fillMaxWidth(),vertical=false)
                }
            }
        }else{
            Column(Modifier.fillMaxSize()){
                Workspace(state,scenario,Modifier.weight(1f).statusBarsPadding(),wide=false)
                ListeningSpine(state,Modifier.fillMaxWidth(),vertical=false)
                IndexStrip(state)
            }
        }
        if(state.settingsExpanded!=null) SettingsOverlay(state,{state.settingsExpanded=null})
        state.banner?.let { msg ->
            Box(Modifier.align(Alignment.TopCenter).padding(top=18.dp).background(p.ink).semantics{contentDescription="Dismiss message";role=Role.Button}.clickable{state.banner=null}.padding(horizontal=16.dp,vertical=10.dp)){ Text(msg,style=Type.meta.copy(color=p.inverse)) }
        }
    }
}

@Composable private fun Workspace(state:ShellState,scenario:String,modifier:Modifier,wide:Boolean){
    Box(modifier.padding(horizontal=if(wide)32.dp else 20.dp,vertical=16.dp)){
        if(state.reducedMotion){
            WorkspaceContent(state.primary,state,scenario)
        }else{
            AnimatedContent(
                targetState=state.primary,
                transitionSpec={
                    val order=listOf(PrimarySpace.LISTEN,PrimarySpace.LIBRARY,PrimarySpace.FIND,PrimarySpace.SIGNAL)
                    val direction=if(order.indexOf(targetState)>=order.indexOf(initialState)) 1 else -1
                    (slideInHorizontally(tween(160)){direction*(it/5)}+fadeIn(tween(120))) togetherWith
                        (slideOutHorizontally(tween(140)){-direction*(it/5)}+fadeOut(tween(100)))
                },
                label="primary-workspace"
            ){space->WorkspaceContent(space,state,scenario)}
        }
    }
}

@Composable private fun WorkspaceContent(space:PrimarySpace,state:ShellState,scenario:String){
    when(space){
        PrimarySpace.LISTEN -> ListenScreen(state,scenario)
        PrimarySpace.LIBRARY -> LibraryScreen(state)
        PrimarySpace.FIND -> FindScreen(state)
        PrimarySpace.SIGNAL -> SignalScreen(state)
    }
}

private val nav=listOf(PrimarySpace.LISTEN to "Listen",PrimarySpace.LIBRARY to "Library",PrimarySpace.FIND to "Find",PrimarySpace.SIGNAL to "Signal")

@Composable private fun IndexRail(state:ShellState,modifier:Modifier){
    val p=LocalTsunamiPalette.current
    Column(modifier.padding(horizontal=18.dp,vertical=20.dp)){
        TsunamiMark(Modifier.width(44.dp).height(38.dp)); Spacer(Modifier.height(42.dp))
        nav.forEach{(space,label)->
            val active=state.primary==space
            Row(Modifier.fillMaxWidth().heightIn(min=58.dp).semantics{role=Role.Tab;if(active) stateDescription="Selected"}.clickable{state.primary=space},verticalAlignment=Alignment.CenterVertically){
                Box(Modifier.width(if(active)3.dp else 1.dp).height(26.dp).background(if(active)p.selected else p.rule)); Spacer(Modifier.width(12.dp));
                Text(label,style=Type.body.copy(color=if(active)p.ink else p.ink2,fontWeight=if(active)FontWeight.SemiBold else FontWeight.Normal))
            }
        }
        Spacer(Modifier.weight(1f));
        Text("Settings",style=Type.meta.copy(color=p.ink2),modifier=Modifier.fillMaxWidth().heightIn(min=48.dp).clickable{state.settingsExpanded="root"}.wrapContentHeight(Alignment.CenterVertically))
    }
}

@Composable private fun IndexStrip(state:ShellState){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxWidth().background(p.ground)){
        Rule(); Row(Modifier.fillMaxWidth().navigationBarsPadding()){
            nav.forEach{(space,label)->
                val active=state.primary==space
                Column(Modifier.weight(1f).height(58.dp).clickable{state.primary=space},horizontalAlignment=Alignment.CenterHorizontally,verticalArrangement=Arrangement.Center){
                    Box(Modifier.width(if(active)26.dp else 10.dp).height(if(active)2.dp else 1.dp).background(if(active)p.selected else Color.Transparent)); Spacer(Modifier.height(6.dp));
                    Text(label,style=Type.micro.copy(color=if(active)p.ink else p.ink3,fontWeight=if(active)FontWeight.SemiBold else FontWeight.Normal))
                }
            }
            Box(Modifier.width(54.dp).height(58.dp).semantics{contentDescription="Settings";role=Role.Button}.clickable{state.settingsExpanded="root"},contentAlignment=Alignment.Center){GlyphIcon(Glyph.SETTINGS,Modifier.size(18.dp),p.ink3)}
        }
    }
}

@Composable fun ListeningSpine(state:ShellState,modifier:Modifier,vertical:Boolean){
    val p=LocalTsunamiPalette.current; val t=state.currentTrack
    if(t==null){ Box(modifier.padding(18.dp)){Text("Nothing playing",style=Type.meta.copy(color=p.ink3))};return }
    val progress=(state.positionMs.toFloat()/t.durationMs.coerceAtLeast(1)).coerceIn(0f,1f)
    val transportGlyph=if(state.playing && !state.buffering)Glyph.PAUSE else Glyph.PLAY
    val transportLabel=when{state.buffering->"Finish mock buffering";!t.available->"${t.title} unavailable";state.playing->"Pause";else->"Play"}
    val statusLabel=when{!t.available->"UNAVAILABLE";state.buffering->"BUFFERING";state.playing->"PLAYING";else->"PAUSED"}
    if(vertical){
        Column(modifier.padding(22.dp)){
            Text("LISTENING",style=Type.micro.copy(color=p.ink3)); Spacer(Modifier.height(26.dp)); Artwork(t,Modifier.fillMaxWidth().aspectRatio(1f),state.fixture.missingArtwork); Spacer(Modifier.height(20.dp))
            Text(t.title,style=Type.title.copy(color=if(t.available)p.ink else p.ink3),maxLines=3); Spacer(Modifier.height(4.dp)); Text(t.artist,style=Type.body.copy(color=p.ink2)); Spacer(Modifier.height(4.dp)); Text(statusLabel,style=Type.micro.copy(color=if(!t.available)p.danger else if(state.buffering)p.possession else p.ink3,fontWeight=FontWeight.SemiBold)); Spacer(Modifier.height(14.dp));
            TimeRuler(progress,state::seekFraction); Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text(formatTime(state.positionMs),style=Type.numeric.copy(color=p.ink3));Text(formatTime(t.durationMs),style=Type.numeric.copy(color=p.ink3))}
            Spacer(Modifier.height(16.dp)); Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly){HitIcon(Glyph.PREVIOUS,"Previous",state::previous);HitIcon(transportGlyph,transportLabel,state::togglePlayback,enabled=t.available);HitIcon(Glyph.NEXT,"Next",state::next)}
            Spacer(Modifier.height(10.dp)); Text("Open listening environment",style=Type.meta.copy(color=p.selected),modifier=Modifier.fillMaxWidth().heightIn(min=48.dp).clickable{state.expandedPlayer=true}.wrapContentHeight(Alignment.CenterVertically)); Spacer(Modifier.weight(1f)); Rule(); Spacer(Modifier.height(14.dp)); Text("${t.quality}\n${state.output}",style=Type.micro.copy(color=p.ink3))
        }
    }else{
        Column(modifier.background(p.groundAlt)){
            Box(Modifier.fillMaxWidth().height(2.dp).background(p.rule)){
                Box(Modifier.fillMaxWidth(progress).fillMaxHeight().background(p.selected))
            }
            Row(
                Modifier.fillMaxWidth().heightIn(min=78.dp)
                    .semantics { contentDescription = "Open listening environment" }
                    .clickable{state.expandedPlayer=true}
                    .padding(horizontal=16.dp),
                verticalAlignment=Alignment.CenterVertically
            ){
                Box(Modifier.width(3.dp).height(44.dp).background(when{!t.available->p.danger;state.buffering->p.possession;state.playing->p.selected;else->p.rule}))
                Spacer(Modifier.width(11.dp))
                Column(Modifier.width(54.dp)){
                    Text(formatTime(state.positionMs),style=Type.numeric.copy(color=p.ink))
                    Text(formatTime(t.durationMs),style=Type.micro.copy(color=p.ink3))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)){
                    Text("LISTENING · $statusLabel",style=Type.micro.copy(color=if(!t.available)p.danger else if(state.buffering)p.possession else p.ink3,fontWeight=FontWeight.SemiBold))
                    Text(t.title,style=Type.row.copy(color=if(t.available)p.ink else p.ink3),maxLines=1)
                    Text(t.artist,style=Type.meta.copy(color=p.ink2),maxLines=1)
                }
                HitIcon(transportGlyph,transportLabel,state::togglePlayback,enabled=t.available)
                HitIcon(Glyph.NEXT,"Next",state::next)
            }
        }
    }
}
