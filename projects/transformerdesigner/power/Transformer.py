import pprint,math,csv,os
import operator
import __main__

INCHTOMM=25.4
BOBBINMARGIN=0.02    # estimate by looking at edcor bobbin lengths/2
BOBBINTHICKNESS=0.04 # majority of edcor bobbins are 0.04 thick
BOBBINPADDING=0.02   # a little play

# winding length
# windowlength = margin + thickness + padding + windinglength + padding + thickness + margin 

import Bobbin

# references
#    Transformer Desing and Manufacturing Manual - Wolpert
#    Electronic Transformers and Circuits - Lee

class Transformer():
    def compute(self):
        primary = self.primary
        self.va = 0

        for secondary in self.secondaries:
            self.va += secondary.voltage * secondary.current


        # find initial layer turns and wire diameter, then iterate from there, no voltage drops considered yet

        primary.current = self.va * (1/self.efficiency) / primary.voltage
        self.coreArea = self.lamination['area']
        self.coreAreaEffective = self.coreArea * self.stackingFactor
        primary.turns = float(math.floor((primary.voltage * 10**8)/(4.44 * self.fluxDensity * self.coreAreaEffective * self.lineFrequency)))
        primary.wireDiameter = primary.current * self.circularMilsPerAmp
        # scan for larger diameter
        for w in self.wires:
            if w['cmArea'] > primary.wireDiameter:
                primary.wire = w
                primary.wireDiameter = w['diameter']
                break
        primary.layers = math.ceil(primary.turns / (self.bobbin.windingLength / primary.wireDiameter))

        for secondary in self.secondaries:
            secondary.wireDiameter = secondary.current * self.circularMilsPerAmp
            for w in self.wires:
                if w['cmArea'] > secondary.wireDiameter:
                    secondary.wire = w
                    secondary.wireDiameter = w['diameter']
                    break
            secondary.turns = float(math.floor(primary.turns/primary.voltage * (1/self.lossFactor) * secondary.voltage)) # from wolpert, not very accurate
            secondary.layers = math.ceil(secondary.turns / (self.bobbin.windingLength / secondary.wireDiameter))

            
        # with initial turns and layers, we can calculate winding MPL, resistance, vdrop etc
        # doing this twice, first time through primary vdrop = 0 because didn't know MPL
        for i in range(4):
            # now calculate meanPathLength
            # height and length here are from core center to where we are
            height = self.lamination['stackHeight']/2.00 + self.bobbin.border   # at the surface of the bobbin
            length = (self.lamination['area']/self.lamination['stackHeight'])/2.0 + self.bobbin.border
            # print height,length
            for winding in self.windings:
                height += (winding.layers * winding.wireDiameter) / 2.0 # this puts in the center of the winding
                length += (winding.layers * winding.wireDiameter) / 2.0
                winding.meanPathLength = 4 * (height + length)

                if winding.type == 's':
                    tinitial = float(math.floor(primary.turns/primary.voltage * (1/self.lossFactor) * winding.voltage)) # from wolpert, not very accurate
                    # so we're going to loop through turns and find the best one, based on resistance at this MPL
                    errormin = 1000
                    for t in range(int(0.75*tinitial),int(1.5*tinitial),1):
                        winding.wireLength = winding.meanPathLength * t
                        winding.resistance = winding.wireLength * (winding.wire['ohmsPer1000Inches']/1000.0)
                        winding.voltageDrop = winding.resistance * winding.current
                        winding.vout = (primary.voltage - primary.voltageDrop)*t/primary.turns - winding.voltageDrop
                        error = math.fabs(winding.vout - winding.voltage)
                        if error < errormin:
                            terrormin = t
                            errormin = error
                    winding.turns = terrormin

                # now have winding.turns with minimal error

                winding.wireLength = winding.meanPathLength * winding.turns
                winding.resistance = winding.wireLength * (winding.wire['ohmsPer1000Inches']/1000.0)
                winding.voltageDrop = winding.resistance * winding.current
                if winding.type == 's':
                    winding.vout = (primary.voltage - primary.voltageDrop)*winding.turns/primary.turns - winding.voltageDrop
                    winding.voutNoLoad = primary.voltage*winding.turns/primary.turns
                    winding.voutRegulation = 100*(winding.voutNoLoad-winding.vout)/winding.vout
                winding.layers = math.ceil(winding.turns / (self.bobbin.windingLength / winding.wireDiameter))


                height += (winding.layers * winding.wireDiameter) / 2.0 # the other half so to speak
                length += (winding.layers * winding.wireDiameter) / 2.0
                height += self.isolationThickness
                length += self.isolationThickness
                winding.turnsPerLayer = math.floor(self.bobbin.windingLength/winding.wireDiameter)
                winding.weight = winding.resistance / winding.wire['ohmsPerPound']

        self.weight = 0
        for winding in self.windings:
            self.weight += winding.weight
            self.loss = winding.voltageDrop*winding.current 

        self.bobbin.stack = []
        self.bobbin.stack.append({'type':'insulation','height':BOBBINTHICKNESS,'layers':1,'description':'Bobbin Base','turns':1,'turnsPerLayer':1})
        for winding in self.windings:
            self.bobbin.stack.append({'type':'wire','height':winding.wireDiameter,'layers':winding.layers,'description':'%s %dAWG'%(winding.typeText,winding.wire['size']),'turns':winding.turns,'turnsPerLayer':winding.turnsPerLayer})
            self.bobbin.stack.append({'type':'insulation','height':self.isolationThickness,'layers':self.insulationLayers,'description':'Insulation','turns':1,'turnsPerLayer':1})
        del(self.bobbin.stack[-1])
        self.bobbin.stack.append({'type':'insulation','height':self.wrappingThickness,'layers':self.insulationLayers,'description':'Wrapping','turns':1,'turnsPerLayer':1})

        self.weight += self.lamination['weight']*self.stackingFactor

        self.bobbin.stackHeight = 0.0
        for s in self.bobbin.stack:
            self.bobbin.stackHeight += s['layers']*s['height']
        self.bobbin.fill = self.bobbin.stackHeight / self.lamination['windowHeight'] * 100

        # add in core loss and other stuff
        self.loss += self.weight * self.coreLoss
        self.temperatureRise = self.loss/(0.1*math.pow((self.weight/1.073),2.0/3.0))
        self.weight = self.weight * self.weightExtra

    def report(self):
        print "Requirements"
        print "  %-20s = %.1f V"%("Primary",self.primary.voltage)
        for secondary in self.secondaries:
            if secondary.taps:
                taps = "Taps "+','.join(str(x) for x in secondary.taps)
            else:
                taps = ""
            print "  %-20s = %5.1f V @ %5.3f A %s"%("Secondary",secondary.voltage,secondary.current,taps)
        print "  %-20s = %s"%("Size",self.lamination['size'])
        avail = ""
        for w in self.wires:
            avail += "%d "%int(w['size'])
        print "  %-20s = %s"%("AWG Selection",avail)
        print "  %-20s = %.1f VA"%("VA Selection",self.laminationVA)
        print

        print "Transformer"
        print "  %-20s = %.1f VA"%("VA Computed",self.va)
        print "  %-20s = %d lines, %d gauss"%("Flux Density",self.fluxDensity, float(self.fluxDensity) / 6.4516)
        print "  %-20s = %d"%("Circular Mils/Amp",self.circularMilsPerAmp)
        print "  %-20s = %.1flbs"%("Weight",self.weight)
        print "  %-20s = %.1fW"%("Loss",self.loss)
        print "  %-20s = %dC"%("Temp Rise",self.temperatureRise)
        print

        print "Lamination"
        print "  %-20s = %s"%("Size",self.lamination['size'])
        print "  %-20s = %s"%("Stack Height",self.lamination['stackHeight'])
        print "  %-20s = %.3f"%("Stacking Factor",self.stackingFactor)
        print "  %-20s = %.3f in*in"%("Core Area",self.coreArea)
        print "  %-20s = %.3f in*in"%("Core Area Effective",self.coreAreaEffective)
        print "  %-20s = %s"%("Window Height",self.lamination['windowHeight'])
        print "  %-20s = %s"%("Window Length",self.lamination['windowLength'])
        print


        print "Windings"
        wdata = []
        wdata.append("  Type                  ")
        wdata.append("  Voltage V             ")
        wdata.append("  Current A             ")
        wdata.append("  Turns                 ")
        wdata.append("  Layers                ")
        wdata.append("  Turns/layer           ")
        wdata.append("  AWG                   ")
        wdata.append("  Wire Diameter         ")
        wdata.append("  Ohms/1000 feet        ")
        wdata.append("  Mean Path Length inch ")
        wdata.append("  Wire Length feet      ")
        wdata.append("  Resistance            ")
        wdata.append("  Voltage Drop          ")
        wdata.append("  Voltage Out           ")
        wdata.append("  Voltage No Load       ")
        wdata.append("  Voltage Regulation    ")

        for winding in self.windings:
            wdata[0] += "%-12s"%winding.typeText
            wdata[1] += "%-12.1f"%winding.voltage
            wdata[2] += "%-12.1f"%winding.current
            wdata[3] += "%-12d"%winding.turns
            wdata[4] += "%-12d"%winding.layers
            wdata[5] += "%-12d"%winding.turnsPerLayer
            wdata[6] += "%-12d"%winding.wire['size']
            wdata[7] += "%-12s"%winding.wireDiameter
            wdata[8] += "%-12.4f"%winding.wire['ohmsPer1000ft']
            wdata[9] += "%-12.2f"%winding.meanPathLength
            wdata[10] += "%-12.1f"%(winding.wireLength/12.0)
            wdata[11] += "%-12.4f"%winding.resistance
            wdata[12] += "%-12.3f"%winding.voltageDrop
            if winding.type == 's':
                wdata[13] += "%-12.2f"%winding.vout
                wdata[14] += "%-12.2f"%winding.voutNoLoad
                wdata[15] += "%-12.2f"%winding.voutRegulation
            else:
                wdata[13] += "            "
                wdata[14] += "            "
                wdata[15] += "            "


        print "\n".join(wdata)
        print

        print "Bobbin"
        print "  %-20s = %.3f in"%("Winding Length",self.bobbin.windingLength)
        print "  Winding Stack"
        print "    Description          Layers Turns T/L   Height LHeight"
        for s in self.bobbin.stack:
            per = int(100*s['turns']/s['turnsPerLayer'])
            if per < 100:
                extra = str(per)+"% layer filled"
            else:
                extra = ""
            print "    %-20s %-6d %-5d %-5d %-6.3f %-6.3f %s"%(s['description'],s['layers'],s['turns'],s['turnsPerLayer'],s['layers']*s['height'],s['height'],extra)
        print "  %-20s = %0.2f in"%("Stack Height",self.bobbin.stackHeight)
        print "  %-20s = %0.2f in"%("Window Height",self.lamination['windowHeight'])
        if self.bobbin.fill > 93.0:
            note = "<<<<<<<<<<<<<<<<<<<<<< 93% or greater, increase lamination VA"
        else:
            note = ""
        print "  %-20s = %0.1f %% %s"%("Fill",self.bobbin.fill,note)
        print
        
    def wireTable(self):
        l = "Wire Table\nsize diameter turns/\" cmArea  ohms/1000ft ohms/lb   amps\n"
        for w in self.wires:
            w['turnsPerInch'] = 1.00/w['diameter']
            l += "%-5d"%w['size']
            l += "%-9.5f"%w['diameter']
            l += "%-8d"%w['turnsPerInch']
            l += "%-8.1f"%w['cmArea']
            l += "%-12.3f"%w['ohmsPer1000ft']
            l += "%-10s"%w['ohmsPerPound']
            l += "%-.3f"%(w['cmArea']/self.circularMilsPerAmp)
            l += "\n"
        print l
        
    def laminationTable(self):    
        rv = "Lam Table\nsize      stackH VA   Area   windH   windL   wind            weight\n"
        for l in self.laminations:
            rv += "%-10s"%l['size']
            rv += "%-7s"%l['stackHeight']
            rv += "%-5s"%l['VA']
            rv += "%-7s"%l['area']
            rv += "%-8s"%l['windowHeight']
            rv += "%-8s"%l['windowLength']
            rv += "%-16s"%l['window']
            rv += "%-8s"%l['weight']
            rv += "\n"
        print rv
        
    def __repr__(self):
        from pprint import pformat
        return pformat(vars(self), indent=2, width=1)
    
    def __init__(self,windings,lamva,have=1):
        self.windings = windings
        self.secondaries = []
        for winding in windings:
            if winding.type == 'p':
                winding.typeText = 'Primary'
                self.primary = winding
            if winding.type == 's':
                winding.typeText = 'Secondary'
                self.secondaries.append(winding)
            
        # change these for your designs
        self.laminationVA           = lamva
        self.fluxDensity            = 0.00
        self.circularMilsPerAmp     = 800.0
        self.coreLoss               = 0.66 # watts/lbs
        self.efficiency             = 0.90 # 1/1.11 in wolpert p10
        self.lineFrequency          = 60.0
        self.stackingFactor         = 0.92 # stacking factor wolpert p11 0.92 1x1 interleave, 0.95 butt stack
        self.lossFactor             = 0.95 # 1/1.05 in wolpert p11
        self.isolationThickness     = 0.003
        self.wrappingThickness      = 0.015
        self.weightExtra            = 1.15 # percentage of extra stuff like bells, brackets, screws
        self.insulationLayers       = 3
        self.tapeSetback            = 10

        # these are computed
        self.lamination             = None
        self.coreArea               = 0.00
        self.coreAreaEffective      = 0.00
        self.temperatureRise        = 0.00
        self.loss                   = 0.00
        self.weight                 = 0.00

        self.routed                 = False
    
        self.wires = []
        f = open('wire table.csv','rb')
        reader = csv.DictReader(f)
        for r in reader:
            if have == 1:
                if r['Have'][0] == "0":
                    continue
            for k in r:
                try:
                    r[k] = float(r[k])
                except:
                    pass
            self.wires.append(r)

        self.laminations = []
        f = open('lamination table.csv','rb')
        reader = csv.DictReader(f)
        for r in reader:
            if r['VA'] == str(lamva):
                self.lamination = r
                self.bobbin = Bobbin.Bobbin(float(r['windowLength'])-(2.0*BOBBINMARGIN),BOBBINTHICKNESS,BOBBINPADDING)
            self.laminations.append(r)

        for k in self.lamination:
            try:
                self.lamination[k] = float(self.lamination[k])
            except:
                pass
    
    def route(self):
        for winding in self.windings:
            winding.route = []

            for i in range(1,int(winding.layers+1)):
                if i % 2 == 0:
                    direction = 0.0
                    label = 'left'
                else:
                    direction = 1
                    label = 'right'
                if i == winding.layers:
                    winding.route.append((direction*self.bobbin.windingLength,float(winding.turns),label))
                else:
                    winding.route.append((direction*self.bobbin.windingLength,float(i*winding.turnsPerLayer),label))

            if winding.taps:
                for i in range(len(winding.taps)):
                    tapturn = float(winding.taps[i])*float(winding.turns)/100.0
                    for i in range(len(winding.route)):
                        if winding.route[i-1][1] < tapturn and winding.route[i][1] > tapturn:
                            m = (winding.route[i][0]-winding.route[i-1][0])/(winding.route[i][1] - winding.route[i-1][1])
                            if i % 2 == 0:
                                winding.route.insert(i,(self.bobbin.windingLength + m*(tapturn-winding.route[i-1][1]),tapturn,'tap'))
                                winding.route.insert(i,(self.bobbin.windingLength + m*(tapturn-self.tapeSetback-winding.route[i-1][1]),tapturn-self.tapeSetback,'tape'))
                            else:
                                winding.route.insert(i,(m*(tapturn-winding.route[i-1][1]),tapturn,'tap'))
                                winding.route.insert(i,(m*(tapturn-self.tapeSetback-winding.route[i-1][1]),tapturn-self.tapeSetback,'tape'))
        self.routed = True

    def gcode(self): 
        nc = ""
        nc += "(-----------------------------------------------------------)\n"
        nc += "(-- design %-46s --)\n"%os.path.basename(__main__.__file__).replace(".py","")
        nc += "(-----------------------------------------------------------)\n"
        nc += "\n"
        nc += "(-- Requirements -------------------------------------------)\n"
        nc += "(  %-20s = %.1f V                           )\n"%("Primary",self.primary.voltage)
        for secondary in self.secondaries:
            if secondary.taps:
                taps = "Taps "+','.join(str(x) for x in secondary.taps)
            else:
                taps = ""
            nc += "(  %-20s = %5.1f V @ %5.3f A %-15s )\n"%("Secondary",secondary.voltage,secondary.current,taps)
        nc += "(  %-20s = %-15s                   )\n"%("Size",self.lamination['size'])
        avail = ""
        for w in self.wires:
            avail += "%d "%int(w['size'])
        nc += "(  %-20s = %-20s )\n"%("AWG Selection",avail)
        nc += "(  %-20s = %.1f VA                           )\n"%("VA Selection",self.laminationVA)

        nc += "\n"
        nc += "(-- setup -------------------------------------)\n"
        nc += "( inches, work offset 54, absolute             )\n"
        nc += "G20 G54 G90\n"
        nc += "G1 F125\n"
        nc += "\n"
        for winding in self.windings:
            if self.routed == False:
                self.route()
            nc += "(-- winding - %6.1fV %-10s --------------)\n"%(winding.voltage,winding.typeText)
            nc += "( load #%2d AWG wire                            )\n"%winding.wire['size']
            nc += "( winding %4d turns                           )\n"%winding.turns
            nc += "( move to 0.0                                  )\n"
            nc += "( wind leadin                                  )\n"
            nc += "M0\n"
            for r in winding.route:
                nc += "X%-10.4f Y%-10.4f     ( %-16s )\n"%r
                if r[2] == 'tape' or r[2] == 'tap':
                    nc += "M0                          ( %-16s )\n"%r[2]
            nc += "\n"

        fn = os.path.basename(__main__.__file__).replace(".py",".nc")
        open(fn,"w").write(nc)
        print nc
        return nc

    def fluxTable(self,sort=None,min=50000,max=103000):
        # this modifies transformer
        print 
        print "Core Size %s"%self.lamination['size']
        print "FluxDen  Gauss  Fill  Loss    ",
        for secondary in self.secondaries: 
            print "%-8.2f     "%secondary.voltage,
        print "   Error"
        print "-----------------------------------------------------------------------------------------"

        fluxorder = {}
        for b in range(min,max,1000):
            fluxorder[b] = 0

        if sort=='error':
            for b in fluxorder.keys():
                self.fluxDensity = b
                self.compute()
                error = 0.0
                for secondary in self.secondaries: 
                    error += 100.0*(math.fabs((secondary.voltage - secondary.vout)/secondary.vout) + math.fabs((secondary.voutNoLoad - secondary.vout)/secondary.vout))
                error = error / len(self.secondaries)
                fluxorder[b] = error
            fluxorder = sorted(fluxorder.items(), key=operator.itemgetter(1))
        else:
            fluxorder = sorted(fluxorder.items(), key=operator.itemgetter(0))

        for b,e in fluxorder:
            self.fluxDensity = b
            self.compute()
            error = 0.0
            print "%-6d   %-6d %-5d %-4.1f    "%(b,b/6.45,self.bobbin.fill,self.loss),
            for secondary in self.secondaries: 
                error += 100.0*(math.fabs((secondary.voltage - secondary.vout)/secondary.vout) + math.fabs((secondary.voutNoLoad - secondary.vout)/secondary.vout))
                print "%-6.2f %-6.2f"%(secondary.vout,secondary.voutNoLoad),
            error = error / len(self.secondaries)
            print "   %-.2f"%error

    def fluxFind(self,bmin=20000,bmax=103000,inc=1000,fillmax=150):
        # 1.6T = 103225.6 flux lines
        errormin = 1000.00
        bminimal = 0.0
        for b in range(bmin,bmax,inc): 
            self.fluxDensity = b
            self.compute()
            if self.bobbin.fill > fillmax:
                continue
            error = 0.0
            for secondary in self.secondaries: 
                error += math.fabs((secondary.voltage - secondary.vout)/secondary.vout) + math.fabs((secondary.voutNoLoad - secondary.vout)/secondary.vout)
            if error < errormin:
                bminimal = b
                errormin = error
            # print b,error
        self.fluxDensity = bminimal
        self.compute()
        return bminimal
         
