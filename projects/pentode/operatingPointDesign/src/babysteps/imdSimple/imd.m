#!/usr/bin/env octave

% Intermodulation products
clc; clear;
pkg load communications;

fs = 5e6; % sample rate
N = 4096; % samples

M1 = 173; % tone1 bin
M2 = 211; % tone2 bin

f1 = fs/N*M1; % tone1 freq ~211KHz
f2 = fs/N*M2; % tone2 freq ~258Khz

t = (0:N-1)/fs; % time vector

x1 = cos(2*pi*f1*t); % tone1
x2 = cos(2*pi*f2*t); % tone2
x = x1 + x2; % input two-tone signal

x = awgn(x,80); % add white noise with snr = 80dB

figure('Position',[0,0,1920,1080]);

subplot(3,1,1);
plot(t,x); % plot two-tone input signal
xlabel('time');
ylabel('amplitude');
ylim([-5 5]);
title('input');
grid on;

% amplifier output with 2nd and 3rd order products
y = 2*x + 1e-3*(x.^2) + 1e-3*(x.^3);

subplot(3,1,2);
plot(t,y); % plot output signal with non-linearities
xlabel('time');
ylabel('amplitude');
title('output');
grid on;

yf = fft(y,N); % output fft
Y = abs(yf(1:N/2+1)); % single-sided
Ydb = mag2db(Y); % convert to db
Ydb = Ydb - max(Ydb);
n = 1:1:N/2+1;

subplot(3,1,3);
stairs(n,Ydb); % plot fft
xlabel('samples');
ylabel('magnitude');
grid on;
title('Two-tome output FFT with Intermodulation products');
set(gca,'xtick',0:100:2048)

M1 = M1 + 1; M2 = M2 + 1; % moved 1 bin up in fft

m1dB = Ydb(M1); % tone1 mag
m2dB = Ydb(M2); % tone2 mag
fprintf('f1 = %e Hz, f1dB = %f dB\n', f1, m1dB);
fprintf('f2 = %e Hz, f2dB = %f dB\n\n', f2, m2dB);

IM1 = Ydb(2*M1-M2);
IM2 = Ydb(2*M2-M1);

IM3 = (IM1+IM2)/2;

fprintf('IM3 = %f dB\n', IM3);
pause();
