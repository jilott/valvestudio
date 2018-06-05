#!/usr/bin/env python

# uses a lot of global variables, its a hack I know

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons

ftable = {
    '300':(300,0,0),
    '300-400':(300,400,0),
    'GDG':(196,294,392),
    'Gm' :(196,247,294),
    'Play':(0,0,0)
}

# vout = gain*np.arctan(offset+level*vin)

clean = True

gtable = {
#   label          gain  bias offset  level
    '/ clean'   : (50.0, 1, 0,      1.0),
    'bias0'     : (50.0, 1, 0,      0.2),
    'even1'     : (50.0, 1, 0.65,   0.6),
    'even20'    : (50.0, 1, 1e-1,   1.0),
    'even40'    : (50.0, 1, 1e-2,   1.0),
    'even60'    : (50.0, 1, 1e-3,   1.0),
    'odd20'     : (50.0, 1, 1e-1,   1.0),
    'odd40'     : (50.0, 1, 1e-2,   1.0),
}

freq1,freq2,freq3       = ftable['300']
gain,bias,offset,level       = gtable['/ clean']

Fs = 22050.0;           # sampling rate
Ts = 1.0/Fs;            # sampling interval
t = np.arange(0,1,Ts)   # time vector

n   = len(t) # length of the signal
k   = np.arange(n)
T   = n/Fs
fftfrq = k/T # two sides frequency range
fftfrq = fftfrq[range(n/2)] # one side frequency range
noise  = np.random.normal(0.0,0.1,Fs)/100.0

ampl1  = 1.0
phase1 = 0.0
ampl2  = 0.0
phase2 = 0.0
ampl3  = 0.0
phase3 = 0.0

transfermax     = 20
transferplot    = None
transferallvin  = transfermax*np.arange(-1.0,1.0,2*Ts)
transfervallplot= None

vin1 = ampl1*np.sin(2*np.pi*freq1*t+phase1)
vin2 = ampl2*np.sin(2*np.pi*freq2*t+phase2)
vin3 = ampl3*np.sin(2*np.pi*freq3*t+phase3)
vin = vin1 + vin2 + vin3

def voutCalc():
    global clean,vout
    if clean:
        vout = gain*vin + noise
    else:
        vout = gain*np.arctan(offset+level*vin) + noise  # adding a noise to have a noise floor

voutCalc()

def updatetransfer():
    global transferallvin,transferallvout,transfervin,offset
    if clean:
        transferallvout = gain*(bias*transferallvin)
    else:
        transferallvout = gain*np.arctan(bias*transferallvin)
    '''
    if clean:
        transferallvout = gain*(offset+level*transferallvin)
    else:
        transferallvout = gain*np.arctan(offset+level*transferallvin)
    '''
    if transfervallplot: # this checks if plot exists yet
        # print len(vin),len(transferallvin)
        # transfervallplot.set_xdata(vin)
        transfervallplot.set_ydata(transferallvout)
    if transferplot:
        r = np.logical_and(transferallvin>=offset+level*vin.min(), transferallvin<=offset+level*vin.max())
        transferplot.set_xdata(transferallvin[r])
        transferplot.set_ydata(transferallvout[r])

updatetransfer() # should do this all functions

fftout   = np.fft.fft(vout)/n # fft computing and normalization
fftout   = fftout[range(n/2)]
fftmag   = 20*np.log10(np.abs(fftout))

fig,axa = plt.subplots(2,2)

fig.text(0.70,0.965,"vout = gain * vin     or\nvout = gain * atan(offset + (level * vin))")

vin3plot, = axa[0,0].plot(t,vin3,label='%dHz'%freq3)
vin2plot, = axa[0,0].plot(t,vin2,label='%dHz'%freq2)
vin1plot, = axa[0,0].plot(t,vin1,label='%dHz'%freq1)
axa[0,0].set_xlim(0,5.0/freq1)
axa[0,0].set_ylim(-2.0,2.0)
handles, labels = axa[0,0].get_legend_handles_labels()
axa[0,0].legend(handles[::-1], labels[::-1])

vinplot,  = axa[0,1].plot(t,vin,label='Vin')
voutplot,  = axa[0,1].plot(t,vout,label='Vout')
axa[0,1].set_xlim(0,10.0/freq1)
handles, labels = axa[0,1].get_legend_handles_labels()
axa[0,1].legend(handles[::-1], labels[::-1])
# axa[0,1].set_ylim(-100.0,100.0)
axa[0,1].relim()
axa[0,1].autoscale_view(True,True,True)

transfervallplot,  = axa[1,0].plot(transferallvin,transferallvout,color='blue')
transferplot,      = axa[1,0].plot(vin,vout,color='green',linewidth=3)
axa[1,0].set_xlim(-transfermax,transfermax)
axa[1,0].set_ylim(-100.0,100.0)

