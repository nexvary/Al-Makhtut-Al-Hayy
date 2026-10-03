package org.almakhutut.alhayy.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import org.almakhutut.alhayy.R
import org.almakhutut.alhayy.data.LocalBook
import org.almakhutut.alhayy.model.Manuscript

@Composable
fun HomeScreen(
    localBooks: List<LocalBook>,
    remoteBooks: List<Manuscript>,
    status: String,
    onRefresh: () -> Unit,
    onAddBook: () -> Unit,
    onOpenLocal: (LocalBook) -> Unit,
    onOpenRemote: (Manuscript) -> Unit,
) {
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Column(Modifier.weight(1f)) {
                    Text(stringResource(R.string.app_name), style = MaterialTheme.typography.headlineMedium)
                    Text(
                        stringResource(R.string.app_subtitle),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                IconButton(onClick = onRefresh) {
                    Icon(Icons.Default.Refresh, contentDescription = stringResource(R.string.refresh))
                }
            }
        }
        item {
            Button(
                onClick = onAddBook,
                modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
            ) {
                Icon(Icons.Default.Add, contentDescription = null)
                Spacer(Modifier.width(8.dp))
                Text(stringResource(R.string.add_book))
            }
        }
        if (status.isNotBlank()) item { Text(status, style = MaterialTheme.typography.bodySmall) }

        if (localBooks.isNotEmpty()) {
            item { Text(stringResource(R.string.my_books), style = MaterialTheme.typography.titleLarge) }
            items(localBooks, key = { it.id }) { book ->
                Card(Modifier.fillMaxWidth().clickable { onOpenLocal(book) }) {
                    Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Icon(
                            Icons.Default.MenuBook,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.secondary,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(book.title, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            Text(
                                stringResource(R.string.page_count, book.pageCount),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }
            }
        }

        if (remoteBooks.isNotEmpty()) {
            item { Text(stringResource(R.string.server_library), style = MaterialTheme.typography.titleLarge) }
            items(remoteBooks, key = { it.id }) { manuscript ->
                Card(Modifier.fillMaxWidth().clickable { onOpenRemote(manuscript) }) {
                    Row(Modifier.padding(14.dp), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        Icon(
                            Icons.Default.MenuBook,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                        )
                        Column(Modifier.weight(1f)) {
                            Text(manuscript.title, maxLines = 2, overflow = TextOverflow.Ellipsis)
                            manuscript.author?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                            Text(
                                stringResource(R.string.page_count, manuscript.pages.size),
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }
            }
        }

        if (localBooks.isEmpty() && remoteBooks.isEmpty()) {
            item {
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(18.dp)) {
                        Text(
                            stringResource(R.string.empty_library_title),
                            style = MaterialTheme.typography.titleMedium,
                        )
                        Text(stringResource(R.string.empty_library_body))
                    }
                }
            }
        }
    }
}
