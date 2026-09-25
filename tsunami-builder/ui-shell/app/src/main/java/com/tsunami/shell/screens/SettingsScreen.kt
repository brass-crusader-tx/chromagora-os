package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.runtime.Composable
import androidx.compose.ui.*
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.tsunami.shell.components.*
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun SettingsOverlay(state:ShellState,onClose:()->Unit){
    val p=LocalTsunamiPalette.current
    val page=state.settingsExpanded ?: "root"
    val goBack={ if(page=="root") onClose() else state.settingsExpanded="root" }
    Box(Modifier.fillMaxSize().background(p.ground)){
        Column(Modifier.fillMaxSize().statusBarsPadding().padding(horizontal=20.dp)){
            Row(Modifier.fillMaxWidth().height(58.dp),verticalAlignment=Alignment.CenterVertically){
                HitIcon(Glyph.BACK,"Back",goBack)
                Spacer(Modifier.width(4.dp))
                Text(settingsTitle(page),style=Type.title.copy(color=p.ink))
            }
            Rule()
            when(page){
                "audio" -> AudioSettings(state)
                "visualizer" -> VisualizerSettings(state)
                "shuffle" -> ShuffleSettings(state)
                "library-roots" -> LibraryRootsSettings(state)
                "library-sections" -> LibrarySectionsSettings(state)
                "library-profiles" -> LibraryProfilesSettings(state)
                "metadata" -> MetadataSettings(state)
                "scrobbling" -> ScrobblingSettings(state)
                "backup" -> BackupSettings(state)
                "controls" -> ControlSettings(state)
                "context-rules" -> ContextRuleSettings(state)
                "quick-actions" -> QuickActionSettings(state)
                "custom-sections" -> CustomSectionsSettings(state)
                "audio-profiles" -> AudioProfilesSettings(state)
                "lyrics" -> LyricsSettings(state)
                "presentation" -> PresentationSettings(state)
                else -> SettingsRoot(state,onClose)
            }
        }
    }
}

private fun settingsTitle(page:String)=when(page){
    "audio"->"Audio processing"
    "visualizer"->"Visualizer"
    "shuffle"->"Shuffle behavior"
    "library-roots"->"Library roots"
    "library-sections"->"Library sections"
    "library-profiles"->"Library profiles"
    "metadata"->"Metadata presentation"
    "scrobbling"->"Listening services"
    "backup"->"Backup & portability"
    "controls"->"Controls & gestures"
    "context-rules"->"Context rules"
    "quick-actions"->"Quick actions & sessions"
    "custom-sections"->"Custom library sections"
    "audio-profiles"->"Output profiles"
    "lyrics"->"Lyrics & timing"
    "presentation"->"Presentation"
    else->"Settings"
}