def play():
    import pyaudio

    # need to recalc a temp version because repeated playing clicks at end-start discontinuity
    play_t = np.arange(0,25,Ts)   # time vector
    play_vin1 = ampl1*np.sin(2*np.pi*freq1*play_t+phase1)
    play_vin2 = ampl2*np.sin(2*np.pi*freq2*play_t+phase2)
    play_vin3 = ampl3*np.sin(2*np.pi*freq3*play_t+phase3)
    play_vin = play_vin1 + play_vin2 + play_vin3
    if clean:
        play_vout = gain*play_vin
    else:
        play_vout = gain*np.arctan(offset+level*play_vin)

    p = pyaudio.PyAudio()
    stream = p.open(format = pyaudio.paFloat32, channels = 1, rate = int(Fs), output = True)
    data = (play_vout/np.absolute(play_vout).max()).astype(np.float32)
    # print np.absolute(play_vout).max(), data.max()
    stream.write(data)
    stream.stop_stream()
    stream.close()
    p.terminate()


def updatefft():
    global fftfrq
    global vout,fftplot,ax,n,noise
    fftout   = np.fft.fft(vout)/n # fft computing and normalization
    fftout   = fftout[range(n/2)]
    fftmag   = 20*np.log10(np.abs(fftout))

    peakindices = fftmag > -90
    peakfrqs = fftfrq[peakindices]
    peaks    = fftmag[peakindices]
    peaksgtdc = len(peaks[peakfrqs > 10])
    handles, labels = axa[1,1].get_legend_handles_labels()
    axa[1,1].legend(handles[::-1], ["%d peaks"%peaksgtdc])

    fftplot.set_ydata(fftmag)

fftplot, = axa[1,1].semilogx(fftfrq,fftmag,'r',label="Peaks") # plotting the spectrum
axa[1,1].set_xlabel('Freq (Hz)')
axa[1,1].set_xlim(10,10000)
axa[1,1].grid(True,'both')
axa[1,1].set_ylabel('Vout dB')
axa[1,1].set_ylim(-120,40)
axa[1,1].autoscale_view(True,True,True)
handles, labels = axa[1,1].get_legend_handles_labels()
axa[1,1].legend(handles[::-1], labels[::-1])
updatefft()

def updatevout():
    global vin,vout,gain,offset,level,voutplot,axa
    # vout = gain*np.arctan(offset+level*vin)
    voutCalc()
    voutmean = vout.mean()
    vout = vout - voutmean + np.random.normal(0.0,0.1,Fs)/100.0
    voutplot.set_ydata(vout)
    axa[0,1].relim()
    axa[0,1].autoscale_view(True,True,True)
    updatetransfer()
    updatefft()

def updategain(val,update=True):
    global gain
    gain = val
    updatevout()
def updatebias(val,update=True):
    global bias
    bias = val
    updatevout()
def updateoffset(val,update=True):
    global offset
    offset = val
    updatevout()
def updatelevel(val,update=True):
    global level
    level = val
    updatevout()

def updatevin():
    global vin,vin1,vin2,vin3,vinplot
    vin = vin1 + vin2 + vin3
    vinplot.set_ydata(vin)
    updatevout()

def updatevin1plot():
    global vin1,vin1plot,freq1,ampl1,phase1
    vin1 = ampl1*np.sin(2*np.pi*freq1*t+phase1)
    vin1plot.set_ydata(vin1)
    vin1plot.set_label("%dHz"%freq1)
    handles, labels = axa[0,0].get_legend_handles_labels()
    axa[0,0].legend(handles[::-1], labels[::-1])
    updatevin()
def updatefreq1(val):
    global freq1
    freq1 = int(val)
    updatevin1plot()
def updateampl1(val):
    global ampl1
    ampl1 = val
    updatevin1plot()
def updatephase1(val):
    global phase1
    phase1 = val
    updatevin1plot()

def updatevin2plot():
    global vin2,vin2plot,freq2,ampl2,phase2
    vin2 = ampl2*np.sin(2*np.pi*freq2*t+phase2)
    vin2plot.set_ydata(vin2)
    vin2plot.set_label("%dHz"%freq2)
    handles, labels = axa[0,0].get_legend_handles_labels()
    axa[0,0].legend(handles[::-1], labels[::-1])
    updatevin()
def updatefreq2(val):
    global freq2
    freq2 = int(val)
    updatevin2plot()
def updateampl2(val):
    global ampl2
    ampl2 = val
    updatevin2plot()
def updatephase2(val):
    global phase2
    phase2 = val
    updatevin2plot()

def updatevin3plot():
    global vin3,vin3plot,freq3,ampl3,phase3
    vin3 = ampl3*np.sin(2*np.pi*freq3*t+phase3)
    vin3plot.set_ydata(vin3)
    vin3plot.set_label("%dHz"%freq3)
    handles, labels = axa[0,0].get_legend_handles_labels()
    axa[0,0].legend(handles[::-1], labels[::-1])
    updatevin()
def updatefreq3(val):
    global freq3
    freq3 = int(val)
    updatevin3plot()
def updateampl3(val):
    global ampl3
    ampl3 = val
    updatevin3plot()
