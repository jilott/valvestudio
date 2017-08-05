#!/usr/bin/env python
import math
import Winding, Transformer, Machine

primary      = Winding.Winding('p',120.0,0.0,None)

secondary5   = Winding.Winding('s',4.95 ,3.0,[50],fill=False)
secondary5b   = Winding.Winding('s',4.95 ,3.0,[50],fill=False)

t = Transformer.Transformer([primary,secondary5,secondary5b],55)
t.circularMilsPerAmp = 800.0
t.coreLoss           = 0.80 # watts/lbs
t.isolationThickness = 0.003
t.wrappingThickness  = 0.015
t.insulationLayers   = 2

t.fluxDensity = t.fluxFind(bmax=103000,inc=100,fillmax=95)
#t.fluxDensity = 90000
t.compute()
t.report()



#t.fluxTable(sort='error')

#t.gcode()

#m = Machine.Machine(windings=t.windings)
# m.run()
