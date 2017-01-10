import pprint,math,csv

INCHTOMM=25.4

# references
#    Transformer Desing and Manufacturing Manual - Wolpert
#    Electronic Transformers and Circuits - Lee

class Transformer():
    def compute(self):
        primary = self.primary
        self.va = 0

        for secondary in self.secondaries:
            self.va += secondary.voltage * secondary.current
            
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

        # assuming square core
        crossSectionLength = math.sqrt(self.coreArea) + 2*self.bobbin.border + primary.layers*primary.wireDiameter # its really half the distance but there are 2 sides
        primary.meanPathLength = 4 * crossSectionLength
        primary.wireLength = primary.meanPathLength * primary.turns / 12.0
        primary.resistance = primary.wireLength * (primary.wire['ohmsPer1000ft']/1000.0) 
        primary.voltageDrop = primary.resistance * primary.current
        
        primary.weight = primary.resistance / primary.wire['ohmsPerPound']

        self.weight = primary.weight
        self.loss = primary.voltageDrop*primary.current 

        primary.turnsPerLayer = math.floor(self.bobbin.windingLength/primary.wireDiameter)
    

        for secondary in self.secondaries:
            secondary.wireDiameter = secondary.current * self.circularMilsPerAmp
            for w in self.wires:
                if w['cmArea'] > secondary.wireDiameter:
                    secondary.wire = w
                    secondary.wireDiameter = w['diameter']
                    break

            # this loop scans through secondary turns minimizing vout-voltage, a straight calc of turns isn't very accurate
            tinitial = float(math.floor(primary.turns/primary.voltage * (1/self.lossFactor) * secondary.voltage)) # from wolpert, not very accurate
            errormin = 1000
            for t in range(int(0.75*tinitial),int(1.5*tinitial),1):
                l = math.ceil(t / (self.bobbin.windingLength / secondary.wireDiameter))
                cl = crossSectionLength + 2*self.isolationThickness + secondary.layers*secondary.wireDiameter
                mpl = 4 * cl
                wl = mpl * t / 12.0
                r = wl * (secondary.wire['ohmsPer1000ft']/1000.0)
                vdrop = r * secondary.current
                vout = (primary.voltage - primary.voltageDrop)*t/primary.turns - vdrop
                error = math.fabs(vout - secondary.voltage)
                # print vout
                if error < errormin:
                    terrormin = t
                    errormin = error

            secondary.turns = terrormin
            secondary.layers = math.ceil(secondary.turns / (self.bobbin.windingLength / secondary.wireDiameter))

            crossSectionLength += 2*self.isolationThickness + secondary.layers*secondary.wireDiameter
            secondary.meanPathLength = 4 * crossSectionLength
            secondary.wireLength = secondary.meanPathLength * secondary.turns / 12.0
            secondary.resistance = secondary.wireLength * (secondary.wire['ohmsPer1000ft']/1000.0)
            secondary.voltageDrop = secondary.resistance * secondary.current
            secondary.weight = secondary.resistance / secondary.wire['ohmsPerPound']
            secondary.vout = (primary.voltage - primary.voltageDrop)*secondary.turns/primary.turns - secondary.voltageDrop
            # secondary.voutRMS = secondary.voltage/2.0*0.7071
            secondary.voutNoLoad = primary.voltage*secondary.turns/primary.turns
            secondary.voutRegulation = 100*(secondary.voutNoLoad-secondary.vout)/secondary.vout

            secondary.turnsPerLayer = math.floor(self.bobbin.windingLength/secondary.wireDiameter)

            self.weight += secondary.weight
            self.loss += secondary.voltageDrop*secondary.current 

        self.bobbin.stack = []
        for winding in self.windings:
            if winding.type == 'p':
                desc = "Primary"
            if winding.type == 's':
                desc = "Secondary"
            self.bobbin.stack.append({'type':'wire','height':winding.wireDiameter,'layers':winding.layers,'description':'%s %dAWG'%(desc,winding.wire['size']),'turns':winding.turns,'turnsPerLayer':winding.turnsPerLayer})
            self.bobbin.stack.append({'type':'insulation','height':self.isolationThickness,'layers':self.insulationLayers,'description':'Insulation','turns':1,'turnsPerLayer':1})
        del(self.bobbin.stack[-1])
        self.bobbin.stack.append({'type':'insulation','height':self.wrappingThickness,'layers':self.insulationLayers,'description':'Wrapping','turns':1,'turnsPerLayer':1})

        self.weight += self.lamination['weight']*self.stackingFactor

        self.bobbin.stackHeight = 0.0
        for s in self.bobbin.stack:
            self.bobbin.stackHeight += s['layers']*s['height']
        self.bobbin.fill = self.bobbin.stackHeight / self.lamination['windowHeight'] * 100

        # add in core loss
        self.loss += self.weight * self.coreLoss

        self.temperatureRise = self.loss/(0.1*math.pow((self.weight/1.073),2.0/3.0))

        self.weight = self.weight * self.weightExtra

    def report(self):
        print "Requirements"
        print "  %-20s = %.1f V"%("Primary",self.primary.voltage)
        for secondary in self.secondaries:
            if secondary.taps:
                taps = "CT"
            else:
                taps = ""
            print "  %-20s = %5.1f V @ %5.3f A %s"%("Secondary",secondary.voltage,secondary.current,taps)
        print "  %-20s = %s"%("Size",self.lamination['size'])
        avail = ""
        for w in self.wires:
            avail += "%d "%int(w['size'])
        print "  %-20s = %s"%("AWG Selection",avail)
        print

        print "Transformer"
        print "  %-20s = %.1f VA"%("VA",self.va)
        print "  %-20s = %d lines, %d gauss"%("Flux Density",self.fluxDensity, float(self.fluxDensity) / 6.4516)
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
        print "  %-20s = %.3f in"%("Bobbin Window Length",self.bobbin.windingLength)
        print

        print "Bobbin"
        print "  Winding Stack"
        print "    Description          Layers Turns T/L  Height"
        for s in self.bobbin.stack:
            print "    %-20s %-6d %-5d %-5d %-6.3f"%(s['description'],s['layers'],s['turns'],s['turnsPerLayer'],s['height'])
        print "  %-20s = %0.4f in"%("Stack Height",self.bobbin.stackHeight)
        print "  %-20s = %0.4f in"%("Window Height",self.lamination['windowHeight'])
        print "  %-20s = %0.1f %%"%("Fill",self.bobbin.fill)
        print

        print "Winding Primary"
        print "  %-20s = %.1f V"%("Voltage",self.primary.voltage)
        print "  %-20s = %.3f A"%("Current",self.primary.current)
        print "  %-20s = %d"%("AWG",int(self.primary.wire['size']))
        print "  %-20s = %d"%("Turns",self.primary.turns)
        print "  %-20s = %d"%("Layers",self.primary.layers)
        print "  %-20s = %d"%("Turns/layer",self.primary.turnsPerLayer)
        print "  %-20s = %.1f in"%("Mean Path Length",self.primary.meanPathLength)
        print "  %-20s = %0.1f ft"%("Wire Length",self.primary.wireLength)
        print "  %-20s = %s"%("Wire Diameter",self.primary.wireDiameter)
        print "  %-20s = %0.4f  %0.4fohms/1000ft"%("Resistance",self.primary.resistance,self.primary.wire['ohmsPer1000ft'])
        print "  %-20s = %0.3f V"%("Voltage Drop",self.primary.voltageDrop)
        print

        for secondary in self.secondaries:
            print "Winding Secondary"
            print "  %-20s = %.1f V"%("Voltage",secondary.voltage)
            print "  %-20s = %.3f A"%("Current",secondary.current)
            print "  %-20s = %d"%("AWG",int(secondary.wire['size']))
            print "  %-20s = %d"%("Turns",secondary.turns)
            print "  %-20s = %d"%("Layers",secondary.layers)
            print "  %-20s = %d"%("Turns/layer",secondary.turnsPerLayer)
            print "  %-20s = %.1f in"%("Mean Path Length",secondary.meanPathLength)
            print "  %-20s = %0.1f ft"%("Wire Length",secondary.wireLength)
            print "  %-20s = %s"%("Wire Diameter",secondary.wireDiameter)
            print "  %-20s = %0.4f  %0.4fohms/1000ft"%("Resistance",secondary.resistance,secondary.wire['ohmsPer1000ft'])
            print "  %-20s = %0.4f V"%("Voltage Drop",secondary.voltageDrop)
            print "  %-20s = %.3f V"%("Vout",secondary.vout)
            # print "  %-20s = %.3f V"%("VoutRMS",secondary.voutRMS)
            print "  %-20s = %.3f V"%("VoutNoLoad",secondary.voutNoLoad)
            print "  %-20s = %0.1f %%"%("Regulation",secondary.voutRegulation)
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
    
    def __init__(self,windings,lamva,bobbin,have=1):
        self.windings = windings
        self.secondaries = []
        for winding in windings:
            if winding.type == 'p':
                self.primary = winding
            if winding.type == 's':
                self.secondaries.append(winding)
            
        self.laminationVA = lamva
        self.bobbin = bobbin
        
        self.fluxDensity            = 0.00
        self.circularMilsPerAmp     = 800.0
        self.coreLoss               = 0.66 # watts/lbs
        self.efficiency             = 0.90 # 1/1.11 in wolpert p10
        self.lineFrequency          = 60.0
        self.stackingFactor         = 0.92 # stacking factor wolpert p11 0.92 1x1 interleave, 0.95 butt stack
        self.lossFactor             = 0.95 # 1/1.05 in wolpert p11
        self.isolationThickness     = 0.003
        self.wrappingThickness      = 0.015
        self.weightExtra            = 1.15
        self.insulationLayers       = 3

        self.lamination = None
        self.coreArea=0.00
        self.coreAreaEffective=0.00
        self.temperatureRise=0.00
        self.loss=0.00
        self.weight=0.00
    
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
            self.laminations.append(r)

        for k in self.lamination:
            try:
                self.lamination[k] = float(self.lamination[k])
            except:
                pass
    
    def gcode(self):
        # gcode generation here
        print "(load #%sAWG wire)"%self.NpWire['size']
        print "(set bobbin zero)"
        print "(winding %d turns)"%self.Np
        print "G21 G54 G90 F1000"
        print "M0 (next move is 0,0)"
        print "G0 X0 Y0"

        turns = self.Np
        lturns = math.floor(self.BobbinWindowLength * float(self.NpWire['turnsPerInch']))
        layerHeight = float(self.NpWire['diameter'])
        count = 1
        while turns > lturns:
            if count%2 == 0:
                print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,count*lturns,lturns,count)
            else:
                print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,count*lturns,lturns,count)
            turns -= lturns
            count += 1
        if count%2 == 0:
            print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,(count-1)*lturns+turns,turns,count)
        else:
            print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,(count-1)*lturns+turns,turns,count)

        print
        print "(load #%sAWG wire)"%self.NsWire['size']
        print "(set bobbin zero)"
        print "(winding %d turns)"%self.Ns
        if (self.CenterTapped):
            print "(center tap %d turns)"%(self.Ns/2)
        print "G21 G54 G90 F1000"
        print "M0 (next move is 0,0)"
        print "G0 X0 Y0"

        if self.CenterTapped:
            turns = self.Ns / 2
            lturns = math.floor(self.BobbinWindowLength * float(self.NsWire['turnsPerInch']))
            layerHeight = float(self.NsWire['diameter'])
            count = 1
            while turns > lturns:
                if count%2 == 0:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,count*lturns,lturns,count)
                else:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,count*lturns,lturns,count)
                turns -= lturns
                count += 1
            if count%2 == 0:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,(count-1)*lturns+turns,turns,count)
            else:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,(count-1)*lturns+turns,turns,count)
            
            print "M0 (center tapout)"
            turns = self.Ns / 2
            count = 1
            while turns > lturns:
                if count%2 == 0:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,count*lturns,lturns,count)
                else:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,count*lturns,lturns,count)
                turns -= lturns
                count += 1
            if count%2 == 0:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,(count-1)*lturns+turns,turns,count)
            else:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,(count-1)*lturns+turns,turns,count)
        else:
            turns = self.Ns
            lturns = math.floor(self.BobbinWindowLength * float(self.NsWire['turnsPerInch']))
            layerHeight = float(self.NsWire['diameter'])
            count = 1
            while turns > lturns:
                if count%2 == 0:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,count*lturns,lturns,count)
                else:
                    print "G01 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,count*lturns,lturns,count)
                turns -= lturns
                count += 1
            if count%2 == 0:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(0,(count-1)*lturns+turns,turns,count)
            else:
                print "G00 X%-15.4f Y%-15.4f (%3d turns layer %d)"%(self.BobbinWindowLength*INCHTOMM,(count-1)*lturns+turns,turns,count)

    def fluxTable(self,va,npawg,nsawg):
        # this modifies transformer
        print "Core Size %s"%t.Lamination['size']
        print "  B    Gauss  Np    Ns    Vout     Fill  Loss"
        print "---------------------------------------------------"
        for b in range(70000,110000,1000):
            t.B = b
            t.compute(va=va,npawg=npawg,nsawg=nsawg)
            print "%-6d %-6d %-5d %-5d %-8.2f %-5.1f %-.1f"%(b,b/6.45,t.Np,t.Ns,t.Vout,t.Fill,t.Loss)

    def fluxFind(self,bmin=20000,bmax=104000,inc=500):
        # 1.6T = 103225.6 flux lines
        errormin = 1000.00
        bminimal = 0.0
        for b in range(bmin,bmax,inc): 
            self.fluxDensity = b
            self.compute()
            if self.bobbin.fill > 95.0:
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
         
