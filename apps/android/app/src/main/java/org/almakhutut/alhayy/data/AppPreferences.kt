package org.almakhutut.alhayy.data

import android.content.Context

class AppPreferences(context: Context) {
    private val prefs = context.getSharedPreferences("al-makhtut-settings", Context.MODE_PRIVATE)

    var apiBase: String
        get() {
            val saved = prefs.getString(KEY_API, "") ?: ""
            // 10.0.2.2 is an Android-emulator host alias and must never be treated as
            // the production server on a physical phone.
            return if (saved == "http://10.0.2.2:8000") "" else saved
        }
        set(value) = prefs.edit().putString(KEY_API, value.trim().trimEnd('/')).apply()

    companion object {
        private const val KEY_API = "api_base"
    }
}
