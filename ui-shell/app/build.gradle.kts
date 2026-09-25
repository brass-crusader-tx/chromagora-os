plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

android {
    namespace = "com.tsunami.shell"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.tsunami.shell"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "genesis-1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures { compose = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
}

dependencies {
    implementation("androidx.activity:activity-compose:1.13.0")
    implementation("androidx.core:core-ktx:1.17.0")
    implementation("androidx.compose.ui:ui:1.11.4")
    implementation("androidx.compose.ui:ui-tooling-preview:1.11.4")
    implementation("androidx.compose.foundation:foundation:1.11.4")
    implementation("androidx.compose.animation:animation:1.11.4")
    implementation("androidx.compose.runtime:runtime:1.11.4")

    debugImplementation("androidx.compose.ui:ui-tooling:1.11.4")
    debugImplementation("androidx.compose.ui:ui-test-manifest:1.11.4")
    androidTestImplementation("androidx.test:runner:1.7.0")
    androidTestImplementation("androidx.test.ext:junit:1.3.0")
    androidTestImplementation("androidx.compose.ui:ui-test-junit4:1.11.4")
}


val tsunamiFontPython = providers.environmentVariable("TSUNAMI_FONT_PYTHON").orElse("python3")

val generateTsunamiSans by tasks.registering(Exec::class) {
    group = "build setup"
    description = "Generate the five TSUNAMI Sans masters from the checked-in font source."
    workingDir(rootProject.projectDir)
    commandLine(tsunamiFontPython.get(), "tools/prepare_fonts.py")
    inputs.files(
        rootProject.file("tools/prepare_fonts.py"),
        rootProject.file("tools/generate_tsunami_sans.py"),
    )
    outputs.files(
        listOf("light", "regular", "medium", "semibold", "bold").map { weight ->
            project.file("src/main/res/font/tsunami_sans_${weight}.ttf")
        }
    )
}

tasks.named("preBuild").configure {
    dependsOn(generateTsunamiSans)
}
