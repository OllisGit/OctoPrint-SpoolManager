# coding=utf-8
from __future__ import absolute_import

class SettingsKeys():

	SETTINGS_KEY_SELECTED_SPOOL_DATABASE_ID = "selectedSpoolDatabaseId"
	SETTINGS_KEY_HIDE_EMPTY_SPOOL_IN_SIDEBAR = "hideEmptySpoolsInSidebar"
	SETTINGS_KEY_HIDE_INACTIVE_SPOOL_IN_SIDEBAR = "hideInactiveSpoolsInSidebar"

	SETTINGS_KEY_REMINDER_SELECTING_SPOOL = "reminderSelectingSpool"
	SETTINGS_KEY_WARN_IF_SPOOL_NOT_SELECTED = "warnIfSpoolNotSelected"
	SETTINGS_KEY_WARN_IF_FILAMENT_NOT_ENOUGH = "warnIfFilamentNotEnough"

	SETTINGS_KEY_CURRENCY_SYMBOL = "currencySymbol"

	## QR - Code
	SETTINGS_KEY_QR_CODE_ENABLED = "qrCodeEnabled"
	SETTINGS_KEY_QR_CODE_FILL_COLOR = "qrCodeFillColor"
	SETTINGS_KEY_QR_CODE_BACKGROUND_COLOR = "qrCodeBackgroundColor"
	SETTINGS_KEY_QR_CODE_WIDTH = "qrCodeWidth"
	SETTINGS_KEY_QR_CODE_HEIGHT = "qrCodeHeight"

	## Export / Import
	SETTINGS_KEY_IMPORT_CSV_MODE = "importCSVMode"
	KEY_IMPORTCSV_MODE_REPLACE = "replace"
	KEY_IMPORTCSV_MODE_APPEND = "append"

	## Storage
	SETTINGS_KEY_DATABASE_USE_EXTERNAL = "useExternal"
	SETTINGS_KEY_DATABASE_LOCAL_FILELOCATION = "databaseFileLocation"
	SETTINGS_KEY_DATABASE_TYPE = "databaseType"
	SETTINGS_KEY_DATABASE_HOST = "databaseHost"
	SETTINGS_KEY_DATABASE_PORT = "databasePort"
	SETTINGS_KEY_DATABASE_NAME = "databaseName"
	SETTINGS_KEY_DATABASE_USER = "databaseUser"
	SETTINGS_KEY_DATABASE_PASSWORD = "databasePassword"

	## Debugging
	SETTINGS_KEY_SQL_LOGGING_ENABLED = "sqlLoggingEnabled"
