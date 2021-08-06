# -*-python-*-

__version__ = "1.0"
__author__ = "cyberspace69"
__url__ = "https://dumph.one"
__date__ = "$Date: 2021/05/15 09:46:09 $"

#
# This is a Symbian s60 port of the Python 2.2 version of simplejson
# https://github.com/simplejson/simplejson/tree/python2.2
#
# To reference this in python scripts on Symbian s60 devices:
# 1) Make sure you have a compatible Python app installed on the Symbian device
# 2) On the Symbian device, place this file in the following path:
#
# "C:\Data\python\lib\s60_simplejson.py"
#
# For other projects:
# 1) https://anon.sh - security projects and information
# 2) https://dumbph.one - resources for "dumbphone" apps & more

#
# scanner.py
#

"""
Iterator based sre token scanner
"""
import sre_parse, sre_compile, sre_constants
from sre_constants import BRANCH, SUBPATTERN
from sre import VERBOSE, MULTILINE, DOTALL
import re

__all__ = ['Scanner', 'pattern']

FLAGS = (VERBOSE | MULTILINE | DOTALL)


class Scanner(object):
    def __init__(self, lexicon, flags=FLAGS):
        self.actions = [None]
        # combine phrases into a compound pattern
        s = sre_parse.Pattern()
        s.flags = flags
        p = []
        for idx, token in enumerate(lexicon):
            phrase = token.pattern
            try:
                subpattern = sre_parse.SubPattern(s,
                                                  [(SUBPATTERN, (idx + 1, sre_parse.parse(phrase, flags)))])
            except sre_constants.error:
                raise
            p.append(subpattern)
            self.actions.append(token)

        p = sre_parse.SubPattern(s, [(BRANCH, (None, p))])
        self.scanner = sre_compile.compile(p)

    def iterscan(self, string, idx=0, context=None):
        """
        Yield match, end_idx for each match
        """
        match = self.scanner.scanner(string, idx).match
        actions = self.actions
        lastend = idx
        end = len(string)
        while True:
            m = match()
            if m is None:
                break
            matchbegin, matchend = m.span()
            if lastend == matchend:
                break
            action = actions[m.lastindex]
            if action is not None:
                rval, next_pos = action(m, context)
                if next_pos is not None and next_pos != matchend:
                    # "fast forward" the scanner
                    matchend = next_pos
                    match = self.scanner.scanner(string, matchend).match
                yield rval, matchend
            lastend = matchend


def pattern(pattern, flags=FLAGS):
    def decorator(fn):
        fn.pattern = pattern
        fn.regex = re.compile(pattern, flags)
        return fn

    return decorator


def InsignificantWhitespace(match, context):
    return None, None


pattern(r'\s+')(InsignificantWhitespace)

#
# decoder.py
#

"""
Implementation of JSONDecoder
"""

def _floatconstants():
    import struct
    import sys
    _BYTES = '7FF80000000000007FF0000000000000'.decode('hex')
    if sys.byteorder != 'big':
        # slicing not available in Python 2.2
        # _BYTES = _BYTES[:8][::-1] + _BYTES[8:][::-1]
        _BYTES = '000000000000f87f000000000000f07f'.decode('hex')
    nan, inf = struct.unpack('dd', _BYTES)
    return nan, inf, -inf


NaN, PosInf, NegInf = _floatconstants()


def linecol(doc, pos):
    lineno = doc.count('\n', 0, pos) + 1
    if lineno == 1:
        colno = pos
    else:
        colno = pos - doc.rindex('\n', 0, pos)
    return lineno, colno


def errmsg(msg, doc, pos, end=None):
    lineno, colno = linecol(doc, pos)
    if end is None:
        return '%s: line %d column %d (char %d)' % (msg, lineno, colno, pos)
    endlineno, endcolno = linecol(doc, end)
    return '%s: line %d column %d - line %d column %d (char %d - %d)' % (
        msg, lineno, colno, endlineno, endcolno, pos, end)


