# coding=utf-8
from __future__ import absolute_import

from octoprint_SpoolManager.models.BaseModel import BaseModel
from peewee import CharField, Model, DecimalField, FloatField, DateField, DateTimeField, TextField, ForeignKeyField


class PluginMetaDataModel(BaseModel):

	KEY_PLUGIN_VERSION = "pluginVersion"
	KEY_DATABASE_SCHEME_VERSION = "databaseSchemeVersion"

	key = CharField(null=False)
	value = CharField(null=False)
