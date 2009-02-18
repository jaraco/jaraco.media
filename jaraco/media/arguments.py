#!python
# -*- coding: utf-8 -*-

__all__ = ['DelimitedArgs', 'HyphenArgs', 'ColonDelimitedArgs']

from itertools import ifilter
from jaraco.util.odict import odict
from jaraco.util import flatten

class DelimitedArgs(odict):
	value_join = '='
	
	def __str__(self):
		return self.delimiter.join(self.get_args())

	arg_items = odict.items

	def get_args(self):
		args = self.arg_items()
		remove_none_values = lambda item: filter(None, item)
		join_key_values = lambda item: self.value_join.join(item)
		args = map(join_key_values, map(remove_none_values, args))
		return args

class HyphenArgs(DelimitedArgs):
	"""
	Construct args suitable for unix-style command lines.
	
	e.g. -flag
	>>> print HyphenArgs({'flag':None})
	-flag
	
	e.g. -filename myfile.txt
	>>> print HyphenArgs(filename='myfile.txt')
	-filename myfile.txt
	
	>>> args = HyphenArgs([('a','a'), ('b','b')])
	>>> args_copy = args.copy()
	>>> print args_copy
	-a a -b b
	>>> print HyphenArgs([('a', '1'), ('b', None)])
	-a 1 -b
	""" 
	value_join=' '
	delimiter=' '
	
	@staticmethod
	def add_hyphen(value):
		return '-%s' % value

	def arg_items(self):
		return zip(self.hyphenated_keys(), self.values())

	def hyphenated_keys(self):
		return map(self.add_hyphen, super(self.__class__, self).keys())

	def __iter__(self):
		return ifilter(None, flatten(self.arg_items()))
		#for key, value in self.arg_items():
		#	yield key
		#	yield value

class ColonDelimitedArgs(DelimitedArgs):
	"""
	>>> print ColonDelimitedArgs(x='3', y='4')
	y=4:x=3
	"""
	delimiter = ':'
	
	def __iter__(self):
		yield str(self)

