package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun LibraryScreen(state:ShellState){
    val p=LocalTsunamiPalette.current
    val lenses=state.librarySectionOrder.mapNotNull{label->
        val lens=when(label){
            "Tracks"->LibraryLens.TRACKS
            "Albums"->LibraryLens.ALBUMS
            "Artists"->LibraryLens.ARTISTS
            "Playlists"->LibraryLens.PLAYLISTS
            "Folders"->LibraryLens.FOLDERS
            "Longform"->LibraryLens.LONGFORM
            "Radio"->LibraryLens.RADIO
            else->null
        }
        lens?.let{it to label}
    }.filterNot{it.second in state.hiddenLibrarySections}
    val offlineIds=if(state.offlineOnly) state.downloads.filterValues{it==DownloadState.DOWNLOADED}.keys.toSet() else emptySet()
    val filtered=remember(state.fixture.tracks,state.offlineOnly,offlineIds){
        if(!state.offlineOnly) state.fixture.tracks else state.fixture.tracks.filter{it.id in offlineIds}
    }
    val ordered=remember(filtered,state.sortLabel){ if(state.sortLabel=="Title A–Z") filtered.sortedBy{it.title.lowercase()} else filtered }
    val folderRows=remember(ordered){
        val groups=ordered.filter{it.provenance==Provenance.OWNED}.groupBy(::libraryFolderFor)
        listOf("/Music/Library","/Music/Field Recordings","/Audiobooks").map{name->
            val items=groups[name].orEmpty()
            val noun=if(name=="/Audiobooks") if(items.size==1)"book" else "books" else if(items.size==1)"track" else "tracks"
            Triple(name,"Folder","${items.size} $noun")
        }
    }
    val listState=rememberLazyListState()
    val scope=rememberCoroutineScope()
    val focused=state.focusedObject
    if(focused!=null){
        LibraryObjectDetail(state,focused,filtered)
        return
    }
    Column(Modifier.fillMaxSize()){
        Text("LIBRARY",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold));Spacer(Modifier.height(8.dp));
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text("${state.fixture.libraryCount}",style=Type.display.copy(color=p.ink));Text("owned + indexed",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(top=12.dp))};Spacer(Modifier.height(10.dp));Rule()
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){lenses.forEach{(lens,label)->TextCommand(label,{if(state.libraryLens!=lens){state.clearSelection();state.libraryLens=lens}},state.libraryLens==lens)}}
        Rule()
        Row(Modifier.fillMaxWidth(),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically){
            TextCommand(state.sortLabel,{state.sortLabel=if(state.sortLabel=="Recently played")"Title A–Z" else "Recently played"},true)
            TextCommand("Offline",{state.offlineOnly=!state.offlineOnly},state.offlineOnly)
            TextCommand("Ledger",{state.libraryViewMode="Ledger";state.banner="Library view · Ledger"},state.libraryViewMode=="Ledger")
            TextCommand("Index",{state.libraryViewMode="Index";state.sortLabel="Title A–Z";state.banner="Library view · Index"},state.libraryViewMode=="Index")
            TextCommand(if(state.denseLibrary)"Comfortable" else "Dense",{state.denseLibrary=!state.denseLibrary},state.denseLibrary)
            if(state.libraryLens==LibraryLens.TRACKS) TextCommand(if(state.selectionMode)"Selecting" else "Select",{
                state.selectionMode=!state.selectionMode
                if(!state.selectionMode) state.selectedTrackIds.clear()
            },state.selectionMode)
            if(state.libraryLens==LibraryLens.PLAYLISTS) TextCommand("New playlist",{state.createEmptyPlaylist()})
        }
        if(state.selectionMode && state.libraryLens==LibraryLens.TRACKS){
            Rule()
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),verticalAlignment=Alignment.CenterVertically){
                Text("${state.selectedTrackIds.size} selected",style=Type.meta.copy(color=p.ink2),modifier=Modifier.padding(horizontal=6.dp))
                TextCommand("Queue next",{state.queueSelectionNext()},state.selectedTrackIds.isNotEmpty())
                TextCommand("Playlist",{state.addSelectionToPlaylist()},state.selectedTrackIds.isNotEmpty())
                TextCommand("Favourite",{state.favouriteSelection()},state.selectedTrackIds.isNotEmpty())
                TextCommand("Offline",{state.downloadSelection()},state.selectedTrackIds.isNotEmpty())
                TextCommand("Clear",{state.clearSelection()})
            }
            Rule()
        }
        when(state.libraryLens){
            LibraryLens.TRACKS -> Column(Modifier.weight(1f)){
                if(state.sortLabel=="Title A–Z"){
                    val letters=remember(ordered){ ordered.mapNotNull{it.title.firstOrNull()?.uppercaseChar()}.distinct().filter{it.isLetter()}.take(26) }
                    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                        letters.forEach{letter->TextCommand(letter.toString(),{
                            val index=ordered.indexOfFirst{it.title.startsWith(letter,ignoreCase=true)}
                            if(index>=0) scope.launch{listState.animateScrollToItem(if(state.libraryViewMode=="Index") index + letters.count{it < letter} else index)}
                        })}
                    }
                    Rule()
                }
                if(state.libraryViewMode=="Index"){
                    val groups=remember(ordered){ordered.groupBy{it.title.firstOrNull()?.uppercaseChar()?.takeIf(Char::isLetter) ?: '#'}}
                    LazyColumn(Modifier.weight(1f),state=listState){
                        groups.toSortedMap().forEach{(letter,tracks)->
                            item("index-$letter"){
                                Row(Modifier.fillMaxWidth().padding(top=18.dp,bottom=6.dp),verticalAlignment=Alignment.CenterVertically){
                                    Text(letter.toString(),style=Type.title.copy(color=p.ink),modifier=Modifier.width(42.dp))
                                    Box(Modifier.weight(1f).height(1.dp).background(p.rule))
                                    Text("${tracks.size}",style=Type.numeric.copy(color=p.ink3),modifier=Modifier.padding(start=10.dp))
                                }
                            }
                            items(tracks,key={it.id}){t->
                                TrackLedgerRow(
                                    t,
                                    buildString{append(t.year);append(" · ");append(formatTime(t.durationMs));append(" · ");append(if(t.provenance==Provenance.OWNED)"OWNED" else t.provenance.name)},
                                    onOpen={if(state.selectionMode) state.toggleSelection(t.id) else {state.selectTrack(t,false);state.expandedPlayer=true}},
                                    onPlay={if(state.selectionMode) state.toggleSelection(t.id) else state.selectTrack(t,true)},
                                    onFavourite={state.toggleFavourite(t.id)},
                                    onDownload={state.toggleDownload(t.id)},
                                    compact=true,
                                    forceMissing=state.fixture.missingArtwork,
                                    onPlayNext={state.playNext(t)},
                                    onShuffleNext={state.shuffleNext(t)},
                                    onAddToPlaylist={state.addToPlaylist(t)},
                                    downloadState=state.downloads[t.id]?:DownloadState.REMOTE,
                                    selected=t.id in state.selectedTrackIds,
                                    selectionMode=state.selectionMode,
                                    secondaryLabel=metadataLine(t,state.metadataTemplate),
                                    showArtwork=false
                                )
                            }
                        }
                    }
                }else{
                    LazyColumn(Modifier.weight(1f),state=listState){items(ordered,key={it.id}){t->TrackLedgerRow(
                        t,
                        buildString{append(t.year);append(" · ");append(formatTime(t.durationMs));append(" · ");append(if(t.provenance==Provenance.OWNED)"OWNED" else t.provenance.name)},
                        onOpen={if(state.selectionMode) state.toggleSelection(t.id) else {state.selectTrack(t,false);state.expandedPlayer=true}},
                        onPlay={if(state.selectionMode) state.toggleSelection(t.id) else state.selectTrack(t,true)},
                        onFavourite={state.toggleFavourite(t.id)},
                        onDownload={state.toggleDownload(t.id)},
                        compact=state.denseLibrary,
                        forceMissing=state.fixture.missingArtwork,
                        showArtwork=state.libraryViewMode=="Ledger",
                        onPlayNext={state.playNext(t)},
                        onShuffleNext={state.shuffleNext(t)},
                        onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE,
                        selected=t.id in state.selectedTrackIds,
                        selectionMode=state.selectionMode,
                        secondaryLabel=metadataLine(t,state.metadataTemplate)
                    )}}
                }
            }
            LibraryLens.ALBUMS -> ObjectLedger(state,ordered.groupBy{it.album}.map{(k,v)->Triple(k,"Album","${v.first().artist} · ${v.size} tracks · ${v.first().year}")})
            LibraryLens.ARTISTS -> ObjectLedger(state,ordered.groupBy{it.artist}.map{(k,v)->Triple(k,"Artist","${v.size} tracks · ${v.map{it.album}.distinct().size} releases")})
            LibraryLens.PLAYLISTS -> ObjectLedger(
                state,
                state.playlistTracks.entries.map{(name,ids)->Triple(name,if(name=="Unfinished albums")"Smart list" else "Playlist","${ids.size} tracks · local playlist")},
                playable=true,
                queueable=true
            )
            LibraryLens.FOLDERS -> ObjectLedger(state,folderRows)
            LibraryLens.LONGFORM -> Column(Modifier.weight(1f)){
                Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                    TextCommand("All",{state.longformScope=LongformScope.ALL},state.longformScope==LongformScope.ALL)
                    TextCommand("Audiobooks",{state.longformScope=LongformScope.BOOKS},state.longformScope==LongformScope.BOOKS)
                    TextCommand("Podcasts",{state.longformScope=LongformScope.PODCASTS},state.longformScope==LongformScope.PODCASTS)
                }
                Rule()
                val longform=ordered.filter{t->
                    t.longform && when(state.longformScope){
                        LongformScope.ALL->true
                        LongformScope.BOOKS->t.longformType==LongformType.AUDIOBOOK
                        LongformScope.PODCASTS->t.longformType==LongformType.PODCAST
                    }
                }
                if(longform.isEmpty()){
                    Text("No ${when(state.longformScope){LongformScope.BOOKS->"audiobooks";LongformScope.PODCASTS->"podcasts";else->"longform media"}} in this view.",style=Type.body.copy(color=p.ink2),modifier=Modifier.padding(vertical=20.dp))
                }else LazyColumn(Modifier.weight(1f)){items(longform,key={it.id}){t->
                    TrackLedgerRow(
                        t,t.chapter?:"Longform",
                        onOpen={state.selectTrack(t,false);state.expandedPlayer=true},
                        onPlay={state.selectTrack(t,true)},
                        onFavourite={state.toggleFavourite(t.id)},
                        onDownload={state.toggleDownload(t.id)},
                        forceMissing=state.fixture.missingArtwork,
                        onPlayNext={state.playNext(t)},
                        onShuffleNext={state.shuffleNext(t)},
                        onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE
                    )
                }}
            }
            LibraryLens.RADIO -> ObjectLedger(state,listOf(Triple("Library radio","Radio","Generated locally · drawn only from your library"),Triple("Night signal","Radio","Connected source · preview"),Triple("Recent favourites","Radio","23-track rotation")),playable=true)
        }
    }
}

