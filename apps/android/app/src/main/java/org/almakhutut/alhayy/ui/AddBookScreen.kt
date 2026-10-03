package org.almakhutut.alhayy.ui

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Collections
import androidx.compose.material.icons.filled.AutoStories
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.LocalBook
import org.almakhutut.alhayy.data.LocalBookStore

@Composable
fun AddBookScreen(
    store: LocalBookStore,
    onBack: () -> Unit,
    onImported: (LocalBook) -> Unit,
) {
    var title by remember { mutableStateOf("") }
    var iiifUrl by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()\n    val iiifAccessDenied = stringResource(R.string.iiif_access_denied)

    fun runImport(block: suspend () -> LocalBook) {
        if (busy) return
        busy = true
        status = ""
        scope.launch {
            runCatching { block() }
                .onSuccess(onImported)
                .onFailure { error ->\n                    status = if (error.message == "IIIF_ACCESS_DENIED") iiifAccessDenied\n                    else error.message ?: "Import failed"\n                }
            busy = false
        }
    }

    val pdfPicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) runImport { store.importPdf(uri, title) }
    }
    val imagePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        if (uris.isNotEmpty()) runImport { store.importImages(uris, title) }
    }

    Scaffold(topBar = { AppTopBar(stringResource(R.string.add_book), onBack) }) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text(stringResource(R.string.book_title_optional)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )

            ElevatedCard(
                onClick = {
                    runImport {
                        store.importIiif(
                            "https://gallica.bnf.fr/iiif/ark:/12148/btv1b84061750/manifest.json",
                            title.ifBlank { "الزهراوي — التصريف" },
                        )
                    }
                },
                enabled = !busy,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(
                    Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    Icon(Icons.Default.AutoStories, contentDescription = null)
                    Column(Modifier.weight(1f)) {
                        Text(
                            stringResource(R.string.demo_zahrawi),
                            style = MaterialTheme.typography.titleMedium,
                        )
                        Text(
                            stringResource(R.string.demo_zahrawi_hint),
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }

            ImportButton(
                icon = { Icon(Icons.Default.PictureAsPdf, null) },
                title = stringResource(R.string.import_pdf),
                subtitle = stringResource(R.string.import_pdf_hint),
                enabled = !busy,
            ) { pdfPicker.launch(arrayOf("application/pdf")) }

            ImportButton(
                icon = { Icon(Icons.Default.Collections, null) },
                title = stringResource(R.string.import_images),
                subtitle = stringResource(R.string.import_images_hint),
                enabled = !busy,
            ) { imagePicker.launch(arrayOf("image/*")) }

            HorizontalDivider()
            Text(stringResource(R.string.import_iiif), style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = iiifUrl,
                onValueChange = { iiifUrl = it },
                label = { Text(stringResource(R.string.iiif_url)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Button(
                onClick = { runImport { store.importIiif(iiifUrl.trim(), title) } },
                enabled = !busy && iiifUrl.startsWith("https://"),
                modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
            ) {
                Icon(Icons.Default.AutoStories, null)
                Spacer(Modifier.width(8.dp))
                Text(stringResource(R.string.open_iiif))
            }

            if (busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            if (status.isNotBlank()) Text(status, color = MaterialTheme.colorScheme.error)
        }
    }
}

@Composable
private fun ImportButton(
    icon: @Composable () -> Unit,
    title: String,
    subtitle: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    ElevatedCard(onClick = onClick, enabled = enabled, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(16.dp), horizontalArrangement = Arrangement.spacedBy(14.dp)) {
            icon()
            Column(Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(subtitle, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}
