package com.tsunami.shell.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
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
    LazyColumn(Modifier.fillMaxSize(),contentPadding=PaddingValues(bottom=24.dp)){
        item {
            Text("LISTEN",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold));Spacer(Modifier.height(10.dp))
            Text("Your listening line",style=Type.display.copy(color=p.ink));Spacer(Modifier.height(10.dp))
            Text("Continue where you left off, or move through your library.",style=Type.body.copy(color=p.ink2));Spacer(Modifier.height(18.dp));Rule()
        }
        if(state.loading){ item{ Spacer(Modifier.height(28.dp));Text("Reconstructing the listening context…",style=Type.body.copy(color=p.ink2));Spacer(Modifier.height(14.dp));Rule(color=p.selected,thickness=2.dp) };return@LazyColumn }
        if(state.sourceError){ item{ SectionHeader("Recovery");Text("The library index could not be read. Playback state is preserved.",style=Type.body.copy(color=p.danger));TextCommand("Retry",{state.sourceError=false;state.diagnosticsFault=false;state.banner="Index recovered"}); } }
        if(state.fixture.empty){ item{ SectionHeader("Library");Text("No music is indexed yet.",style=Type.title.copy(color=p.ink));Spacer(Modifier.height(6.dp));Text("Add a music folder or connect a service to begin.",style=Type.body.copy(color=p.ink2));Spacer(Modifier.height(12.dp));Row{TextCommand("Add folder",{state.banner="Folder chooser opened"});TextCommand("Connect service",{state.settingsExpanded="services"})} } ;return@LazyColumn }
        item{SectionHeader("Resume")}
        state.fixture.tracks.take(3).forEachIndexed{index,t-> item(key=t.id){ TrackLedgerRow(t,if(index==0)"${formatTime(state.positionMs)} of ${formatTime(t.durationMs)}" else "Played ${index+1} days ago",onOpen={state.selectTrack(t,false);state.expandedPlayer=true},onPlay={state.selectTrack(t,true)},onFavourite={state.toggleFavourite(t.id)},onDownload={state.toggleDownload(t.id)},forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",onPlayNext={state.playNext(t)},onShuffleNext={state.shuffleNext(t)},onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE) } }
        item{SectionHeader("Pinned to your library")}
        state.fixture.tracks.filter{it.id in state.favourites}.take(4).forEach{t-> item(key="fav-${t.id}"){TrackLedgerRow(t,"FAVOURITE · ${t.year}",onOpen={state.selectTrack(t,false);state.expandedPlayer=true},onPlay={state.selectTrack(t,true)},onFavourite={state.toggleFavourite(t.id)},onDownload={state.toggleDownload(t.id)},compact=true,forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",onPlayNext={state.playNext(t)},onShuffleNext={state.shuffleNext(t)},onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE)} }
        item{
            SectionHeader("Choose from your library")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                listOf("Deep cuts","Rediscover","Never heard","Most played","Unfinished").forEach{lens->
                    TextCommand(lens,{state.listenLens=lens},state.listenLens==lens)
                }
            }
            Rule()
        }
        listenLensTracks(state).take(5).forEach{t-> item(key="lens-${state.listenLens}-${t.id}"){
            TrackLedgerRow(
                t,
                "${state.listenLens.uppercase()} · ${t.year}",
                onOpen={state.selectTrack(t,false);state.expandedPlayer=true},
                onPlay={state.selectTrack(t,true)},
                onFavourite={state.toggleFavourite(t.id)},
                onDownload={state.toggleDownload(t.id)},
                compact=true,
                forceMissing=state.fixture.missingArtwork||scenario=="no-artwork",
                onPlayNext={state.playNext(t)},
                onShuffleNext={state.shuffleNext(t)},
                onAddToPlaylist={state.addToPlaylist(t)},
                downloadState=state.downloads[t.id]?:DownloadState.REMOTE
            )
        } }
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
