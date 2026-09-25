plugins {
    id("com.android.application") version "9.2.1" apply false
    // AGP 9.2 provides built-in Kotlin (KGP 2.2.10). Keep the Compose compiler
    // plugin on that same Kotlin line instead of applying kotlin-android.
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.10" apply false
}
