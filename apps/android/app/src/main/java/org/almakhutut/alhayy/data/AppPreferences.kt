package org.almakhutut.alhayy.data

import android.content.Context

class AppPreferences(context: Context) {
    private val prefs = context.getSharedPreferences("al-makhtut-settings", Context.MODE_PRIVATE)

    var apiBase: String
        get() = prefs.getString(KEY_API, "http://10.0.2.2:8000") ?: "http://10.0.2.2:8000"
        set(value) = prefs.edit().putString(KEY_API, value.trim().trimEnd('/')).apply()

    companion object {
        private const val KEY_API = "api_base"
    }
}
