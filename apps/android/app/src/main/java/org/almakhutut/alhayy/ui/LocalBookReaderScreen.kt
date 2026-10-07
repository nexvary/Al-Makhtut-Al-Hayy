package org.almakhutut.alhayy.ui

import android.graphics.Bitmap
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.NavigateBefore
import androidx.compose.material.icons.automirrored.filled.NavigateNext
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.Alignment
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.delay
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.LocalBook
import org.almakhutut.alhayy.data.LocalBookKind
import org.almakhutut.alhayy.data.IiifPageLoader
import org.almakhutut.alhayy.data.IiifRequestException
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
                    Modifier.fillMaxWidth().navigationBarsPadding().padding(8.dp),
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
                LocalBookKind.IIIF -> {
                    IiifPageImage(book.pages.getOrNull(pageIndex))
                }
                LocalBookKind.IMAGES -> {
                    ZoomableImage(book.pages.getOrNull(pageIndex))
                }
            }
        }
    }
}

@Composable
private fun PdfPage(path: String, pageIndex: Int) {
    var bitmap by remember(path, pageIndex) { mutableStateOf<Bitmap?>(null) }
    var failed by remember(path, pageIndex) { mutableStateOf(false) }
    LaunchedEffect(path, pageIndex) {
        try {
            bitmap = withContext(Dispatchers.IO) {
                ParcelFileDescriptor.open(File(path), ParcelFileDescriptor.MODE_READ_ONLY).use { pfd ->
                    PdfRenderer(pfd).use { renderer ->
                        renderer.openPage(pageIndex).use { page ->
                            // Bound pixels for unusual page aspect ratios on low-memory phones.
                            val factor = minOf(1600f / page.width, 2400f / page.height)
                            val width = (page.width * factor).toInt().coerceAtLeast(1)
                            val height = (page.height * factor).toInt().coerceAtLeast(1)
                            Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888).also {
                                it.eraseColor(android.graphics.Color.WHITE)
                                page.render(it, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                            }
                        }
                    }
                }
            }
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (_: Exception) {
            failed = true
        }
    }
    if (failed) {
        Text(stringResource(R.string.page_load_failed), Modifier.padding(24.dp))
        return
    }
    bitmap?.let {
        ZoomableContent("$path:$pageIndex", Modifier.fillMaxSize()) {
            Image(
                bitmap = it.asImageBitmap(),
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxSize().testTag("page-image"),
            )
        }
    } ?: Box(Modifier.fillMaxSize()) {
        CircularProgressIndicator(Modifier.padding(24.dp))
    }
}

@Composable
private fun ZoomableImage(source: String?) {
    if (source == null) return
    var failed by remember(source) { mutableStateOf(false) }
    if (failed) {
        Text(stringResource(R.string.page_load_failed), Modifier.padding(24.dp))
        return
    }
    ZoomableContent(source, Modifier.fillMaxSize()) {
        AsyncImage(
            model = source,
            onError = { failed = true },
            contentDescription = null,
            contentScale = ContentScale.Fit,
            modifier = Modifier.fillMaxSize().testTag("page-image"),
        )
    }
}


@Composable
internal fun IiifPageImage(source: String?, loader: IiifPageLoader = IiifPageLoader(LocalContext.current)) {
    var attempt by remember(source) { mutableIntStateOf(0) }
    var bitmap by remember(source, attempt) { mutableStateOf<Bitmap?>(null) }
    var error by remember(source, attempt) { mutableStateOf<Exception?>(null) }
    var remaining by remember(source, attempt) { mutableLongStateOf(0) }
    LaunchedEffect(source, attempt) {
        if (source == null) return@LaunchedEffect
        try { bitmap = loader.load(source) }
        catch (cancelled: CancellationException) { throw cancelled }
        catch (failure: Exception) { error = failure }
    }
    LaunchedEffect(error) {
        val deadline = (error as? IiifRequestException)?.retryAt ?: 0
        do {
            remaining = ((deadline - System.currentTimeMillis() + 999) / 1000).coerceAtLeast(0)
            if (remaining > 0) delay(1000)
        } while (remaining > 0)
    }
    val image = bitmap
    if (image != null) {
        ZoomableContent("$source:$attempt", Modifier.fillMaxSize()) {
            Image(image.asImageBitmap(), null, Modifier.fillMaxSize().testTag("page-image"), contentScale = ContentScale.Fit)
        }
    } else {
        Column(Modifier.fillMaxSize().padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center) {
            if (error == null && source != null) {
                CircularProgressIndicator(Modifier.testTag("iiif-page-loading"))
                Text(stringResource(R.string.loading), Modifier.padding(top = 12.dp))
            } else {
                val failure = error as? IiifRequestException
                Text(when (failure?.status) {
                    429, 503 -> stringResource(R.string.iiif_wait_seconds, remaining)
                    403 -> stringResource(R.string.iiif_access_denied)
                    else -> stringResource(R.string.page_load_failed)
                }, Modifier.testTag("iiif-page-error"))
                if (failure != null) Text("HTTP ${failure.status}", style = MaterialTheme.typography.bodySmall)
                Button(onClick = { attempt++ }, enabled = remaining == 0L && source != null,
                    modifier = Modifier.padding(top = 16.dp).testTag("iiif-page-retry")) {
                    Text(stringResource(R.string.retry_page))
                }
            }
        }
    }
}
