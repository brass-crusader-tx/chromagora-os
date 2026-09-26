package com.tsunami.shell

import android.content.pm.ActivityInfo

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class GenesisInteractionTest {
    @get:Rule val compose = createAndroidComposeRule<MainActivity>()

    private fun openSetting(label: String) {
        compose.onNodeWithTag("settings-root-list").performScrollToNode(hasText(label))
        compose.onNodeWithText(label).assertHasClickAction().performClick()
    }

    private fun scrollListTo(tag: String, label: String) {
        compose.onNodeWithTag(tag).performScrollToNode(hasText(label))
    }

    @Test fun rotationPreservesLibraryAndListeningContext() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("owned + indexed").assertExists()
        compose.activity.requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        compose.waitForIdle()
        compose.onNodeWithText("owned + indexed").assertExists()
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
        compose.activity.requestedOrientation=ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        compose.waitForIdle()
        compose.onNodeWithText("owned + indexed").assertExists()
    }

    @Test fun primaryIndexChangesWorkspaceAndBackPreservesPlaybackContext() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("owned + indexed").assertExists()
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Track, album, artist, folder…").assertExists()
        compose.onNodeWithText("Signal", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Playback truth").assertExists()
        compose.onNodeWithText("Listen", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Your listening line").assertExists()
    }

    @Test fun transportAndExpandedListeningAreInteractive() {
        compose.onAllNodesWithContentDescription("Track actions").onFirst().performClick()
        compose.onNodeWithText("Play next").performClick()
        compose.onNodeWithText("Already playing · Afterglow at the Edge of the City").assertExists()
        compose.onNodeWithContentDescription("Pause").performClick()
        compose.onNodeWithContentDescription("Play").assertExists()
        compose.onNodeWithContentDescription("Open listening environment").performClick()
        compose.onNodeWithText("NOW PLAYING").assertExists()
        compose.onNodeWithText("Share 1:34").performClick()
        compose.onNodeWithText("Timestamp ready · 1:34").assertExists()
        compose.onAllNodesWithText("Lyrics").onFirst().performClick()
        compose.onNodeWithText("Streetlights fold into the rain").assertExists()
        compose.onNodeWithText("Output").performClick()
        compose.onNodeWithText("Sony WH-1000X").performClick()
        compose.onNodeWithText("Output: Sony WH-1000X").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Your listening line").assertExists()
    }

    @Test fun libraryIndexModeRemovesArtworkDependencyStructurally() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onAllNodesWithContentDescription("Artwork for Afterglow at the Edge of the City").onFirst().assertExists()
        compose.onNodeWithText("Index").performClick()
        compose.onNodeWithText("Library view · Index").assertExists()
        compose.onNodeWithText("Dense").assertDoesNotExist()
        compose.onNodeWithText("Comfortable").assertDoesNotExist()
        compose.onNodeWithText("Title A–Z").assertDoesNotExist()
        compose.onAllNodesWithContentDescription("Artwork for Afterglow at the Edge of the City").assertCountEquals(0)
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
        compose.onNodeWithText("Ledger").performClick()
        compose.onNodeWithText("Title A–Z").assertExists()
        compose.onNodeWithText("Dense").assertExists()
        compose.onAllNodesWithContentDescription("Artwork for Afterglow at the Edge of the City").onFirst().assertExists()
    }

    @Test fun libraryMultiSelectMutatesMockState() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Select").performClick()
        compose.onNodeWithText("Passage / Northbound").performClick()
        compose.onNodeWithText("1 selected").assertExists()
        compose.onAllNodesWithText("Offline").onLast().performClick()
        compose.onNodeWithText("1 available offline").assertExists()
        compose.onNodeWithText("Select").assertExists()
    }


    @Test fun folderObjectsUseFixtureTruthAndDistinctContents() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Folders").performClick()
        compose.onNodeWithText("3,912 tracks").assertDoesNotExist()
        compose.onNodeWithText("/Audiobooks").performClick()
        compose.onNodeWithText("The Cartographer's Sleep").assertExists()
        compose.onNodeWithText("Designing for Interruption").assertDoesNotExist()
        compose.onNodeWithContentDescription("Back to library").performClick()
        compose.onNodeWithText("owned + indexed").assertExists()
    }

    @Test fun libraryObjectsHaveReversibleDepth() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Albums").performClick()
        compose.onNodeWithText("Refractions").performClick()
        compose.onNodeWithText("ALBUM").assertExists()
        compose.onNodeWithContentDescription("Back to library").performClick()
        compose.onNodeWithText("owned + indexed").assertExists()
    }

    @Test fun searchIntentWorksBeforeTyping() {
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Find downloaded music").performClick()
        compose.onNodeWithText("Downloaded").assertExists()
        compose.onNodeWithText("4 results").assertExists()
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
    }


    @Test fun searchToleratesOneEditOrAdjacentTransposition() {
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithContentDescription("Search music").performTextInput("Mria")
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
    }

    @Test fun searchObjectDepthReturnsToResults() {
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithContentDescription("Search music").performTextInput("Refractions")
        compose.onNodeWithText("Albums").performClick()
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().performClick()
        compose.onNodeWithText("FIND / ALBUM").assertExists()
        compose.onNodeWithContentDescription("Back to search results").performClick()
        compose.onNodeWithText("1 results").assertExists()
    }



    @Test fun listenLensesStayLibraryCentricAndInteractive() {
        scrollListTo("listen-list", "Deep cuts")
        compose.onNodeWithText("Deep cuts").assertExists()
        compose.onNodeWithText("Rediscover").performClick()
        compose.onNodeWithTag("listen-list").performScrollToNode(hasContentDescription("REDISCOVER", substring = true))
        compose.onAllNodes(hasContentDescription("REDISCOVER", substring = true) and hasClickAction()).onFirst().assertExists()
        compose.onNodeWithTag("listen-list").performScrollToNode(hasText("Unfinished"))
        compose.onNodeWithText("Unfinished").performClick()
        compose.onNodeWithTag("listen-list").performScrollToNode(hasText("The Cartographer's Sleep"))
        compose.onNodeWithText("The Cartographer's Sleep").assertExists()
    }

    @Test fun folderSearchNavigatesARealObject() {
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Folders").performClick()
        compose.onNodeWithTag("find-results-list").performScrollToNode(hasContentDescription("/Music/Library", substring = true))
        compose.onNode(hasContentDescription("/Music/Library", substring = true) and hasClickAction()).performClick()
        compose.onNodeWithText("FIND / FOLDER").assertExists()
        compose.onNodeWithContentDescription("Back to search results").performClick()
        compose.onNodeWithText("Folders").assertExists()
    }

    @Test fun signalDepthIsInteractiveAndTruthful() {
        compose.onNodeWithText("Signal", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Audio").performClick()
        compose.onNodeWithText("Audio path").assertExists()
        scrollListTo("signal-audio-list", "Test next transition")
        compose.onNodeWithText("Test next transition").assertHasClickAction().performClick()
        scrollListTo("signal-audio-list", "Retest transition")
        compose.onNodeWithText("Retest transition").assertExists()
        // SIGNAL's section command and the persistent primary Index both say “Library”.
        // Select the section command rendered inside the workspace, not the persistent destination.
        compose.onAllNodesWithText("Library").onFirst().performClick()
        compose.onNodeWithText("Library integrity").assertExists()
        scrollListTo("signal-library-list", "Audit library")
        compose.onNodeWithText("Audit library").performClick()
        compose.onNodeWithText("Lyrics audit · 1 missing").assertExists()
        scrollListTo("signal-library-list", "Scan hashes")
        compose.onNodeWithText("Scan hashes").performClick()
        compose.onNodeWithText("SHA-256 duplicate scan · 2 groups").assertExists()
        compose.onNodeWithText("History").performClick()
        compose.onNodeWithText("TSUNAMI Replay").assertExists()
        compose.onNodeWithText("CSV").performClick()
        compose.onNodeWithText("TSUNAMI Replay · CSV export ready").assertExists()
        compose.onNodeWithText("Logs").performClick()
        compose.onNodeWithText("Export bundle").performClick()
        compose.onNodeWithText("Diagnostics bundle preview ready").assertExists()
    }

    @Test fun settingsPlaybackStateResponds() {
        compose.onNodeWithContentDescription("Settings").performClick()
        compose.onNodeWithText("Settings").assertExists()
        scrollListTo("settings-root-list", "Gapless")
        compose.onNodeWithText("Gapless").assertHasClickAction().performClick()
        compose.onNodeWithText("Crossfade").assertHasClickAction().performClick()
        compose.onNodeWithText("3s").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Your listening line").assertExists()
    }



    @Test fun playlistInsertionIsVisibleInLibraryObject() {
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithContentDescription("Search music").performTextInput("Serein")
        compose.onNodeWithContentDescription("Track actions").performClick()
        compose.onNodeWithText("Add to playlist").performClick()
        compose.onAllNodesWithText("Library", useUnmergedTree = true).onLast().performClick()
        compose.onNodeWithText("Playlists").performClick()
        compose.onNodeWithText("5 tracks · local playlist").assertExists()
        compose.onNodeWithText("Late driving").performClick()
        scrollListTo("library-object-contents-list", "Serein")
        compose.onNodeWithText("Serein").assertExists()
    }

    @Test fun consequentialHistoryClearRequiresConfirmation() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Clear history")
        compose.onNodeWithText("Clear listening history?").assertExists()
        compose.onNodeWithText("Cancel").performClick()
        compose.onNodeWithText("Clear listening history?").assertDoesNotExist()
        openSetting("Clear history")
        compose.onNodeWithText("Clear").performClick()
        compose.onNodeWithText("Listening history cleared").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Signal", useUnmergedTree = true).performClick()
        compose.onNodeWithText("History").performClick()
        compose.onNodeWithText("No listening history in this preview.").assertExists()
    }

    @Test fun advancedSettingsUseProgressiveDisclosure() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Audio processing")
        compose.onNodeWithText("ReplayGain").assertExists()
        compose.onNodeWithText("Track").performClick()
        compose.onNodeWithText("Album").assertExists()
        scrollListTo("settings-page-list", "10-band equalizer")
        compose.onNodeWithText("10-band equalizer").performClick()
        compose.onNodeWithText("31 Hz").performClick()
        compose.onNodeWithText("+3 dB").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Audio processing").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Settings").assertExists()
    }

    @Test fun lyricsTimingAndPresentationSettingsAreStateful() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Lyrics & timing")
        compose.onNodeWithText("Global delay").performClick()
        compose.onNodeWithText("250 ms").assertExists()
        compose.onNodeWithText("Word timing").performClick()
        compose.onNodeWithText("LINE").assertExists()
        compose.onNodeWithText("Source priority").performClick()
        compose.onNodeWithContentDescription("Move LRC sidecar up").performClick()
        compose.onNodeWithText("Lyrics priority updated").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Lyrics & timing").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        openSetting("Presentation")
        compose.onNodeWithText("Artwork").performClick()
        compose.onNodeWithText("HIDDEN").assertExists()
        compose.onNodeWithText("Metadata density").performClick()
        compose.onNodeWithText("COMPACT").assertExists()
    }

    @Test fun libraryExclusionsHaveAnIntentionalSettingsHome() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Library roots")
        compose.onNodeWithText("Excluded folders").performClick()
        compose.onNodeWithText("1 paths").assertExists()
        compose.onNodeWithText("Excluded extensions").performClick()
        compose.onNodeWithText("part, temp, opus.preview").assertExists()
    }
    @Test fun librarySectionVisibilityAndMetadataTemplateAffectLibrary() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Sections")
        compose.onNodeWithContentDescription("Move Albums up").performClick()
        compose.onNodeWithText("Library order updated · Albums").assertExists()
        compose.onNodeWithText("Hide Albums").performClick()
        compose.onNodeWithText("Show Albums").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        openSetting("Metadata template")
        compose.onNodeWithText("Track rows").performClick()
        compose.onAllNodesWithText("Title · Album · Year").onFirst().assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Albums").assertDoesNotExist()
        compose.onNodeWithText("Refractions · 2026").assertExists()
    }



    @Test fun migratedProductionCapabilitiesHaveIntentionalHomes() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Library roots")
        compose.onNodeWithText("Excluded genres").performClick()
        compose.onNodeWithText("Audiobook, Spoken").assertExists()
        compose.onNodeWithText("Excluded playlist paths").performClick()
        compose.onNodeWithText("/Imported/Temporary").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()

        openSetting("Metadata template")
        compose.onNodeWithText("Album artist").performClick()
        compose.onNodeWithText("Track artist only").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()

        openSetting("Controls & gestures")
        scrollListTo("settings-page-list", "Swipe up")
        compose.onNodeWithText("Swipe up").performClick()
        compose.onNode(hasText("Swipe up") and hasText("Lyrics")).assertExists()
        scrollListTo("settings-page-list", "Swipe down")
        compose.onNodeWithText("Swipe down").performClick()
        compose.onNode(hasText("Swipe down") and hasText("Queue")).assertExists()
        compose.onNodeWithContentDescription("Back").performClick()

        openSetting("Backup & portability")
        compose.onNodeWithText("TSUNAMI device migration").performClick()
        compose.onNodeWithText("Ready to send").assertExists()
        compose.onNodeWithText("Share TSUNAMI APK").performClick()
        compose.onNodeWithText("TSUNAMI APK share handoff preview").assertExists()
    }


    @Test fun externalPlaybackSurfacesHaveExplicitMockContracts() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("External playback surfaces")

        compose.onNodeWithContentDescription("Quick Settings action: Previous").performClick()
        compose.onNodeWithText("Quick Settings exposes two transport actions").assertExists()
        compose.onNodeWithContentDescription("Quick Settings action: Next").performClick()
        compose.onNodeWithContentDescription("Quick Settings action: Previous").performClick()

        compose.onNodeWithText("Home-screen widget").performClick()
        compose.onNodeWithText("Listening").assertExists()

        compose.onNodeWithText("Wear transport").performClick()
        compose.onNodeWithText("Wear secondary action").assertDoesNotExist()
        compose.onNodeWithText("Wear transport").performClick()
        compose.onNodeWithText("Wear secondary action").performClick()
        compose.onNodeWithText("Wear secondary action · Queue").assertExists()
    }

    @Test fun experienceLevelControlsAdvancedDisclosure() {
        compose.onNodeWithContentDescription("Settings").performClick()
        scrollListTo("settings-root-list", "Experience level")
        compose.onNodeWithText("Experience level").performClick()
        compose.onNodeWithText("Context rules").assertDoesNotExist()
        compose.onNodeWithText("Experience level").performClick()
        scrollListTo("settings-root-list", "Context rules")
        compose.onNodeWithText("Context rules").assertExists()
    }


    @Test fun progressiveSettingsRoutesRoundTripToStableRoot() {
        compose.onNodeWithContentDescription("Settings").performClick()
        val routes = listOf(
            "Library profile" to "Library profiles",
            "Custom sections" to "Custom library sections",
            "Output profiles" to "Output profiles",
            "Shuffle behavior" to "Shuffle behavior",
            "Visualizer" to "Visualizer",
            "Listening services" to "Listening services",
            "Context rules" to "Context rules",
            "Quick actions & sessions" to "Quick actions & sessions",
        )
        routes.forEach { (entry, title) ->
            scrollListTo("settings-root-list", entry)
            compose.onNodeWithText(entry).performClick()
            compose.onNodeWithText(title).assertExists()
            compose.onNodeWithContentDescription("Back").performClick()
            compose.onNodeWithText("Settings").assertExists()
        }
    }

    @Test fun providerImportAuditPreservesLibraryAcrossDisconnect() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Connected services")
        compose.onNodeWithText("YouTube Music").assertExists()
        compose.onNodeWithText("Apple Music").assertExists()
        compose.onNodeWithText("Amazon Music").assertExists()
        compose.onNodeWithText("Spotify").assertExists()
        compose.onNodeWithText("TIDAL").assertExists()
        compose.onNodeWithText("Import YouTube Music").performScrollTo().performClick()
        compose.onNodeWithText("Import YouTube Music").performClick()
        compose.onNodeWithText("Import YouTube Music").performClick()
        compose.onNodeWithText("Import YouTube Music").performClick()
        compose.onNodeWithText("YouTube Music import complete · 1842 imported").assertExists()
        compose.onNodeWithText("Import audit · YouTube Music").performClick()
        compose.onNodeWithText("YouTube Music: 1842 imported · Shorts 38 · video-only 19 · samples 7 · unmatched 4").assertExists()
        compose.onNodeWithText("YouTube Music").performClick()
        compose.onNodeWithText("DISCONNECTED · IMPORTED LIBRARY KEPT").assertExists()
        compose.onNodeWithText("Import audit · YouTube Music").assertExists()
    }

    @Test fun nonYouTubeProviderUsesSameImportLifecycle() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Connected services")
        compose.onNodeWithText("Apple Music").performScrollTo().performClick()
        repeat(4) {
            compose.onNodeWithText("Import Apple Music").performScrollTo().performClick()
        }
        compose.onNodeWithText("Apple Music import complete · 428 imported").assertExists()
        compose.onNodeWithText("Import audit · Apple Music").assertExists()
    }

    @Test fun longformSeparatesAudiobooksAndPodcasts() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Longform").performClick()
        compose.onNodeWithText("Audiobooks").performClick()
        compose.onNodeWithText("The Cartographer's Sleep").assertExists()
        compose.onNodeWithText("Designing for Interruption").assertDoesNotExist()
        compose.onNodeWithText("Podcasts").performClick()
        compose.onNodeWithText("Designing for Interruption").assertExists()
        compose.onNodeWithText("The Cartographer's Sleep").assertDoesNotExist()

        compose.onNodeWithText("Designing for Interruption").performClick()
        compose.onNodeWithText("PODCAST").assertExists()
        compose.onNodeWithText("Back 30 sec").performClick()
        compose.onNodeWithText("Back 30 seconds").assertExists()
        compose.onNodeWithText("Mark played").performClick()
        compose.onNodeWithText("Marked played · Designing for Interruption").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()

        compose.onNodeWithText("Audiobooks").performClick()
        compose.onNodeWithText("The Cartographer's Sleep").performClick()
        compose.onNodeWithText("AUDIOBOOK").assertExists()
        compose.onNodeWithContentDescription("Add bookmark").performClick()
        compose.onNodeWithText("Bookmark added").assertExists()
    }




    @Test fun fullPlayerObjectActionsDriveListeningCore() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Controls & gestures")
        compose.onNodeWithTag("settings-page-list").performScrollToIndex(1)
        compose.onNodeWithText("Share").assertIsDisplayed().assertIsSelected().performClick()
        compose.onNodeWithText("Share").assertIsNotSelected()
        compose.onNodeWithTag("full-player-action-row").performScrollToNode(hasText("Add to playlist"))
        compose.onNodeWithText("Add to playlist").assertIsDisplayed().assertIsNotSelected().performClick()
        compose.onNodeWithText("Add to playlist").assertIsSelected()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithContentDescription("Open listening environment").performClick()
        compose.onNodeWithTag("expanded-listening-scroll").performScrollToNode(hasText("Add to playlist"))
        compose.onNodeWithText("Add to playlist").assertExists()
        compose.onNodeWithText("Share 1:34").assertDoesNotExist()
        compose.onNodeWithText("Add to playlist").performClick()
        compose.onNodeWithText("Already in Late driving").assertExists()
    }

    @Test fun miniPlayerActionCustomizationChangesPersistentSpine() {
        compose.onNodeWithContentDescription("Previous").assertExists()
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Controls & gestures")
        compose.onNodeWithContentDescription("Mini player extra: Favourite").performClick()
        compose.onNodeWithContentDescription("Mini player extra: Queue").performClick()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Queue").assertExists()
        compose.onNodeWithText("Lyrics").assertExists()
        compose.onNodeWithText("Queue").performClick()
        compose.onNodeWithContentDescription("Queue item 1: Afterglow at the Edge of the City, Mira Sol").assertExists()
    }

    @Test fun unavailableTrackCanOpenWithoutPretendingToPlay() {
        val state = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("unavailable"))
        val blocked = state.fixture.tracks.first { !it.available }
        state.selectTrack(blocked, false)
        assertTrue(state.currentTrack?.id == blocked.id)
        assertFalse(state.playing)
        assertFalse(state.buffering)
        assertTrue(state.banner == "Unavailable · ${blocked.title}")
        state.runPlayerAction("Play/Pause")
        assertFalse(state.playing)
        assertTrue(state.banner?.startsWith("Unavailable · ") == true)
    }

    @Test fun customizedPlayPauseHonorsUnavailableTrackState() {
        val state = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("unavailable"))
        val blocked = state.fixture.tracks.first { !it.available }
        state.selectTrack(blocked, true)
        state.runPlayerAction("Play/Pause")
        assertFalse(state.playing)
        assertTrue(state.banner?.startsWith("Unavailable · ") == true)
    }

    @Test fun removingCurrentQueueItemAdvancesLocallyAndEmptyQueueStopsPlayback() {
        val state = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("default"))
        val expectedNext = state.queue[1].id
        state.removeFromQueue(0)
        assertTrue(state.currentTrack?.id == expectedNext)
        while (state.queue.isNotEmpty()) state.removeFromQueue(0)
        assertTrue(state.currentTrack == null)
        assertFalse(state.playing)
        assertTrue(state.banner == "Queue empty")
    }


    @Test fun adverseFixtureStatesRecoverWithoutDestroyingContext() {
        val search = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("search-error"))
        assertTrue(search.searchFault)
        search.searchQuery = "Refractions"
        search.retrySearch()
        assertFalse(search.searchFault)
        assertTrue(search.searchQuery == "Refractions")

        val connecting = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("provider-connecting"))
        assertTrue(connecting.providerTransient == "connecting")
        connecting.retryProvider()
        assertTrue(connecting.providerTransient.isEmpty())

        val providerError = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("provider-error"))
        assertTrue(providerError.providerTransient == "error")
        providerError.retryProvider()
        assertTrue(providerError.providerTransient.isEmpty())

        val downloads = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("downloads-error"))
        assertTrue(downloads.downloadsFault)
        downloads.retryDownloads()
        assertFalse(downloads.downloadsFault)

        val active = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("downloads-active"))
        assertTrue(active.downloads.values.any { it == com.tsunami.shell.model.DownloadState.DOWNLOADING })
    }

    @Test fun emptyQueueFixtureCannotPretendToPlay() {
        val state = com.tsunami.shell.state.ShellState(com.tsunami.shell.model.defaultFixture("queue-empty"))
        assertTrue(state.queue.isEmpty())
        assertTrue(state.currentTrack == null)
        assertFalse(state.playing)
        assertFalse(state.buffering)
        assertTrue(state.positionMs == 0L)
        state.runPlayerAction("Play/Pause")
        assertFalse(state.playing)
        assertTrue(state.currentTrack == null)
    }

    @Test fun libraryRootMutationPropagatesIntoFolderLens() {
        compose.onNodeWithContentDescription("Settings").performClick()
        openSetting("Library roots")
        compose.onNodeWithText("Add").performClick()
        compose.onNodeWithText("/Music/Field Recordings").assertExists()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithContentDescription("Back").performClick()
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Folders").performClick()
        compose.onNodeWithText("/Music/Field Recordings").assertExists()
    }

    @Test fun albumObjectPlayUsesTrackFromThatAlbum() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Albums").performClick()
        scrollListTo("library-object-list", "Glass Meridian")
        compose.onNodeWithText("Glass Meridian").performClick()
        compose.onNodeWithText("Play").performClick()
        compose.onNodeWithContentDescription("Open listening environment").performClick()
        compose.onAllNodesWithText("Glass Meridian").onFirst().assertExists()
        compose.onAllNodesWithText("Ari Nox").onFirst().assertExists()
    }

    @Test fun libraryAndSearchStateRespond() {
        compose.onNodeWithText("Library", useUnmergedTree = true).performClick()
        compose.onNodeWithText("Offline").performClick()
        compose.onNodeWithText("Dense").performClick()
        compose.onNodeWithText("Find", useUnmergedTree = true).performClick()
        compose.onNodeWithContentDescription("Search music").performTextInput("Mira")
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
        compose.onNodeWithText("Owned only").performClick()
        compose.onAllNodesWithText("Afterglow at the Edge of the City").onFirst().assertExists()
    }
}