def JSONInfinity(match, context):
    return PosInf, None


pattern('Infinity')(JSONInfinity)


def JSONNegInfinity(match, context):
    return NegInf, None


pattern('-Infinity')(JSONNegInfinity)


def JSONNaN(match, context):
    return NaN, None


pattern('NaN')(JSONNaN)


def JSONTrue(match, context):
    return True, None


pattern('true')(JSONTrue)


def JSONFalse(match, context):
    return False, None


pattern('false')(JSONFalse)


def JSONNull(match, context):
    return None, None


pattern('null')(JSONNull)


def JSONNumber(match, context):
    match = JSONNumber.regex.match(match.string, *match.span())
    integer, frac, exp = match.groups()
    if frac or exp:
        res = float(integer + (frac or '') + (exp or ''))
    else:
        res = int(integer)
    return res, None


pattern(r'(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?')(JSONNumber)

STRINGCHUNK = re.compile(r'("|\\|[^"\\]+)', FLAGS)
STRINGBACKSLASH = re.compile(r'([\\/bfnrt"]|u[A-Fa-f0-9]{4})', FLAGS)
BACKSLASH = {
    '"': u'"', '\\': u'\\', '/': u'/',
    'b': u'\b', 'f': u'\f', 'n': u'\n', 'r': u'\r', 't': u'\t',
}

DEFAULT_ENCODING = "utf-8"


def scanstring(s, end, encoding=None):
    if encoding is None:
        encoding = DEFAULT_ENCODING
    chunks = []
    while 1:
        chunk = STRINGCHUNK.match(s, end)
        end = chunk.end()
        m = chunk.group(1)
        if m == '"':
            break
        if m == '\\':
            chunk = STRINGBACKSLASH.match(s, end)
            if chunk is None:
                raise ValueError(errmsg("Invalid \\escape", s, end))
            end = chunk.end()
            esc = chunk.group(1)
            try:
                m = BACKSLASH[esc]
            except KeyError:
                m = unichr(int(esc[1:], 16))
        if not isinstance(m, unicode):
            m = unicode(m, encoding)
        chunks.append(m)
    return u''.join(chunks), end


def JSONString(match, context):
    encoding = getattr(context, 'encoding', None)
    return scanstring(match.string, match.end(), encoding)


pattern(r'"')(JSONString)

WHITESPACE = re.compile(r'\s+', FLAGS)


def skipwhitespace(s, end):
    m = WHITESPACE.match(s, end)
    if m is not None:
        return m.end()
    return end


def JSONObject(match, context):
    pairs = {}
    s = match.string
    end = skipwhitespace(s, match.end())
    nextchar = s[end:end + 1]
    # trivial empty object
    if nextchar == '}':
        return pairs, end + 1
    if nextchar != '"':
        raise ValueError(errmsg("Expecting property name", s, end))
    end += 1
    encoding = getattr(context, 'encoding', None)
    while True:
        key, end = scanstring(s, end, encoding)
        end = skipwhitespace(s, end)
        if s[end:end + 1] != ':':
            raise ValueError(errmsg("Expecting : delimiter", s, end))
        end = skipwhitespace(s, end + 1)
        try:
            value, end = JSONScanner.iterscan(s, idx=end).next()
        except StopIteration:
            raise ValueError(errmsg("Expecting object", s, end))
        pairs[key] = value
        end = skipwhitespace(s, end)
        nextchar = s[end:end + 1]
        end += 1
        if nextchar == '}':
            break
        if nextchar != ',':
            raise ValueError(errmsg("Expecting , delimiter", s, end - 1))
        end = skipwhitespace(s, end)
        nextchar = s[end:end + 1]
        end += 1
        if nextchar != '"':
            raise ValueError(errmsg("Expecting property name", s, end - 1))
    return pairs, end


pattern(r'{')(JSONObject)


