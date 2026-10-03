package org.almakhutut.alhayy

enum class AppScreen {
    HOME,
    ADD_BOOK,
    ABOUT,
    SETTINGS,
    REMOTE_READER,
    LOCAL_READER,
}

val AppScreen.hasInternalBack: Boolean
    get() = this != AppScreen.HOME