@Composable private fun ColumnScope.ObjectLedger(state:ShellState,rows:List<Triple<String,String,String>>,playable:Boolean=false,queueable:Boolean=false){
    val p=LocalTsunamiPalette.current
    LazyColumn(Modifier.fillMaxWidth().weight(1f)){itemsIndexed(rows){index,(name,type,meta)->
        val representative=when(type){
            "Playlist","Smart list" -> state.playlistTracks[name]?.firstOrNull()?.let{id->state.fixture.tracks.firstOrNull{it.id==id}}
            else -> state.fixture.tracks.getOrNull(index % state.fixture.tracks.size.coerceAtLeast(1))
        }
        var focused by remember(name,type){ mutableStateOf(false) }
        Column(
            Modifier.fillMaxWidth().heightIn(min=70.dp)
                .semantics{role=Role.Button;contentDescription="$name, $type, $meta"}
                .onFocusChanged{focused=it.isFocused}
                .clickable{state.focusedObject=LibraryObject(name,type,meta)}
                .background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)
                .padding(vertical=12.dp)
        ){
            Row(verticalAlignment=Alignment.CenterVertically){
                Box(Modifier.width(if(focused)3.dp else 1.dp).height(28.dp).background(if(focused)p.selected else androidx.compose.ui.graphics.Color.Transparent))
                Spacer(Modifier.width(if(focused)8.dp else 0.dp))
                Column(Modifier.weight(1f)){
                    Text(name,style=Type.row.copy(color=p.ink));Spacer(Modifier.height(3.dp))
                    Row{Text(type,style=Type.meta.copy(color=p.ink2));Spacer(Modifier.weight(1f));Text(meta,style=Type.meta.copy(color=p.ink3))}
                }
            }
            if(playable && representative!=null){
                Spacer(Modifier.height(4.dp))
                Row{TextCommand("Play",{state.selectTrack(representative,true)});if(queueable)TextCommand("Queue next",{state.playNext(representative)})}
            }
        };Rule()
    }}
}


