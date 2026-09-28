package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.semantics.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun FindScreen(state:ShellState){
    val p=LocalTsunamiPalette.current
    val q=state.searchQuery.trim()
    val downloadedIds=if(state.searchIntent==SearchIntent.DOWNLOADED) state.downloads.filterValues{it==DownloadState.DOWNLOADED}.keys.toSet() else emptySet()
    val results=remember(state.fixture.tracks,q,state.searchOwnedOnly,state.searchKind,state.searchIntent,downloadedIds){
        state.fixture.tracks
            .asSequence()
            .filter{!state.searchOwnedOnly || it.provenance==Provenance.OWNED}
            .filter{t->
                when(state.searchIntent){
                    SearchIntent.UNFINISHED -> t.longform
                    SearchIntent.DOWNLOADED -> t.id in downloadedIds
                    SearchIntent.CATALOGUE -> t.provenance==Provenance.CATALOGUE
                    SearchIntent.ARTISTS -> true
                    null -> when(state.searchKind){
                        SearchKind.ALL -> q.isEmpty()||fuzzyContains(t.title,q)||fuzzyContains(t.artist,q)||fuzzyContains(t.album,q)
                        SearchKind.TRACKS -> !t.longform && (q.isEmpty()||fuzzyContains(t.title,q))
                        SearchKind.ALBUMS -> q.isEmpty()||fuzzyContains(t.album,q)
                        SearchKind.ARTISTS -> q.isEmpty()||fuzzyContains(t.artist,q)
                        SearchKind.FOLDERS -> q.isEmpty()||fuzzyContains(folderFor(t),q)
                        SearchKind.LONGFORM -> t.longform && (q.isEmpty()||fuzzyContains(t.title,q)||fuzzyContains(t.artist,q)||fuzzyContains(t.album,q))
                    }
                }
            }
            .toList()
    }
    val rows=remember(results,state.searchKind){
        when(state.searchKind){
            SearchKind.ALBUMS -> results.distinctBy{it.album.lowercase()}
            SearchKind.ARTISTS -> results.distinctBy{it.artist.lowercase()}
            SearchKind.FOLDERS -> results.distinctBy{folderFor(it).lowercase()}
            else -> results
        }
    }
    state.findFocusedObject?.let{ obj ->
        FindObjectDetail(state,obj)
        return
    }
    Column(Modifier.fillMaxSize()){
        Text("FIND",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold));Spacer(Modifier.height(12.dp));UnderlineSearch(state.searchQuery,{state.clearSearchIntent();state.searchQuery=it},"Track, album, artist, folder…")
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
            listOf(SearchKind.ALL to "All",SearchKind.TRACKS to "Tracks",SearchKind.ALBUMS to "Albums",SearchKind.ARTISTS to "Artists",SearchKind.FOLDERS to "Folders",SearchKind.LONGFORM to "Longform").forEach{(kind,label)->TextCommand(label,{state.clearSearchIntent();state.searchKind=kind},state.searchIntent==null&&state.searchKind==kind)}
        }
        Rule()
        Row(Modifier.fillMaxWidth()){TextCommand("Any source",{state.searchOwnedOnly=false},!state.searchOwnedOnly,enabled=!state.offlineMode);TextCommand("Owned only",{state.searchOwnedOnly=true},state.searchOwnedOnly)}
        if(state.fixture.partial){
            Text("CONNECTED SOURCE DEGRADED · local and indexed results remain available",style=Type.micro.copy(color=p.possession,fontWeight=FontWeight.SemiBold),modifier=Modifier.padding(vertical=8.dp))
            Rule()
        }
        if(state.searchFault){
            Spacer(Modifier.height(28.dp))
            Text("Search source unavailable",style=Type.title.copy(color=p.ink))
            Spacer(Modifier.height(8.dp))
            Text("Your indexed library is intact. Connected search failed before results could be resolved.",style=Type.body.copy(color=p.ink2))
            Spacer(Modifier.height(16.dp))
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand("Retry",{state.retrySearch()})
                TextCommand("Owned only",{state.searchFault=false;state.searchOwnedOnly=true})
            }
            Spacer(Modifier.height(18.dp))
            Rule()
            Text("No query or selection was discarded.",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(vertical=12.dp))
        }else if(q.isEmpty() && state.searchIntent==null && state.searchKind==SearchKind.ALL){
            SectionHeader("Start with a task")
            listOf(
                Triple(SearchIntent.UNFINISHED,"Resume something unfinished","history · longform"),
                Triple(SearchIntent.DOWNLOADED,"Find downloaded music","offline · owned"),
                Triple(SearchIntent.CATALOGUE,"Browse connected catalogue","catalogue · source shown"),
                Triple(SearchIntent.ARTISTS,"Jump to an artist","library index")
            ).forEach{(intent,label,detail)->
                val enabled=!(state.offlineMode && intent==SearchIntent.CATALOGUE)
                var focused by remember(intent){ mutableStateOf(false) }
                Column(
                    Modifier.fillMaxWidth().heightIn(min=62.dp)
                        .semantics{role=Role.Button;contentDescription="$label. ${if(enabled)detail else "Unavailable while offline"}";if(!enabled)disabled()}
                        .onFocusChanged{focused=it.isFocused}
                        .clickable(enabled=enabled){state.chooseSearchIntent(intent)}
                        .background(if(focused&&enabled)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)
                        .padding(vertical=10.dp)
                ){
                    Row(verticalAlignment=androidx.compose.ui.Alignment.CenterVertically){
                        Box(Modifier.width(if(focused&&enabled)3.dp else 1.dp).height(28.dp).background(if(focused&&enabled)p.selected else androidx.compose.ui.graphics.Color.Transparent))
                        Spacer(Modifier.width(if(focused&&enabled)8.dp else 0.dp))
                        Column{
                            Text(label,style=Type.row.copy(color=if(enabled)p.ink else p.ink3.copy(alpha=.56f),fontWeight=if(focused&&enabled)FontWeight.SemiBold else FontWeight.Normal))
                            Text(if(enabled)detail else "unavailable while offline",style=Type.meta.copy(color=p.ink3))
                        }
                    }
                }
                Rule()
            }
            SectionHeader("Recent queries")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){listOf("Mira Sol","Night Trains","lossless","audiobook").forEach{s->TextCommand(s,{state.clearSearchIntent();state.searchQuery=s})}}
        }else{
            Row(Modifier.fillMaxWidth(),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically){
                Text("${rows.size} results",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(vertical=10.dp).weight(1f))
                state.searchIntent?.let{intent->TextCommand(when(intent){SearchIntent.UNFINISHED->"Unfinished";SearchIntent.DOWNLOADED->"Downloaded";SearchIntent.CATALOGUE->"Catalogue";SearchIntent.ARTISTS->"Artists"},{state.clearSearchIntent()},true)}
            };Rule()
            LazyColumn(Modifier.weight(1f).testTag("find-results-list")){
                val local=rows.filter{it.provenance!=Provenance.CATALOGUE}; if(local.isNotEmpty()){item{SectionHeader("Library")};local.forEach{t->item(t.id){TrackLedgerRow(t,when(state.searchKind){SearchKind.ALBUMS->"ALBUM MATCH · ${t.album}";SearchKind.ARTISTS->"ARTIST MATCH · ${t.artist}";SearchKind.FOLDERS->"FOLDER MATCH · ${folderFor(t)}";SearchKind.LONGFORM->"LONGFORM";else->if(t.provenance==Provenance.OWNED)"OWNED" else "CONNECTED LIBRARY"},{
                    when(state.searchKind){
                        SearchKind.ALBUMS -> state.findFocusedObject=LibraryObject(t.album,"Album","${t.artist} · ${results.count{it.album==t.album}} tracks")
                        SearchKind.ARTISTS -> state.findFocusedObject=LibraryObject(t.artist,"Artist","${results.count{it.artist==t.artist}} matching tracks")
                        SearchKind.FOLDERS -> {
                            val folder=folderFor(t)
                            state.findFocusedObject=LibraryObject(folder,"Folder","${results.count{folderFor(it)==folder}} matching tracks")
                        }
                        else -> {state.selectTrack(t,false);state.expandedPlayer=true}
                    }
                },{state.selectTrack(t,true)},{state.toggleFavourite(t.id)},{state.toggleDownload(t.id)},compact=true,forceMissing=state.fixture.missingArtwork,onPlayNext={state.playNext(t)},onShuffleNext={state.shuffleNext(t)},onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE)}}}
                val cat=rows.filter{it.provenance==Provenance.CATALOGUE}; if(cat.isNotEmpty()){item{SectionHeader("Catalogue")};cat.forEach{t->item("cat-${t.id}"){TrackLedgerRow(t,when(state.searchKind){SearchKind.ALBUMS->"CATALOGUE ALBUM · ${t.album}";SearchKind.ARTISTS->"CATALOGUE ARTIST · ${t.artist}";SearchKind.FOLDERS->"CATALOGUE FOLDER · ${folderFor(t)}";else->"CATALOGUE · resolves on play"},{
                    when(state.searchKind){
                        SearchKind.ALBUMS -> state.findFocusedObject=LibraryObject(t.album,"Catalogue album","${t.artist} · catalogue")
                        SearchKind.ARTISTS -> state.findFocusedObject=LibraryObject(t.artist,"Catalogue artist","Connected catalogue")
                        SearchKind.FOLDERS -> state.findFocusedObject=LibraryObject(folderFor(t),"Catalogue folder","Connected catalogue")
                        else -> state.banner="Opened catalogue release"
                    }
                },{state.selectTrack(t,true)},{state.toggleFavourite(t.id)},{state.toggleDownload(t.id)},compact=true,onPlayNext={state.playNext(t)},onShuffleNext={state.shuffleNext(t)},onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE)}}}
                if(rows.isEmpty())item{Spacer(Modifier.height(28.dp));Text("Nothing matched. Try fewer terms or another source.",style=Type.body.copy(color=p.ink2))}
            }
        }
    }
}


