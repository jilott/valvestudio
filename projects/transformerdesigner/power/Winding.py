class Winding():
    def __init__(self,type,voltage,current,taps=None,fill=True):
        self.type           = type
        self.voltage        = voltage
        self.current        = current     
        self.taps           = taps
        self.fillLast       = fill

        self.va             = voltage*current
        self.turns          = 0.0
        self.layers         = 0.0
        self.turnsPerLayer  = 0.0
        self.meanPathLength = 0.0
        self.wireLength     = 0.0        # feet
        self.wireDiameter   = 0.0
        self.layers         = 0.0
        self.resistance     = 0.0
        self.voltageDrop    = 0.0
        self.weight         = 0.0
        self.height         = 0.0
        self.wire           = None
        self.vout           = 0.0
        self.voutRMS        = 0.0
        self.voutNoLoad     = 0.0
        self.voutRegulation = 0.0
