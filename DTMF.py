#!/usr/bin/python
# -*- coding: UTF-8 -*-

#Usage: python DTMF.py SomeSound.wav
#currently only tested with 16bit wav files that were sampled at 44.1kHz

#You might want to convert this file http://upload.wikimedia.org/wikipedia/commons/b/b4/DTMF_all_16.ogg to a 16bit wav file with a sample rate of 44.1kHz to test decoding


#Yeah, I know, there are better alternatives tha FFT to decode 
#DTMF signals. Goertzel does a pretty good job here for example.
#But when I needed to decode DTMF, I thought it was a good point to 
#finally learn using FFT since I wanted to try it for a long time.
#And had some ideas for projects that could use it.

#Most parts of this code are taken from tutorials, are based of my talking to other people
#that already used FFT and some might only work by accident as I 
#coded them without understanding everything I needed.


#The MIT License (MIT)
#Copyright (c) 2015 Martin Zell
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.


from pylab import*
from scipy.io import wavfile
import sys

debug = False

#Method to wrap the actual FFT
def doFFT(samples,sfreq):
	#Samples are already normalized by main method, so just do an fft
	frequencies = fft(samples)
	#Sample rate/2 = max. frequency that can be reconstructed, so discard the rest
	#fft is symmetrical
	uniquePoints = ceil((len(samples)+1)/2.)
	frequencies = frequencies[0:uniquePoints]
	#frequency data is in complex number format, we only need the real part:
	frequencies = abs(frequencies)
	# scale by number of contained points
	#nobody could explain me why, but the common reason for that seems to be:
	#"Everyone does it (by that)!"
	frequencies = frequencies/float(len(samples))
	# Power of frequency
	frequencies = frequencies ** 2
	#since we discarded half of the data, we need to adjust the power now (*2)
	#if number of frequencies is even, the Nyquist point is included, which should not be doubled
	if (len(samples) %2 > 0):
		frequencies[1:len(samples)] = frequencies[1:len(samples)] * 2
	else:
		frequencies[1:len(samples)-1] = frequencies[1:len(samples)-1] * 2

	if debug:
		freqArray = arange(0, uniquePoints, 1.0) * (sfreq / len(samples));
		plot(freqArray/1000, 10*log10(frequencies[:uniquePoints]), color='k')
		xlabel('Frequency (kHz)')
		ylabel('Power (dB)')
		show()
	#power of frequency x can be found around position x/(samplefreq / numSamplesUsedForFFT)
	return frequencies	

#Method to get the power of a given frequency - usually from more than one bin
#so we need to interpolate the value
def getPower(f,frequencies, sfreq, numSamples):
	#get bin as float (usually between two discrete values)
	index = (float(f)/(sfreq / numSamples))
	#the first bin
	indexf = int(floor(index))
	#the second bin
	indexc = int(ceil(index))
	#where in between
	interpolate = index-indexf
	
	#base value from first bin
	powerBase = frequencies[indexf]
	#difference between the two bins
	difference = frequencies[indexc]-frequencies[indexf]
	#linear interpolation seems to be sufficient in this case
	power = powerBase+(difference*interpolate)

	if debug:
		print str(indexf)+ " - "+str(index)+" - "+str(indexc)+" - "+str(interpolate)
		print "powerBase:"+str(powerBase)
		print "powerNext:"+str(frequencies[indexc])
		print "power:"+str(power)

	return power
#	This will lead to garbage - don't even think about it
#	return max(frequencies[indexc],frequencies[indexf])


#Actual decoding of the DTMF signals goes here
def doDecodeDTMF(frequencies, sfreq, numSamples):
	
	#At first power -> decibel. Not neccessary for the next step, but 
	#plot for debug is nicer and more readable
	frequencies = 10*log10(frequencies)

	#DTMF uses 8 tones, of which 2 are mixed.
	#4 columns, 4 rows
	#by identifying the tones, we can locate the buttons
	#buttons are arranged like this:
	codeTable = [
	['1','2','3','A'],
	['4','5','6','B'],
	['7','8','9','C'],
	['*','0','#','D'],
	]

	#initialize list for the power of the tones
	col = [0,0,0,0]
	row = [0,0,0,0]
	
	#get the power of the specified frequency (in Hz)
	row[0] = getPower(697,frequencies, sfreq, numSamples)
	row[1] = getPower(770,frequencies, sfreq, numSamples)
	row[2] = getPower(852,frequencies, sfreq, numSamples)
	row[3] = getPower(941,frequencies, sfreq, numSamples)
	
	col[0] = getPower(1209,frequencies, sfreq, numSamples)
	col[1] = getPower(1336,frequencies, sfreq, numSamples)
	col[2] = getPower(1477,frequencies, sfreq, numSamples)
	col[3] = getPower(1633,frequencies, sfreq, numSamples)
	if debug:
		print "col: " + str(col)
		print "row: " + str(row)
	maxCol = 0
	maxRow = 0
	maxVal = None
	#search for the strongest signal in column tones
	for i in range(len(col)):
		if maxVal < col[i]:
			maxVal = col[i]
			maxCol = i
	maxVal = None
	#search for the strongest signal in row tones
	for i in range(len(row)):
		if maxVal < row[i]:
			maxVal = row[i]
			maxRow = i
	#...and return the char from the code table at said position
	return codeTable[maxRow][maxCol]

