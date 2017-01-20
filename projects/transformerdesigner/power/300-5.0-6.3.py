#!/usr/bin/env python
import math, sys
import Winding, Transformer, Machine

primary      = Winding.Winding('p',115.0,0.0)
secondary5   = Winding.Winding('s',  5.0,2.0,fill=False)
secondary6   = Winding.Winding('s',  6.3,1.6,taps=[50])
secondary300 = Winding.Winding('s',300.0,0.100,[20,50,80],False)

t = Transformer.Transformer([secondary5,secondary6,primary,secondary300],50)
t.circularMilsPerAmp = 700.0

t.fluxDensity = t.fluxFind(bmax=90000)
t.compute()
t.report()

#t.fluxTable(sort='error')

t.route()
t.gcode()

if len(sys.argv) > 1:
    m = Machine.Machine(windings=t.windings)
    m.run()
    m.shutdown()
