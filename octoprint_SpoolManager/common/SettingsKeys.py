# coding=utf-8
from __future__ import absolute_import

class SettingsKeys():

	SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID = "selectedSpoolDatabaseId"
	SETTINGS_KEY_HIDE_EMPTY_SPOOL_IN_SIDEBAR = "hideEmptySpoolsInSidebar"

	SETTINGS_KEY_REMINDER_SELECTING_SPOOL = "reminderSelectingSpool"
	SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED = "warnIfSpoolNotSelected"
	SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH = "warnIfFilamentNotEnough"

	SETTINGS_KEY_CURRENCY_SYMBOL = "currencySymbol"

	## Export / Import
	SETTINGS_KEY_IMPORT_CSV_MODE = "importCSVMode"
	KEY_IMPORTCSV_MODE_REPLACE = "replace"
	KEY_IMPORTCSV_MODE_APPEND = "append"

	## Storage
	SETTINGS_KEY_DATABASE_PATH = "databaseFileLocation"

	## Debugging
	SETTINGS_KEY_SQL_LOGGING_ENABLED = "sqlLoggingEnabled"

	SETTINGS_KEY_TOOL_OFFSET_ENABLED = "toolOffsetEnabled"
	SETTINGS_KEY_BED_OFFSET_ENABLED = "bedOffsetEnabled"
	SETTINGS_KEY_ENCLOSURE_OFFSET_ENABLED = "enclosureOffsetEnabled"
