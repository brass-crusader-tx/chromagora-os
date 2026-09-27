package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.tsunami.shell.components.*
import com.tsunami.shell.model.DownloadState
import com.tsunami.shell.model.formatTime
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun SignalScreen(state:ShellState){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxSize()){
        Text("SIGNAL",style=Type.micro.copy(color=p.ink3,fontWeight=FontWeight.SemiBold))
        Spacer(Modifier.height(8.dp))
        Text(signalTitle(state),style=Type.display.copy(color=if(state.diagnosticsFault)p.danger else p.ink))
        Spacer(Modifier.height(8.dp))
        Text("Source, route, integrity and recovery status.",style=Type.body.copy(color=p.ink2))
        Spacer(Modifier.height(14.dp))
        Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
            listOf("Summary","Audio","Library","History","Logs").forEach{section->
                TextCommand(section,{state.signalSection=section},state.signalSection==section)
            }
        }
        Rule()
        when(state.signalSection){
            "Audio" -> AudioSignal(state)
            "Library" -> LibrarySignal(state)
            "History" -> HistorySignal(state)
            "Logs" -> LogsSignal(state)
            else -> SummarySignal(state)
        }
    }
}

private fun signalTitle(state:ShellState)=when(state.signalSection){
    "Audio" -> "Audio path"
    "Library" -> if(state.diagnosticsFault)"Library attention" else "Library integrity"
    "History" -> "Listening record"
    "Logs" -> if(state.diagnosticsFault)"Diagnostics" else "System trace"
    else -> if(state.diagnosticsFault)"Attention required" else "Playback truth"
}

@Composable private fun ColumnScope.SummarySignal(state:ShellState){
    val p=LocalTsunamiPalette.current
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=28.dp)){
        item{
            SectionHeader("Now playing")
            val t=state.currentTrack
            if(t==null) Text("Nothing playing",style=Type.body.copy(color=p.ink3),modifier=Modifier.padding(vertical=14.dp))
            else MetricGrid(listOf(
                "TRACK" to t.title,
                "SOURCE" to t.quality,
                "OUTPUT" to state.output,
                "POSITION" to "${formatTime(state.positionMs)} / ${formatTime(t.durationMs)}",
                "STATE" to if(state.playing)"PLAYING" else "PAUSED",
                "OFFLINE" to if(state.downloads[t.id]==DownloadState.DOWNLOADED)"YES" else "NO"
            ))
        }
        item{
            SectionHeader("Audio path")
            val t=state.currentTrack
            MetricGrid(listOf(
                "FORMAT" to (t?.quality ?: "No active source"),
                "OUTPUT" to state.output,
                "SPEED" to "${state.playbackSpeed}×",
                "REPLAYGAIN" to state.replayGainMode,
                "DSP" to if(state.dspEnabled)"ON · ${signedSignalDb(state.dspPreampDb)} dB" else "BYPASS",
                "GAPLESS" to state.gaplessProbeResult
            ))
        }
        item{
            SectionHeader("Library health")
            val offlineTracks=state.downloads.count{it.value==DownloadState.DOWNLOADED}
            MetricGrid(listOf(
                "INDEXED" to state.fixture.libraryCount.toString(),
                "ROOTS" to state.libraryRoots.size.toString(),
                "LYRICS MISSING" to state.lyricMissingCount.toString(),
                "OFFLINE TRACKS" to offlineTracks.toString(),
                "DUPLICATES" to if(state.duplicateGroups<0)"NOT SCANNED" else state.duplicateGroups.toString(),
                "FLAC FAIL" to if(state.flacIntegrityFailures<0)"NOT SCANNED" else state.flacIntegrityFailures.toString()
            ))
        }
        item{
            SectionHeader("Listening")
            Row(Modifier.fillMaxWidth().padding(vertical=12.dp)){
                SmallMetric("42h","this month")
                SmallMetric("78%","avg completion")
                SmallMetric("17","new artists")
            }
            Rule()
        }
    }
}