@Composable private fun FindObjectDetail(state:ShellState,obj:LibraryObject){
    val p=LocalTsunamiPalette.current
    val contents=when{
        obj.kind.contains("Album",ignoreCase=true) -> state.fixture.tracks.filter{it.album==obj.title}
        obj.kind.contains("Artist",ignoreCase=true) -> state.fixture.tracks.filter{it.artist==obj.title}
        obj.kind.contains("Folder",ignoreCase=true) -> state.fixture.tracks.filter{folderFor(it)==obj.title}
        else -> emptyList()
    }
    Column(Modifier.fillMaxSize()){
        Row(Modifier.fillMaxWidth().heightIn(min=58.dp),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically){
            HitIcon(Glyph.BACK,"Back to search results",{state.findFocusedObject=null})
            Spacer(Modifier.width(6.dp))
            Text("FIND / ${obj.kind.uppercase()}",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold))
        }
        Text(obj.title,style=Type.display.copy(color=p.ink),maxLines=3)
        Spacer(Modifier.height(5.dp))
        Text(obj.meta,style=Type.body.copy(color=p.ink2),maxLines=2)
        Spacer(Modifier.height(14.dp))
        contents.firstOrNull()?.let{first->
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand("Play",{state.selectTrack(first,true)})
                TextCommand("Play next",{state.playNext(first)})
                TextCommand("Shuffle next",{state.shuffleNext(first)})
            }
        }
        Rule()
        SectionHeader("Matches")
        if(contents.isEmpty()){
            Text("This connected object has no local tracks. Its source stays identified until playback starts.",style=Type.body.copy(color=p.ink2),modifier=Modifier.padding(vertical=18.dp))
        }else{
            LazyColumn(Modifier.weight(1f)){
                contents.forEach{t->item(t.id){
                    TrackLedgerRow(t,if(t.provenance==Provenance.CATALOGUE)"CATALOGUE" else "OWNED",onOpen={state.selectTrack(t,false);state.expandedPlayer=true},onPlay={state.selectTrack(t,true)},onFavourite={state.toggleFavourite(t.id)},onDownload={state.toggleDownload(t.id)},compact=true,forceMissing=state.fixture.missingArtwork,onPlayNext={state.playNext(t)},onShuffleNext={state.shuffleNext(t)},onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE)
                }}
            }
        }
    }
}