def JSONArray(match, context):
    values = []
    s = match.string
    end = skipwhitespace(s, match.end())
    # look-ahead for trivial empty array
    nextchar = s[end:end + 1]
    if nextchar == ']':
        return values, end + 1
    while True:
        try:
            value, end = JSONScanner.iterscan(s, idx=end).next()
        except StopIteration:
            raise ValueError(errmsg("Expecting object", s, end))
        values.append(value)
        end = skipwhitespace(s, end)
        nextchar = s[end:end + 1]
        end += 1
        if nextchar == ']':
            break
        if nextchar != ',':
            raise ValueError(errmsg("Expecting , delimiter", s, end))
        end = skipwhitespace(s, end)
    return values, end


pattern(r'\[')(JSONArray)

ANYTHING = [
    JSONTrue,
    JSONFalse,
    JSONNull,
    JSONNaN,
    JSONInfinity,
    JSONNegInfinity,
    JSONNumber,
    JSONString,
    JSONArray,
    JSONObject,
]

JSONScanner = Scanner(ANYTHING)


class JSONDecoder(object):
    """
    Simple JSON <http://json.org> decoder
    Performs the following translations in decoding:

    +---------------+-------------------+
    | JSON          | Python            |
    +===============+===================+
    | object        | dict              |
    +---------------+-------------------+
    | array         | list              |
    +---------------+-------------------+
    | string        | unicode           |
    +---------------+-------------------+
    | number (int)  | int, long         |
    +---------------+-------------------+
    | number (real) | float             |
    +---------------+-------------------+
    | true          | True              |
    +---------------+-------------------+
    | false         | False             |
    +---------------+-------------------+
    | null          | None              |
    +---------------+-------------------+
    It also understands ``NaN``, ``Infinity``, and ``-Infinity`` as
    their corresponding ``float`` values, which is outside the JSON spec.
    """

    _scanner = Scanner(ANYTHING)
    __all__ = ['__init__', 'decode', 'raw_decode']

    def __init__(self, encoding=None):
        """
        ``encoding`` determines the encoding used to interpret any ``str``
        objects decoded by this instance (utf-8 by default).  It has no
        effect when decoding ``unicode`` objects.

        Note that currently only encodings that are a superset of ASCII work,
        strings of other encodings should be passed in as ``unicode``.
        """
        self.encoding = encoding

    def decode(self, s):
        """
        Return the Python representation of ``s`` (a ``str`` or ``unicode``
        instance containing a JSON document)
        """
        obj, end = self.raw_decode(s, idx=skipwhitespace(s, 0))
        end = skipwhitespace(s, end)
        if end != len(s):
            raise ValueError(errmsg("Extra data", s, end, len(s)))
        return obj

    def raw_decode(self, s, **kw):
        """
        Decode a JSON document from ``s`` (a ``str`` or ``unicode`` beginning
        with a JSON document) and return a 2-tuple of the Python
        representation and the index in ``s`` where the document ended.
        This can be used to decode a JSON document from a string that may
        have extraneous data at the end.
        """
        kw.setdefault('context', self)
        try:
            obj, end = self._scanner.iterscan(s, **kw).next()
        except StopIteration:
            raise ValueError("No JSON object could be decoded")
        return obj, end


__all__ = ['JSONDecoder']

#
# encoder.py
#

"""
Implementation of JSONEncoder
"""

# this should match any kind of infinity
INFCHARS = re.compile(r'[infINF]')
ESCAPE = re.compile(r'[\x00-\x19\\"\b\f\n\r\t]')
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
ESCAPE_DCT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}
for i in range(20):
    ESCAPE_DCT.setdefault(chr(i), '\\u%04x' % (i,))