@Composable private fun ColumnScope.AudioSignal(state:ShellState){
    val p=LocalTsunamiPalette.current
    val t=state.currentTrack
    LazyColumn(Modifier.weight(1f).testTag("signal-audio-list"),contentPadding=PaddingValues(bottom=28.dp)){
        item{
            SectionHeader("Source capability")
            SignalLine("Track",t?.let{"${it.artist} — ${it.title}"}?:"Nothing playing")
            SignalLine("Container",t?.quality?.substringBefore(" ·")?:"Unknown")
            SignalLine("Bitrate","Not exposed by this source")
            SignalLine("Sample rate",t?.quality?.substringAfter("·",missingDelimiterValue="Unknown")?.trim()?:"Unknown")
            SignalLine("Bit depth",if(t?.quality?.contains("24")==true)"24-bit" else if(t?.quality?.contains("16")==true)"16-bit" else "Unknown / not exposed")
            SignalLine("Provider",if(t?.provenance?.name=="CATALOGUE")"Connected catalogue" else "Local / indexed")
        }
        item{
            SectionHeader("Cloud byte source")
            SignalLine("Effective provider",if(t?.provenance?.name=="CATALOGUE")"Connected provider route" else "Not applicable")
            SignalLine("Byte verification",if(t?.provenance?.name=="CATALOGUE")"Provider-reported when available" else "Local / platform source")
            SignalLine("Seekability",if(t==null)"Unknown" else "Seekable timeline")
            SignalLine("Cache","Bound to offline/download state")
        }
        item{
            SectionHeader("Output route")
            SignalLine("Current",state.output)
            SignalLine("Route format","Negotiated by selected output")
            SignalLine("Encoding","Reported when the platform exposes it")
            SignalLine("Offload",state.offloadPolicy)
            SignalLine("Resampling",state.resamplingPolicy)
            SignalLine("Bit-perfect","Eligibility described; active state not claimed")
        }
        item{
            SectionHeader("Audio pipeline")
            listOf(
                "1 · Source" to (t?.quality?:"Nothing playing"),
                "2 · Decoder" to "Decoder route · timeline available",
                "3 · TSUNAMI DSP" to if(state.dspEnabled)"Configured" else "Bypassed",
                "4 · Platform output" to "Negotiated by route",
                "5 · Conversion" to "Shown only when reported",
                "6 · Route" to state.output
            ).forEach{SignalLine(it.first,it.second)}
        }
        item{
            SectionHeader("Playback integrity")
            SignalLine("Audio underruns",state.diagnosticUnderruns.toString())
            SignalLine("Audio sink errors",state.diagnosticSinkErrors.toString())
            SignalLine("Codec errors",state.diagnosticCodecErrors.toString())
            SignalLine("Gapless probe",state.gaplessProbeResult)
            Column(Modifier.fillMaxWidth()){
                TextCommand(if(state.gaplessProbeResult=="Not run")"Test next transition" else "Retest transition",{state.runGaplessProbe()})
                TextCommand("Reset counters",{state.resetDiagnosticCounters()})
            }
            Text("SIGNAL SNAPSHOT · source, route, processing and library state",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(vertical=12.dp))
        }
    }
}