private fun folderFor(track:Track)=when{
    track.longform -> "/Audiobooks"
    track.provenance==Provenance.CATALOGUE -> "Connected catalogue"
    track.provenance==Provenance.CONNECTED -> "/Music/Connected"
    else -> "/Music/Library"
}


private fun fuzzyContains(text:String,query:String):Boolean{
    val needle=query.trim().lowercase()
    if(needle.isEmpty()) return true
    val hay=text.lowercase()
    if(hay.contains(needle)) return true
    if(needle.length<4) return false
    return hay.split(' ','/','·','—','-','_').asSequence()
        .map{it.trim('(',')','[',']',',','.','!','?',':',';','“','”','\'')}
        .filter{it.isNotEmpty() && kotlin.math.abs(it.length-needle.length)<=1}
        .any{withinOneEditOrTranspose(it,needle)}
}

private fun withinOneEditOrTranspose(a:String,b:String):Boolean{
    if(a==b) return true
    if(a.length==b.length){
        val diffs=a.indices.filter{a[it]!=b[it]}
        if(diffs.size==1) return true
        return diffs.size==2 && diffs[1]==diffs[0]+1 &&
            a[diffs[0]]==b[diffs[1]] && a[diffs[1]]==b[diffs[0]]
    }
    val short=if(a.length<b.length)a else b
    val long=if(a.length<b.length)b else a
    if(long.length-short.length!=1) return false
    var i=0;var j=0;var skipped=false
    while(i<short.length && j<long.length){
        if(short[i]==long[j]){i++;j++}
        else if(skipped)return false
        else{skipped=true;j++}
    }
    return true
}
