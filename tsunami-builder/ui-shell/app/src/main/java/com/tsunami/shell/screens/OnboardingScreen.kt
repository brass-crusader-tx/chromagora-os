package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.*
import androidx.compose.ui.unit.dp
import com.tsunami.shell.brand.TsunamiMark
import com.tsunami.shell.components.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun OnboardingScreen(state:ShellState){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(28.dp)){
        TsunamiMark(Modifier.width(68.dp).height(58.dp));Spacer(Modifier.height(44.dp));Text("TSUNAMI",style=Type.micro.copy(color=p.ink3));Spacer(Modifier.height(10.dp));Text("Start with what you own.",style=Type.display.copy(color=p.ink));Spacer(Modifier.height(10.dp));Text("The prototype never asks for production permissions. Choose the path you want to explore; every source below is deterministic mock state.",style=Type.body.copy(color=p.ink2));Spacer(Modifier.height(34.dp));Rule()
        OnboardChoice("Index a music folder","Local library · folders · offline",{state.banner="Mock folder indexed";state.onboardingComplete=true;state.primary=com.tsunami.shell.model.PrimarySpace.LIBRARY});OnboardChoice("Connect a music service","Catalogue + imported library provenance",{state.settingsExpanded="root"});OnboardChoice("Enter with the demo library","4,268 indexed items · no account",{state.banner="Demo library ready";state.onboardingComplete=true;state.primary=com.tsunami.shell.model.PrimarySpace.LISTEN});Spacer(Modifier.weight(1f));Text("Backend-free experiential shell",style=Type.micro.copy(color=p.ink3))
    }
    if(state.settingsExpanded!=null)SettingsOverlay(state,{state.settingsExpanded=null})
}
@Composable private fun OnboardChoice(title:String,detail:String,onClick:()->Unit){val p=LocalTsunamiPalette.current;Column(Modifier.fillMaxWidth().heightIn(min=82.dp).clickable(onClick=onClick).padding(vertical=14.dp)){Text(title,style=Type.title.copy(color=p.ink));Spacer(Modifier.height(3.dp));Text(detail,style=Type.meta.copy(color=p.ink3))};Rule()}
