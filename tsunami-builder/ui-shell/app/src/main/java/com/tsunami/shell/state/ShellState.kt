package com.tsunami.shell.state

import androidx.compose.runtime.*
import com.tsunami.shell.model.*

@Stable
class ShellState(val fixture: ShellFixture, initialScreen: PrimarySpace = PrimarySpace.LISTEN, initialTheme: ThemeMode = ThemeMode.LIGHT) {
    var primary by mutableStateOf(initialScreen)
    var expandedPlayer by mutableStateOf(false)
    var playerMode by mutableStateOf(PlayerMode.QUEUE)
    var theme by mutableStateOf(initialTheme)
    var reducedMotion by mutableStateOf(false)
    var highContrast by mutableStateOf(false)
    var largeControls by mutableStateOf(false)
    var hapticStrength by mutableIntStateOf(1)
    var denseLibrary by mutableStateOf(false)
    var advancedExperience by mutableStateOf(true)
    var listenLens by mutableStateOf("Deep cuts")
    var selectionMode by mutableStateOf(false)
    var currentIndex by mutableIntStateOf(0)
    var playing by mutableStateOf(!fixture.queueEmpty && !fixture.buffering && fixture.tracks.firstOrNull()?.available != false)
    var buffering by mutableStateOf(fixture.buffering)
    var positionMs by mutableLongStateOf(if(fixture.queueEmpty)0L else 94_000L)
    var shuffle by mutableStateOf(false)
    var repeat by mutableStateOf(RepeatMode.OFF)
    var sleepMinutes by mutableIntStateOf(0)
    var output by mutableStateOf("This device")
    var libraryLens by mutableStateOf(LibraryLens.TRACKS)
    var longformScope by mutableStateOf(LongformScope.ALL)
    var focusedObject by mutableStateOf<LibraryObject?>(null)
    var findFocusedObject by mutableStateOf<LibraryObject?>(null)
    var sortLabel by mutableStateOf("Recently played")
    var offlineOnly by mutableStateOf(false)
    var searchQuery by mutableStateOf("")
    var searchOwnedOnly by mutableStateOf(false)
    var searchKind by mutableStateOf(SearchKind.ALL)
    var searchIntent by mutableStateOf<SearchIntent?>(null)
    var settingsExpanded by mutableStateOf<String?>(null)
    var historyEnabled by mutableStateOf(true)
    var historyCleared by mutableStateOf(false)
    var pendingConfirmation by mutableStateOf<ConfirmationKind?>(null)
    var offlineMode by mutableStateOf(false)
    var wifiOnlyDownloads by mutableStateOf(true)
    var showOnlineOnMobileData by mutableStateOf(false)
    var downloadQuality by mutableStateOf("Source quality")
    var gapless by mutableStateOf(true)
    var crossfadeSeconds by mutableIntStateOf(0)
    var audioPreference by mutableStateOf("Source")
    var playbackSpeed by mutableFloatStateOf(1f)
    var preservePitch by mutableStateOf(true)
    var replayGainMode by mutableStateOf("Track")
    var dspEnabled by mutableStateOf(false)
    var dspPreampDb by mutableFloatStateOf(0f)
    var bassDb by mutableFloatStateOf(0f)
    var trebleDb by mutableFloatStateOf(0f)
    val eqBandsDb = mutableStateListOf(0f,0f,0f,0f,0f,0f,0f,0f,0f,0f)
    val lyricSourceOrder = mutableStateListOf("Embedded","LRC sidecar","LRCLIB","Whisper alignment")
    var monoDownmix by mutableStateOf(false)
    var stereoWidth by mutableFloatStateOf(1f)
    var visualizerMode by mutableStateOf("Spectrum")
    var visualizerSensitivity by mutableFloatStateOf(1f)
    var visualizerMonochrome by mutableStateOf(false)
    var visualizerAttack by mutableFloatStateOf(.25f)
    var visualizerRelease by mutableFloatStateOf(.35f)
    var visualizerSmoothing by mutableFloatStateOf(.55f)
    var visualizerGain by mutableFloatStateOf(1f)
    var visualizerLayers by mutableIntStateOf(4)
    var visualizerBatterySaver by mutableStateOf(true)
    var visualizerBeatBacklight by mutableStateOf(false)
    var visualizerBehindLyrics by mutableStateOf(false)
    var lyricsFollowPlayback by mutableStateOf(true)
    var lyricsWordTiming by mutableStateOf(true)
    var lyricsGlobalDelayMs by mutableIntStateOf(0)
    var lyricsArtworkBackdrop by mutableStateOf(false)
    var missingLyricsFallback by mutableStateOf(true)
    var lyricsAutoFetch by mutableStateOf(true)
    var showArtworkInPlayer by mutableStateOf(true)
    var compactPlayerMetadata by mutableStateOf(false)
    var squareArtwork by mutableStateOf(true)
    var excludedFolderCount by mutableIntStateOf(0)
    var excludedExtensions by mutableStateOf("m4a.tmp, part")
    var excludedGenres by mutableStateOf("none")
    var excludedPlaylistPaths by mutableStateOf("none")
    var shuffleMode by mutableStateOf("Balanced")
    var excludeAudiobooks by mutableStateOf(true)
    var seasonalExclusion by mutableStateOf(false)
    var seasonalStartMonth by mutableIntStateOf(11)
    var seasonalEndMonth by mutableIntStateOf(1)
    var suppressDuplicateTitles by mutableStateOf(true)
    var groupAlternateVersions by mutableStateOf(true)
    var artistSpacing by mutableIntStateOf(2)
    var albumSpacing by mutableIntStateOf(3)
    var genreSpacing by mutableIntStateOf(1)
    var moodSpacing by mutableIntStateOf(1)
    var shuffleNovelty by mutableFloatStateOf(.55f)
    var shuffleFamiliarity by mutableFloatStateOf(.45f)
    var compatibleKey by mutableStateOf(false)
    var genreBlend by mutableStateOf("Dance 50 · Trance 25 · Pop 25")
    val shufflePresets = mutableStateListOf("Balanced library","Discovery night")
    var crossfadeCurve by mutableStateOf("Equal power")
    var crossfadePolicy by mutableStateOf("Music only")
    var fadePauseMs by mutableIntStateOf(120)
    var fadeStopMs by mutableIntStateOf(180)
    var fadeSkipMs by mutableIntStateOf(80)
    var playbackPitch by mutableFloatStateOf(1f)
    var offloadPolicy by mutableStateOf("Automatic")
    var resamplingPolicy by mutableStateOf("Source-first")
    var skipSilenceLongform by mutableStateOf(false)
    var smartRewindSeconds by mutableIntStateOf(12)
    var loudnessNormalization by mutableStateOf(false)
    var preventClipping by mutableStateOf(true)
    var compressorEnabled by mutableStateOf(false)
    var limiterEnabled by mutableStateOf(true)
    var agcEnabled by mutableStateOf(false)
    var balance by mutableFloatStateOf(0f)
    var reverseStereo by mutableStateOf(false)
    var crossfeed by mutableFloatStateOf(0f)
    var reverb by mutableFloatStateOf(0f)
    var oneHandedNowPlaying by mutableStateOf(true)
    var swipeLeft by mutableStateOf("Previous")
    var swipeRight by mutableStateOf("Next")
    var swipeUp by mutableStateOf("Queue")
    var swipeDown by mutableStateOf("Collapse player")
    var longPressAction by mutableStateOf("Actions")
    var headsetSingle by mutableStateOf("Play/Pause")
    var headsetDouble by mutableStateOf("Next")
    var headsetTriple by mutableStateOf("Previous")
    var headsetLong by mutableStateOf("Actions")
    var listenBrainzEnabled by mutableStateOf(false)
    var lastFmEnabled by mutableStateOf(false)
    var playingNowEnabled by mutableStateOf(true)
    var loveHateSync by mutableStateOf(false)
    var scrobbleThreshold by mutableIntStateOf(50)
    var scrobbleThresholdCapSeconds by mutableIntStateOf(240)
    var autoBackupEnabled by mutableStateOf(false)
    var backupKeep by mutableIntStateOf(5)
    var backupIntervalHours by mutableIntStateOf(24)
    var remapOldPath by mutableStateOf("/Music")
    var remapNewPath by mutableStateOf("/Storage/Music")
    var activeLibraryProfile by mutableStateOf("Main library")
    var metadataTemplate by mutableStateOf("Title · Artist · Album")
    var albumArtistMode by mutableStateOf("Prefer album artist")
    var deviceMigrationStatus by mutableStateOf("Not prepared")
    var diagnosticsFault by mutableStateOf(fixture.error)
    var signalSection by mutableStateOf("Summary")
    var gaplessProbeResult by mutableStateOf("Not run")
    var diagnosticUnderruns by mutableIntStateOf(if(fixture.error)3 else 0)
    var diagnosticSinkErrors by mutableIntStateOf(0)
    var diagnosticCodecErrors by mutableIntStateOf(0)
    var lyricAuditStatus by mutableStateOf("Not audited")
    var lyricMissingCount by mutableIntStateOf(if(fixture.missingLyrics)3 else 1)
    var duplicateGroups by mutableIntStateOf(-1)
    var flacIntegrityFailures by mutableIntStateOf(-1)
    var analysisStatus by mutableStateOf("Ready")
    var replayPeriod by mutableStateOf("Month")
    var replayExportCount by mutableIntStateOf(0)
    val diagnosticLog = mutableStateListOf(
        "15:08:41 · route=AudioTrack · sink=stable",
        "15:08:38 · queue=8 · state=playing",
        "15:08:33 · library index coherent"
    )
    var sourceError by mutableStateOf(fixture.error)
    var searchFault by mutableStateOf(fixture.searchError)
    var downloadsFault by mutableStateOf(fixture.downloadsError)
    var providerTransient by mutableStateOf(when{fixture.providerConnecting->"connecting";fixture.providerError->"error";else->""})
    var loading by mutableStateOf(fixture.loading)
    var onboardingComplete by mutableStateOf(false)
    var banner by mutableStateOf<String?>(null)
    val favourites = mutableStateListOf<String>("afterglow", "vector", "serein")
    val selectedTrackIds = mutableStateListOf<String>()
    val downloads = mutableStateMapOf<String, DownloadState>().apply {
        fixture.tracks.take(4).forEach { put(it.id, DownloadState.DOWNLOADED) }
        if(fixture.downloadsActive) fixture.tracks.firstOrNull{it.provenance!=Provenance.OWNED}?.let{put(it.id,DownloadState.DOWNLOADING)}
    }
    val queue = mutableStateListOf<Track>().apply { if(!fixture.queueEmpty) addAll(fixture.tracks.take(8)) }
    val bookmarks = mutableStateMapOf<String, Long>()
    val playedLongform = mutableStateListOf<String>()
    val resumePositions = mutableStateMapOf<String, Long>().apply {
        fixture.tracks.filter{it.longform}.forEach{ put(it.id,it.durationMs/3) }
    }
    val services = mutableStateListOf<ServiceConnection>().apply { addAll(fixture.services) }
    val importProgress = mutableStateMapOf<String, Int>()
    val importAudits = mutableStateMapOf<String, ProviderImportAuditMock>()
    val playlistTracks = mutableStateMapOf<String, List<String>>().apply {
        put("Late driving", fixture.tracks.filterNot{it.longform}.take(4).map{it.id})
        put("Reference masters", fixture.tracks.filter{it.quality.contains("FLAC")}.take(6).map{it.id})
        put("Unfinished albums", fixture.tracks.filter{it.longform}.map{it.id})
    }
    val libraryRoots = mutableStateListOf("/Music/Library", "/Audiobooks")
    val librarySectionOrder = mutableStateListOf("Tracks","Albums","Artists","Playlists","Folders","Longform","Radio")
    val hiddenLibrarySections = mutableStateListOf<String>()
    val orientationLocks = mutableStateMapOf<String,String>()
    val quickActions = mutableStateListOf("Sleep timer")
    val miniPlayerExtras = mutableStateListOf("Favourite","Lyrics")
    val fullPlayerButtons = mutableStateListOf("Favourite","Offline","Share")
    val notificationActions = mutableStateListOf("Previous","Play/Pause","Next","Favourite")
    val quickSettingsActions = mutableStateListOf("Play/Pause","Next")
    var widgetLayout by mutableStateOf("Transport")
    var wearControlsEnabled by mutableStateOf(true)
    var wearSecondaryAction by mutableStateOf("Favourite")
    var activeSession by mutableStateOf<String?>(null)
    val contextRules = mutableStateListOf(
        ContextRuleMock("Morning focus",true,"06:00–10:00","Music"),
        ContextRuleMock("Late-night calm",false,"22:00–02:00","Music"),
    )
    val customSections = mutableStateListOf(
        CustomSectionMock("Lossless","format:FLAC","List"),
        CustomSectionMock("Unfinished longform","longform:true progress:<95%","Dense"),
    )
    val audioProfiles = mutableStateListOf(
        AudioProfileMock("Sony WH-1000X","Bluetooth headphones","DSP bypass"),
        AudioProfileMock("Living room","Cast speaker","Bass +3 dB"),
    )