@Composable private fun ColumnScope.LibrarySignal(state:ShellState){
    val p=LocalTsunamiPalette.current
    LazyColumn(Modifier.weight(1f).testTag("signal-library-list"),contentPadding=PaddingValues(bottom=28.dp)){
        item{
            SectionHeader("Health audit")
            val offlineTracks=state.downloads.count{it.value==DownloadState.DOWNLOADED}
            MetricGrid(listOf(
                "INDEXED" to state.fixture.libraryCount.toString(),
                "ROOTS" to state.libraryRoots.size.toString(),
                "SOURCE ISSUES" to if(state.sourceError)"1" else "0",
                "LYRICS MISSING" to state.lyricMissingCount.toString(),
                "OFFLINE TRACKS" to offlineTracks.toString(),
                "PROFILE" to state.activeLibraryProfile
            ))
            TextCommand("Refresh health",{state.diagnosticsFault=false;state.sourceError=false;state.banner="Library health refreshed"})
        }
        item{
            SectionHeader("Lyrics quality & repair queue")
            SignalLine("Status",state.lyricAuditStatus)
            SignalLine("Missing exact lyrics",state.lyricMissingCount.toString())
            SignalLine("Timing model",if(state.lyricsWordTiming)"Word-level" else "Line-level")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand(if(state.lyricAuditStatus=="Not audited")"Audit library" else "Reaudit",{state.auditLyrics()})
                TextCommand("Fetch missing",{state.fetchMissingLyrics()},enabled=state.lyricMissingCount>0)
                TextCommand("Export lyrics",{state.banner="Lyrics archive export ready"})
                TextCommand("Import lyrics",{state.banner="Lyrics archive import ready"})
            }
        }
        item{
            SectionHeader("Exact duplicate hashes")
            SignalLine("Method","SHA-256 over the indexed audio payload")
            SignalLine("Groups",if(state.duplicateGroups<0)"Not scanned" else state.duplicateGroups.toString())
            TextCommand(if(state.duplicateGroups<0)"Scan hashes" else "Rescan hashes",{state.scanDuplicateHashes()})
        }
        item{
            SectionHeader("FLAC integrity")
            SignalLine("Lossless fixtures","7 FLAC-like objects")
            SignalLine("Failures",if(state.flacIntegrityFailures<0)"Not scanned" else state.flacIntegrityFailures.toString())
            TextCommand(if(state.flacIntegrityFailures<0)"Decode-scan FLAC" else "Run again",{state.scanFlacIntegrity()})
        }
        item{
            SectionHeader("ReplayGain & local analysis")
            SignalLine("State",state.analysisStatus)
            state.currentTrack?.let{t->
                SignalLine("ReplayGain policy",if(state.replayGainMode=="Off")"Not applied" else state.replayGainMode)
                SignalLine("Current",t.title)
                SignalLine("Analysis result",state.analysisStatus)
            }
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand("Analyse track",{state.analyzeCurrentTrack()},enabled=state.currentTrack!=null)
                TextCommand("Analyse library",{state.analyzeLibrary()},enabled=state.fixture.libraryCount>0)
            }
        }
        item{
            SectionHeader("Formats")
            val visible=state.fixture.tracks
            val flac=visible.count{it.quality.startsWith("FLAC")}
            val aac=visible.count{it.quality.startsWith("AAC") || it.quality.startsWith("M4B")}
            val mp3=visible.count{it.quality.startsWith("MP3")}
            val bit24=visible.count{it.quality.contains("24 /")}
            val khz96=visible.count{it.quality.contains("/ 96")}
            val other=(visible.size-flac-aac-mp3).coerceAtLeast(0)
            MetricGrid(listOf(
                "FLAC" to flac.toString(),
                "AAC / M4B" to aac.toString(),
                "MP3" to mp3.toString(),
                "24-BIT" to bit24.toString(),
                "96 KHZ" to khz96.toString(),
                "OTHER" to other.toString()
            ))
            Text("LIBRARY FORMAT MIX · counts reflect the indexed library state.",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(vertical=12.dp))
        }
    }
}

@Composable private fun ColumnScope.HistorySignal(state:ShellState){
    val p=LocalTsunamiPalette.current
    if(state.historyCleared){
        LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=28.dp)){
            item{
                SectionHeader("Listening history")
                Text("No listening history yet.",style=Type.title.copy(color=p.ink),modifier=Modifier.padding(top=18.dp))
                Spacer(Modifier.height(6.dp))
                Text("New listening activity will repopulate this workspace.",style=Type.body.copy(color=p.ink2))
                Spacer(Modifier.height(18.dp))
                Rule()
            }
        }
        return
    }
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=28.dp)){
        item{
            SectionHeader("Listening totals")
            MetricGrid(listOf(
                "PLAYS" to "1,284",
                "SKIPS" to "119",
                "COMPLETIONS" to "904",
                "COMPLETION" to "78%",
                "LISTENING" to "42h 18m",
                "UNIQUE" to "612"
            ))
            SignalLine("Top track","Afterglow at the Edge of the City · 31 plays")
            SignalLine("Top artist","Mira Sol · 3h 42m")
            SignalLine("Top album","Refractions · 2h 08m")
            SignalLine("Top genre","Electronic · 11h 09m")
        }
        item{
            SectionHeader("TSUNAMI Replay")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand(state.replayPeriod,{state.cycleReplayPeriod()},true)
                TextCommand("CSV",{state.exportReplay("CSV")})
                TextCommand("JSON",{state.exportReplay("JSON")})
                TextCommand("Share card",{state.exportReplay("share card")})
            }
            SignalLine("Period",state.replayPeriod)
            SignalLine("Longest session","2h 14m")
            SignalLine("Lossless listening","31h 05m")
            SignalLine("Hi-Res listening","9h 48m")
            SignalLine("Discovery ratio","18%")
            SignalLine("Export actions",state.replayExportCount.toString())
        }
        item{
            SectionHeader("Listening by time")
            MetricGrid(listOf(
                "07:00" to "5h 08m",
                "12:00" to "4h 11m",
                "18:00" to "7h 26m",
                "23:00" to "8h 04m",
                "STREAK" to "11 days",
                "AVG REACHED" to "78%"
            ))
        }
        item{
            SectionHeader("Library activity")
            SignalLine("Recently edited / retagged","14")
            SignalLine("Recently gained lyrics","7")
            SignalLine("Recently identified via AcoustID","3")
            SignalLine("Yesterday · 23:14","Playlist paths remapped · 18 entries")
            SignalLine("Yesterday · 22:51","Artwork changed · Refractions")
            SignalLine("Yesterday · 21:09","Lyrics gained · Serein")
            Text("HISTORY STATE · follows the History preference.",style=Type.meta.copy(color=p.ink3),modifier=Modifier.padding(vertical=12.dp))
        }
    }
}

