package org.almakhutut.alhayy.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val NeonCyan = Color(0xFF00F5FF)
val NeonPurple = Color(0xFFB65CFF)
val NeonGold = Color(0xFFFFD84D)
val NeonGreen = Color(0xFF42FFB0)
val InkBlack = Color(0xFF03060B)
val DeepNavy = Color(0xFF07101C)
val PanelNavy = Color(0xFF0B1522)

private val Colors = darkColorScheme(
    primary = NeonCyan,
    secondary = NeonPurple,
    tertiary = NeonGold,
    background = InkBlack,
    surface = DeepNavy,
    surfaceVariant = PanelNavy,
    onPrimary = Color(0xFF001316),
    onSecondary = Color(0xFF13001E),
    onTertiary = Color(0xFF211A00),
    onBackground = Color(0xFFF5FAFF),
    onSurface = Color(0xFFF5FAFF),
    onSurfaceVariant = Color(0xFFC9D7E8),
    outline = Color(0xFF4D6378),
)

@Composable
fun AlMakhtutTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, content = content)
}
