package org.almakhutut.alhayy

import android.os.Bundle
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import kotlinx.coroutines.launch
import org.almakhutut.alhayy.data.ApiClient
import org.almakhutut.alhayy.data.AppPreferences
import org.almakhutut.alhayy.data.LocalBook
import org.almakhutut.alhayy.data.LocalBookStore
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.ui.*

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            AlMakhtutTheme {
                Surface(Modifier.fillMaxSize()) { LivingManuscriptApp() }
            }
        }
    }
}

@Composable
private fun LivingManuscriptApp() {
    val context = LocalContext.current
    val preferences = remember { AppPreferences(context) }
    val localStore = remember { LocalBookStore(context) }
    val api = remember { ApiClient() }
    val scope = rememberCoroutineScope()
    val loadingText = stringResource(R.string.loading)
    val emptyServerText = stringResource(R.string.no_server_books)
    val loadedText = stringResource(R.string.loaded_ok)
    val unavailableText = stringResource(R.string.server_unavailable)
    val savedText = stringResource(R.string.saved)


    var screen by remember { mutableStateOf(AppScreen.HOME) }
    var selectedRemote by remember { mutableStateOf<Manuscript?>(null) }
    var selectedLocal by remember { mutableStateOf<LocalBook?>(null) }
    var localBooks by remember { mutableStateOf(localStore.list()) }
    var remoteBooks by remember { mutableStateOf<List<Manuscript>>(emptyList()) }
    var apiBase by remember { mutableStateOf(preferences.apiBase) }
    var status by remember { mutableStateOf("") }

    fun goHome() {
        selectedRemote = null
        selectedLocal = null
        screen = AppScreen.HOME
    }

    BackHandler(enabled = screen.hasInternalBack) { goHome() }

    fun refreshRemote() {
        status = loadingText
        scope.launch {
            runCatching { api.manuscripts(apiBase) }
                .onSuccess {
                    remoteBooks = it
                    status = if (it.isEmpty()) {
                        emptyServerText
                    } else {
                        loadedText
                    }
                }
                .onFailure {
                    status = unavailableText
                }
        }
    }

    when (screen) {
        AppScreen.REMOTE_READER -> selectedRemote?.let { manuscript ->
            ReaderScreen(manuscript, apiBase, onBack = ::goHome)
        } ?: goHome()

        AppScreen.LOCAL_READER -> selectedLocal?.let { book ->
            LocalBookReaderScreen(book, onBack = ::goHome)
        } ?: goHome()

        AppScreen.ADD_BOOK -> AddBookScreen(
            store = localStore,
            onBack = ::goHome,
            onImported = { book ->
                localBooks = localStore.list()
                selectedLocal = book
                screen = AppScreen.LOCAL_READER
            },
        )

        AppScreen.ABOUT -> AboutScreen(onBack = ::goHome)

        AppScreen.SETTINGS -> SettingsScreen(
            apiBase = apiBase,
            onApiBaseChange = {
                apiBase = it.trim()
                preferences.apiBase = apiBase
                status = savedText
            },
            onBack = ::goHome,
        )

        AppScreen.HOME -> Scaffold(
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(
                        selected = true,
                        onClick = { screen = AppScreen.HOME },
                        icon = { Icon(Icons.Default.Home, null) },
                        label = { Text(stringResource(R.string.home)) },
                    )
                    NavigationBarItem(
                        selected = false,
                        onClick = { screen = AppScreen.ADD_BOOK },
                        icon = { Icon(Icons.Default.Add, null) },
                        label = { Text(stringResource(R.string.add_book)) },
                    )
                    NavigationBarItem(
                        selected = false,
                        onClick = { screen = AppScreen.ABOUT },
                        icon = { Icon(Icons.Default.Info, null) },
                        label = { Text(stringResource(R.string.about)) },
                    )
                    NavigationBarItem(
                        selected = false,
                        onClick = { screen = AppScreen.SETTINGS },
                        icon = { Icon(Icons.Default.Settings, null) },
                        label = { Text(stringResource(R.string.settings)) },
                    )
                }
            },
        ) { padding ->
            Box(Modifier.fillMaxSize().padding(padding)) {
                HomeScreen(
                    localBooks = localBooks,
                    remoteBooks = remoteBooks,
                    status = status,
                    onRefresh = ::refreshRemote,
                    onAddBook = { screen = AppScreen.ADD_BOOK },
                    onOpenLocal = {
                        selectedLocal = it
                        screen = AppScreen.LOCAL_READER
                    },
                    onOpenRemote = {
                        selectedRemote = it
                        screen = AppScreen.REMOTE_READER
                    },
                )
            }
        }
    }
}
