<#
.SYNOPSIS
   Decodes a binary message given as string
.PARAMETER inputString
   The input to be decoded - formatted like this: '01010111 01100101'
#>
Function ConvertFrom-BinaryString{
[Cmdletbinding()]
param(
[String]
$inputString
)
$in = $inputString.trim().split("")
$out = $in | Foreach-Object {
	$string = $_.toCharArray()
	$value = 0
	for($i = 0; $i -lt $string.Count; $i++)
	{
		if($string[$i] -eq [char]"1")
		{
				$pos = $string.Count - 1 - $i
				$mask = 1 -shl $pos
				$value = $value -bor $mask
		}
	}
	$value
}
[char[]]$out -join ""
}
