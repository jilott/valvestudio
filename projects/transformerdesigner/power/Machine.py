#!/usr/bin/env python

# grbl v1.1 docs
#   https://github.com/gnea/grbl/blob/master/doc/markdown

# G10 P0 L20 X0
# G10 P0 L20 Y0

X=0
TURNS=1
LABEL=2
BUFFERTHRES=13

import time,sys,os,csv

try:
    import serial
except ImportError:
    pass

try:
    import termios
except ImportError:
    pass

class Machine():
    def windingWind(self,which):
        self.windingDisplayRoute(which)
        self.windingWhich = which
        route = self.windings[which].route
        self.wire = self.windings[which].wire

        self.screenPos(1,5)
        self.screenClear('eol')
        sys.stdout.write("position for wind, zero grbl, zero counter, wind lead-in. 'y' when ready ")
        sys.stdout.flush()

        while self.running:
            self.loop()
            time.sleep(0.001)
            c = self.getchar()
            if len(c):
                if c == 'y':
                    self.screenPos(1,5)
                    self.screenClear('eol')
                    break
                self.processChar(c)

        if c == 'y':
            self.windingNextUpdate = 0
            self._port.write('\x90') # put feed rate back to 100%
            i = 0

            windingState = "windingLoop"
            windingNextLeg = 0
            debugTimeout = 0

            while True:
                now = time.time()

                self.loop()
                c = self.getchar()
                if c == chr(27):
                    windingState = "waitingForIdle"
                if len(c):
                    self.processChar(c)
                    if c == 'w':
                        self.windingDisplayRoute(which)

                    if not self.running:
                        self.statusTimeout = 0
                        self.screenClear()
                        windingState = "waitingForIdle"

                if self.debug:
                    if now > debugTimeout:
                        self.screenPos(1,32)
                        self.screenClear('eol')
                        print windingState, self.status['bufferIndex'],now
                        debugTimeout = now + 1.0

                # running the winding statemap here

                if windingState == "windingLoop":
                    if now > windingNextLeg:
                        if self.status['bufferIndex'] > BUFFERTHRES:
                            leg = route[i]
                            self.command("X%-10.4fY%-10.4f"%(leg[X],leg[TURNS])) 

                            if self.debug:
                                self.screenPos(1,36)
                                self.screenClear('eol')
                                print leg

                            if leg[LABEL].count('tap'): # could be tap or tape
                                self.command("M0") 
                                windingState = "waitingForHold"
                            i += 1
                            if i == len(route):
                                windingState = "waitingForIdle"
                        windingNextLeg = now + 2.0

                if windingState == "waitingForHold":
                    if self.status['state'] == "Hold:0":
                        windingState = "waitingForIdleToContinue"
                        continue

                if windingState == "waitingForIdleToContinue":
                    if self.status['state'] == "Idle":
                        windingNextLeg = now + 1.0
                        windingState = "windingLoop"
                        continue

                if windingState == "waitingForIdle":
                    if self.status['state'] == "Idle":
                        break

                self.windingUpdate()

            self.screenPos(1,7+len(route))
            sys.stdout.write("-")
            

    def windingUpdate(self):
        if time.time() > self.windingNextUpdate:
            self.windingNextUpdate = time.time() + 1.0
            route = self.windings[self.windingWhich].route

            i = 0
            for leg in route:
                self.screenPos(1,8+i)
                sys.stdout.write("-")
                sys.stdout.flush()
                if  leg[TURNS] > (self.status['turns']-1):
                    self.screenPos(1,8+i)
                    if leg[LABEL].count('left'):
                        sys.stdout.write("<")
                        self.direction = -1
                    if leg[LABEL].count('right'):
                        sys.stdout.write(">")
                        self.direction = 1
                    sys.stdout.flush()
                    return
                i += 1

    def __init__(self,port='/dev/ttyUSB0',windings=None):
        self._port = serial.Serial(port,115200,timeout=0)
        self.windings = windings
        self.statusTimeout = time.time() + 5.0
        self.modalTimeout = time.time() + 5.0
        self.buffer = ""
        self.keybuffer = ""
        self.status = {'lastPn':"",'Pn':""}
        self.running = True
        self.wire = None
        self.debug=False
        self.direction = 1
        self.leadin = True
        self.windingNextUpdate = 0

        self.fd = sys.stdin.fileno()
        self.old = termios.tcgetattr(self.fd)
        new = termios.tcgetattr(self.fd)
        new[3] = (new[3] & ~termios.ICANON) & ~termios.ECHO
        new[6][termios.VMIN] = 0
        new[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, new)
        termios.tcsendbreak(self.fd,0)

        self.wires = []
        f = open('wire table.csv','rb')
        reader = csv.DictReader(f)
        for r in reader:
            for k in r:
                try:
                    r[k] = float(r[k])
                except:
                    pass
            self.wires.append(r)
            if int(r['size']) == 22:
                self.wire = r

        self.windingSetup()

    def windingSetup(self):
        if self.windings:
            wdata = []
            wdata.append("  Type                  ")
            wdata.append("  Voltage V             ")
            wdata.append("  Current A             ")
            wdata.append("  Turns                 ")
            wdata.append("  Layers                ")
            wdata.append("  Turns/layer           ")
            wdata.append("  AWG                   ")
            wdata.append("  Wire Diameter         ")
            wdata.append("  Taps                  ")
            wdata.append("  Fill Last Layer       ")
            for winding in self.windings:
                wdata[0] += "%-12s"%winding.typeText
                wdata[1] += "%-12.1f"%winding.voltage
                wdata[2] += "%-12.1f"%winding.current
                wdata[3] += "%-12d"%winding.turns
                wdata[4] += "%-12d"%winding.layers
                wdata[5] += "%-12d"%winding.turnsPerLayer
                wdata[6] += "%-12d"%winding.wire['size']
                wdata[7] += "%-12s"%winding.wireDiameter
                wdata[8] += "%-12s"%winding.taps
                wdata[9] += "%-12s"%winding.fillLast

            self.windingInfo = "\n".join(wdata)
        else:
            self.windingInfo = ""

    def windingDisplay(self):
        self.screenPos(1,7)
        self.screenClear("eos")
        if self.windings == None:
            return
        print "Windings               ",
        for i in range(len(self.windings)):
            print "%-11d"%i,
        print
        print self.windingInfo

    def windingWindStart(self):
        number = ""
        self.screenPos(1,5)
        self.screenClear('eol')
        sys.stdout.write("wind? "+number)
        sys.stdout.flush()
        while True:
            c = self.getchar()
            if len(c):
                if ord(c[0]) == 10:
                    which = int(number)
                    self.windingWind(which)
                    '''
                    try:
                        which = int(number)
                        self.windingWind(which)
                    except:
                        self.screenClear()
                        self.statusTimeout = 0.0
                        self.modalTimeout = 0.0
                    '''
                    return
                else:
                    number += c
                self.screenPos(1,5)
                self.screenClear('eol')
                sys.stdout.write("wind? "+number)
                sys.stdout.flush()

    def windingDisplayRoute(self,which):
        self.screenPos(1,7)
        self.screenClear("eos")
        winding = self.windings[which]
        if winding.taps:
            t = len(winding.taps)
        else:
            t = 0
        print "Route Winding %d, Type %s, AWG %d, Turns %d, Layers %d, Taps %d"%(which,winding.typeText,winding.wire['size'],winding.turns,winding.layers,t)
        for r in self.windings[which].route:
            print "  P %-10.4f T %-10.4f     ( %-16s )"%r


    def help(self):
        self.screenPos(1,7)
        self.screenClear("eos")
        print "Help"
        print "%-20s %-10s"%("command","key")
        print "%-20s %-10s"%("help","?")
        print "%-20s %-10s"%("refresh screen","space")
        print "%-20s %-10s"%("quit","q")
        print "%-20s %-10s"%("zero","z")
        print "%-20s %-10s"%("absolute, relative","a r")
        print "%-20s %-10s"%("small move","i j k l")
        print "%-20s %-10s"%("big move","I J K L")
        print "%-20s %-10s"%("move X to zero","<")
        print "%-20s %-10s"%("override speed","- +")
        print "%-20s %-10s"%("debug","D")
        print "%-20s %-10s"%("wire choice","A")
        print "%-20s %-10s"%("speed leadin/wind","s")
        print "%-20s %-10s"%("windings","w")
        print "%-20s %-10s"%("wind","W")
        print "%-20s %-10s"%("config","C")

    def getchar(self):
        return os.read(self.fd,1)

    def timeGet(self):
        return time.strftime("%H:%M:%S", time.localtime())

    def command(self,command):
        self._port.write(command+"\n");

    def loop(self):
        c = self._port.read(1)
        if len(c):
            if c == "\n":
                self.processBuffer()
            else:
                self.buffer += c
        now = time.time()
        if now > self.statusTimeout:
            self._port.write("?")
            self.statusTimeout = now + 0.20
            return
        if now > self.modalTimeout:
            self.command("$G")
            self.modalTimeout = now + 5.00
            return

    def loopSwitches(self):
        # Pn could be any of XYZSH
        if self.debug:
            self.screenPos(1,31)
            self.screenClear('eol')
            print "lastPn:"+self.status['lastPn']+" Pn:"+self.status['Pn']

        pn = self.status['Pn']
        lpn = self.status['lastPn']
        if pn.count('X') == 1 and lpn.count('X') == 0: # buttonDown
            self.command("$J=G91X6.0F10")
        if pn.count('X') == 0 and lpn.count('X') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('Y') == 1 and lpn.count('Y') == 0: # buttonDown
            self.command("$J=G91X-6.0F10")
        if pn.count('Y') == 0 and lpn.count('Y') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        '''
        just do rotation only from keyboard
        if pn.count('Z') == 1 and lpn.count('Z') == 0: # buttonDown
            self.command("$J=G91Y100F25")
        if pn.count('Z') == 0 and lpn.count('Z') == 1: # buttonUp
            self._port.write('\x85') # jog cancel
        '''

        if pn.count('Z') == 1 and lpn.count('Z') == 0: # buttonDown
            y = 6.0/self.wire['diameter']
            x = self.direction * 6.0
            if self.leadin:
                self.command("$J=G91X%0.5fY%0.4fF25"%(x,y))
            else:
                self.command("$J=G91X%0.5fY%0.4fF100"%(x,y))
        if pn.count('Z') == 0 and lpn.count('Z') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('S') == 0 and lpn.count('S') == 1: # buttonUp
            if self.status['state'] == 'Idle':
                self.direction = -self.direction

    def wireSet(self):
        number = ""
        self.screenPos(1,5)
        self.screenClear('eol')
        sys.stdout.write("awg? "+number)
        sys.stdout.flush()
        while True:
            c = self.getchar()
            if len(c):
                if ord(c[0]) == 10:
                    awg = int(number)
                    for w in self.wires:
                        if awg == int(w['size']):
                            self.wire = w
                            print self.wire
                            break
                    break
                else:
                    number += c
                self.screenPos(1,5)
                self.screenClear('eol')
                sys.stdout.write("awg? "+number)
                sys.stdout.flush()
        
    def processBuffer(self):
        # <Idle|WPos:0.0000,0.0000,0.0000|Bf:15,128|FS:0.0,0|WCO:0.0000,0.0000,0.0000>
        if len(self.buffer) > 5:
            if self.debug:
                self.screenPos(1,30)
                self.screenClear('eol')
                print self.buffer
            self.buffer = self.buffer.strip()
            if self.buffer.count("Grbl"):
                self.statusTimeout = 0
                self.modalTimeout = 0
            if self.buffer[0] == '<' and self.buffer[-1] == '>':
                fields = self.buffer[1:-1].split("|")
                self.status['state'] = fields[0]
                self.status['lastPn'] = self.status['Pn']
                self.status['Pn'] = ""
                for field in fields[1:]:
                    k,v = field.split(":")
                    self.status[k] = v
                self.loopSwitches()
                
                x,y,z = self.status['WPos'].split(',')
                self.status['position'] = float(x)
                self.status['turns'] = float(y)
                self.status['override'] = self.status['FS'].split(',')[0]
                self.status['bufferIndex'] = int(self.status['Bf'].split(',')[0])

                self.screenPos(1,1)
                self.screenClear('eol')
                if self.direction == 1:
                    dir = ">>"
                if self.direction == -1:
                    dir = "<<"
                if self.leadin:
                    windchar = "L"
                else:
                    windchar = "W"
                print "%-8s POS %-7.4f TURNS %-7.2f OVERRIDE %5s%%  AWG %d/%0.3f\" %s %c "%(self.status['state'],self.status['position'],self.status['turns'],self.status['override'],self.wire['size'],self.wire['diameter'],dir,windchar)
                self.screenPos(73,1)
                print self.timeGet()

            elif self.buffer[0] == '[' and self.buffer[-1] == ']':
                self.screenPos(1,2)
                self.screenClear('eol')
                print self.buffer[4:-1] 
                self.screenPos(45,2)
                self.screenClear('eol')
                if self.buffer.count("G0 "):
                    print "rapid ",
                if self.buffer.count("G1 "):
                    print "linear ",
                if self.buffer.count("G20 "):
                    print "inch ",
                if self.buffer.count("G21 "):
                    print "mm ",
                if self.buffer.count("G90"):
                    print "absolute "
                if self.buffer.count("G91"):
                    print "relative "
            else:
                self.screenPos(1,1)
                self.screenClear('eol')
                print self.buffer
        self.buffer = ""

    def processChar(self,c):
        # these are the single key commands

        if c == '!':
            self._port.write('!')
            self.statusTimeout = 0.0
            return
        if c == '~':
            self._port.write('~')
            self.statusTimeout = 0.0
            return
        if c == 'w':
            self.windingDisplay()
            return
        if c == 'W':
            self.windingWindStart()
            return
        if c == 'q':
            self.running = False
            return
        if c == '?':
            self.help()
            return
        if c == 'K':
            self.command("$J=G91Y0.05F30")
            return
        if c == 'I':
            self.command("$J=G91Y-0.05F30")
            return
        if c == 'J':
            self.command("$J=G91X-0.1F30")
            return
        if c == 'L':
            self.command("$J=G91X0.1F30")
            return
        if c == 'k':
            self.command("$J=G91Y0.01F100")
            return
        if c == 'i':
            self.command("$J=G91Y-0.01F100")
            return
        if c == 'j':
            self.command("$J=G91X-0.01F30")
            return
        if c == 'l':
            self.command("$J=G91X0.01F30")
            return
        if c == '<':
            self.modalTimeout = 0.0
            self.command("G90X0.0")
            return
        if c == 'z':
            self.zero()
            return
        if c == ' ': # clear
            self.screenClear()
            self.statusTimeout = 0.0
            self.modalTimeout = 0.0
            return
        if c == 'a': # absolute
            self.command("G90")
            self.modalTimeout = 0.0
            return
        if c == 'r': # linear
            self.command("G91")
            self.modalTimeout = 0.0
            return
        if c == '-': # override
            if self.status['state'] == 'Run':
                self.modalTimeout = 0.0
                self.statusTimeout = 0.0
                self._port.write('\x92')
                return
        if c == '+': # override
            if self.status['state'] == 'Run':
                self.modalTimeout = 0.0
                self.statusTimeout = 0.0
                self._port.write('\x91')
                return
        if c == 'D': # debug
            # self.screenClear()
            # self.modalTimeout = 0.0
            # self.statusTimeout = 0.0
            self.debug = not self.debug
            return
        if c == 's': # leadin choice
            self.screenClear()
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            self.leadin = not self.leadin
            return
        if c == 'A':
            self.wireSet()
            self.screenClear()
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            return
        if c == 'C':
            self.screenClear()
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            self.grblConfig()
            return

        # if c == '0':
        #    self.command("G90X0")
        #    return
        # if c == ' ':
        #    self.command("!")
        #    return
        # if c == '~':
        #    self.command("~")
        #    return
        
        if ord(c[0]) == 127:
            self.keybuffer = self.keybuffer[:-1]
        else:
            self.keybuffer += c

        self.screenPos(1,5)
        self.screenClear('eol')
        print "> "+self.keybuffer

        if ord(c[0]) == 10:
            self.screenPos(1,4)
            self.screenClear('eol')
            print "COMMAND "+self.keybuffer
            self._port.write(self.keybuffer)
            self.keybuffer = ""
            self.statusTimeout = 0.0
            self.modalTimeout = 0.0
            self.screenPos(1,5)
            self.screenClear('eol')
            print "> "

    def screenClear(self,what='screen'):
        '''
        erase functions:
                what: screen => erase screen and go home
                      line   => erase line and go to start of line
                      bos    => erase to begin of screen
                      eos    => erase to end of screen
                      bol    => erase to begin of line
                      eol    => erase to end of line
        '''
        clear = {
                'screen': '\x1b[2J\x1b[H',
                'line': '\x1b[2K\x1b[G',
                'bos': '\x1b[1J',
                'eos': '\x1b[J',
                'bol': '\x1b[1K',
                'eol': '\x1b[K',
                }
        sys.stdout.write(clear[what])
        sys.stdout.flush()

    def screenPos(self,x,y):
        sys.stdout.write('\x1b[%d;%dH'%(y,x))
        sys.stdout.flush()

    def cursorHide(self):
        sys.stdout.write('\x1b[?25l')
        sys.stdout.flush()

    def zero(self):
        self.command("G10 P0 L20 X0 Y0")

    def shutdown(self):
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old)

    def run(self):
        self.screenClear()
        print "startup"
        self.cursorHide()

        if self.windings:
            self.windingDisplay()
        
        while self.running:
            self.loop()
            time.sleep(0.001)
            c = self.getchar()
            if len(c):
                self.processChar(c)

        self.shutdown()
        self.screenClear()

    def grblConfig(self):
        time.sleep(1.0)
        self._port.flush()
        grblconfig = open("grbl.conf","r")
        for l in grblconfig.readlines():
            print "%-20s"%l.strip(),
            sys.stdout.flush()
            self._port.write(l)
            time.sleep(0.5)
            print self._port.read(100).strip()
        self.screenClear()
        self.statusTimeout = 0.0
        self.modalTimeout = 0.0

    def query(command):
        self._port.write('\n')
        time.sleep(0.5) # let remaining grbl string transmitting finish
        self._port.flush()
        self._port.write(command+'\n')
        rv = self._port.readline()
        return rv.strip()

    def grblConfigalt(self):
        time.sleep(5)
        self._port.flush()
        grblconfig = open("grbl.conf","r")
        for l in grblconfig.readlines():
            print l
            l = l.strip()
            print self.query(l)
            print



    

if __name__ == '__main__':
    m = Machine()
    m.run()
