package org.almakhutut.alhayy.ui

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Colors = darkColorScheme(
    primary = Color(0xFF55C8C0),
    secondary = Color(0xFFD9B35B),
    background = Color(0xFF070B12),
    surface = Color(0xFF0B121D),
    onPrimary = Color(0xFF07100F),
    onBackground = Color(0xFFF4EAD5),
    onSurface = Color(0xFFF4EAD5),
)

@Composable
fun AlMakhtutTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = Colors, content = content)
}
