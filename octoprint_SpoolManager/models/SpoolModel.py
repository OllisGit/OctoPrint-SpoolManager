# coding=utf-8
from __future__ import absolute_import

from peewee import CharField, Model, DecimalField, FloatField, DateField, DateTimeField, TextField, IntegerField, \
	BooleanField

from octoprint_SpoolManager.models.BaseModel import BaseModel


class SpoolModel(BaseModel):

	version = IntegerField(null=True) # since V3
	isTemplate = BooleanField(null=True)
	displayName = CharField(null=True)
	vendor = CharField(null=True)
	material = CharField(null=True)
	density = FloatField(null=True)
	diameter = FloatField(null=True)
	diameterTolerance = FloatField(null=True) # since V3
	colorName = CharField(null=True)
	color = CharField(null=True)
	flowRateCompensation = IntegerField(null=True) #since V3
	# Temperature
	temperature = IntegerField(null=True)
	bedTemperature = IntegerField(null=True) # since V3
	encloserTemperature = IntegerField(null=True) # since V3
	# in g
	totalWeight = FloatField(null=True)
	spoolWeight = FloatField(null=True) # since V3
	# in g
	usedWeight = FloatField(null=True)
	# in g
	remainingWeight = FloatField(null=True)

	# in mm
	totalLength = IntegerField(null=True) # since V3
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
