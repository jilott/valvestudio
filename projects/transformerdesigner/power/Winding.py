class Winding():
    def __init__(self,type,voltage,current,taps):
        self.type = type
        self.voltage = voltage
        self.current = current     
        self.taps = taps

        self.va = voltage*current
        self.turns = 0.0
        self.layers = 0.0
        self.meanPathLength=0.00
        self.wireLength=0.00        # feet
        self.wireDiameter = 0.0
        self.layers = 0.0
        self.resistance = 0.0
        self.voltageDrop = 0.0
        self.weight = 0.0
        self.height = 0.0
        self.wire = None
        self.vout=0.00
        self.voutRMS=0.00
        self.voutNoLoad=0.00
        self.voutRegulation=0.00