@Composable private fun LibraryObjectDetail(state:ShellState,obj:LibraryObject,filtered:List<Track>){
    val p=LocalTsunamiPalette.current
    val contents=when{
        obj.kind=="Album" -> filtered.filter{it.album==obj.title}
        obj.kind=="Artist" -> filtered.filter{it.artist==obj.title}
        obj.kind=="Folder" -> filtered.filter{it.provenance==Provenance.OWNED && libraryFolderFor(it)==obj.title}
        obj.kind=="Playlist" || obj.kind=="Smart list" -> {
            val ids=state.playlistTracks[obj.title].orEmpty().toSet()
            filtered.filter{it.id in ids}
        }
        obj.kind=="Radio" -> filtered.take(8)
        else -> filtered.take(8)
    }
    Column(Modifier.fillMaxSize()){
        Row(Modifier.fillMaxWidth().heightIn(min=58.dp),verticalAlignment=Alignment.CenterVertically){
            HitIcon(Glyph.BACK,"Back to library",{state.focusedObject=null})
            Spacer(Modifier.width(6.dp))
            Text(obj.kind.uppercase(),style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold))
        }
        Text(obj.title,style=Type.display.copy(color=p.ink),maxLines=3)
        Spacer(Modifier.height(5.dp))
        Text(obj.meta,style=Type.body.copy(color=p.ink2),maxLines=2)
        Spacer(Modifier.height(16.dp))
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
            contents.firstOrNull()?.let{first->
                TextCommand("Play",{state.selectTrack(first,true)})
                TextCommand("Play next",{state.playNext(first)})
                TextCommand("Shuffle next",{state.shuffleNext(first)})
            }
        }
        Rule()
        SectionHeader("Contents")
        if(contents.isEmpty()){
            Text("Nothing in this object matches the active library filter.",style=Type.body.copy(color=p.ink2),modifier=Modifier.padding(vertical=18.dp))
        }else{
            LazyColumn(Modifier.weight(1f)){
                items(contents,key={it.id}){t->
                    TrackLedgerRow(
                        t,
                        "${t.year} · ${formatTime(t.durationMs)} · ${if(t.provenance==Provenance.OWNED)"OWNED" else t.provenance.name}",
                        onOpen={state.selectTrack(t,false);state.expandedPlayer=true},
                        onPlay={state.selectTrack(t,true)},
                        onFavourite={state.toggleFavourite(t.id)},
                        onDownload={state.toggleDownload(t.id)},
                        compact=state.denseLibrary || state.libraryViewMode=="Index",
                        forceMissing=state.fixture.missingArtwork,
                        showArtwork=state.libraryViewMode=="Ledger",
                        onPlayNext={state.playNext(t)},
                        onShuffleNext={state.shuffleNext(t)},
                        onAddToPlaylist={state.addToPlaylist(t)},downloadState=state.downloads[t.id]?:DownloadState.REMOTE,
                        secondaryLabel=metadataLine(t,state.metadataTemplate)
                    )
                }
            }
        }
    }
}


private fun metadataLine(track:Track,template:String)=when(template){
    "Title · Album · Year" -> "${track.album} · ${track.year}"
    "Title · Format · Source" -> "${track.quality} · ${if(track.provenance==Provenance.OWNED)"OWNED" else track.provenance.name}"
    else -> "${track.artist} · ${track.album}"
}


private fun libraryFolderFor(track:Track)=when{
    track.longformType==LongformType.AUDIOBOOK -> "/Audiobooks"
    ((track.id.hashCode() and Int.MAX_VALUE)%9)==0 -> "/Music/Field Recordings"
    else -> "/Music/Library"
}
