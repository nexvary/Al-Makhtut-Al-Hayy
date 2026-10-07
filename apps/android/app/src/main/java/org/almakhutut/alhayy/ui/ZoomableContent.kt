package org.almakhutut.alhayy.ui

import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.unit.IntSize

/** Clip the transformed page inside its viewport; reset for each page. */
@Composable
internal fun ZoomableContent(
    pageKey: Any,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit,
) {
    var scale by remember(pageKey) { mutableFloatStateOf(1f) }
    var offset by remember(pageKey) { mutableStateOf(Offset.Zero) }
    var viewport by remember { mutableStateOf(IntSize.Zero) }
    Box(modifier.clipToBounds().onSizeChanged { viewport = it }
        .pointerInput(pageKey) {
            detectTransformGestures { _, pan, zoom, _ ->
                scale = (scale * zoom).coerceIn(1f, 6f)
                val limitX = viewport.width * (scale - 1f) / 2f
                val limitY = viewport.height * (scale - 1f) / 2f
                offset = Offset(
                    (offset.x + pan.x).coerceIn(-limitX, limitX),
                    (offset.y + pan.y).coerceIn(-limitY, limitY),
                )
            }
        }) {
        Box(Modifier.fillMaxSize().graphicsLayer {
            scaleX = scale
            scaleY = scale
            translationX = offset.x
            translationY = offset.y
        }, content = content)
    }
}
