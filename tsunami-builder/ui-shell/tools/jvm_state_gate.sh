#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
command -v kotlinc >/dev/null || { echo 'JVM_STATE_GATE=SKIP kotlinc unavailable'; exit 2; }
command -v java >/dev/null || { echo 'JVM_STATE_GATE=SKIP java unavailable'; exit 2; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/androidx/compose/runtime"
cat > "$TMP/androidx/compose/runtime/RuntimeStubs.kt" <<'KOTLIN'
package androidx.compose.runtime
import kotlin.reflect.KProperty
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.PROPERTY) annotation class Stable
@Target(AnnotationTarget.FUNCTION) annotation class Composable
class MutableState<T>(var value:T){operator fun getValue(thisRef:Any?,property:KProperty<*>):T=value;operator fun setValue(thisRef:Any?,property:KProperty<*>,newValue:T){value=newValue}}
class MutableIntState(var value:Int){operator fun getValue(thisRef:Any?,property:KProperty<*>):Int=value;operator fun setValue(thisRef:Any?,property:KProperty<*>,newValue:Int){value=newValue}}
class MutableLongState(var value:Long){operator fun getValue(thisRef:Any?,property:KProperty<*>):Long=value;operator fun setValue(thisRef:Any?,property:KProperty<*>,newValue:Long){value=newValue}}
class MutableFloatState(var value:Float){operator fun getValue(thisRef:Any?,property:KProperty<*>):Float=value;operator fun setValue(thisRef:Any?,property:KProperty<*>,newValue:Float){value=newValue}}
fun <T> mutableStateOf(v:T)=MutableState(v)
fun mutableIntStateOf(v:Int)=MutableIntState(v)
fun mutableLongStateOf(v:Long)=MutableLongState(v)
fun mutableFloatStateOf(v:Float)=MutableFloatState(v)
fun <T> mutableStateListOf(vararg v:T):MutableList<T> = v.toMutableList()
fun <K,V> mutableStateMapOf(vararg v:Pair<K,V>):MutableMap<K,V> = linkedMapOf(*v)
fun <T> remember(vararg keys:Any?, calculation:()->T):T=calculation()
KOTLIN
cat > "$TMP/StateBehavior.kt" <<'KOTLIN'
import com.tsunami.shell.model.*
import com.tsunami.shell.state.ShellState
fun ok(v:Boolean,m:String){if(!v) error(m)}
fun main(){
 val f=defaultFixture("default"); val s=ShellState(f)
 ok(f.services.map{it.name}==listOf("YouTube Music","Apple Music","Amazon Music","TIDAL","Spotify"),"provider fixture parity")
 ok(s.currentTrack?.id=="afterglow","initial current")
 val serein=f.tracks.first{it.id=="serein"}; s.playNext(serein); ok(s.queue.getOrNull(1)?.id=="serein","playNext"); ok(s.currentTrack?.id=="afterglow","preserve current")
 s.shuffleMode="Album-aware"; val slow=f.tracks.first{it.id=="slowarc"}; s.shuffleNext(slow); ok(s.queue.any{it.id=="slowarc"},"shuffleNext")
 val beforeRemoval=s.queue.toList(); val removeIndex=s.currentIndex; val expectedNext=beforeRemoval.getOrNull(removeIndex+1)?.id ?: beforeRemoval.getOrNull(removeIndex-1)?.id; s.removeFromQueue(removeIndex); ok(s.currentTrack?.id==expectedNext,"remove current preserves queue locality")
 val drain=ShellState(f); while(drain.queue.isNotEmpty()) drain.removeFromQueue(0); ok(drain.currentTrack==null&&!drain.playing&&drain.banner=="Queue empty","empty queue state")
 s.toggleSelection("passage"); s.toggleSelection("vector"); s.queueSelectionNext(); ok(!s.selectionMode&&s.selectedTrackIds.isEmpty(),"selection clear")
 s.selectionMode=true;s.toggleSelection("serein");val playlistBefore=s.playlistTracks["Late driving"].orEmpty().size;s.addSelectionToPlaylist();ok(s.playlistTracks["Late driving"].orEmpty().size==playlistBefore+1,"selection playlist");ok(!s.selectionMode&&s.selectedTrackIds.isEmpty(),"selection playlist clear")
 s.addToPlaylist(serein); ok("serein" in s.playlistTracks["Late driving"].orEmpty(),"playlist")
 s.toggleDownload("catalogue"); ok(s.downloads["catalogue"]==DownloadState.DOWNLOADING,"download pending"); s.toggleDownload("catalogue"); ok(s.downloads["catalogue"]==DownloadState.DOWNLOADED,"download complete")
 repeat(4){s.advanceImport(0)}; ok(s.importProgress["YouTube Music"]==100,"import")
 val originalOrder=s.librarySectionOrder.toList();s.moveLibrarySection(1,-1);ok(s.librarySectionOrder.first()=="Albums","library order");s.moveLibrarySection(0,1);ok(s.librarySectionOrder==originalOrder,"library order restore");s.libraryLens=LibraryLens.ALBUMS; s.toggleLibrarySection("Albums"); ok(s.libraryLens==LibraryLens.TRACKS,"lens fallback")
 s.seekFraction(.5f); ok(s.positionMs==s.currentTrack!!.durationMs/2,"seek")
 val book=f.tracks.first{it.id=="book"};s.selectTrack(book,true);val resumeStart=s.positionMs;s.seekFraction(.62f);val saved=s.positionMs;s.selectTrack(serein,true);s.selectTrack(book,false);ok(s.positionMs==saved && s.positionMs!=resumeStart,"longform resume")
 s.cycleCrossfadeCurve(); ok(s.crossfadeCurve=="Linear","crossfade curve"); s.cycleOffload(); ok(s.offloadPolicy=="Never","offload"); s.cycleEqBand(0);ok(s.eqBandsDb[0]==3f,"equalizer");s.resetEq();ok(s.eqBandsDb.all{it==0f},"equalizer reset"); s.cycleVisualizerLayers(); ok(s.visualizerLayers==6,"visualizer")
 s.cycleLyricsDelay();ok(s.lyricsGlobalDelayMs==250,"lyrics delay");s.lyricsWordTiming=false;ok(!s.lyricsWordTiming,"lyrics timing mode");s.lyricsAutoFetch=false;ok(!s.lyricsAutoFetch,"lyrics auto-fetch");val sourceFirst=s.lyricSourceOrder.first();s.moveLyricSource(1,-1);ok(s.lyricSourceOrder.first()!=sourceFirst&&s.lyricSourceOrder.first()=="LRC sidecar","lyric source priority");s.showArtworkInPlayer=false;ok(!s.showArtworkInPlayer,"player artwork toggle");s.cycleExcludedFolders();ok(s.excludedFolderCount==1,"folder exclusions");s.cycleExcludedExtensions();ok(s.excludedExtensions=="part, temp, opus.preview","extension exclusions");s.cycleExcludedGenres();ok(s.excludedGenres=="Audiobook, Spoken","genre exclusions");s.cycleExcludedPlaylistPaths();ok(s.excludedPlaylistPaths=="/Imported/Temporary","playlist path exclusions")
 s.highContrast=true;s.largeControls=true;s.cycleHapticStrength();ok(s.hapticStrength==2,"accessibility state");s.advancedExperience=false;ok(!s.advancedExperience,"standard experience");s.advancedExperience=true;s.cycleSwipeUp();ok(s.swipeUp=="Lyrics","swipe up");s.cycleSwipeDown();ok(s.swipeDown=="Queue","swipe down");s.cycleAlbumArtistMode();ok(s.albumArtistMode=="Track artist only","album artist");s.prepareDeviceMigration();ok(s.deviceMigrationStatus=="Ready to send","device migration")
 s.shuffleMode="Balanced";s.cycleShuffleMode();ok(s.shuffleMode=="Discovery","shuffle mode");s.cycleArtistSpacing();ok(s.artistSpacing==4,"shuffle artist spacing");s.cycleGenreBlend();ok(s.genreBlend=="Electronic 70 · Ambient 30","genre blend");s.compatibleKey=true;ok(s.compatibleKey,"compatible key")
 s.wifiOnlyDownloads=false;s.showOnlineOnMobileData=true;s.cycleDownloadQuality();ok(s.downloadQuality=="Lossless preferred","download policy")
 s.playingNowEnabled=false;s.loveHateSync=true;s.cycleScrobbleCap();ok(s.scrobbleThresholdCapSeconds==420,"scrobble cap")
 val oldPath=s.remapOldPath;s.cycleRemapPath();ok(s.remapNewPath==oldPath,"path remap")
 val r=s.contextRules.size;s.addContextRule();ok(s.contextRules.size==r+1,"context add");s.toggleContextRule(0);ok(!s.contextRules[0].enabled,"context toggle")
 val q=s.quickActions.size;s.addQuickAction();ok(s.quickActions.size==q+1,"quick action")
 val mini=s.miniPlayerExtras.size;s.toggleMiniPlayerExtra("Queue");ok(s.miniPlayerExtras.size==mini,"mini extras cap");s.toggleMiniPlayerExtra("Favourite");ok("Favourite" !in s.miniPlayerExtras,"mini extra remove");s.toggleMiniPlayerExtra("Queue");ok("Queue" in s.miniPlayerExtras,"mini extra add")
 s.toggleNotificationAction("Shuffle");ok("Shuffle" in s.notificationActions&&s.notificationActions.size==5,"notification action add");s.toggleNotificationAction("Repeat");ok("Repeat" !in s.notificationActions&&s.banner=="Notification allows five actions","notification cap")
 val sh=s.shuffle;s.runPlayerAction("Shuffle");ok(s.shuffle!=sh,"customized player action");s.runPlayerAction("Lyrics");ok(s.playerMode==PlayerMode.LYRICS&&s.expandedPlayer,"player action route")
 s.toggleSession();ok(s.activeSession=="Focus","session start");s.toggleSession();ok(s.activeSession==null,"session end")
 val p=s.audioProfiles.size;s.addAudioProfile();ok(s.audioProfiles.size==p+1,"profile")
 val cs=s.customSections.size;s.addCustomSection();ok(s.customSections.size==cs+1,"custom section")
 val bufferingState=ShellState(defaultFixture("buffering"));ok(bufferingState.buffering&&!bufferingState.playing,"buffering fixture");bufferingState.togglePlayback();ok(!bufferingState.buffering&&bufferingState.playing,"buffer resolution")
 val unavailableState=ShellState(defaultFixture("unavailable"));ok(unavailableState.currentTrack?.available==false&&!unavailableState.playing,"unavailable fixture");unavailableState.togglePlayback();ok(unavailableState.banner?.startsWith("Unavailable")==true,"unavailable guard");unavailableState.next();ok(unavailableState.currentTrack?.available==true,"unavailable skip")
 ok(defaultFixture("partial").partial,"partial fixture")
 s.libraryViewMode="Index";ok(s.libraryViewMode=="Index","library index view");s.libraryViewMode="Ledger";ok(s.libraryViewMode=="Ledger","library ledger view")
 val emptyQueue=ShellState(defaultFixture("queue-empty"));ok(emptyQueue.queue.isEmpty()&&emptyQueue.currentTrack==null&&!emptyQueue.playing&&emptyQueue.positionMs==0L,"queue-empty fixture")
 val searchFailure=ShellState(defaultFixture("search-error"));ok(searchFailure.searchFault,"search-error fixture");searchFailure.retrySearch();ok(!searchFailure.searchFault,"search recovery")
 val providerConnecting=ShellState(defaultFixture("provider-connecting"));ok(providerConnecting.providerTransient=="connecting","provider connecting");providerConnecting.retryProvider();ok(providerConnecting.providerTransient.isEmpty(),"provider connecting recovery")
 val providerFailure=ShellState(defaultFixture("provider-error"));ok(providerFailure.providerTransient=="error","provider error");providerFailure.retryProvider();ok(providerFailure.providerTransient.isEmpty(),"provider error recovery")
 val downloadFailure=ShellState(defaultFixture("downloads-error"));ok(downloadFailure.downloadsFault,"downloads error");downloadFailure.retryDownloads();ok(!downloadFailure.downloadsFault,"downloads recovery")
 val downloadActive=ShellState(defaultFixture("downloads-active"));ok(downloadActive.downloads.values.any{it==DownloadState.DOWNLOADING},"downloads active")
 ok(defaultFixture("small-list").tracks.size==40,"40 fixture");ok(defaultFixture("long-list").tracks.size==4008,"4k fixture");ok(defaultFixture("huge-list").tracks.size==40008,"40k fixture")
 ok(formatTime(94_000)=="1:34","time")
 println("JVM_STATE_GATE=PASS queue=\${s.queue.size} playlist=\${s.playlistTracks[\"Late driving\"]?.size} rules=\${s.contextRules.size} profiles=\${s.audioProfiles.size} shuffle=\${s.shuffleMode} accessibility=\${s.highContrast}/\${s.largeControls} library40k=\${defaultFixture(\"huge-list\").tracks.size}")
}
KOTLIN
kotlinc "$TMP/androidx/compose/runtime/RuntimeStubs.kt"   "$ROOT/app/src/main/java/com/tsunami/shell/model/MockModels.kt"   "$ROOT/app/src/main/java/com/tsunami/shell/state/ShellState.kt"   "$TMP/StateBehavior.kt" -include-runtime -d "$TMP/state-gate.jar"
java -jar "$TMP/state-gate.jar"
