#!/usr/bin/python
# -*- coding: UTF-8 -*-

#Usage: python ListingRotate.py path/to/encoded/text/file.txt

#Will encode/decode the text with rot13 while encoding/decoding numbers with rot5 at the same time.
#Other characters won't be touched.
#Encoded/decoded text is written to sysout
#Encoding/decoding is transitive

import sys

def rot_listing(line):
  out = []
  for char in list(line):
    i = ord(char)
    if (i >= 97 and i <= 122):
      i-=97
      i+=13
      i%=26
      i+=97
    elif (i >= 65 and i <= 90):
      i-=65
      i+=13
      i%=26
      i+=65
    elif (i >= 48 and i <= 57):
      i-=48
      i+=5
      i%=10
      i+=48
    out.append(chr(i))
  return out
  

if __name__ == "__main__":
  f = open(sys.argv[1], 'rb')
  for line in f:
    print ''.join(rot_listing(line))
  f.close()