def floatstr(o, allow_nan=True):
    s = str(o)
    # If the first non-sign is a digit then it's not a special value
    if (o < 0.0 and s[1].isdigit()) or s[0].isdigit():
        return s
    elif not allow_nan:
        raise ValueError("Out of range float values are not JSON compliant: %r"
                         % (o,))
    # These are the string representations on the platforms I've tried
    if s == 'nan':
        return 'NaN'
    if s == 'inf':
        return 'Infinity'
    if s == '-inf':
        return '-Infinity'
    # NaN should either be inequal to itself, or equal to everything
    if o != o or o == 0.0:
        return 'NaN'
    # Last ditch effort, assume inf
    if o < 0:
        return '-Infinity'
    return 'Infinity'


def encode_basestring(s):
    """
    Return a JSON representation of a Python string
    """

    def replace(match):
        return ESCAPE_DCT[match.group(0)]

    return '"' + ESCAPE.sub(replace, s) + '"'


def encode_basestring_ascii(s):
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DCT[s]
        except KeyError:
            return '\\u%04x' % (ord(s),)

    return '"' + str(ESCAPE_ASCII.sub(replace, s)) + '"'


class JSONEncoder(object):
    """
    Extensible JSON <http://json.org> encoder for Python data structures.
    Supports the following objects and types by default:

    +-------------------+---------------+
    | Python            | JSON          |
    +===================+===============+
    | dict              | object        |
    +-------------------+---------------+
    | list, tuple       | array         |
    +-------------------+---------------+
    | str, unicode      | string        |
    +-------------------+---------------+
    | int, long, float  | number        |
    +-------------------+---------------+
    | True              | true          |
    +-------------------+---------------+
    | False             | false         |
    +-------------------+---------------+
    | None              | null          |
    +-------------------+---------------+
    To extend this to recognize other objects, subclass and implement a
    ``.default()`` method with another method that returns a serializable
    object for ``o`` if possible, otherwise it should call the superclass
    implementation (to raise ``TypeError``).
    """
    __all__ = ['__init__', 'default', 'encode', 'iterencode']

    def __init__(self, skipkeys=False, ensure_ascii=True, check_circular=True,
                 allow_nan=True):
        """
        Constructor for JSONEncoder, with sensible defaults.

        If skipkeys is False, then it is a TypeError to attempt
        encoding of keys that are not str, int, long, float or None.  If
        skipkeys is True, such items are simply skipped.
        If ensure_ascii is True, the output is guaranteed to be str
        objects with all incoming unicode characters escaped.  If ensure_ascii
        is false, the output will be unicode object.
        If check_circular is True, then lists, dicts, and custom encoded
        objects will be checked for circular references during encoding to
        prevent an infinite recursion (which would cause an OverflowError).
        Otherwise, no such check takes place.
        If allow_nan is True, then NaN, Infinity, and -Infinity will be
        encoded as such.  This behavior is not JSON specification compliant,
        but is consistent with most JavaScript based encoders and decoders.
        Otherwise, it will be a ValueError to encode such floats.
        """

        self.skipkeys = skipkeys
        self.ensure_ascii = ensure_ascii
        self.check_circular = check_circular
        self.allow_nan = allow_nan

    def _iterencode_list(self, lst, markers=None):
        if not lst:
            yield '[]'
            return
        if markers is not None:
            markerid = id(lst)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = lst
        yield '['
        first = True
        for value in lst:
            if first:
                first = False
            else:
                yield ', '
            for chunk in self._iterencode(value, markers):
                yield chunk
        yield ']'
        if markers is not None:
            del markers[markerid]

    def _iterencode_dict(self, dct, markers=None):
        if not dct:
            yield '{}'
            return
        if markers is not None:
            markerid = id(dct)
            if markerid in markers:
                raise ValueError("Circular reference detected")
            markers[markerid] = dct
        yield '{'
        first = True
        if self.ensure_ascii:
            encoder = encode_basestring_ascii
        else:
            encoder = encode_basestring
        allow_nan = self.allow_nan
        for key, value in dct.iteritems():
            if isinstance(key, (str, unicode)):
                pass
            # JavaScript is weakly typed for these, so it makes sense to
            # also allow them.  Many encoders seem to do something like this.
            elif isinstance(key, float):
                key = floatstr(key, allow_nan)
            elif isinstance(key, (int, long)):
                key = str(key)
            elif key is True:
                key = 'true'
            elif key is False:
                key = 'false'
            elif key is None:
                key = 'null'
            elif self.skipkeys:
                continue
            else:
                raise TypeError("key %r is not a string" % (key,))
            if first:
                first = False
            else:
                yield ', '
            yield encoder(key)
            yield ':'
            for chunk in self._iterencode(value, markers):
                yield chunk
        yield '}'
        if markers is not None:
            del markers[markerid]

    def _iterencode(self, o, markers=None):
        if isinstance(o, (str, unicode)):
            if self.ensure_ascii:
                encoder = encode_basestring_ascii
            else:
                encoder = encode_basestring
            yield encoder(o)
        elif o is None:
            yield 'null'
        elif o is True:
            yield 'true'
        elif o is False:
            yield 'false'
        elif isinstance(o, (int, long)):
            yield str(o)
        elif isinstance(o, float):
            yield floatstr(o, self.allow_nan)
        elif isinstance(o, (list, tuple)):
            for chunk in self._iterencode_list(o, markers):
                yield chunk
        elif isinstance(o, dict):
            for chunk in self._iterencode_dict(o, markers):
                yield chunk
        else:
            if markers is not None:
                markerid = id(o)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = o
            for chunk in self._iterencode_default(o, markers):
                yield chunk
            if markers is not None:
                del markers[markerid]

    def _iterencode_default(self, o, markers=None):
        newobj = self.default(o)
        return self._iterencode(newobj, markers)

    def default(self, o):
        """
        Implement this method in a subclass such that it returns
        a serializable object for ``o``, or calls the base implementation
        (to raise a ``TypeError``).
        For example, to support arbitrary iterators, you could
        implement default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)
        """
        raise TypeError("%r is not JSON serializable" % (o,))

    def encode(self, o):
        """
        Return a JSON string representation of a Python data structure.
        >>> JSONEncoder().encode({"foo": ["bar", "baz"]})
        '{"foo":["bar", "baz"]}'
        """
        # This doesn't pass the iterator directly to ''.join() because it
        # sucks at reporting exceptions.  It's going to do this internally
        # anyway because it uses PySequence_Fast or similar.
        chunks = list(self.iterencode(o))
        return ''.join(chunks)

    def iterencode(self, o):
        """
        Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)
        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        return self._iterencode(o, markers)


__all__ = ['JSONEncoder']

#
# simplejson.py
#

class simplejson:

    def __init__(self):
        pass

    def dump(self, obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
             allow_nan=True, cls=None, **kw):

        if cls is None:
            cls = JSONEncoder
            iterable = cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                           check_circular=check_circular, allow_nan=allow_nan,
                           **kw).iterencode(obj)

            # could accelerate with writelines in some versions of Python, at
            # a debuggability cost

            for chunk in iterable:
                fp.write(chunk)

    def dumps(self, obj, skipkeys=False, ensure_ascii=True, check_circular=True,
              allow_nan=True, cls=None, **kw):

        if cls is None:
            cls = JSONEncoder

        return cls(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
                   check_circular=check_circular, allow_nan=allow_nan, **kw).encode(obj)

    def load(self, fp, encoding=None, cls=None, object_hook=None, **kw):

        if cls is None:
            cls = JSONDecoder

        if object_hook is not None:
            kw['object_hook'] = object_hook

        return cls(encoding=encoding, **kw).decode(fp.read())

    def loads(self, s, encoding=None, cls=None, object_hook=None, **kw):

        if cls is None:
            cls = JSONDecoder

        if object_hook is not None:
            kw['object_hook'] = object_hook

        return cls(encoding=encoding, **kw).decode(s)


#
# END
#