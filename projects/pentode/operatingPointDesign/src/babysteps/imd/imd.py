#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np

# G,D,G 98,147,196
f1      = 98            # freqs of the notes
f2      = 147           # can be 0 to null the note
f3      = 196

# G major triad
f1      = 196
f2      = 247
f3      = 294

Fs = 44000.0;           # sampling rate
Ts = 1.0/Fs;            # sampling interval
t = np.arange(0,1,Ts)   # time vector

vin1 = np.sin(2*np.pi*f1*t)
vin2 = np.sin(2*np.pi*f2*t)
vin3 = np.sin(2*np.pi*f3*t)

vin  = vin1 + vin2 + vin3
vout = 2.0*vin + 500e-3*(vin**2) + 300e-3*(vin**3)   # amplifier non-linear

n   = len(vout) # length of the signal
k   = np.arange(n)
T   = n/Fs
frq = k/T # two sides frequency range
frq = frq[range(n/2)] # one side frequency range

Y   = np.fft.fft(vout)/n # fft computing and normalization
Y   = Y[range(n/2)]
mag = 20*np.log10(np.abs(Y))

peakindices  = mag > -90
peakfrqs = frq[peakindices]
peaks    = mag[peakindices]

fig, ax = plt.subplots(3, 1,figsize=(10, 20))
ax[0].plot(t,vin1,label='Vin1')
if f2:
    ax[0].plot(t,vin2,label='Vin2')
if f3:
    ax[0].plot(t,vin3,label='Vin3')
ax[0].set_xlabel('Time')
ax[0].set_xlim(0,5.0/f1)
ax[0].set_ylabel('Amplitude')
handles, labels = ax[0].get_legend_handles_labels()
ax[0].legend(handles[::-1], labels[::-1])

ax[1].plot(t,vin, label='Vin')
ax[1].plot(t,vout, label='Vout')
ax[1].set_xlabel('Time')
ax[1].set_xlim(0,5.0/f1)
ax[1].set_ylabel('Amplitude')
handles, labels = ax[1].get_legend_handles_labels()
ax[1].legend(handles[::-1], labels[::-1])

ax[2].semilogx(frq,mag,'r') # plotting the spectrum
ax[2].set_xlabel('Freq (Hz)')
ax[2].set_xlim(10,20000)
ax[2].grid(True,'both')
ax[2].set_ylabel('Vout dB')
ax[2].set_ylim(-120,20)

for i in range(len(peakfrqs)):
    ax[2].annotate("%.0f,%.1f"%(peakfrqs[i],peaks[i]),
        xy=(peakfrqs[i],peaks[i]),
        xycoords='data',
        xytext=(-5,8),
        textcoords='offset points',
        verticalalignment='left',
        rotation=90,
        bbox=dict(boxstyle="round", fc="1.0"),
        size=10)

print
print len(frq[peakfrqs > 10]),"peaks above DC"
print "Hz      dB"
for i in range(len(peakfrqs)):
    print "%-7.0f %-0.2f"%(peakfrqs[i],peaks[i])

plt.show()

