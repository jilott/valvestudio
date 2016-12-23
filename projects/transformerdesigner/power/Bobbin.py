class Bobbin():
    def __init__(self,length,border,padding):
        self.border = border
        self.padding = padding
        self.length = length
        self.windingLength = self.length - 2*(self.border + self.padding)
        self.stackHeight = 0.0
        self.stack = [] # {type,layers,thickness,description} thickness is per layer
        self.fill = 0.0