@Composable private fun ColumnScope.SettingsRoot(state:ShellState,onClose:()->Unit){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Appearance")
            ToggleRow("Theme",if(state.theme==ThemeMode.LIGHT)"Light" else "Dark"){state.theme=if(state.theme==ThemeMode.LIGHT)ThemeMode.DARK else ThemeMode.LIGHT}
            ToggleRow("High contrast",if(state.highContrast)"ON" else "OFF"){state.highContrast=!state.highContrast}
            ToggleRow("Large controls",if(state.largeControls)"56 DP" else "48 DP"){state.largeControls=!state.largeControls}
            ActionRow("Haptic intensity",when(state.hapticStrength){0->"OFF";1->"STANDARD";else->"STRONG"}){state.cycleHapticStrength()}
            ToggleRow("Reduced motion",if(state.reducedMotion)"ON" else "OFF"){state.reducedMotion=!state.reducedMotion}
            ToggleRow("Library density",if(state.denseLibrary)"DENSE" else "COMFORTABLE"){state.denseLibrary=!state.denseLibrary}
            ActionRow("Presentation","Player geometry · orientation · artwork"){state.settingsExpanded="presentation"}
        }
        item{
            IntentSection("Library")
            ActionRow("Library roots","${state.libraryRoots.size} folders · ${state.fixture.libraryCount} indexed"){state.settingsExpanded="library-roots"}
            ActionRow("Library profile",state.activeLibraryProfile){state.settingsExpanded="library-profiles"}
            ActionRow("Sections","Tracks · Albums · Artists · Playlists · Longform"){state.settingsExpanded="library-sections"}
            ActionRow("Custom sections","${state.customSections.size} saved query views"){state.settingsExpanded="custom-sections"}
            ActionRow("Metadata template",state.metadataTemplate){state.settingsExpanded="metadata"}
        }
        item{
            IntentSection("Playback")
            ActionRow("Resume behavior","Longform remembers position"){state.banner="Resume behavior · remember longform position"}
            ToggleRow("Gapless",if(state.gapless)"ON" else "OFF"){state.gapless=!state.gapless}
            ActionRow("Crossfade",if(state.crossfadeSeconds==0)"OFF" else "${state.crossfadeSeconds}s"){state.cycleCrossfade()}
            ActionRow("Default speed","${state.playbackSpeed}×"){state.cyclePlaybackSpeed()}
            ActionRow("Audio quality","${state.audioPreference} · truthful output reporting"){state.cycleAudioPreference()}
            ActionRow("Audio processing","ReplayGain ${state.replayGainMode} · DSP ${if(state.dspEnabled)"ON" else "OFF"}"){state.settingsExpanded="audio"}
            ActionRow("Output profiles","${state.audioProfiles.size} route profiles"){state.settingsExpanded="audio-profiles"}
            ActionRow("Controls & gestures","One-handed ${if(state.oneHandedNowPlaying)"ON" else "OFF"} · ${state.quickActions.size} quick actions"){state.settingsExpanded="controls"}
            ActionRow("Shuffle behavior",state.shuffleMode){state.settingsExpanded="shuffle"}
            ActionRow("Visualizer","${state.visualizerMode} · ${if(state.visualizerMonochrome)"monochrome" else "structural palette"}"){state.settingsExpanded="visualizer"}
            ActionRow("Lyrics & timing","${if(state.lyricsWordTiming)"word timing" else "line timing"} · ${state.lyricsGlobalDelayMs} ms"){state.settingsExpanded="lyrics"}
        }
        item{
            IntentSection("Offline")
            ToggleRow("Offline mode",if(state.offlineMode)"LOCAL ONLY" else "NETWORK ALLOWED"){state.offlineMode=!state.offlineMode}
            ToggleRow("Wi‑Fi downloads",if(state.wifiOnlyDownloads)"ONLY" else "ANY NETWORK"){state.wifiOnlyDownloads=!state.wifiOnlyDownloads}
            ToggleRow("Online library on mobile data",if(state.showOnlineOnMobileData)"VISIBLE" else "HIDDEN"){state.showOnlineOnMobileData=!state.showOnlineOnMobileData}
            ActionRow("Download quality",state.downloadQuality){state.cycleDownloadQuality()}
            ActionRow("Downloads","3.2 GB · ${if(state.wifiOnlyDownloads)"Wi‑Fi preferred" else "network allowed"}"){state.banner="Download policy · ${state.downloadQuality}"}
        }
        item{
            IntentSection("Services")
            state.services.forEachIndexed{i,s->
                val progress=state.importProgress[s.name]
                ActionRow(s.name,if(s.connected)"CONNECTED · ${s.detail}" else "DISCONNECTED"){state.toggleService(i)}
                if(s.connected) ActionRow("Import ${s.name}",when(progress){null->"READY";100->"COMPLETE";else->"${progress}% · tap to continue"}){state.advanceImport(i)}
            }
        }
        item{
            IntentSection("Privacy")
            ToggleRow("Listening history",if(state.historyEnabled)"ON" else "OFF"){state.historyEnabled=!state.historyEnabled}
            ActionRow("Listening services","${if(state.listenBrainzEnabled)"ListenBrainz " else ""}${if(state.lastFmEnabled)"Last.fm" else if(!state.listenBrainzEnabled)"OFF" else ""}"){state.settingsExpanded="scrobbling"}
            ActionRow("Clear history","Local mock state only"){state.banner="Listening history cleared in prototype"}
        }
        item{
            IntentSection("Advanced")
            ActionRow("Context rules","${state.contextRules.count{it.enabled}} active · ${state.contextRules.size} total"){state.settingsExpanded="context-rules"}
            ActionRow("Quick actions & sessions",state.activeSession?.let{"SESSION · $it"}?:"No active session"){state.settingsExpanded="quick-actions"}
            ActionRow("Backup & portability",if(state.autoBackupEnabled)"AUTO · every ${state.backupIntervalHours}h" else "MANUAL"){state.settingsExpanded="backup"}
            ActionRow("Diagnostics",if(state.diagnosticsFault)"ATTENTION" else "HEALTHY"){state.primary=PrimarySpace.SIGNAL;onClose()}
            ActionRow("About","UI Genesis · isolated shell"){state.banner="TSUNAMI UI Genesis · backend-free experiential prototype"}
            ActionRow("Prototype status","No production data access"){state.banner="Shell is backend-free"}
        }
    }
}

