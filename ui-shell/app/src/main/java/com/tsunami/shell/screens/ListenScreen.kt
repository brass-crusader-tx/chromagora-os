package com.tsunami.shell.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun ListenScreen(state:ShellState,scenario:String){
    val p=LocalTsunamiPalette.current
    if(state.loading) LaunchedEffect("loading-resolve"){ delay(2200); state.loading=false; state.banner="Listening context ready" }

    val resumeTracks=remember(state.currentTrack?.id,state.fixture.tracks){
        buildList {
            state.currentTrack?.let{add(it)}
            state.fixture.tracks.filterNot{it.id==state.currentTrack?.id}.take(2).forEach{add(it)}
        }
    }
    val resumeIds=resumeTracks.map{it.id}.toSet()
    val pinned=state.fixture.tracks.filter{it.id in state.favourites && it.id !in resumeIds}.take(4)

    LazyColumn(Modifier.fillMaxSize().testTag("listen-list"),contentPadding=PaddingValues(bottom=24.dp)){
        item {
            Text("LISTEN",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold))
            Spacer(Modifier.height(10.dp))
            Text("Your listening line",style=Type.display.copy(color=p.ink))
            Spacer(Modifier.height(10.dp))
            Text("Playback context first; deliberate choice follows it.",style=Type.body.copy(color=p.ink2))
            Spacer(Modifier.height(18.dp))
            Rule()
        }
        if(state.loading){
            item{
                Spacer(Modifier.height(28.dp))
                Text("Reconstructing the listening context…",style=Type.body.copy(color=p.ink2))
                Spacer(Modifier.height(14.dp))
                Rule(color=p.selected,thickness=2.dp)
            }
            return@LazyColumn
        }
        if(state.sourceError){
            item{
                ListeningBandHeader("RECOVERY","INDEX")
                Text("The library index could not be read. Playback state is preserved.",style=Type.body.copy(color=p.danger),modifier=Modifier.padding(vertical=10.dp))
                TextCommand("Retry",{state.sourceError=false;state.diagnosticsFault=false;state.banner="Index recovered"})
            }
        }
        if(state.fixture.empty){
            item{
                ListeningBandHeader("LIBRARY","EMPTY")
                Text("No music is indexed yet.",style=Type.title.copy(color=p.ink),modifier=Modifier.padding(top=12.dp))
                Spacer(Modifier.height(6.dp))
                Text("Add a music folder or connect a service to begin.",style=Type.body.copy(color=p.ink2))
                Spacer(Modifier.height(12.dp))
                Row{
                    TextCommand("Add folder",{state.banner="Folder chooser opened"})
                    TextCommand("Connect service",{state.settingsExpanded="services"})
                }
            }
            return@LazyColumn
        }

        item{ ListeningBandHeader("CURRENT THREAD","TIME") }
        resumeTracks.forEachIndexed{index,t->
            item(key="resume-${t.id}"){
                TemporalTrackRow(
                    marker=when(index){0->"NOW";1->"−1D";else->"−2D"},
                    track=t,
                    stateLabel=if(index==0)"${formatTime(state.positionMs)} of ${formatTime(t.durationMs)}" else "Last heard ${index} day${if(index==1)"" else "s"} ago",
                    state=state,
                    forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",
                )
            }
        }

        if(pinned.isNotEmpty()){
            item{ ListeningBandHeader("OWNED ANCHORS","PINNED") }
            pinned.forEach{t->
                item(key="fav-${t.id}"){
                    TemporalTrackRow(
                        marker="PIN",
                        track=t,
                        stateLabel="FAVOURITE · ${t.year}",
                        state=state,
                        forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",
                    )
                }
            }
        }

        item{
            ListeningBandHeader("LIBRARY LENS","CHOOSE")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                listOf("Deep cuts","Rediscover","Never heard","Most played","Unfinished").forEach{lens->
                    TextCommand(lens,{state.listenLens=lens},state.listenLens==lens)
                }
            }
            Rule()
        }
        listenLensTracks(state).filterNot{it.id in resumeIds}.take(5).forEachIndexed{index,t->
            item(key="lens-${state.listenLens}-${t.id}"){
                TemporalTrackRow(
                    marker=(index+1).toString().padStart(2,'0'),
                    track=t,
                    stateLabel="${state.listenLens.uppercase()} · ${t.year}",
                    state=state,
                    forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",
                )
            }
        }
    }
}

@Composable private fun ListeningBandHeader(label:String,indexLabel:String){
    val p=LocalTsunamiPalette.current
    Row(Modifier.fillMaxWidth().padding(top=20.dp,bottom=8.dp),verticalAlignment=Alignment.Bottom){
        Text(indexLabel,style=Type.micro.copy(color=p.selected,fontWeight=FontWeight.SemiBold),modifier=Modifier.width(50.dp))
        Box(Modifier.width(1.dp).height(18.dp).background(p.rule))
        Spacer(Modifier.width(12.dp))
        Text(label,style=Type.micro.copy(color=p.ink2,fontWeight=FontWeight.SemiBold))
    }
    Rule()
}

@Composable private fun TemporalTrackRow(marker:String,track:Track,stateLabel:String,state:ShellState,forceMissing:Boolean){
    val p=LocalTsunamiPalette.current
    Row(Modifier.fillMaxWidth().then(if(marker=="NOW") Modifier.testTag("listen-current-${track.id}") else Modifier),verticalAlignment=Alignment.Top){
        Column(Modifier.width(50.dp).padding(top=14.dp),horizontalAlignment=Alignment.Start){
            Text(marker,style=Type.numeric.copy(color=if(marker=="NOW")p.selected else p.ink3,fontWeight=if(marker=="NOW")FontWeight.SemiBold else FontWeight.Medium))
        }
        Box(Modifier.width(1.dp).heightIn(min=64.dp).background(if(marker=="NOW")p.selected else p.rule))
        Spacer(Modifier.width(12.dp))
        Box(Modifier.weight(1f)){
            TrackLedgerRow(
                track,
                stateLabel,
                onOpen={state.selectTrack(track,false);state.expandedPlayer=true},
                onPlay={state.selectTrack(track,true)},
                onFavourite={state.toggleFavourite(track.id)},
                onDownload={state.toggleDownload(track.id)},
                compact=true,
                forceMissing=forceMissing,
                onPlayNext={state.playNext(track)},
                onShuffleNext={state.shuffleNext(track)},
                onAddToPlaylist={state.addToPlaylist(track)},
                downloadState=state.downloads[track.id]?:DownloadState.REMOTE,
                showArtwork=false,
            )
        }
    }
}

private fun listenLensTracks(state:ShellState):List<Track>{
    val music=state.fixture.tracks.filterNot{it.longform}
    return when(state.listenLens){
        "Rediscover" -> music.sortedBy{it.year}.take(8)
        "Never heard" -> music.filter{it.id !in state.favourites}.reversed()
        "Most played" -> music.sortedByDescending{it.id.length*17 + it.year%11}
        "Unfinished" -> state.fixture.tracks.filter{it.longform}
        else -> music.filterIndexed{index,_->index%2==1}.ifEmpty{music}
    }
}
