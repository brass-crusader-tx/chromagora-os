package com.tsunami.shell.screens

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.role
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import com.tsunami.shell.brand.TsunamiMark
import com.tsunami.shell.components.*
import com.tsunami.shell.state.ShellState
import com.tsunami.shell.theme.*

@Composable fun OnboardingScreen(state:ShellState){
    val p=LocalTsunamiPalette.current
    Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(28.dp)){
        TsunamiMark(Modifier.width(68.dp).height(58.dp));Spacer(Modifier.height(44.dp));Text("TSUNAMI",style=Type.micro.copy(color=p.ink3));Spacer(Modifier.height(10.dp));Text("Start with what you own.",style=Type.display.copy(color=p.ink));Spacer(Modifier.height(10.dp));Text("Choose where your library begins. This preview does not request media permissions or alter your existing TSUNAMI data.",style=Type.body.copy(color=p.ink2));Spacer(Modifier.height(34.dp));Rule()
        OnboardChoice("Index a music folder","Local library · folders · offline",{state.banner="Sample folder indexed";state.onboardingComplete=true;state.primary=com.tsunami.shell.model.PrimarySpace.LIBRARY});OnboardChoice("Connect a music service","Catalogue + imported library source",{state.settingsExpanded="services"});OnboardChoice("Enter with the sample library","4,268 indexed items · no account",{state.banner="Sample library ready";state.onboardingComplete=true;state.primary=com.tsunami.shell.model.PrimarySpace.LISTEN});Spacer(Modifier.weight(1f));Text("PREVIEW LIBRARY · LOCAL SAMPLE STATE",style=Type.micro.copy(color=p.ink3))
    }
    if(state.settingsExpanded!=null)SettingsOverlay(state,{state.settingsExpanded=null})
}
@Composable private fun OnboardChoice(title:String,detail:String,onClick:()->Unit){
    val p=LocalTsunamiPalette.current
    var focused by remember(title){ mutableStateOf(false) }
    Row(
        Modifier.fillMaxWidth().heightIn(min=82.dp)
            .semantics{role=Role.Button;contentDescription="$title. $detail"}
            .onFocusChanged{focused=it.isFocused}
            .clickable(onClick=onClick)
            .background(if(focused)p.groundAlt else androidx.compose.ui.graphics.Color.Transparent)
            .padding(vertical=14.dp),
        verticalAlignment=Alignment.CenterVertically
    ){
        Box(Modifier.width(if(focused)3.dp else 1.dp).height(30.dp).background(if(focused)p.selected else androidx.compose.ui.graphics.Color.Transparent))
        Spacer(Modifier.width(if(focused)10.dp else 0.dp))
        Column{
            Text(title,style=Type.title.copy(color=p.ink,fontWeight=if(focused)androidx.compose.ui.text.font.FontWeight.SemiBold else androidx.compose.ui.text.font.FontWeight.Medium))
            Spacer(Modifier.height(3.dp))
            Text(detail,style=Type.meta.copy(color=p.ink3))
        }
    }
    Rule()
}
