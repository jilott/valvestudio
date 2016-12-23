#!/usr/bin/env python
import math
import Winding, Bobbin, Transformer

bobbin = Bobbin.Bobbin(1.47,0.05,0.02)
primary   = Winding.Winding('p',115.0,0.0,None)
secondary6 = Winding.Winding('s',6.3,2.0,[50])
secondary200 = Winding.Winding('s',200.0,0.02,None)
secondary300 = Winding.Winding('s',300.0,0.100,[50])

t = Transformer.Transformer([secondary6,primary,secondary300,secondary200],50,bobbin)
t.circularMilsPerAmp = 800.0
t.coreLoss           = 0.66 # watts/lbs
t.efficiency         = 0.90 # 1/1.11 in wolpert p10
t.lineFrequency      = 60.0
t.isolationThickness = 0.005
t.stackingFactor     = 0.92 # stacking factor wolpert p11 0.92 1x1 interleave, 0.95 butt stack
t.lossFactor         = 0.95 # 1/1.05 in wolpert p11
t.wrappingThickness  = 0.015
t.WeightExtra        = 1.15

# t.laminationTable()

t.fluxDensity = t.fluxFind()
t.compute()
t.report()