def updatephase3(val):
    global phase3
    phase3 = val
    updatevin3plot()


axfreq1 = plt.axes([0.25, 0.1150, 0.65, 0.01])
sfreq1  = Slider(axfreq1,  'Freq1', 10.0, 1000, valinit=freq1,valfmt='%1d')
sfreq1.on_changed(updatefreq1)

axampl1 = plt.axes([0.25, 0.1025, 0.65, 0.01])
sampl1  = Slider(axampl1,  'Ampl1',  0.0, 2.0, valinit=ampl1)
sampl1.on_changed(updateampl1)

axphase1 = plt.axes([0.25, 0.09, 0.65, 0.01])
sphase1  = Slider(axphase1, 'Phase1', -90, 90, valinit=0,valfmt='%1d')
sphase1.on_changed(updatephase1)

axfreq2 = plt.axes([0.25, 0.0750, 0.65, 0.01])
sfreq2  = Slider(axfreq2,  'Freq2', 10.0, 1000, valinit=freq2,valfmt='%1d')
sfreq2.on_changed(updatefreq2)

axampl2  = plt.axes([0.25, 0.0625, 0.65, 0.01])
sampl2  = Slider(axampl2,  'Ampl2',  0.0, 2.0, valinit=ampl2)
sampl2.on_changed(updateampl2)

axphase2 = plt.axes([0.25, 0.05, 0.65, 0.01])
sphase2 = Slider(axphase2, 'Phase2', -90, 90, valinit=0,valfmt='%1d')
sphase2.on_changed(updatephase2)

axfreq3  = plt.axes([0.25, 0.0350, 0.65, 0.01])
sfreq3  = Slider(axfreq3,  'Freq3', 10.0, 1000, valinit=freq3,valfmt='%1d')
sfreq3.on_changed(updatefreq3)

axampl3  = plt.axes([0.25, 0.0225, 0.65, 0.01])
sampl3  = Slider(axampl3,  'Ampl3',  0.0, 2.0, valinit=ampl3)
sampl3.on_changed(updateampl3)

axphase3 = plt.axes([0.25, 0.0100, 0.65, 0.01])
sphase3 = Slider(axphase3, 'Phase3', -90, 90, valinit=0,valfmt='%1d')
sphase3.on_changed(updatephase3)

axgain = plt.axes([0.25, 0.1675, 0.65, 0.01])
sgain  = Slider(axgain,  'gain', 0.0, 100, valinit=gain)
sgain.on_changed(updategain)

axbias = plt.axes([0.25, 0.1550, 0.65, 0.01])
sbias  = Slider(axbias,  'bias', 0.0, 4.0, valinit=bias)
sbias.on_changed(updatebias)

axoffset = plt.axes([0.25, 0.1425, 0.65, 0.01])
soffset  = Slider(axoffset,  'offset', -5, 5, valinit=offset)
soffset.on_changed(updateoffset)

axlevel = plt.axes([0.25, 0.13, 0.65, 0.01])
slevel  = Slider(axlevel,  'level', 0.0, 10, valinit=level)
slevel.on_changed(updatelevel)

def freqSet(label):
    if label == 'Play':
        play()
        return
    freq1,freq2,freq3 = ftable[label]
    ampl1,ampl2,ampl3 = [1.0,1.0,1.0]
    updatefreq1(freq1)
    updatefreq2(freq2)
    updatefreq3(freq3)
    updateampl1(ampl1)
    updateampl2(ampl2)
    updateampl3(ampl3)
    sfreq1.set_val(freq1)
    sfreq2.set_val(freq2)
    sfreq3.set_val(freq3)
    sampl1.set_val(ampl1)
    sampl2.set_val(ampl2)
    sampl3.set_val(ampl3)
    fig.canvas.draw_idle()

freqradiox = plt.axes([0.025, 0.02, 0.07, 0.02*len(ftable)])
freqradio = RadioButtons(freqradiox,  sorted(ftable.keys()), active=0)
for circ in freqradio.circles:
    circ.set_radius(0.01*len(ftable))
freqradio.on_clicked(freqSet)

def gainSet(label):
    global clean
    if label == '/ clean':
        clean = True
    else:
        clean = False
    gain,bias,offset,level = gtable[label]
    updategain(gain,False)
    updateoffset(offset,False)
    updatelevel(level,True)
    updatevout()
    sgain.set_val(gain)
    soffset.set_val(offset)
    slevel.set_val(level)
    fig.canvas.draw_idle()

gainradiox = plt.axes([0.1, 0.02, 0.08, 0.015*len(gtable)])
gainradio = RadioButtons(gainradiox,  sorted(gtable.keys()), active=0)
for circ in gainradio.circles:
    circ.set_radius(0.002*len(gtable))
gainradio.on_clicked(gainSet)

mng = plt.get_current_fig_manager()
# mng.resize(*mng.window.maxsize())
mng.resize(1920,1080)

plt.tight_layout(rect=[0, 0.1, 1, 1])
plt.show()