@Composable private fun ColumnScope.LogsSignal(state:ShellState){
    val p=LocalTsunamiPalette.current
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=28.dp)){
        item{
            SectionHeader("Diagnostics")
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState())){
                TextCommand("Copy summary",{state.banner="Diagnostic summary copied"})
                TextCommand("Export bundle",{state.exportDiagnostics()})
                TextCommand("Clear log",{state.clearDiagnosticLog()},enabled=state.diagnosticLog.isNotEmpty())
                TextCommand(if(state.diagnosticsFault)"Retry" else "Simulate fault",{
                    if(state.diagnosticsFault){
                        state.diagnosticsFault=false
                        state.sourceError=false
                        state.diagnosticUnderruns=0
                        state.banner="Diagnostics healthy"
                    }else{
                        state.diagnosticsFault=true
                        state.diagnosticUnderruns=3
                        state.diagnosticLog.add("15:10:02 · underrun cluster detected")
                        state.banner="Diagnostic fault injected"
                    }
                },state.diagnosticsFault)
            }
            Spacer(Modifier.height(8.dp))
            Text(if(state.diagnosticsFault)"Decoder route recovered after underruns. Library cache requires review." else "No active playback fault. Audio route, queue state and library index agree.",style=Type.body.copy(color=if(state.diagnosticsFault)p.danger else p.ink2))
        }
        item{
            SectionHeader("Recent log")
            if(state.diagnosticLog.isEmpty()) Text("Log cleared.",style=Type.body.copy(color=p.ink3),modifier=Modifier.padding(vertical=16.dp))
            else state.diagnosticLog.takeLast(25).forEach{line->
                Text(line,style=Type.micro.copy(color=p.ink3),modifier=Modifier.fillMaxWidth().padding(vertical=6.dp))
                Rule()
            }
        }
    }
}

@Composable private fun SignalLine(label:String,value:String){
    val p=LocalTsunamiPalette.current
    Row(Modifier.fillMaxWidth().padding(vertical=8.dp)){
        Text(label,style=Type.meta.copy(color=p.ink3),modifier=Modifier.weight(.42f))
        Text(value,style=Type.meta.copy(color=p.ink),modifier=Modifier.weight(.58f),maxLines=4)
    }
    Rule()
}

@Composable private fun MetricGrid(values:List<Pair<String,String>>){
    Column{
        values.chunked(2).forEach{row->
            Row(Modifier.fillMaxWidth()){
                row.forEach{(k,v)->
                    Column(Modifier.weight(1f).padding(start=0.dp,top=12.dp,end=12.dp,bottom=12.dp)){
                        Text(k,style=Type.micro.copy(color=LocalTsunamiPalette.current.ink3))
                        Spacer(Modifier.height(4.dp))
                        Text(v,style=Type.row.copy(color=LocalTsunamiPalette.current.ink),maxLines=3)
                    }
                }
                if(row.size==1) Spacer(Modifier.weight(1f))
            }
            Rule()
        }
    }
}

@Composable private fun RowScope.SmallMetric(value:String,label:String){
    val p=LocalTsunamiPalette.current
    Column(Modifier.weight(1f)){
        Text(value,style=Type.title.copy(color=p.ink))
        Text(label,style=Type.meta.copy(color=p.ink3))
    }
}

private fun signedSignalDb(v:Float)=when{
    v>0f->"+${v.toInt()}"
    v<0f->v.toInt().toString()
    else->"0"
}
