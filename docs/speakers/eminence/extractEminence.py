#!/usr/bin/env python

import BeautifulSoup,urllib2,re,traceback,pprint,sys,time,os,html
from HTMLParser import HTMLParser
hp = HTMLParser()

urls = ['http://www.eminence.com/guitar-bass/guitar/','http://www.eminence.com/guitar-bass/signature-series/','http://www.eminence.com/guitar-bass/patriot-series/','http://www.eminence.com/guitar-bass/redcoat-series/','http://www.eminence.com/guitar-bass/legend-series/']


for url in urls:
    fn = "data/"+url.replace("/","_")
    if os.path.exists(fn):
        html = open(fn).read()
    else:
        req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
        html = urllib2.urlopen(req).read()
        open(fn,'w').write(html)

    soupmain = BeautifulSoup.BeautifulSoup(html)
    for td in soupmain.findAll("td",{'class':'model'}):
        model = td.find("a")
        modelurl = model['href']
        name = str(model.text).replace("&trade;","")
        # print name
        # print modelurl

        fn = "data/"+modelurl.replace("/","_")
        if os.path.exists(fn):
            html = open(fn).read()
        else:
            req = urllib2.Request(modelurl, headers={ 'User-Agent': 'Mozilla/5.0' })
            html = urllib2.urlopen(req).read()
            open(fn,'w').write(html)
            time.sleep(30)
    
        # html at this point is the page
        soupmodel = BeautifulSoup.BeautifulSoup(html)
        data = {} 
        for table in soupmodel.findAll("table",{'id':'em-detail'}):
            for tr in table.findAll("tr"):
                tds = tr.findAll("td")
                try:
                    # print "%-30s %s"%(tds[0].text, tds[1].text.encode('ascii','ignore'))
                    data[tds[0].text.replace("*","")] = tds[1].text.encode('ascii','ignore')
                except:
                    pass
        size = data['Nominal Basket Diameter'].split('&')[0]
        power = data['Watts'].split(' ')[0]
        imp = data['Nominal Impedance'].split(' ')[0]
        sens = data['Sensitivity'].split(' ')[0]
        mag = data['Magnet Composition'].split(' ')[0]
        reson = data['Resonance'].split(' ')[0]
        dcr = data['DC Resistance (Re)'].split(' &')[0]
        ran = data['Usable Frequency Range'].split(' - ')
        rl = ran[0].split(' ')[0]
        rh = float(ran[1].split(' ')[0])*1000

        style = soupmodel.find("div",{'id':'large-img'})['style']
        img = "http://www.eminence.com"+style.split("url(")[1].split(")")[0] 
        freqres = "http://www.eminence.com"+soupmodel.find("img",{'alt':'response graph'})['src']

        out = "%s,%s,%s,%s,%s,%s,%s,%s,%d,%s,%s,%s,%s,%s"%(name,"Eminence",size,power,imp,sens,mag,rl,rh,reson,dcr,modelurl,img,freqres)
        print out


'''
Nominal Basket Diameter        12&quot;, 305 mm
Nominal Impedance*             8 &Omega;
Program Power                  N/A
Watts                          150 W
Resonance                      82 Hz
Usable Frequency Range         80 Hz - 3.8 kHz
Sensitivity*                   101.4 dB
Magnet Weight                  11 oz.
Gap Height                     0.375&quot;, 9.53 mm
Voice Coil Diameter            2.5&quot;, 64 mm
Resonant Frequency (fs)        82 Hz
DC Resistance (Re)             7.46 &Omega;
Coil Inductance (Le)           0.43m H
Mechanical Q (Qms)             14.28
Electromagnetic Q (Qes)        0.44
Total Q (Qts)                  0.43
Compliance Equivalent Volume (Vas) 47.22 liters / 1.67  cu.ft.
Peak Diaphragm Displacement Volume (Vd) 118.19 cc
Mechanical Compliance of Suspension (Cms) 0.12 mm/N
BL Product (BL)                16.31 T-M
Diaphragm Mass Inc. Airload (MMs) 30 grams
Efficiency Bandwidth Product (EBP) 187
Maximum Linear Excursion (Xmax) 2.22 mm
Surface Area of Cone (Sd)      532.4 cm2
Maximum Mechanical Limit (Xlim) 0.00 mm
Sealed                         Acceptable
Vented                         Acceptable
Driver Volume Displaced        0.06 cu.ft. / 1.81 liters
Overall Diameter               12.17&quot;, 309.12 mm
Baffle Hole Diameter           11.13&quot;, 282.7 mm
Front Sealing Gasket           Yes
Rear Sealing Gasket            No
Mounting Holes Diameter        0.24&quot;, 6.1mm
Mounting Holes B.C.D.          11.75&quot;, 298.45mm
Depth                          5&quot;, 127 mm
Net Weight                     6.6 lbs, 2.99 kg
Shipping Weight                8.7 lbs, 3.95 kgs
Coil Construction              Edge-wound aluminum
Coil Former                    Polyimide former
Magnet Composition             Neodymium
Core Details                   Vented core
&nbsp;                         &nbsp;
Basket Materials               Pressed steel
Cone Composition               Full molded paper
Cone Edge Composition          Paper
Dust Cap Composition           Treated paper
'''
