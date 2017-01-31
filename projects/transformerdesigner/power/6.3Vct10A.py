#!/usr/bin/env python
import math
import Winding, Transformer, Machine

primary     = Winding.Winding('p',115.0,0.0,None)
secondary   = Winding.Winding('s',6.3 ,10.0,[50],False)

t = Transformer.Transformer([primary,secondary],65,have=0)
t.circularMilsPerAmp = 800.0
t.coreLoss           = 0.80 # watts/lbs
t.isolationThickness = 0.003
t.wrappingThickness  = 0.015
t.insulationLayers   = 2

t.fluxDensity = t.fluxFind(bmax=103000,inc=100,fillmax=95)
#t.fluxDensity = 95000
t.compute()
t.report()

#t.fluxTable(sort='error')
t.fluxTable()

#t.gcode()

