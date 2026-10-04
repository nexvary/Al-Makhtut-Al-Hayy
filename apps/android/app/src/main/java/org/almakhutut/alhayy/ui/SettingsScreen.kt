package org.almakhutut.alhayy.ui

import androidx.appcompat.app.AppCompatDelegate
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Language
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.os.LocaleListCompat
import org.almakhutut.alhayy.R

data class AppLanguage(val tag: String, val label: String)

val supportedLanguages = listOf(
    AppLanguage("ar", "العربية"), AppLanguage("en", "English"),
    AppLanguage("tr", "Türkçe"), AppLanguage("es", "Español"),
    AppLanguage("de", "Deutsch"), AppLanguage("it", "Italiano"),
    AppLanguage("fr", "Français"), AppLanguage("ur", "اردو"),
    AppLanguage("fa", "فارسی"), AppLanguage("ru", "Русский"),
)

@Composable
fun SettingsScreen(apiBase: String, onApiBaseChange: (String) -> Unit, onBack: () -> Unit) {
    var expanded by remember { mutableStateOf(false) }
    var value by remember(apiBase) { mutableStateOf(apiBase) }
    val currentTag = AppCompatDelegate.getApplicationLocales().toLanguageTags()
        .substringBefore(",").ifBlank { "ar" }

    Scaffold(topBar = { AppTopBar(stringResource(R.string.settings), onBack) }) { padding ->
        Column(
            Modifier.fillMaxSize().padding(padding).imePadding()
                .verticalScroll(rememberScrollState()).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(stringResource(R.string.language), style = MaterialTheme.typography.titleMedium)
            Box {
                OutlinedButton(onClick = { expanded = true }, modifier = Modifier.fillMaxWidth()) {
                    Icon(Icons.Default.Language, null)
                    Spacer(Modifier.width(8.dp))
                    Text(supportedLanguages.firstOrNull { it.tag == currentTag }?.label ?: "العربية")
                }
                DropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                    supportedLanguages.forEach { language ->
                        DropdownMenuItem(text = { Text(language.label) }, onClick = {
                            expanded = false
                            AppCompatDelegate.setApplicationLocales(LocaleListCompat.forLanguageTags(language.tag))
                        })
                    }
                }
            }

            Text(stringResource(R.string.server_settings), style = MaterialTheme.typography.titleMedium)
            OutlinedTextField(
                value = value,
                onValueChange = { value = it },
                label = { Text(stringResource(R.string.api_address)) },
                placeholder = { Text("https://your-server.example/api") },
                supportingText = { Text(stringResource(R.string.api_optional_note)) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            Button(onClick = { onApiBaseChange(value) }, modifier = Modifier.fillMaxWidth()) {
                Text(stringResource(R.string.save))
            }
            Text(stringResource(R.string.android_compatibility_note), style = MaterialTheme.typography.bodySmall)
        }
    }
}
