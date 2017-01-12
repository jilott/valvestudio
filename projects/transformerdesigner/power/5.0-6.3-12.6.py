#!/usr/bin/env python
import math
import Winding, Transformer

primary   = Winding.Winding('p',115.0,0.0,None)

secondary5   = Winding.Winding('s',5.0 ,2.5,[50])
secondary5b  = Winding.Winding('s',5.0 ,2.5,[50])
secondary6   = Winding.Winding('s',6.3 ,4.0,[50])
secondary6b  = Winding.Winding('s',6.3 ,4.0,[50])
secondary12  = Winding.Winding('s',12.6,3.0,[50])
secondary12b = Winding.Winding('s',12.6,3.0,[50])

t = Transformer.Transformer([primary,secondary6,secondary6b,secondary12,secondary12b,secondary5,secondary5b],160,have=1)
t.circularMilsPerAmp = 800.0
t.coreLoss           = 0.80 # watts/lbs
t.isolationThickness = 0.003
t.wrappingThickness  = 0.015
t.insulationLayers   = 2

t.fluxDensity = t.fluxFind(bmax=103000,inc=100,fillmax=95)
#t.fluxDensity = 90000
t.compute()
t.report()

# t.fluxTable(sort='error')

t.gcode()
