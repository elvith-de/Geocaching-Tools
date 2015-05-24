# Geocaching-Tools
Tools that I produce while geocaching or while trying to solve puzzling mystery caches

## ConvertFrom-BinaryString
Ever stumbled upon a text like "01000111 00010110 ..."?

Dot source this powershell script and then run the function "ConvertFrom-BinaryString" e.g.

PS> . ConvertFrom-BinaryString.ps1

PS> $text = "01000111 ..."

PS> ConvertFrom-BinaryString -inputString $text

## DTMF.py
Tries to decode DTMF. Not clean, but worked for me.
