# coding=utf-8
from __future__ import absolute_import

from peewee import CharField, Model, DecimalField, FloatField, DateField, DateTimeField, TextField, IntegerField, \
	BooleanField

from octoprint_SpoolManager.models.BaseModel import BaseModel


class SpoolModel(BaseModel):

	isTemplate = BooleanField(null=True)
	displayName = CharField(null=True)
	vendor = CharField(null=True)
	material = CharField(null=True)
	density = FloatField(null=True)
	diameter = FloatField(null=True)
	colorName = CharField(null=True)
	color = CharField(null=True)
	# Grad
	temperature = IntegerField(null=True)
	# in g
	totalWeight = FloatField(null=True)
	# in g
	usedWeight = FloatField(null=True)
	# in g
	remainingWeight = FloatField(null=True)

	# in mm
	usedLength = IntegerField(null=True)
	# Bar or QR Code
	code = CharField(null=True)

	firstUse = DateTimeField(null=True)
	lastUse = DateTimeField(null=True)

	purchasedFrom = CharField(null=True)
	purchasedOn = DateField(null=True)
	cost = FloatField(null=True)
	costUnit = CharField(null=True)	# deprecated needs to be removed, value should be used from pluginSettings

	labels = TextField(null=True)

	noteText = TextField(null=True)
	noteDeltaFormat = TextField(null=True)
	noteHtml = TextField(null=True)

	# def __init__(self):
	# 	#self.displayname = CharField(unique=True)
	# 	pass
