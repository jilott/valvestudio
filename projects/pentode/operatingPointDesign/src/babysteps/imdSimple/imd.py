#!/usr/bin/env python
import numpy as np
import scipy
import matcompat
from numpy.fft import fft

np.set_printoptions(precision=4,suppress=True)

def mag2db(x):
    """Convert magnitude to decibels (dB)
    The relationship between magnitude and decibels is:
    .. math::    X_{dB} = 20 * \log_{10}(x)
    """
    return 20. * np.log10(x)

# if available import pylab (from matlibplot)

import matplotlib.pylab as plt
plt.rcParams["figure.figsize"] = 15,9


# Intermodulation products
fs = 5e6                                        # sample rate
N = 4096.0                                      # number of samples
M1 = 180.0                                      # tone1 bin
M2 = 220.0                                      # tone2 bin

f1 = np.dot(fs/N, M1)                           # tone1 freq ~211KHz
f2 = np.dot(fs/N, M2)                           # tone2 freq ~258Khz
t = np.arange(0., (N-1.0)+1)/fs                 # time vector
x1 = np.cos(np.dot(np.dot(2.*np.pi, f1), t))    # tone1
x2 = np.cos(np.dot(np.dot(2.*np.pi, f2), t))    # tone2
x = x1 + x2

x = np.random.normal(x, 0.0001)                 # add white noise with snr = 80dB


plt.subplot(3, 1, 1)
plt.plot(t, x)                                  # plot two-tone input signal
plt.xlabel('time')
plt.ylabel('amplitude')
plt.ylim(np.array(np.hstack((-5.0, 5.0))))
plt.title('input - linear')

# plot output signal with non-linearities
# amplifier output with 2nd and 3rd order products
y = 2.0*x + 5e-3*(x**2) + 1e-3*(x**3)

plt.subplot(3, 1, 2)
plt.plot(t, y)
plt.xlabel('time')
plt.ylabel('amplitude')
plt.title('output non-linear')

yf = fft(y, int(N))                             # output fft
Y = np.abs(yf[0:int(N/2.0+1.0)])                # single-sided
Ydb = mag2db(Y)                                 # convert to db
Ydb = Ydb-np.amax(Ydb)
n = np.arange(1.0,(N/2.0+1.0)+(1.0), 1.0)
plt.subplot(3, 1, 3)

indices = Ydb[0:1000] > -90
peakf = n[indices]
peaka = Ydb[indices]


plt.step(n[0:1000],Ydb[0:1000])
plt.xlabel('KHz')
yr = range(40,-121,-20)
#yr.insert(0,10)
plt.yticks(yr)
plt.xticks(range(0,1000,50))
plt.ylabel('magnitude')
plt.title('Two-tone output FFT with Intermodulation products')
plt.grid(True)

for i in range(len(peakf)):
    plt.annotate("%.0f\n%.1f"%(peakf[i],peaka[i]),
        xy=(peakf[i],peaka[i]),
        xycoords='data',
        xytext=(-15,5),
        textcoords='offset points',
        size=12)
        


M1 = M1+1.0                                 # moved 1 bin up in fft
M2 = M2+1.0

m1dB = Ydb[int(M1)-1]                       # tone1 mag
m2dB = Ydb[int(M2)-1]                       # tone2 mag
print 'f1 = %10.1f Hz, f1dB = %f dB'%(f1, m1dB)
print 'f2 = %10.1f Hz, f2dB = %f dB\n'%(f2, m2dB)
IM1 = Ydb[int((2.0*M1-M2))-1]
IM2 = Ydb[int((2.0*M2-M1))-1]
IM3 = (IM1+IM2)/2.
print "IM3 = %f dB\n"% IM3

plt.tight_layout()
plt.show()

#       bbox=dict(boxstyle="round", fc="1.0"),
