#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyparsing import \
    Combine, \
    Group, \
    OneOrMore, \
    Optional, \
    Suppress, \
    Word, \
    alphanums, \
    delimitedList, \
    nums, \
    oneOf

'''
Reference:
https://www.accelebrate.com/blog/pyparseltongue-parsing-text-with-pyparsing://www.accelebrate.com/blog/pyparseltongue-parsing-text-with-pyparsing/

URL grammar
  url ::= scheme '://' [userinfo] host [port] [path] [query] [fragment]
  scheme ::= http | https | ftp | file
  userinfo ::= url_chars+ ':' url_chars+ '@'
  host ::= alphanums | host (. + alphanums)
  port ::= ':' nums
  path ::= url_chars+
  query ::= '?' + query_pairs
  query_pairs ::= query_pairs | (query_pairs '&' query_pair)
  query_pair = url_chars+ '=' url_chars+
  fragment = '#' + url_chars
  url_chars = alphanums + '-_.~%+'
'''

url_chars = alphanums + '-_.~%+'

fragment = Combine((Suppress('#') + Word(url_chars)))('fragment')

scheme = oneOf('http https ftp file')('scheme')
host = Combine(delimitedList(Word(url_chars), '.'))('host')
port = Suppress(':') + Word(nums)('port')
user_info = (
    Word(url_chars)('username') +
    Suppress(':') +
    Word(url_chars)('password') +
    Suppress('@')
)

query_pair = Group(Word(url_chars) + Suppress('=') + Word(url_chars))
query = Group(Suppress('?') + delimitedList(query_pair, '&'))('query')

path = Combine(
    Suppress('/') + OneOrMore(~query + Word(url_chars + '/'))
)('path')

url_parser = (
    scheme +
    Suppress('://') +
    Optional(user_info) +
    host +
    Optional(port) +
    Optional(path) +
    Optional(query) +
    Optional(fragment)
)
