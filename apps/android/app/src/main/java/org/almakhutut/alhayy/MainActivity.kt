package org.almakhutut.alhayy

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import org.almakhutut.alhayy.data.ApiClient
import org.almakhutut.alhayy.model.Manuscript
import org.almakhutut.alhayy.ui.AlMakhtutTheme
import org.almakhutut.alhayy.ui.ReaderScreen

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AlMakhtutTheme {
                Surface(Modifier.fillMaxSize()) { App() }
            }
        }
    }
}

@Composable
private fun App() {
    val api = remember { ApiClient() }
    val scope = rememberCoroutineScope()
    var apiBase by remember { mutableStateOf("http://10.0.2.2:8000") }
    var manuscripts by remember { mutableStateOf<List<Manuscript>>(emptyList()) }
    var selected by remember { mutableStateOf<Manuscript?>(null) }
    var status by remember { mutableStateOf("أدخل عنوان الخادم ثم حمّل المخطوطات.") }

    selected?.let { manuscript ->
        ReaderScreen(manuscript, apiBase) { selected = null }
        return
    }

    Column(Modifier.fillMaxSize().padding(16.dp)) {
        Text("المخطوط الحي", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        OutlinedTextField(
            value = apiBase,
            onValueChange = { apiBase = it },
            label = { Text("عنوان API") },
            modifier = Modifier.fillMaxWidth(),
        )
        Button(onClick = {
            status = "جارٍ التحميل…"
            scope.launch {
                runCatching { api.manuscripts(apiBase) }
                    .onSuccess {
                        manuscripts = it
                        status = if (it.isEmpty()) "لا توجد مخطوطات مستوردة بعد." else "تم التحميل."
                    }
                    .onFailure { status = "تعذر الاتصال: ${it.message}" }
            }
        }) { Text("تحميل المخطوطات") }
        Text(status)
        LazyColumn {
            items(manuscripts, key = { it.id }) { manuscript ->
                Card(
                    Modifier
                        .fillMaxWidth()
                        .padding(vertical = 5.dp)
                        .clickable { selected = manuscript },
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(manuscript.title, style = MaterialTheme.typography.titleMedium)
                        manuscript.author?.let { Text(it) }
                        Text("${manuscript.pages.size} صفحة")
                    }
                }
            }
        }
    }
}