@Composable private fun ColumnScope.LyricsSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Synchronization")
            ToggleRow("Follow playback",if(state.lyricsFollowPlayback)"ON" else "OFF"){state.lyricsFollowPlayback=!state.lyricsFollowPlayback}
            ToggleRow("Word timing",if(state.lyricsWordTiming)"WORD" else "LINE"){state.lyricsWordTiming=!state.lyricsWordTiming}
            ActionRow("Global delay","${state.lyricsGlobalDelayMs} ms"){state.cycleLyricsDelay()}
            ToggleRow("Missing-lyrics fallback",if(state.missingLyricsFallback)"ON" else "OFF"){state.missingLyricsFallback=!state.missingLyricsFallback}
            ToggleRow("Auto-fetch exact matches",if(state.lyricsAutoFetch)"ON" else "OFF"){state.lyricsAutoFetch=!state.lyricsAutoFetch}
        }
        item{
            IntentSection("Environment")
            ToggleRow("Artwork backdrop",if(state.lyricsArtworkBackdrop)"ON" else "OFF"){state.lyricsArtworkBackdrop=!state.lyricsArtworkBackdrop}
            ToggleRow("Visualizer behind lyrics",if(state.visualizerBehindLyrics)"ON" else "OFF"){state.visualizerBehindLyrics=!state.visualizerBehindLyrics}
            Text("Timing controls are prototype state only. No transcription, network lookup, microphone capture, or production lyric store is accessed.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.PresentationSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Now playing")
            ToggleRow("Artwork",if(state.showArtworkInPlayer)"VISIBLE" else "HIDDEN"){state.showArtworkInPlayer=!state.showArtworkInPlayer}
            ToggleRow("Artwork geometry",if(state.squareArtwork)"SQUARE" else "FREE"){state.squareArtwork=!state.squareArtwork}
            ToggleRow("Metadata density",if(state.compactPlayerMetadata)"COMPACT" else "EDITORIAL"){state.compactPlayerMetadata=!state.compactPlayerMetadata}
            ActionRow("Phone orientation",state.orientationLocks["phone"]?:"Auto"){state.cycleOrientation("phone")}
            ActionRow("Wide orientation",state.orientationLocks["wide"]?:"Auto"){state.cycleOrientation("wide")}
            ToggleRow("One-handed player",if(state.oneHandedNowPlaying)"ON" else "OFF"){state.oneHandedNowPlaying=!state.oneHandedNowPlaying}
        }
        item{
            IntentSection("Artwork independence")
            Text("Artwork can be hidden without changing navigation, selection, transport hierarchy, or the product’s neutral and selected-state system.",style=Type.body.copy(color=LocalTsunamiPalette.current.ink2),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}
@Composable private fun ColumnScope.AudioSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Playback gain")
            ActionRow("ReplayGain",state.replayGainMode){state.cycleReplayGain()}
            ActionRow("Preamp","${signedDb(state.dspPreampDb)} dB"){state.cycleDspPreamp()}
            ToggleRow("Preserve pitch",if(state.preservePitch)"ON" else "OFF"){state.preservePitch=!state.preservePitch}
            ActionRow("Default speed","${state.playbackSpeed}×"){state.cyclePlaybackSpeed()}
            ActionRow("Pitch","${state.playbackPitch}×"){state.cyclePitch()}
            ActionRow("Offload",state.offloadPolicy){state.cycleOffload()}
            ActionRow("Resampling",state.resamplingPolicy){state.cycleResampling()}
            ToggleRow("Loudness normalization",if(state.loudnessNormalization)"ON" else "OFF"){state.loudnessNormalization=!state.loudnessNormalization}
            ToggleRow("Prevent clipping",if(state.preventClipping)"ON" else "OFF"){state.preventClipping=!state.preventClipping}
            ActionRow("Crossfade curve",state.crossfadeCurve){state.cycleCrossfadeCurve()}
            ActionRow("Crossfade policy",state.crossfadePolicy){state.cycleCrossfadePolicy()}
            ActionRow("Fade on pause","${state.fadePauseMs} ms"){state.cycleFadePause()}
            ActionRow("Fade on stop","${state.fadeStopMs} ms"){state.cycleFadeStop()}
            ActionRow("Fade on skip","${state.fadeSkipMs} ms"){state.cycleFadeSkip()}
            ToggleRow("Skip silence in longform",if(state.skipSilenceLongform)"ON" else "OFF"){state.skipSilenceLongform=!state.skipSilenceLongform}
            ActionRow("Smart rewind","${state.smartRewindSeconds}s after a long pause"){state.cycleSmartRewind()}
        }
        item{
            IntentSection("Processing")
            ToggleRow("DSP",if(state.dspEnabled)"ON" else "BYPASS"){state.dspEnabled=!state.dspEnabled}
            ActionRow("Bass","${signedDb(state.bassDb)} dB"){state.cycleBass()}
            ActionRow("Treble","${signedDb(state.trebleDb)} dB"){state.cycleTreble()}
            ToggleRow("Mono downmix",if(state.monoDownmix)"ON" else "OFF"){state.monoDownmix=!state.monoDownmix}
            ActionRow("Stereo width","${state.stereoWidth}×"){state.cycleStereoWidth()}
            ToggleRow("Compressor",if(state.compressorEnabled)"ON" else "OFF"){state.compressorEnabled=!state.compressorEnabled}
            ToggleRow("Limiter",if(state.limiterEnabled)"ON" else "OFF"){state.limiterEnabled=!state.limiterEnabled}
            ToggleRow("Automatic gain control",if(state.agcEnabled)"ON" else "OFF"){state.agcEnabled=!state.agcEnabled}
            ActionRow("Channel balance",if(state.balance==0f)"CENTER" else if(state.balance>0)"RIGHT" else "LEFT"){state.balance=when(state.balance){0f->.35f;.35f->-.35f;else->0f}}
            ToggleRow("Reverse stereo",if(state.reverseStereo)"ON" else "OFF"){state.reverseStereo=!state.reverseStereo}
            ActionRow("Crossfeed","${(state.crossfeed*100).toInt()}%"){state.crossfeed=when(state.crossfeed){0f->.25f;.25f->.5f;else->0f}}
            ActionRow("Reverb","${(state.reverb*100).toInt()}%"){state.reverb=when(state.reverb){0f->.15f;.15f->.3f;else->0f}}
            Text("Processing remains explicitly opt-in; the prototype never claims signal changes are occurring.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.VisualizerSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Rendering")
            ActionRow("Mode",state.visualizerMode){state.cycleVisualizerMode()}
            ActionRow("Sensitivity","${state.visualizerSensitivity}×"){state.cycleVisualizerSensitivity()}
            ActionRow("Attack",state.visualizerAttack.toString()){state.cycleVisualizerAttack()}
            ActionRow("Release",state.visualizerRelease.toString()){state.cycleVisualizerRelease()}
            ActionRow("Smoothing",state.visualizerSmoothing.toString()){state.cycleVisualizerSmoothing()}
            ActionRow("Gain","${state.visualizerGain}×"){state.cycleVisualizerGain()}
            ActionRow("Layers",state.visualizerLayers.toString()){state.cycleVisualizerLayers()}
            ToggleRow("Monochrome",if(state.visualizerMonochrome)"ON" else "OFF"){state.visualizerMonochrome=!state.visualizerMonochrome}
            ToggleRow("Battery saver",if(state.visualizerBatterySaver)"ON" else "OFF"){state.visualizerBatterySaver=!state.visualizerBatterySaver}
            ToggleRow("Beat backlight",if(state.visualizerBeatBacklight)"ON" else "OFF"){state.visualizerBeatBacklight=!state.visualizerBeatBacklight}
            ToggleRow("Behind lyrics",if(state.visualizerBehindLyrics)"ON" else "OFF"){state.visualizerBehindLyrics=!state.visualizerBehindLyrics}
            ToggleRow("Reduced motion",if(state.reducedMotion)"ON" else "OFF"){state.reducedMotion=!state.reducedMotion}
            Text("Visualizer state is deterministic mock state. No microphone, audio-session capture, or production telemetry is accessed.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.ShuffleSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Queue intelligence")
            ActionRow("Mode",state.shuffleMode){state.cycleShuffleMode()}
            ToggleRow("Exclude audiobooks",if(state.excludeAudiobooks)"ON" else "OFF"){state.excludeAudiobooks=!state.excludeAudiobooks}
            ToggleRow("Suppress duplicate titles",if(state.suppressDuplicateTitles)"ON" else "OFF"){state.suppressDuplicateTitles=!state.suppressDuplicateTitles}
            ToggleRow("Group alternate versions",if(state.groupAlternateVersions)"ON" else "OFF"){state.groupAlternateVersions=!state.groupAlternateVersions}
            ToggleRow("Prefer compatible keys",if(state.compatibleKey)"ON" else "OFF"){state.compatibleKey=!state.compatibleKey}
        }
        item{
            IntentSection("Spacing")
            ActionRow("Artist minimum","${state.artistSpacing} tracks"){state.cycleArtistSpacing()}
            ActionRow("Album minimum","${state.albumSpacing} tracks"){state.cycleAlbumSpacing()}
            ActionRow("Genre minimum","${state.genreSpacing} tracks"){state.cycleGenreSpacing()}
            ActionRow("Mood minimum","${state.moodSpacing} tracks"){state.cycleMoodSpacing()}
            ActionRow("Novelty","${(state.shuffleNovelty*100).toInt()}%"){state.cycleShuffleNovelty()}
            ActionRow("Familiarity","${(state.shuffleFamiliarity*100).toInt()}%"){state.cycleShuffleFamiliarity()}
            ActionRow("Genre blend",state.genreBlend){state.cycleGenreBlend()}
        }
        item{
            IntentSection("Seasonality")
            ToggleRow("Seasonal exclusion",if(state.seasonalExclusion)"ON" else "OFF"){state.seasonalExclusion=!state.seasonalExclusion}
            if(state.seasonalExclusion){
                ActionRow("Start month",monthLabel(state.seasonalStartMonth)){state.cycleSeasonalStart()}
                ActionRow("End month",monthLabel(state.seasonalEndMonth)){state.cycleSeasonalEnd()}
            }
        }
        item{
            IntentSection("Presets","Save"){state.saveShufflePreset()}
            state.shufflePresets.forEach{preset->ActionRow(preset,if(preset.contains(state.shuffleMode,true))"CURRENT-LIKE" else "SAVED"){state.banner="Applied shuffle preset · $preset"}}
            Text("All shuffle policies affect deterministic prototype queue choices only; they do not import production queue code.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.LibraryRootsSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Indexed locations","Add"){state.addMockLibraryRoot()}
            state.libraryRoots.forEach{root->
                ActionRow(root,if(root.contains("Audiobooks",true))"LONGFORM ROOT" else "MUSIC ROOT"){state.removeLibraryRoot(root)}
            }
            Text("Tap a listed root to remove it. At least one root is always retained in mock state.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
            IntentSection("Exclusions")
            ActionRow("Excluded folders","${state.excludedFolderCount} paths"){state.cycleExcludedFolders()}
            ActionRow("Excluded extensions",state.excludedExtensions){state.cycleExcludedExtensions()}
            ActionRow("Excluded genres",state.excludedGenres){state.cycleExcludedGenres()}
            ActionRow("Excluded playlist paths",state.excludedPlaylistPaths){state.cycleExcludedPlaylistPaths()}
        }
    }
}

