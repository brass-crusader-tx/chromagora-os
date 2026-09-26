package com.tsunami.shell.theme

import androidx.compose.runtime.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.*
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tsunami.shell.R
import com.tsunami.shell.model.ThemeMode

@Immutable
data class TsunamiPalette(
    val ground: Color,
    val groundAlt: Color,
    val ink: Color,
    val ink2: Color,
    val ink3: Color,
    val rule: Color,
    val selected: Color,
    val possession: Color,
    val danger: Color,
    val inverse: Color,
)

val LightPalette=TsunamiPalette(
    ground=Color(0xFFF4F1EA), groundAlt=Color(0xFFEAE6DD), ink=Color(0xFF101114), ink2=Color(0xFF4B4D53), ink3=Color(0xFF6B6D73),
    rule=Color(0xFFB9B5AC), selected=Color(0xFF3F56C5), possession=Color(0xFF946414), danger=Color(0xFFB3232E), inverse=Color.White)
val DarkPalette=TsunamiPalette(
    ground=Color(0xFF111214), groundAlt=Color(0xFF1A1B1F), ink=Color(0xFFF4F1EA), ink2=Color(0xFFC5C1B8), ink3=Color(0xFF949189),
    rule=Color(0xFF3C3E44), selected=Color(0xFF9EAEFF), possession=Color(0xFFE3B45B), danger=Color(0xFFFF7D89), inverse=Color(0xFF101114))
val LightHighContrast=LightPalette.copy(
    ground=Color.White,groundAlt=Color(0xFFF2F2F2),ink=Color.Black,ink2=Color(0xFF202124),ink3=Color(0xFF34363A),
    rule=Color(0xFF4A4A4A),selected=Color(0xFF1837B8),possession=Color(0xFF6B4100),danger=Color(0xFF8B0010))
val DarkHighContrast=DarkPalette.copy(
    ground=Color.Black,groundAlt=Color(0xFF101114),ink=Color.White,ink2=Color(0xFFF1EEE8),ink3=Color(0xFFD7D3CA),
    rule=Color(0xFF9B9DA3),selected=Color(0xFFC2CCFF),possession=Color(0xFFFFD27A),danger=Color(0xFFFFA0AA))

val TsunamiFont=FontFamily(
    Font(R.font.tsunami_sans_light,FontWeight.Light), Font(R.font.tsunami_sans_regular,FontWeight.Normal),
    Font(R.font.tsunami_sans_medium,FontWeight.Medium), Font(R.font.tsunami_sans_semibold,FontWeight.SemiBold), Font(R.font.tsunami_sans_bold,FontWeight.Bold))

object Type {
    val display=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Medium,fontSize=34.sp,lineHeight=38.sp,letterSpacing=(-.3).sp)
    val title=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.SemiBold,fontSize=22.sp,lineHeight=27.sp)
    val row=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Medium,fontSize=16.sp,lineHeight=20.sp)
    val body=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Normal,fontSize=15.sp,lineHeight=21.sp)
    val meta=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Medium,fontSize=12.sp,lineHeight=16.sp)
    val micro=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Medium,fontSize=11.sp,lineHeight=14.sp,letterSpacing=.1.sp)
    val numeric=TextStyle(fontFamily=TsunamiFont,fontWeight=FontWeight.Medium,fontSize=13.sp,lineHeight=16.sp)
}

val LocalTsunamiPalette=staticCompositionLocalOf { LightPalette }
val LocalControlTarget=staticCompositionLocalOf<Dp> { 48.dp }

@Composable fun TsunamiTheme(mode:ThemeMode,highContrast:Boolean=false,largeControls:Boolean=false,content: @Composable () -> Unit){
    val palette=when{
        mode==ThemeMode.DARK && highContrast -> DarkHighContrast
        mode==ThemeMode.DARK -> DarkPalette
        highContrast -> LightHighContrast
        else -> LightPalette
    }
    CompositionLocalProvider(
        LocalTsunamiPalette provides palette,
        LocalControlTarget provides if(largeControls) 56.dp else 48.dp,
        content=content
    )
}
