# SPDX-License-Identifier: Apache-2.0
import datetime


def singleton(cls):
	class Meta(type(cls)):
		def __init__(self, name, bases, dct):
			self.__instance__ = None
			super().__init__(name, bases, dct)

		def __call__(self, *args, **kwargs):
			if self.__instance__ is None:
				self.__instance__ = super().__call__(*args, **kwargs)
			return self.__instance__

	return Meta(cls.__name__, (cls,), dict(cls.__dict__))


def utc_timestamp() -> float:
	return datetime.datetime.now(tz=datetime.timezone.utc).timestamp()


def timestamp_to_datetime(utc_timestamp: float) -> datetime.datetime:
	return datetime.datetime.fromtimestamp(utc_timestamp, tz=datetime.timezone.utc).astimezone()