#naive method to find start and end of key press
#Assumes silence between keys.
#Optionally increase threshold when audio is noisy
def findSoundToAnalyze(wavdata, threshold=0.2):
	#Start in Mode "silence"
	mode = 'silence'
	start = None
	end = None
	samplesBelowThreshold = 0
	count = 0
	boundaries = []
	for i in range(len(wavdata)):
		if mode == 'silence':
			#When mode is silence
			#and value abve threshold
			#save start index and switch to mode sound
			if abs(wavdata[i]) > threshold:
				start= i
				mode = 'sound'
				samplesBelowThreshold=0
		if mode == 'sound':
			#when there is sound below threshold, count samples
			if abs(wavdata[i]) < threshold:
				samplesBelowThreshold= samplesBelowThreshold+1
			#reset counter to zero at sound above threshold
			if abs(wavdata[i]) >= threshold:
				samplesBelowThreshold=0
			#if more samples than 200 are silence AND we gathered at least 630 samples
			#FIXME: Amount samples depends on sample rate
			if samplesBelowThreshold > 200 and (i-start) >= 630:
					end = i
					if debug:
						print "Start at "+str(start/float(sampFreq))+" ("+str(start)+"), End at "+str((end)/float(sampFreq))+" ("+str(end)+") - Length: "+str((end-start)/sampFreq)+"("+str(end-start)+")"
					mode = 'silence'
					count = count+1
					boundaries.append([start,end])
	if debug:	
		print "Count Keys: "+str(count)
		print "Boundaries:"+str(boundaries)
	return boundaries

#FIXME: Threshold for seperation of key presses should be given on commandline optionally
if __name__ == "__main__":
	#Wavfile is given as argument
	sampFreq, snd = wavfile.read(sys.argv[1])
	numSamples = channels = 1
	samples = None
	datatype = snd.dtype

	#FFT wants all values in th range [1;1), but here we have 16 or 32bit values
	#Normalizing is needed
	if (snd.dtype == dtype(int16)):
		snd = snd / (2.**15)
	elif (snd.dtype == dtype(int32)):
		snd = snd / (2.**31)

	#Check if mono or more than one channel (only first one needed)
	if (len(snd.shape) > 1):
		numSamples = snd.shape[0] #number of samples
		channels = snd.shape[1] #number of channels (shoud be 2 in his case)
		wavdata = snd[:,0] #and the sound data of the first channel (second one ignored)
	else:
		numSamples = snd.shape[0]#number of samples
		wavdata = snd[:]#sound data

	length = float(numSamples)/sampFreq
	#find start and end of keypress
	boundaries = findSoundToAnalyze(wavdata)
	# Print some values
	print "Type: "+str(datatype)
	print "SampleFreq: "+str(sampFreq)
	print "Number of Samples: "+str(numSamples)
	print "Number of Audio Channels: "+str(channels)
	print "Audio length: "+str(length)+" seconds"
	print "Number of keys pressed: "+str(len(boundaries))

	if debug:
		bounds = []
		for i in range(numSamples):			
			bounds.append(0)
		for area in boundaries:
			for i in range(area[1]-area[0]):
				bounds[i+area[0]] = .8
		
		#Show waveform
		timeArray = arange(0, float(numSamples), 1)
		timeArray = timeArray / sampFreq
		timeArray = timeArray * 1000  #scale to milliseconds
		#plot sound
		plot(timeArray, abs(wavdata), color='k')
		#plot bounds		
		plot(timeArray, bounds, color='g')
		ylabel('Amplitude')
		xlabel('Time (ms)')
		show()


	numKey = 0
	keys = []
	#For every keypress
	for area in boundaries:
		numKey = numKey+1
		#FIXME: True for 44.kHz sample rate, nees to be calculated on the fly
		#DTMF says that tones should last atleast about 50ms to ensure recognition, 
		#70ms is optimal
		#DTMF tones are as narrow as about 70Hz, we need a bin width of max. 35Hz
		#to seperate them.
		#frequency spectrum for 44.1kHz is 22.05 kHz (half the sample rate)
		#Amount of samples needed for 35Hz bins: 22.05 kHz / 35 Hz = 630 samples
		#Proven by tests: 35Hz bin with seperates DTMF good; 
		#higher resolution not needed and ould be wste of processing power

		#slice 630 samples from audio data
		sam = wavdata[area[0]:area[0]+631]
		numSam = len(sam)
		
		#get Key
		keys.append(doDecodeDTMF(doFFT(sam,sampFreq),sampFreq,numSam))
	
	#print keys
	print "Keys: "+"".join(keys)
