import abc
from collections import OrderedDict

__all__ = ['DelimitedArgs', 'HyphenArgs', 'ColonDelimitedArgs']


class DelimitedArgs(OrderedDict):
    value_join = '='

    @abc.abstractproperty
    def delimiter(self):
        "The delimited between arguments"

    def __str__(self):
        return self.delimiter.join(self.get_args())

    arg_items = OrderedDict.items

    def get_args(self):
        return [
            self.value_join.join(item for item in arg if item)
            for arg in self.arg_items()
        ]


class HyphenArgs(DelimitedArgs):
    """
    Construct args suitable for unix-style command lines.

    e.g. -flag
    >>> print(HyphenArgs({'flag':None}))
    -flag

    e.g. -filename myfile.txt
    >>> print(HyphenArgs(filename='myfile.txt'))
    -filename myfile.txt

    >>> args = HyphenArgs([('a','a'), ('b','b')])
    >>> args_copy = args.copy()
    >>> print(args_copy)
    -a a -b b
    >>> print(HyphenArgs([('a', '1'), ('b', None)]))
    -a 1 -b
    """

    value_join = ' '
    delimiter = ' '

    @staticmethod
    def add_hyphen(value):
        return '-%s' % value

    def arg_items(self):
        return zip(self.hyphenated_keys(), self.values())

    def hyphenated_keys(self):
        return map(self.add_hyphen, super(self.__class__, self).keys())


class ColonDelimitedArgs(DelimitedArgs):
    """
    >>> args = ColonDelimitedArgs((('x', '3'), ('y', '4')))
    >>> print(args)
    x=3:y=4
    """

    delimiter = ':'