    val currentTrack: Track? get() = queue.getOrNull(currentIndex.coerceIn(0,(queue.size-1).coerceAtLeast(0)))

    private fun storeCurrentLongformPosition(){
        currentTrack?.takeIf{it.longform}?.let{resumePositions[it.id]=positionMs.coerceIn(0L,it.durationMs)}
    }
    private fun restorePosition(track:Track)=if(track.longform) resumePositions[track.id]?.coerceIn(0L,track.durationMs) ?: track.durationMs/3 else 0L

    fun selectTrack(track: Track, play: Boolean = true) {
        if(!track.available && play){ banner="Unavailable · ${track.title}"; return }
        storeCurrentLongformPosition()
        val idx=queue.indexOfFirst { it.id==track.id }
        if(idx>=0) currentIndex=idx else { queue.add(0,track); currentIndex=0 }
        positionMs=restorePosition(track)
        playing=play && track.available
        buffering=false
        if(!track.available) banner="Unavailable · ${track.title}"
    }
    fun next() {
        if(queue.isEmpty()) return
        storeCurrentLongformPosition()
        val target=if(queue.size==1) 0 else if(!shuffle) (currentIndex+1)%queue.size else when(shuffleMode){
            "Album-aware" -> {
                val album=currentTrack?.album
                val same=(1 until queue.size).map{(currentIndex+it)%queue.size}.firstOrNull{queue[it].album==album && queue[it].available}
                same ?: (currentIndex+1)%queue.size
            }
            "Discovery" -> {
                val step=(queue.size/2).coerceAtLeast(1).let{if(it%queue.size==0)1 else it}
                (currentIndex+step)%queue.size
            }
            else -> {
                val step=1+(((currentTrack?.id?.hashCode() ?: currentIndex) and Int.MAX_VALUE)%(queue.size-1))
                (currentIndex+step)%queue.size
            }
        }
        currentIndex=(0 until queue.size).map{(target+it)%queue.size}.firstOrNull{queue[it].available} ?: target
        positionMs=currentTrack?.let(::restorePosition) ?: 0L
        buffering=false
        if(currentTrack?.available==false) playing=false
    }
    fun previous() {
        if(queue.isEmpty()) return
        storeCurrentLongformPosition()
        val target=(currentIndex-1+queue.size)%queue.size
        currentIndex=(0 until queue.size).map{(target-it+queue.size*2)%queue.size}.firstOrNull{queue[it].available} ?: target
        positionMs=currentTrack?.let(::restorePosition) ?: 0L
        buffering=false
        if(currentTrack?.available==false) playing=false
    }
    fun playNext(track:Track){
        val currentId=currentTrack?.id
        if(track.id==currentId){ banner="Already playing · ${track.title}"; return }
        val existing=queue.indexOfFirst{it.id==track.id}
        if(existing>=0 && queue[existing].id!=currentId) queue.removeAt(existing)
        val anchor=queue.indexOfFirst{it.id==currentId}.takeIf{it>=0} ?: currentIndex.coerceIn(0,queue.size)
        queue.add((anchor+1).coerceAtMost(queue.size),track)
        currentIndex=queue.indexOfFirst{it.id==currentId}.takeIf{it>=0}?:0
        banner="Play next · ${track.title}"
    }
    fun shuffleNext(track:Track){
        val currentId=currentTrack?.id
        if(track.id==currentId){ banner="Already playing · ${track.title}"; return }
        val existing=queue.indexOfFirst{it.id==track.id}
        if(existing>=0 && queue[existing].id!=currentId) queue.removeAt(existing)
        val anchor=queue.indexOfFirst{it.id==currentId}.takeIf{it>=0} ?: currentIndex.coerceIn(0,queue.size)
        val slots=(queue.size-anchor).coerceAtLeast(1)
        val offset=when(shuffleMode){
            "Album-aware" -> if(track.album==currentTrack?.album) 1 else 1+((track.id.hashCode() and Int.MAX_VALUE)%slots)
            "Discovery" -> (slots/2).coerceAtLeast(1)
            else -> 1+((track.id.hashCode() and Int.MAX_VALUE)%slots)
        }
        queue.add((anchor+offset).coerceAtMost(queue.size),track)
        currentIndex=queue.indexOfFirst{it.id==currentId}.takeIf{it>=0}?:0
        banner="Shuffled into next · ${track.title}"
    }
    fun chooseSearchIntent(intent:SearchIntent){ searchIntent=intent; searchQuery=""; if(intent==SearchIntent.ARTISTS) searchKind=SearchKind.ARTISTS else if(intent==SearchIntent.UNFINISHED) searchKind=SearchKind.LONGFORM else searchKind=SearchKind.ALL }
    fun clearSearchIntent(){ searchIntent=null }
    fun toggleFavourite(id:String){ if(id in favourites) favourites.remove(id) else favourites.add(id) }
    fun addToPlaylist(track:Track,name:String="Late driving"){
        val current=playlistTracks[name].orEmpty()
        if(track.id in current){banner="Already in $name";return}
        playlistTracks[name]=current+track.id
        banner="Added to $name · ${track.title}"
    }
    fun createPlaylistWith(track:Track){
        val base="New listening set"
        val name=generateSequence(1){it+1}.map{if(it==1)base else "$base $it"}.first{it !in playlistTracks}
        playlistTracks[name]=listOf(track.id)
        banner="Created $name · ${track.title}"
    }
    fun createEmptyPlaylist(){
        val base="Untitled playlist"
        val name=generateSequence(1){it+1}.map{if(it==1)base else "$base $it"}.first{it !in playlistTracks}
        playlistTracks[name]=emptyList()
        banner="Created $name"
    }
    fun toggleSelection(id:String){ if(id in selectedTrackIds) selectedTrackIds.remove(id) else selectedTrackIds.add(id) }
    fun clearSelection(){ selectedTrackIds.clear(); selectionMode=false }
    fun favouriteSelection(){
        selectedTrackIds.forEach{ id-> if(id !in favourites) favourites.add(id) }
        banner="${selectedTrackIds.size} favourited"; clearSelection()
    }
    fun downloadSelection(){
        selectedTrackIds.forEach{ id-> downloads[id]=DownloadState.DOWNLOADED }
        banner="${selectedTrackIds.size} available offline"; clearSelection()
    }
    fun addSelectionToPlaylist(name:String="Late driving"){
        val selected=fixture.tracks.filter{it.id in selectedTrackIds}.map{it.id}
        val current=playlistTracks[name].orEmpty()
        val additions=selected.filterNot{it in current}
        playlistTracks[name]=current+additions
        banner=if(additions.isEmpty())"Selection already in $name" else "${additions.size} added to $name"
        clearSelection()
    }
    fun queueSelectionNext(){
        val currentId=currentTrack?.id
        val chosen=fixture.tracks.filter{it.id in selectedTrackIds && it.id!=currentId}
        chosen.asReversed().forEach(::playNext)
        banner=if(chosen.isEmpty())"No new tracks to queue" else "${chosen.size} queued next"
        clearSelection()
    }
    fun toggleDownload(id:String){
        downloadsFault=false
        when(downloads[id] ?: DownloadState.REMOTE){
            DownloadState.REMOTE -> { downloads[id]=DownloadState.DOWNLOADING; banner="Download queued" }
            DownloadState.DOWNLOADING -> { downloads[id]=DownloadState.DOWNLOADED; banner="Available offline" }
            DownloadState.DOWNLOADED -> { downloads.remove(id); banner="Offline copy removed" }
        }
    }
    fun cycleRepeat(){ repeat=when(repeat){RepeatMode.OFF->RepeatMode.ALL;RepeatMode.ALL->RepeatMode.ONE;RepeatMode.ONE->RepeatMode.OFF} }
    fun cycleSleep(){ sleepMinutes=when(sleepMinutes){0->15;15->30;30->60;else->0} }
    fun runPlayerAction(action:String){
        when(action){
            "Previous" -> previous()
            "Play/Pause" -> togglePlayback()
            "Next" -> next()
            "Shuffle" -> shuffle=!shuffle
            "Repeat" -> cycleRepeat()
            "Favourite" -> currentTrack?.let{toggleFavourite(it.id)}
            "Queue" -> { playerMode=PlayerMode.QUEUE; expandedPlayer=true }
            "Lyrics" -> { playerMode=PlayerMode.LYRICS; expandedPlayer=true }
            "Output" -> { playerMode=PlayerMode.OUTPUT; expandedPlayer=true }
            "Sleep" -> cycleSleep()
            else -> banner="$action ready"
        }
    }
    fun cycleCrossfade(){ crossfadeSeconds=when(crossfadeSeconds){0->3;3->6;6->12;else->0}; banner=if(crossfadeSeconds==0)"Crossfade off" else "Crossfade ${crossfadeSeconds}s" }
    fun cycleHapticStrength(){ hapticStrength=when(hapticStrength){0->1;1->2;else->0}; banner="Haptic intensity · ${when(hapticStrength){0->"Off";1->"Standard";else->"Strong"}}" }
    fun cycleAudioPreference(){ audioPreference=when(audioPreference){"Source"->"Lossless";"Lossless"->"Data saver";else->"Source"}; banner="Audio preference · $audioPreference" }
    fun cyclePlaybackSpeed(){ playbackSpeed=when(playbackSpeed){1f->1.25f;1.25f->1.5f;1.5f->2f;else->1f}; banner="Default speed · ${playbackSpeed}×" }
    fun cycleReplayGain(){ replayGainMode=when(replayGainMode){"Off"->"Track";"Track"->"Album";else->"Off"}; banner="ReplayGain · $replayGainMode" }
    fun cycleDspPreamp(){ dspPreampDb=when(dspPreampDb){0f->3f;3f->-3f;else->0f} }
    fun cycleBass(){ bassDb=when(bassDb){0f->3f;3f->6f;6f->-3f;else->0f} }
    fun cycleTreble(){ trebleDb=when(trebleDb){0f->3f;3f->6f;6f->-3f;else->0f} }
    fun cycleEqBand(index:Int){ if(index !in eqBandsDb.indices)return;eqBandsDb[index]=when(eqBandsDb[index]){0f->3f;3f->6f;6f->-3f;else->0f} }
    fun resetEq(){ for(i in eqBandsDb.indices)eqBandsDb[i]=0f;banner="Equalizer reset · flat" }
    fun moveLyricSource(index:Int,delta:Int){
        if(index !in lyricSourceOrder.indices)return
        val target=(index+delta).coerceIn(0,lyricSourceOrder.lastIndex)
        if(target==index)return
        val item=lyricSourceOrder.removeAt(index);lyricSourceOrder.add(target,item);banner="Lyrics priority updated"
    }
    fun cycleStereoWidth(){ stereoWidth=when(stereoWidth){1f->1.25f;1.25f->1.5f;else->1f} }
    fun cycleVisualizerMode(){ visualizerMode=when(visualizerMode){"Spectrum"->"Line";"Line"->"Field";else->"Spectrum"} }
    fun cycleVisualizerSensitivity(){ visualizerSensitivity=when(visualizerSensitivity){1f->1.5f;1.5f->2f;else->1f} }
    fun cycleLyricsDelay(){ lyricsGlobalDelayMs=when(lyricsGlobalDelayMs){0->250;250->820;820->-250;else->0}; banner="Lyrics delay · ${lyricsGlobalDelayMs} ms" }
    fun cycleExcludedFolders(){ excludedFolderCount=(excludedFolderCount+1)%4; banner="Excluded folders · $excludedFolderCount" }
    fun cycleExcludedExtensions(){ excludedExtensions=when(excludedExtensions){"m4a.tmp, part"->"part, temp, opus.preview";"part, temp, opus.preview"->"none";else->"m4a.tmp, part"} }
    fun cycleExcludedGenres(){ excludedGenres=when(excludedGenres){"none"->"Audiobook, Spoken";"Audiobook, Spoken"->"Christmas, Holiday";else->"none"};banner="Excluded genres · $excludedGenres" }
    fun cycleExcludedPlaylistPaths(){ excludedPlaylistPaths=when(excludedPlaylistPaths){"none"->"/Imported/Temporary";"/Imported/Temporary"->"/Imported/Temporary, /Auto";else->"none"};banner="Excluded playlist paths · $excludedPlaylistPaths" }
    fun cycleVisualizerAttack(){ visualizerAttack=when(visualizerAttack){.25f->.5f;.5f->.75f;else->.25f} }
    fun cycleVisualizerRelease(){ visualizerRelease=when(visualizerRelease){.35f->.6f;.6f->.9f;else->.35f} }
    fun cycleVisualizerSmoothing(){ visualizerSmoothing=when(visualizerSmoothing){.55f->.75f;.75f->.25f;else->.55f} }
    fun cycleVisualizerGain(){ visualizerGain=when(visualizerGain){1f->1.5f;1.5f->2f;else->1f} }
    fun cycleVisualizerLayers(){ visualizerLayers=when(visualizerLayers){4->6;6->8;else->4} }
    fun cycleShuffleMode(){ shuffleMode=when(shuffleMode){"Balanced"->"Discovery";"Discovery"->"Album-aware";else->"Balanced"} }
    fun cycleSeasonalStart(){ seasonalStartMonth=if(seasonalStartMonth==12)1 else seasonalStartMonth+1 }
    fun cycleSeasonalEnd(){ seasonalEndMonth=if(seasonalEndMonth==12)1 else seasonalEndMonth+1 }
    fun cycleArtistSpacing(){ artistSpacing=when(artistSpacing){0->2;2->4;4->8;else->0} }
    fun cycleAlbumSpacing(){ albumSpacing=when(albumSpacing){0->3;3->6;6->12;else->0} }
    fun cycleGenreSpacing(){ genreSpacing=when(genreSpacing){0->1;1->3;3->6;else->0} }
    fun cycleMoodSpacing(){ moodSpacing=when(moodSpacing){0->1;1->3;3->6;else->0} }
    fun cycleShuffleNovelty(){ shuffleNovelty=when(shuffleNovelty){.25f->.55f;.55f->.8f;else->.25f} }
    fun cycleShuffleFamiliarity(){ shuffleFamiliarity=when(shuffleFamiliarity){.25f->.45f;.45f->.75f;else->.25f} }
    fun cycleGenreBlend(){ genreBlend=when(genreBlend){"Dance 50 · Trance 25 · Pop 25"->"Electronic 70 · Ambient 30";"Electronic 70 · Ambient 30"->"No genre weighting";else->"Dance 50 · Trance 25 · Pop 25"} }
    fun saveShufflePreset(){ val name="Preset ${shufflePresets.size+1} · $shuffleMode"; if(name !in shufflePresets)shufflePresets.add(name); banner="Shuffle preset saved" }
    fun cycleCrossfadeCurve(){ crossfadeCurve=when(crossfadeCurve){"Equal power"->"Linear";"Linear"->"Fast out";else->"Equal power"} }
    fun cycleCrossfadePolicy(){ crossfadePolicy=when(crossfadePolicy){"Music only"->"Everything";"Everything"->"Albums";else->"Music only"} }
    fun cycleFadePause(){ fadePauseMs=when(fadePauseMs){120->300;300->0;else->120} }
    fun cycleFadeStop(){ fadeStopMs=when(fadeStopMs){180->400;400->0;else->180} }
    fun cycleFadeSkip(){ fadeSkipMs=when(fadeSkipMs){80->180;180->0;else->80} }
    fun cyclePitch(){ playbackPitch=when(playbackPitch){1f->.95f;.95f->1.05f;else->1f} }
    fun cycleOffload(){ offloadPolicy=when(offloadPolicy){"Automatic"->"Never";"Never"->"Prefer";else->"Automatic"} }
    fun cycleResampling(){ resamplingPolicy=when(resamplingPolicy){"Source-first"->"Device-native";"Device-native"->"Highest quality";else->"Source-first"} }
    fun cycleSmartRewind(){ smartRewindSeconds=when(smartRewindSeconds){12->20;20->30;else->12} }
    fun cycleScrobbleThreshold(){ scrobbleThreshold=when(scrobbleThreshold){50->70;70->90;else->50} }
    fun cycleScrobbleCap(){ scrobbleThresholdCapSeconds=when(scrobbleThresholdCapSeconds){120->240;240->420;else->120} }
    fun cycleDownloadQuality(){ downloadQuality=when(downloadQuality){"Source quality"->"Lossless preferred";"Lossless preferred"->"Data saver";else->"Source quality"} }
    fun cycleRemapPath(){ val old=remapOldPath; remapOldPath=remapNewPath; remapNewPath=old; banner="Path remap preview · $remapOldPath → $remapNewPath" }
    fun cycleBackupKeep(){ backupKeep=when(backupKeep){5->10;10->20;else->5} }
    fun cycleBackupInterval(){ backupIntervalHours=when(backupIntervalHours){24->72;72->168;else->24} }
    fun cycleLibraryProfile(){ activeLibraryProfile=if(activeLibraryProfile=="Main library")"Travel library" else "Main library"; banner="Library profile · $activeLibraryProfile" }
    fun addMockLibraryRoot(){ val root=if("/Field Recordings" in libraryRoots)"/Imported Music" else "/Field Recordings"; if(root !in libraryRoots)libraryRoots.add(root); banner="Library root added · $root" }
    fun removeLibraryRoot(root:String){ if(libraryRoots.size<=1){banner="Keep at least one library root";return}; libraryRoots.remove(root); banner="Library root removed · $root" }
    fun toggleLibrarySection(section:String){
        if(section in hiddenLibrarySections) hiddenLibrarySections.remove(section)
        else {
            hiddenLibrarySections.add(section)
            val activeName=when(libraryLens){
                LibraryLens.TRACKS->"Tracks";LibraryLens.ALBUMS->"Albums";LibraryLens.ARTISTS->"Artists";LibraryLens.PLAYLISTS->"Playlists";LibraryLens.FOLDERS->"Folders";LibraryLens.LONGFORM->"Longform";LibraryLens.RADIO->"Radio"
            }
            if(activeName==section) libraryLens=LibraryLens.TRACKS
        }
    }
    fun moveLibrarySection(index:Int,delta:Int){
        if(index !in librarySectionOrder.indices)return
        val target=(index+delta).coerceIn(0,librarySectionOrder.lastIndex)
        if(target==index)return
        val section=librarySectionOrder.removeAt(index);librarySectionOrder.add(target,section)
        banner="Library order updated · $section"
    }
    fun cycleMetadataTemplate(){ metadataTemplate=when(metadataTemplate){"Title · Artist · Album"->"Title · Album · Year";"Title · Album · Year"->"Title · Format · Source";else->"Title · Artist · Album"} }
    fun cycleAlbumArtistMode(){ albumArtistMode=when(albumArtistMode){"Prefer album artist"->"Track artist only";"Track artist only"->"Album artist first";else->"Prefer album artist"};banner="Album artist · $albumArtistMode" }
    fun runGaplessProbe(){ gaplessProbeResult=if(gaplessProbeResult=="PASS")"Not run" else "PASS"; diagnosticLog.add("15:09:02 · gapless probe · $gaplessProbeResult"); banner="Gapless probe · $gaplessProbeResult" }
    fun resetDiagnosticCounters(){ diagnosticUnderruns=0;diagnosticSinkErrors=0;diagnosticCodecErrors=0;diagnosticsFault=false;diagnosticLog.add("15:09:05 · counters reset");banner="Playback counters reset" }
    fun auditLyrics(){ lyricAuditStatus="Audit complete"; lyricMissingCount=if(fixture.missingLyrics)3 else 1; diagnosticLog.add("15:09:12 · lyrics audit · $lyricMissingCount missing");banner="Lyrics audit · $lyricMissingCount missing" }
    fun fetchMissingLyrics(){ if(lyricMissingCount>0)lyricMissingCount=(lyricMissingCount-1).coerceAtLeast(0); lyricAuditStatus="Exact fetch complete";banner="Exact lyric fetch · $lyricMissingCount still missing" }
    fun scanDuplicateHashes(){ duplicateGroups=if(duplicateGroups<0)2 else 0;banner="SHA-256 duplicate scan · $duplicateGroups groups" }
    fun scanFlacIntegrity(){ flacIntegrityFailures=if(flacIntegrityFailures<0)0 else (flacIntegrityFailures+1)%2;banner="FLAC decode scan · $flacIntegrityFailures failures" }
    fun analyzeCurrentTrack(){ analysisStatus=currentTrack?.let{"${it.title} · 118 BPM · C minor · energy 64%"}?:"Nothing playing";banner="Track analysis complete" }
    fun analyzeLibrary(){ analysisStatus="Analysed ${fixture.libraryCount} indexed items";banner="Library analysis complete" }
    fun cycleReplayPeriod(){ replayPeriod=when(replayPeriod){"Week"->"Month";"Month"->"Year";"Year"->"All";else->"Week"} }
    fun exportReplay(kind:String){ replayExportCount++;banner="TSUNAMI Replay · $kind export ready" }
    fun exportDiagnostics(){ banner="Diagnostics bundle preview ready"; diagnosticLog.add("15:09:30 · diagnostics bundle exported") }
    fun prepareDeviceMigration(){ deviceMigrationStatus=if(deviceMigrationStatus=="Ready to send")"Not prepared" else "Ready to send"; banner=if(deviceMigrationStatus=="Ready to send")"TSUNAMI migration package ready" else "Migration package cleared" }
    fun clearDiagnosticLog(){ diagnosticLog.clear();banner="Diagnostic log cleared" }
    fun cycleOrientation(view:String){ val next=when(orientationLocks[view] ?: "Auto"){"Auto"->"Portrait";"Portrait"->"Landscape";else->"Auto"}; if(next=="Auto")orientationLocks.remove(view) else orientationLocks[view]=next }
    fun cycleSwipeLeft(){ swipeLeft=when(swipeLeft){"Previous"->"Queue";"Queue"->"Favourite";else->"Previous"} }
    fun cycleSwipeRight(){ swipeRight=when(swipeRight){"Next"->"Lyrics";"Lyrics"->"Favourite";else->"Next"} }
    fun cycleSwipeUp(){ swipeUp=when(swipeUp){"Queue"->"Lyrics";"Lyrics"->"Expand player";else->"Queue"} }
    fun cycleSwipeDown(){ swipeDown=when(swipeDown){"Collapse player"->"Queue";"Queue"->"Dismiss overlay";else->"Collapse player"} }
    fun toggleMiniPlayerExtra(action:String){
        if(action in miniPlayerExtras) miniPlayerExtras.remove(action)
        else if(miniPlayerExtras.size<2) miniPlayerExtras.add(action)
        else banner="Mini player allows two extra actions"
    }
    fun toggleFullPlayerButton(action:String){
        if(action in fullPlayerButtons) fullPlayerButtons.remove(action)
        else if(fullPlayerButtons.size<5) fullPlayerButtons.add(action)
        else banner="Full player allows five contextual actions"
    }
    fun toggleNotificationAction(action:String){
        if(action in notificationActions) notificationActions.remove(action)
        else if(notificationActions.size<5) notificationActions.add(action)
        else banner="Notification allows five actions"
    }
    fun toggleQuickSettingsAction(action:String){
        if(action in quickSettingsActions) quickSettingsActions.remove(action)
        else if(quickSettingsActions.size<2) quickSettingsActions.add(action)
        else banner="Quick Settings exposes two transport actions"
    }
    fun cycleWidgetLayout(){
        widgetLayout=when(widgetLayout){"Transport"->"Listening";"Listening"->"Compact";else->"Transport"}
        banner="Widget layout · $widgetLayout"
    }
    fun cycleWearSecondaryAction(){
        wearSecondaryAction=when(wearSecondaryAction){"Favourite"->"Queue";"Queue"->"Output";else->"Favourite"}
        banner="Wear secondary action · $wearSecondaryAction"
    }
    fun cycleLongPress(){ longPressAction=when(longPressAction){"Actions"->"Favourite";"Favourite"->"Queue next";else->"Actions"} }
    fun addQuickAction(){ val candidates=listOf("Sleep timer","Bookmark","Play next","Add to playlist","Shuffle next"); val next=candidates.firstOrNull{it !in quickActions}; if(next!=null){quickActions.add(next);banner="Quick action added · $next"}else banner="All available quick actions already added" }
    fun removeQuickAction(label:String){quickActions.remove(label);banner="Quick action removed · $label"}
    fun toggleSession(){ activeSession=if(activeSession==null)"Focus" else null; banner=activeSession?.let{"Session started · $it"}?:"Session ended" }
    fun toggleContextRule(index:Int){ val r=contextRules[index];contextRules[index]=r.copy(enabled=!r.enabled) }
    fun addContextRule(){ val n=contextRules.size+1;contextRules.add(ContextRuleMock("Context rule $n",true,if(n%2==0)"18:00–23:00" else "Any time",if(n%2==0)"Music" else "Any queue"));banner="Context rule added" }
    fun removeContextRule(index:Int){ if(index in contextRules.indices){val name=contextRules[index].name;contextRules.removeAt(index);banner="Context rule removed · $name"} }
    fun addCustomSection(){ val n=customSections.size+1;customSections.add(CustomSectionMock("Custom $n","favourite:true","List"));banner="Custom library section added" }
    fun removeCustomSection(index:Int){ if(index in customSections.indices){val name=customSections[index].name;customSections.removeAt(index);banner="Custom section removed · $name"} }
    fun addAudioProfile(){ val n=audioProfiles.size+1;audioProfiles.add(AudioProfileMock("Profile $n",output,if(dspEnabled)"DSP active" else "DSP bypass"));banner="Audio profile saved" }
    fun removeAudioProfile(index:Int){ if(index in audioProfiles.indices){val name=audioProfiles[index].name;audioProfiles.removeAt(index);banner="Audio profile removed · $name"} }
    fun shareTimestamp(){ banner="Timestamp ready · ${formatTime(positionMs)}" }
    fun requestClearHistory(){ pendingConfirmation=ConfirmationKind.CLEAR_HISTORY }
    fun dismissConfirmation(){ pendingConfirmation=null }
    fun confirmPending(){
        when(pendingConfirmation){
            ConfirmationKind.CLEAR_HISTORY -> { historyCleared=true; banner="Listening history cleared" }
            null -> Unit
        }
        pendingConfirmation=null
    }
    fun resolveBuffering(){ buffering=false; playing=currentTrack?.available != false; banner=if(playing)"Playback ready" else "Current item unavailable" }
    fun togglePlayback(){
        val track=currentTrack
        if(track?.available==false){ playing=false; buffering=false; banner="Unavailable · ${track.title}"; return }
        if(buffering){ resolveBuffering(); return }
        playing=!playing
    }
    fun seekFraction(f:Float){ currentTrack?.let {
        positionMs=(it.durationMs*f.coerceIn(0f,1f)).toLong()
        if(it.longform) resumePositions[it.id]=positionMs
    } }
    fun seekRelative(deltaMs:Long){
        val track=currentTrack ?: return
        positionMs=(positionMs+deltaMs).coerceIn(0L,track.durationMs)
        if(track.longform) resumePositions[track.id]=positionMs
        banner=if(deltaMs<0)"Back ${(-deltaMs/1000)} seconds" else "Forward ${deltaMs/1000} seconds"
    }
    fun togglePlayedLongform(track:Track?=currentTrack){
        val item=track ?: return
        if(!item.longform) return
        if(item.id in playedLongform){
            playedLongform.remove(item.id)
            banner="Marked unplayed · ${item.title}"
        }else{
            playedLongform.add(item.id)
            resumePositions[item.id]=item.durationMs
            if(item.id==currentTrack?.id) positionMs=item.durationMs
            banner="Marked played · ${item.title}"
        }
    }
    fun moveQueue(from:Int,to:Int){ if(from !in queue.indices || to !in queue.indices)return; val currentId=currentTrack?.id; val t=queue.removeAt(from); queue.add(to,t); currentIndex=queue.indexOfFirst{it.id==currentId}.takeIf{it>=0}?:0 }
    fun removeFromQueue(index:Int){
        if(index !in queue.indices)return
        val currentId=currentTrack?.id
        val removingCurrent=queue[index].id==currentId
        queue.removeAt(index)
        if(queue.isEmpty()){
            currentIndex=0
            positionMs=0L
            playing=false
            buffering=false
            banner="Queue empty"
            return
        }
        currentIndex=if(removingCurrent){
            index.coerceAtMost(queue.lastIndex)
        }else{
            queue.indexOfFirst{it.id==currentId}.takeIf{it>=0} ?: currentIndex.coerceIn(0,queue.lastIndex)
        }
        if(removingCurrent){
            positionMs=currentTrack?.let(::restorePosition) ?: 0L
            buffering=false
        }
    }
    fun retrySearch(){ searchFault=false; banner="Search source recovered" }
    fun retryDownloads(){ downloadsFault=false; banner="Downloads recovered · queued work preserved" }
    fun retryProvider(){ providerTransient=""; banner="Provider connection ready to retry" }
    fun toggleService(index:Int){
        providerTransient=""
        val s=services[index]
        val connected=!s.connected
        val retained=importAudits[s.name]!=null
        services[index]=s.copy(
            connected=connected,
            detail=if(connected)"Connected · preview library ready" else if(retained)"Disconnected · imported library kept" else "Not connected"
        )
        banner=if(connected)"Connected ${s.name}" else if(retained)"Disconnected ${s.name} · imported library kept" else "Disconnected ${s.name}"
    }
    fun advanceImport(index:Int){
        val s=services[index]
        if(!s.connected){ banner="Connect ${s.name} first"; return }
        val next=((importProgress[s.name] ?: 0)+25).coerceAtMost(100)
        importProgress[s.name]=next
        if(next==100){
            val audit=when(s.name){
                "YouTube Music"->ProviderImportAuditMock(1842,38,19,7,4)
                "Spotify"->ProviderImportAuditMock(612,0,0,0,11)
                else->ProviderImportAuditMock(428,0,0,3,6)
            }
            importAudits[s.name]=audit
            banner="${s.name} import complete · ${audit.imported} imported"
        }else banner="${s.name} import ${next}%"
    }
    fun describeImportAudit(name:String):String{
        val audit=importAudits[name] ?: return "No completed import"
        return "${audit.imported} imported · ${audit.excludedTotal} excluded"
    }
    fun announceImportAudit(name:String){
        val audit=importAudits[name] ?: run{banner="No completed import for $name";return}
        banner="${name}: ${audit.imported} imported · Shorts ${audit.shortsExcluded} · video-only ${audit.videoOnlyExcluded} · samples ${audit.samplesExcluded} · unmatched ${audit.unmatched}"
    }
}

@Composable
fun rememberShellState(fixture: ShellFixture, initialScreen: PrimarySpace, theme: ThemeMode): ShellState = remember(fixture,initialScreen,theme){ ShellState(fixture,initialScreen,theme) }
