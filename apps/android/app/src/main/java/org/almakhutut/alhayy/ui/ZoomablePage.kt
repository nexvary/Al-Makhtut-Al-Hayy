package org.almakhutut.alhayy.ui

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import coil3.compose.AsyncImage
import org.almakhutut.alhayy.model.Page

@Composable
fun ZoomablePage(page: Page, selectedRegionId: String?) {
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    val width = page.imageWidth ?: 1000
    val height = page.imageHeight ?: 1400
    val ratio = width.toFloat() / height.toFloat()

    Box(
        Modifier
            .fillMaxWidth()
            .aspectRatio(ratio)
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, _ ->
                    scale = (scale * zoom).coerceIn(1f, 6f)
                    offset += pan
                }
            }
            .graphicsLayer {
                scaleX = scale
                scaleY = scale
                translationX = offset.x
                translationY = offset.y
            }
    ) {
        AsyncImage(
            model = page.image,
            contentDescription = "صفحة المخطوط ${page.label ?: page.sequence}",
            contentScale = ContentScale.Fit,
            modifier = Modifier.matchParentSize(),
        )
        Canvas(Modifier.matchParentSize()) {
            page.regions.forEach { region ->
                if (region.polygon.isEmpty()) return@forEach
                val minX = region.polygon.minOf { it.x } / width
                val minY = region.polygon.minOf { it.y } / height
                val maxX = region.polygon.maxOf { it.x } / width
                val maxY = region.polygon.maxOf { it.y } / height
                drawRect(
                    color = if (region.id == selectedRegionId) Color(0xFFFFD879) else Color(0xFF55C8C0),
                    topLeft = Offset(size.width * minX, size.height * minY),
                    size = Size(size.width * (maxX - minX), size.height * (maxY - minY)),
                    style = androidx.compose.ui.graphics.drawscope.Stroke(width = 3f),
                )
            }
        }
    }
}