@Composable private fun ColumnScope.LibrarySectionsSettings(state:ShellState){
    val sections=listOf("Tracks","Albums","Artists","Playlists","Folders","Longform","Radio")
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Visible lenses")
            sections.forEach{section->
                if(section=="Tracks") ToggleRow(section,"ANCHOR"){state.banner="Tracks remains the stable library anchor"}
                else ToggleRow(section,if(section in state.hiddenLibrarySections)"HIDDEN" else "VISIBLE"){state.toggleLibrarySection(section)}
            }
            Text("The shell keeps the navigation model stable while allowing the library index to be pruned to the listener's actual object classes.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.LibraryProfilesSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Active profile")
            ActionRow("Main library",if(state.activeLibraryProfile=="Main library")"ACTIVE · 2 roots" else "2 roots"){state.activeLibraryProfile="Main library";state.banner="Library profile · Main library"}
            ActionRow("Travel library",if(state.activeLibraryProfile=="Travel library")"ACTIVE · offline-first" else "offline-first"){state.activeLibraryProfile="Travel library";state.banner="Library profile · Travel library"}
            ActionRow("Create profile","Mock profile creation"){state.cycleLibraryProfile()}
        }
    }
}

@Composable private fun ColumnScope.MetadataSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Presentation")
            ActionRow("Track rows",state.metadataTemplate){state.cycleMetadataTemplate()}
            ActionRow("Now playing",state.metadataTemplate){state.cycleMetadataTemplate()}
            ActionRow("Album artist",state.albumArtistMode){state.cycleAlbumArtistMode()}
            ActionRow("Car display","Title · Artist"){state.banner="Car-display template · Title · Artist"}
            Text("Metadata templates are presentation rules only; they do not rewrite source tags in this backend-free shell.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.ScrobblingSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("External listening history")
            ToggleRow("ListenBrainz",if(state.listenBrainzEnabled)"ON" else "OFF"){state.listenBrainzEnabled=!state.listenBrainzEnabled}
            ToggleRow("Last.fm",if(state.lastFmEnabled)"ON" else "OFF"){state.lastFmEnabled=!state.lastFmEnabled}
            ToggleRow("Playing now",if(state.playingNowEnabled)"ON" else "OFF"){state.playingNowEnabled=!state.playingNowEnabled}
            ToggleRow("Love / hate sync",if(state.loveHateSync)"ON" else "OFF"){state.loveHateSync=!state.loveHateSync}
            ActionRow("Scrobble threshold","${state.scrobbleThreshold}%"){state.cycleScrobbleThreshold()}
            ActionRow("Threshold cap","${state.scrobbleThresholdCapSeconds}s"){state.cycleScrobbleCap()}
            ActionRow("Import listening history","CSV / JSON mock"){state.banner="History import preview · 128 matched · 7 unmatched"}
            Text("No credential, OAuth, scrobble, or network operation occurs. The prototype represents only the user-facing control model.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.ControlSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Reachability")
            ToggleRow("One-handed now playing",if(state.oneHandedNowPlaying)"ON" else "OFF"){state.oneHandedNowPlaying=!state.oneHandedNowPlaying}
            listOf("Player","Lyrics","Visualizer","Library","Search","Signal","Settings").forEach{view->
                ActionRow("$view orientation",state.orientationLocks[view]?:"Auto"){state.cycleOrientation(view)}
            }
        }
        item{
            IntentSection("Track gestures")
            ActionRow("Swipe left",state.swipeLeft){state.cycleSwipeLeft()}
            ActionRow("Swipe right",state.swipeRight){state.cycleSwipeRight()}
            ActionRow("Swipe up",state.swipeUp){state.cycleSwipeUp()}
            ActionRow("Swipe down",state.swipeDown){state.cycleSwipeDown()}
            ActionRow("Long press",state.longPressAction){state.cycleLongPress()}
        }
        item{
            IntentSection("Headset controls")
            ActionRow("Single",state.headsetSingle){state.headsetSingle=if(state.headsetSingle=="Play/Pause")"Favourite" else "Play/Pause"}
            ActionRow("Double",state.headsetDouble){state.headsetDouble=if(state.headsetDouble=="Next")"Seek +30s" else "Next"}
            ActionRow("Triple",state.headsetTriple){state.headsetTriple=if(state.headsetTriple=="Previous")"Seek −15s" else "Previous"}
            ActionRow("Long",state.headsetLong){state.headsetLong=if(state.headsetLong=="Actions")"Output" else "Actions"}
            Text("Mappings are represented explicitly; the shell does not listen for hardware buttons.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.ContextRuleSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Adaptive queue rules","Add"){state.addContextRule()}
            state.contextRules.forEachIndexed{index,rule->
                Row(Modifier.fillMaxWidth().heightIn(min=72.dp).padding(vertical=8.dp),verticalAlignment=Alignment.CenterVertically){
                    Box(Modifier.width(if(rule.enabled)3.dp else 1.dp).height(30.dp).background(if(rule.enabled)LocalTsunamiPalette.current.selected else LocalTsunamiPalette.current.rule))
                    Spacer(Modifier.width(10.dp))
                    Column(Modifier.weight(1f)){Text(rule.name,style=Type.row.copy(color=LocalTsunamiPalette.current.ink));Text("${rule.window} · ${rule.scope}",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3))}
                    TextCommand(if(rule.enabled)"On" else "Off",{state.toggleContextRule(index)},rule.enabled)
                    HitIcon(Glyph.CLOSE,"Remove ${rule.name}",{state.removeContextRule(index)})
                }
                Rule()
            }
            Text("Rules express listening context without turning the primary navigation into automation software.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.QuickActionSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Player quick actions","Add"){state.addQuickAction()}
            state.quickActions.forEach{label->
                Row(Modifier.fillMaxWidth().heightIn(min=58.dp),verticalAlignment=Alignment.CenterVertically){
                    Text(label,style=Type.row.copy(color=LocalTsunamiPalette.current.ink),modifier=Modifier.weight(1f))
                    HitIcon(Glyph.CLOSE,"Remove $label",{state.removeQuickAction(label)})
                }
                Rule()
            }
        }
        item{
            IntentSection("Listening session")
            ActionRow(if(state.activeSession==null)"Start Focus session" else "End ${state.activeSession} session",state.activeSession?.let{"ACTIVE"}?:"No active label"){state.toggleSession()}
            Text("Session labels are metadata for later listening-history analysis; playback remains uninterrupted.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.CustomSectionsSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Saved library lenses","Add"){state.addCustomSection()}
            state.customSections.forEachIndexed{index,section->
                Row(Modifier.fillMaxWidth().heightIn(min=72.dp).padding(vertical=8.dp),verticalAlignment=Alignment.CenterVertically){
                    Column(Modifier.weight(1f)){Text(section.name,style=Type.row.copy(color=LocalTsunamiPalette.current.ink));Text("${section.query} · ${section.view}",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3))}
                    HitIcon(Glyph.CLOSE,"Remove ${section.name}",{state.removeCustomSection(index)})
                }
                Rule()
            }
        }
    }
}

