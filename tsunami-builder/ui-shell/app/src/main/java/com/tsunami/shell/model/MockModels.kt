package com.tsunami.shell.model

enum class PrimarySpace { LISTEN, LIBRARY, FIND, SIGNAL }
enum class PlayerMode { QUEUE, LYRICS, OUTPUT, VISUAL }
enum class LibraryLens { TRACKS, ALBUMS, ARTISTS, PLAYLISTS, FOLDERS, LONGFORM, RADIO }
enum class Provenance { OWNED, CATALOGUE, CONNECTED }
enum class DownloadState { REMOTE, DOWNLOADING, DOWNLOADED }
enum class RepeatMode { OFF, ALL, ONE }
enum class ThemeMode { LIGHT, DARK }
enum class SearchKind { ALL, TRACKS, ALBUMS, ARTISTS, FOLDERS, LONGFORM }
enum class SearchIntent { UNFINISHED, DOWNLOADED, CATALOGUE, ARTISTS }
enum class LongformScope { ALL, BOOKS, PODCASTS }

data class Track(
    val id: String,
    val title: String,
    val artist: String,
    val album: String,
    val durationMs: Long,
    val year: Int,
    val quality: String,
    val provenance: Provenance = Provenance.OWNED,
    val artworkSeed: Int? = null,
    val longform: Boolean = false,
    val chapter: String? = null,
    val available: Boolean = true,
)

data class ServiceConnection(val name: String, val connected: Boolean, val detail: String)

data class LibraryObject(val title: String, val kind: String, val meta: String)
data class ContextRuleMock(val name:String,val enabled:Boolean=true,val window:String="Any time",val scope:String="Any queue")
data class CustomSectionMock(val name:String,val query:String,val view:String="List")
data class AudioProfileMock(val name:String,val route:String,val processing:String)

data class ShellFixture(
    val tracks: List<Track>,
    val services: List<ServiceConnection>,
    val libraryCount: Int,
    val missingArtwork: Boolean = false,
    val empty: Boolean = false,
    val loading: Boolean = false,
    val error: Boolean = false,
    val missingLyrics: Boolean = false,
    val buffering: Boolean = false,
    val partial: Boolean = false,
)

fun defaultFixture(scenario: String): ShellFixture {
    val base = listOf(
        Track("afterglow", "Afterglow at the Edge of the City", "Mira Sol", "Refractions", 259_000, 2026, "FLAC · 24 / 96", artworkSeed = 1),
        Track("passage", "Passage / Northbound", "Kite Geometry", "Night Trains", 307_000, 2024, "FLAC · 16 / 44.1", artworkSeed = 2),
        Track("stillwater", "Stillwater", "Vale House", "Interior Weather", 228_000, 2025, "AAC · 256", provenance = Provenance.CONNECTED, artworkSeed = 3),
        Track("vector", "Vector Memory", "Orison", "Vector Memory", 371_000, 2022, "FLAC · 24 / 48", artworkSeed = 4),
        Track("serein", "Serein", "Anna Luce", "Small Hours", 196_000, 2026, "FLAC · 16 / 44.1", artworkSeed = 5),
        Track("longtitle", "A Very Long Album Title About Motion, Memory, Distance, and the Places We Return To", "Mira Sol & The Peripheral Ensemble", "A Catalogue of Departures", 441_000, 2026, "FLAC · 24 / 96", artworkSeed = null),
        Track("book", "The Cartographer's Sleep", "Nadia Venn", "The Cartographer's Sleep", 3_842_000, 2023, "M4B · 64", longform = true, chapter = "Chapter 12 · The Inland Sea"),
        Track("podcast", "Designing for Interruption", "Signal / Noise", "Episode 48", 2_731_000, 2026, "AAC · 128", longform = true, chapter = "48 · Context recovery"),
        Track("atlas", "Atlas Minor", "Fallow", "Maps Without Borders", 284_000, 2021, "FLAC · 24 / 44.1", artworkSeed = 6),
        Track("slowarc", "Slow Arc", "Kite Geometry", "Night Trains", 247_000, 2024, "FLAC · 16 / 44.1", artworkSeed = 2),
        Track("catalogue", "Glass Meridian", "Ari Nox", "Glass Meridian", 214_000, 2026, "STREAM · LOSSLESS", provenance = Provenance.CATALOGUE, artworkSeed = 7),
        Track("emptyart", "No Cover, Still Music", "The Index", "Untitled", 189_000, 2020, "MP3 · 320", artworkSeed = null),
    )
    val tracks = when (scenario) {
        "long-title" -> listOf(base.first { it.id == "longtitle" }) + base.filterNot { it.id == "longtitle" }
        "longform" -> listOf(base.first { it.id == "book" }) + base.filterNot { it.id == "book" }
        "unavailable" -> listOf(base.first().copy(available=false)) + base.drop(1)
        "small-list" -> buildList {
            repeat(4) { cycle ->
                base.forEachIndexed { index, t -> add(t.copy(id="${t.id}-small-$cycle", title=if(cycle==0)t.title else "${t.title} · ${cycle+1}", year=2019 + ((cycle+index)%8))) }
            }
        }.take(40)
        "long-list" -> buildList {
            repeat(334) { cycle ->
                base.forEachIndexed { index, t -> add(t.copy(id="${t.id}-$cycle", title=if(cycle==0)t.title else "${t.title} · ${cycle+1}", year=2014 + ((cycle+index)%13))) }
            }
        }
        "huge-list" -> buildList {
            repeat(3334) { cycle ->
                base.forEachIndexed { index, t -> add(t.copy(id="${t.id}-huge-$cycle", title=if(cycle==0)t.title else "${t.title} · ${cycle+1}", year=2014 + ((cycle+index)%13))) }
            }
        }
        else -> base
    }
    return ShellFixture(
        tracks = if (scenario == "empty") emptyList() else tracks,
        services = listOf(
            ServiceConnection("YouTube Music", true, "Library available · 1,842 indexed"),
            ServiceConnection("TIDAL", false, "Not connected"),
            ServiceConnection("Spotify", true, "History only · enrichment paused"),
        ),
        libraryCount = when(scenario){"small-list"->40;"long-list"->4_008;"huge-list"->40_008;"empty"->0;else->4_268},
        missingArtwork = scenario in setOf("missing-art", "no-artwork"),
        empty = scenario == "empty",
        loading = scenario == "loading",
        error = scenario == "error",
        missingLyrics = scenario == "missing-lyrics",
        buffering = scenario == "buffering",
        partial = scenario == "partial",
    )
}

fun formatTime(ms: Long): String {
    val total=(ms/1000).coerceAtLeast(0)
    val h=total/3600; val m=(total%3600)/60; val s=total%60
    return if(h>0) "%d:%02d:%02d".format(h,m,s) else "%d:%02d".format(m,s)
}
