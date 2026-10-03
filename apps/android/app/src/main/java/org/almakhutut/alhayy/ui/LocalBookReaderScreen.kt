package org.almakhutut.alhayy.ui

import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Image
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.NavigateBefore
import androidx.compose.material.icons.automirrored.filled.NavigateNext
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.LocalBook
import org.almakhutut.alhayy.data.LocalBookKind
import java.io.File

@Composable
fun LocalBookReaderScreen(book: LocalBook, onBack: () -> Unit) {
    BackHandler(onBack = onBack)
    var pageIndex by remember(book.id) { mutableIntStateOf(0) }

    Scaffold(
        topBar = { AppTopBar(book.title, onBack) },
        bottomBar = {
            Surface(tonalElevation = 4.dp) {
                Row(
                    Modifier.fillMaxWidth().padding(8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    IconButton(
                        onClick = { if (pageIndex > 0) pageIndex-- },
                        enabled = pageIndex > 0,
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.NavigateBefore,
                            stringResource(R.string.previous),
                        )
                    }
                    Text(
                        stringResource(R.string.page_of, pageIndex + 1, book.pageCount),
                        modifier = Modifier.padding(top = 12.dp),
                    )
                    IconButton(
                        onClick = { if (pageIndex < book.pageCount - 1) pageIndex++ },
                        enabled = pageIndex < book.pageCount - 1,
                    ) {
                        Icon(
                            Icons.AutoMirrored.Filled.NavigateNext,
                            stringResource(R.string.next),
                        )
                    }
                }
            }
        },
    ) { padding ->
        Box(Modifier.fillMaxSize().padding(padding)) {
            when (book.kind) {
                LocalBookKind.PDF -> PdfPage(book.source, pageIndex)
                LocalBookKind.IMAGES, LocalBookKind.IIIF -> {
                    ZoomableImage(book.pages.getOrNull(pageIndex))
                }
            }
        }
    }
}

@Composable
private fun PdfPage(path: String, pageIndex: Int) {
    var bitmap by remember(path, pageIndex) { mutableStateOf<Bitmap?>(null) }
    LaunchedEffect(path, pageIndex) {
        bitmap = withContext(Dispatchers.IO) {
            val file = File(path)
            ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY).use { pfd ->
                PdfRenderer(pfd).use { renderer ->
                    renderer.openPage(pageIndex).use { page ->
                        val width = 1600
                        val height = (width.toFloat() / page.width * page.height)
                            .toInt()
                            .coerceAtLeast(1)
                        Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).also {
                            page.render(it, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                        }
                    }
                }
            }
        }
    }
    bitmap?.let {
        ZoomableContent {
            Image(
                bitmap = it.asImageBitmap(),
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize(),
            )
        }
    } ?: Box(Modifier.fillMaxSize()) {
        CircularProgressIndicator(Modifier.padding(24.dp))
    }
}

@Composable
private fun ZoomableImage(source: String?) {
    if (source == null) return
    ZoomableContent {
        AsyncImage(
            model = source,
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize(),
        )
    }
}

@Composable
private fun ZoomableContent(content: @Composable BoxScope.() -> Unit) {
    var scale by remember { mutableFloatStateOf(1f) }
    var offset by remember { mutableStateOf(Offset.Zero) }
    Box(
        Modifier
            .fillMaxSize()
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
            },
        content = content,
    )
}
