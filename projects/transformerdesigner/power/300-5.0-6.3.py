#!/usr/bin/env python
import math
import Winding, Transformer

primary   = Winding.Winding('p',115.0,0.0)
secondary5 = Winding.Winding('s',5.0,2.0)
secondary6 = Winding.Winding('s',6.3,1.6,taps=[50])
secondary300 = Winding.Winding('s',300.0,0.100,[40,50,60])

t = Transformer.Transformer([secondary5,secondary6,primary,secondary300],50)
t.circularMilsPerAmp = 700.0
t.coreLoss           = 0.66 # watts/lbs
t.efficiency         = 0.90 # 1/1.11 in wolpert p10
t.lineFrequency      = 60.0
t.isolationThickness = 0.005
t.stackingFactor     = 0.92 # stacking factor wolpert p11 0.92 1x1 interleave, 0.95 butt stack
t.lossFactor         = 0.95 # 1/1.05 in wolpert p11
t.wrappingThickness  = 0.015
t.WeightExtra        = 1.15

# t.laminationTable()

t.fluxDensity = t.fluxFind(bmax=90000)
t.compute()
t.report()

#t.fluxTable(sort='error')
t.gcode()
