#!/usr/bin/env python

# https://github.com/gnea/grbl/blob/master/doc/markdown/interface.md

# G10 P0 L20 X0
# G10 P0 L20 Y0

import serial,time,sys,termios,os,csv


class Machine():
    def __init__(self,port='/dev/ttyUSB0'):
        self._port = serial.Serial(port,115200,timeout=0)
        self.statusTimeout = time.time() + 5.0
        self.modalTimeout = time.time() + 5.0
        self.buffer = ""
        self.keybuffer = ""
        self.status = {'lastPn':"",'Pn':""}
        self.running = True
        self.wire = None
        self.debug=False
        self.direction = 1

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


    def getchar(self):
        return os.read(self.fd,7)

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
        # Pn could be any of XYZS
        if self.debug:
            self.screenPos(1,12)
            self.screenClear('eol')
            print "lastPn:"+self.status['lastPn']+" Pn:"+self.status['Pn']

        pn = self.status['Pn']
        lpn = self.status['lastPn']
        if pn.count('X') == 1 and lpn.count('X') == 0: # buttonDown
            self.command("$J=G91X6.0F25")
        if pn.count('X') == 0 and lpn.count('X') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('Y') == 1 and lpn.count('Y') == 0: # buttonDown
            self.command("$J=G91X-6.0F25")
        if pn.count('Y') == 0 and lpn.count('Y') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('Z') == 1 and lpn.count('Z') == 0: # buttonDown
            self.command("$J=G91Y100F25")
        if pn.count('Z') == 0 and lpn.count('Z') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('S') == 1 and lpn.count('S') == 0: # buttonDown
            y = 6.0/self.wire['diameter']
            x = self.direction * 6.0
            self.command("$J=G91X%0.5fY%0.4fF100"%(x,y))
        if pn.count('S') == 0 and lpn.count('S') == 1: # buttonUp
            self._port.write('\x85') # jog cancel

        if pn.count('H') == 1 and lpn.count('H') == 0: # buttonDown
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
                if ord(c) == 10:
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
                self.screenPos(1,10)
                self.screenClear('eol')
                print self.buffer
            self.buffer = self.buffer.strip()
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


                self.screenPos(1,1)
                self.screenClear('eol')
                if self.direction == 1:
                    dir = ">>>"
                if self.direction == -1:
                    dir = "<<<"
                print "%-8s POS %-7.4f TURNS %-7.2f OVERRIDE %s%%   AWG %d/%0.3f\" %s"%(self.status['state'],self.status['position'],self.status['turns'],self.status['override'],self.wire['size'],self.wire['diameter'],dir)
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

        if c == 'q':
            self.running = False
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
        if c == ' ':
            self.screenClear()
            self.statusTimeout = 0.0
            self.modalTimeout = 0.0
            return
        if c == 'a':
            self.command("G90")
            self.modalTimeout = 0.0
            return
        if c == 'r':
            self.command("G91")
            self.modalTimeout = 0.0
            return
        if c == '-':
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            self._port.write('\x92')
            return
        if c == '+':
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            self._port.write('\x91')
            return
        if c == 'D':
            self.screenClear()
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
            self.debug = not self.debug
            return
        if c == 'W':
            self.wireSet()
            self.screenClear()
            self.modalTimeout = 0.0
            self.statusTimeout = 0.0
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

        
        if ord(c) == 127:
            self.keybuffer = self.keybuffer[:-1]
        else:
            self.keybuffer += c

        self.screenPos(1,5)
        self.screenClear('eol')
        print "> "+self.keybuffer

        if ord(c) == 10:
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

if __name__ == '__main__':
    m = Machine()
    m.screenClear()
    print "startup"
    m.cursorHide()
    
    while m.running:
        m.loop()
        time.sleep(0.001)
        c = m.getchar()
        if len(c):
            m.processChar(c)

    m.shutdown()