@Composable private fun ColumnScope.AudioProfilesSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Route-bound processing","Save current"){state.addAudioProfile()}
            state.audioProfiles.forEachIndexed{index,profile->
                Row(Modifier.fillMaxWidth().heightIn(min=72.dp).padding(vertical=8.dp),verticalAlignment=Alignment.CenterVertically){
                    Column(Modifier.weight(1f)){Text(profile.name,style=Type.row.copy(color=LocalTsunamiPalette.current.ink));Text("${profile.route} · ${profile.processing}",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3))}
                    TextCommand("Apply",{state.output=profile.route;state.banner="Applied ${profile.name}"})
                    HitIcon(Glyph.CLOSE,"Remove ${profile.name}",{state.removeAudioProfile(index)})
                }
                Rule()
            }
            Text("Profiles capture the user-facing relationship between an output and processing policy; no device DSP is invoked.",style=Type.meta.copy(color=LocalTsunamiPalette.current.ink3),modifier=Modifier.padding(vertical=14.dp))
        }
    }
}

@Composable private fun ColumnScope.BackupSettings(state:ShellState){
    LazyColumn(Modifier.weight(1f),contentPadding=PaddingValues(bottom=30.dp)){
        item{
            IntentSection("Portability")
            ActionRow("Export TSUNAMI backup","Settings · playlists · history · progress"){state.banner="Mock backup exported"}
            ActionRow("Restore TSUNAMI backup","Preview before applying"){state.banner="Mock restore preview opened"}
            ActionRow("TSUNAMI device migration",state.deviceMigrationStatus){state.prepareDeviceMigration()}
            ActionRow("Share TSUNAMI APK","Installed-shell handoff mock"){state.banner="TSUNAMI APK share sheet opened · mock"}
            ActionRow("Export longform progress","JSON mock"){state.banner="Longform progress exported"}
            ActionRow("Import longform progress","JSON mock"){state.banner="Longform progress import · 14 matched · 1 unmatched"}
            ActionRow("Preview path remap","${state.remapOldPath} → ${state.remapNewPath}"){state.cycleRemapPath()}
        }
        item{
            IntentSection("Rotating backup")
            ToggleRow("Automatic backup",if(state.autoBackupEnabled)"ON" else "OFF"){state.autoBackupEnabled=!state.autoBackupEnabled}
            if(state.autoBackupEnabled){
                ActionRow("Keep","${state.backupKeep} backups"){state.cycleBackupKeep()}
                ActionRow("Interval","${state.backupIntervalHours} hours"){state.cycleBackupInterval()}
                ActionRow("Backup now","Mock destination selected"){state.banner="Rotating backup complete"}
            }
        }
        item{
            IntentSection("Library state history")
            ActionRow("Previous state","Yesterday · 23:14"){state.banner="Previewed previous library state"}
            ActionRow("Next state","No newer state"){state.banner="Already at newest library state"}
        }
    }
}

