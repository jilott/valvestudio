#!/usr/bin/env python
import numpy as np
import scipy
import matcompat
from numpy.fft import fft

def mag2db(x):
    """Convert magnitude to decibels (dB)
    The relationship between magnitude and decibels is:
    .. math::    X_{dB} = 20 * \log_{10}(x)
    """
    return 20. * np.log10(x)

# if available import pylab (from matlibplot)

import matplotlib.pylab as plt

# Intermodulation products
fs = 5e6                                        # sample rate
N = 4096.0                                      # number of samples
M1 = 173.0                                      # tone1 bin
M2 = 211.0                                      # tone2 bin

f1 = np.dot(fs/N, M1)                           # tone1 freq ~211KHz
f2 = np.dot(fs/N, M2)                           # tone2 freq ~258Khz
t = np.arange(0., (N-1.0)+1)/fs                 # time vector
x1 = np.cos(np.dot(np.dot(2.*np.pi, f1), t))    # tone1
x2 = np.cos(np.dot(np.dot(2.*np.pi, f2), t))    # tone2
x = x1+x2

#x = awgn(x, 80.) need to implement this        # add white noise with snr = 80dB

plt.subplot(3, 1, 1)
plt.plot(t, x)                                  # plot two-tone input signal
plt.xlabel('time')
plt.ylabel('amplitude')
plt.ylim(np.array(np.hstack((-5.0, 5.0))))
plt.title('input')

# plot output signal with non-linearities
# amplifier output with 2nd and 3rd order products
y = 2.0*x + 1e-3*(x**2) + 1e-3*(x**3)

plt.subplot(3, 1, 2)
plt.plot(t, y)
plt.xlabel('time')
plt.ylabel('amplitude')
plt.title('output')

yf = fft(y, int(N))                             # output fft
Y = np.abs(yf[0:int(N/2.0+1.0)])                # single-sided
Ydb = mag2db(Y)                                 # convert to db
Ydb = Ydb-np.amax(Ydb)
n = np.arange(1.0,(N/2.0+1.0)+(1.0), 1.0)
plt.subplot(3, 1, 3)

plt.step(n,Ydb)

plt.xlabel('samples')
plt.ylabel('magnitude')
plt.title('Two-tone output FFT with Intermodulation products')


M1 = M1+1.0                                 # moved 1 bin up in fft
M2 = M2+1.0

m1dB = Ydb[int(M1)-1]                       # tone1 mag
m2dB = Ydb[int(M2)-1]                       # tone2 mag
print 'f1 = %e Hz, f1dB = %f dB'%(f1, m1dB)
print 'f2 = %e Hz, f2dB = %f dB\n'%(f2, m2dB)
IM1 = Ydb[int((2.*M1-M2))-1]
IM2 = Ydb[int((2.*M2-M1))-1]
IM3 = (IM1+IM2)/2.
print "IM3 = %f dB\n"% IM3

plt.show()
