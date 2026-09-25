package com.tsunami.shell

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.*
import androidx.core.view.WindowCompat
import com.tsunami.shell.model.*
import com.tsunami.shell.navigation.GenesisShell
import com.tsunami.shell.state.rememberShellState
import com.tsunami.shell.theme.TsunamiTheme

class MainActivity:ComponentActivity(){
    override fun onCreate(savedInstanceState:Bundle?){
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val screen=intent.getStringExtra("screen")?.lowercase().orEmpty()
        val scenario=intent.getStringExtra("scenario")?.lowercase().orEmpty().ifBlank{"default"}
        val theme=intent.getStringExtra("theme")?.lowercase().orEmpty()
        val mode=intent.getStringExtra("mode")?.lowercase().orEmpty()
        val page=intent.getStringExtra("page")?.lowercase().orEmpty()
        val initial=when(screen){"library"->PrimarySpace.LIBRARY;"find","search"->PrimarySpace.FIND;"signal"->PrimarySpace.SIGNAL;else->PrimarySpace.LISTEN}
        val initialTheme=if(theme=="dark")ThemeMode.DARK else ThemeMode.LIGHT
        setContent{
            val fixture=remember(scenario){defaultFixture(scenario)}
            val state=rememberShellState(fixture,initial,initialTheme)
            TsunamiTheme(state.theme,state.highContrast,state.largeControls){
                val dark=state.theme==ThemeMode.DARK
                SideEffect{
                    WindowCompat.getInsetsController(window,window.decorView).isAppearanceLightStatusBars=!dark
                    WindowCompat.getInsetsController(window,window.decorView).isAppearanceLightNavigationBars=!dark
                }
                GenesisShell(state,scenario)
                if(scenario=="accessibility") LaunchedEffect("accessibility"){
                    state.highContrast=true
                    state.largeControls=true
                    state.reducedMotion=true
                }
                if(scenario=="search-empty") LaunchedEffect("search-empty"){state.searchQuery="Nocturne Zero"}
                if(scenario=="search-error") LaunchedEffect("search-error"){state.searchQuery="Refractions"}
                if(screen=="player" && !state.expandedPlayer) LaunchedEffect(Unit){state.expandedPlayer=true}
                if(mode.isNotBlank()) LaunchedEffect(mode){ state.playerMode=when(mode){"lyrics"->PlayerMode.LYRICS;"output"->PlayerMode.OUTPUT;"visual"->PlayerMode.VISUAL;else->PlayerMode.QUEUE} }
                if(screen=="settings" && state.settingsExpanded==null) LaunchedEffect("settings",page){state.settingsExpanded=page.ifBlank{"root"}}
            }
        }
    }
}