private fun signedDb(v:Float)=when{
    v>0f->"+${v.toInt()}"
    v<0f->v.toInt().toString()
    else->"0"
}

@Composable private fun IntentSection(name:String,action:String?=null,onAction:(()->Unit)?=null){
    val p=LocalTsunamiPalette.current
    Spacer(Modifier.height(22.dp))
    Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically){
        Text(name,style=Type.title.copy(color=p.ink),modifier=Modifier.weight(1f))
        if(action!=null&&onAction!=null) TextCommand(action,onAction)
    }
    Spacer(Modifier.height(8.dp))
    Rule()
}

@Composable private fun ActionRow(title:String,state:String,onClick:()->Unit){
    val p=LocalTsunamiPalette.current
    Row(
        Modifier.fillMaxWidth().heightIn(min=66.dp).semantics{role=Role.Button}.clickable(onClick=onClick).padding(vertical=10.dp),
        verticalAlignment=Alignment.CenterVertically
    ){
        Column(Modifier.weight(1f)){
            Text(title,style=Type.row.copy(color=p.ink))
            Spacer(Modifier.height(2.dp))
            Text(state,style=Type.meta.copy(color=p.ink3),maxLines=2)
        }
        Box(Modifier.width(28.dp).height(1.dp).background(p.rule))
    }
    Rule()
}

@Composable private fun ToggleRow(title:String,state:String,onClick:()->Unit){
    val p=LocalTsunamiPalette.current
    Row(Modifier.fillMaxWidth().heightIn(min=62.dp).semantics{role=Role.Switch;stateDescription=state}.clickable(onClick=onClick).padding(vertical=10.dp),verticalAlignment=Alignment.CenterVertically){
        Text(title,style=Type.row.copy(color=p.ink),modifier=Modifier.weight(1f))
        Text(state,style=Type.micro.copy(color=p.selected,fontWeight=FontWeight.SemiBold))
    }
    Rule()
}


private fun monthLabel(month:Int)=listOf("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec").getOrElse((month-1).coerceIn(0,11)){"?"}
