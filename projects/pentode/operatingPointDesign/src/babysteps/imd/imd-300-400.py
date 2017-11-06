#!/usr/bin/env python

import matplotlib.pyplot as plt
import numpy as np

freqset = '300-400'
ampset  = 'even20'

ftable = {
    '100':(100,0,0),
    '300':(300,0,0),
    '400':(400,0,0),
    '300-400':(300,400,0),
    'GDG':(98,147,196),
    'Gm' :(196,247,294)
}

gtable = {
    'test'     : (0.00,1.0,2.0,0,0),
    'clean'     : (2.00,0,0,0,0),
    'even1'     : (2.0,500e-1,2.0,0,0),
    'even20'    : (2.0,1e-1,2.0,0,0),
    'even40'    : (2.0,1e-2,2.0,0,0),
    'even60'    : (2.0,1e-3,2.0,0,0),
    'even1020'  : (1.0,100e-1,2.0,100e-2,4.0),
    'even2040'  : (2.0,1e-1,2.0,1e-2,4.0),
    'even6080'  : (2.0,1e-3,2.0,1e-4,4.0),
    'odd20'     : (2.0,1e-1,3.0,0,0),
    'odd40'     : (2.0,1e-2,3.0,0,0),
    'odd2040'   : (2.0,1e-1,3.0,1e-2,5.0),
    'odd6080'   : (2.0,1e-3,3.0,1e-4,5.0),
    'odd1020'   : (1.0,100e-1,3.0,100e-2,5.0),
    'tubeeven20': (26,27.0,-1.6,0.3,0),
    'tubeeven40': (55,70.0,-1.0,0.05,0),
    'tubeodd20' : (0,1.0,0.0,1.5,0),
    'tubeodd40' : (0,5.0,0.0,0.35,0),
}

f1,f2,f3         = ftable[freqset]
a0,a1,af1,a2,af2 = gtable[ampset]
# print a0,a1,af1,a2,af2

Fs = 44000.0;           # sampling rate
Ts = 1.0/Fs;            # sampling interval
t = np.arange(0,1,Ts)   # time vector

vin1 = np.sin(2*np.pi*f1*t)
vin2 = np.sin(2*np.pi*f2*t)
vin3 = np.sin(2*np.pi*f3*t)

vin  = vin1 + vin2 + vin3

if ampset.count('tube'):
    vout = a0+a1*np.arctan(af1+a2*vin)
else:
    vout = a0*vin + a1*(vin**af1) + a2*(vin**af2)   # amplifier non-linear

vout = vout + np.random.normal(0.0,0.1,Fs)/100.0



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
peaksgtdc = len(frq[peakfrqs > 10])


fig, ax = plt.subplots(3, 1,figsize=(10, 20))
ax[0].plot(t,vin1,label='%dHz'%f1)
if f2:
    ax[0].plot(t,vin2,label='%dHz'%f2)
if f3:
    ax[0].plot(t,vin3,label='%dHz'%f3)
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

if peaksgtdc == 1:
    plabel = "Peak"
else:
    plabel = "Peaks"

ax[2].semilogx(frq,mag,'r',label="%s\n%d %s"%(ampset,peaksgtdc,plabel)) # plotting the spectrum
ax[2].set_xlabel('Freq (Hz)')
ax[2].set_xlim(10,20000)
ax[2].grid(True,'both')
ax[2].set_ylabel('Vout dB')
ax[2].set_ylim(-120,20)
handles, labels = ax[2].get_legend_handles_labels()
ax[2].legend(handles[::-1], labels[::-1])

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
print peaksgtdc,"peaks above DC"
print "Hz      dB"
for i in range(len(peakfrqs)):
    print "%-7.0f %-0.2f"%(peakfrqs[i],peaks[i])

mng = plt.get_current_fig_manager()
mng.resize(*mng.window.maxsize())

plt.show()

