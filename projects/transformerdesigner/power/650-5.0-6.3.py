#!/usr/bin/env python
import math
import Winding, Transformer

# maybe like http://www.hammondmfg.com/pdf/EDB290AX.pdf

primary   = Winding.Winding('p',120.0,0.0)
secondary5 = Winding.Winding('s',5.0,2.0)
secondary6 = Winding.Winding('s',6.3,2.0,taps=[50])
secondary300 = Winding.Winding('s',650.0,0.081,[50])

t = Transformer.Transformer([secondary5,secondary6,primary,secondary300],90,have=1)
t.circularMilsPerAmp = 600.0
t.coreLoss           = 0.66 # watts/lbs
t.efficiency         = 0.90 # 1/1.11 in wolpert p10
t.lineFrequency      = 60.0
t.isolationThickness = 0.005
t.stackingFactor     = 0.92 # stacking factor wolpert p11 0.92 1x1 interleave, 0.95 butt stack
t.lossFactor         = 0.95 # 1/1.05 in wolpert p11
t.wrappingThickness  = 0.015
t.WeightExtra        = 1.15

# t.laminationTable()

t.fluxDensity = t.fluxFind(bmax=100000,inc=500)
# t.fluxDensity = 70000
t.compute()
t.report()

t.fluxTable(sort='error')
