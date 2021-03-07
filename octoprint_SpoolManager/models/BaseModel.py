# coding=utf-8
from __future__ import absolute_import

import datetime

from peewee import Model, DateTimeField, AutoField, BigAutoField, IntegerField, FixedCharField, TimestampField, \
	SmallIntegerField


# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.

def make_table_name(model_class):
    model_name = model_class.__name__
    return "spo_" + model_name.lower()

class BaseModel(Model):

	databaseId = AutoField()
	created = DateTimeField(default=datetime.datetime.now)	# TODO question: Is this better? DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
	updated = DateTimeField(default=datetime.datetime.now)	# since V4
	version = SmallIntegerField(null=True)					# since V4
	# activeState = FixedCharField(null=True,max_length=60) 	# TODO question: do we really need this? since V4, possible values: deleted, notChoosable
	originator = FixedCharField(null=True, max_length=60) 	# since V4, who created this database entry, username, system, ...

	class Meta:
		table_function = make_table_name
		pass
