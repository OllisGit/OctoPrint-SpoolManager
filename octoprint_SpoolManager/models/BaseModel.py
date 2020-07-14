# coding=utf-8
from __future__ import absolute_import

import datetime

from peewee import Model, DateTimeField, AutoField


# model definitions -- the standard "pattern" is to define a base model class
# that specifies which database to use.  then, any subclasses will automatically
# use the correct storage.

def make_table_name(model_class):
    model_name = model_class.__name__
    return "spo_" + model_name.lower()

class BaseModel(Model):

	databaseId = AutoField()
	created = DateTimeField(default=datetime.datetime.now)

	class Meta:
		table_function = make_table_name
		pass
