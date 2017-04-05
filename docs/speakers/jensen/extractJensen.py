#!/usr/bin/env python

import BeautifulSoup,urllib2,re,traceback,pprint,sys,time,os,html
from HTMLParser import HTMLParser
hp = HTMLParser()
hreftext = re.compile('<a href.*>(.*?)\</a>', re.IGNORECASE)

if len(sys.argv) == 1:
    url = 'http://celestion.com/product/26/heritage_series_g1265/'
else:
    url = sys.argv[1]

url = "https://www.jensentone.com/"
fn = "data/"+url.replace("/","_")
if os.path.exists(fn):
    html = open(fn).read()
else:
    req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
    html = urllib2.urlopen(req).read()
    open(fn,'w').write(html)
soupmain = BeautifulSoup.BeautifulSoup(html)

def doOne(url,name,html):
    # print
    # print "--------------------------------------------"
    # print "%-50s %s"%(url,name)
    soupmain = BeautifulSoup.BeautifulSoup(html)
    data = {}
    for ohm8 in soupmain.findAll("div",{'id':'ohm_table_8'}):
        for tr in ohm8.findAll("tr"):
            tds = tr.findAll("td")
            # print "%-30s %s"%(tds[0].text, tds[2].text.encode('ascii','ignore'))
            data[tds[0].text] = tds[2].text.encode('ascii','ignore')

    size = data['Nominal Overall Diameter'].split(' ')[0]
    power = data['Rated Power'].split(' ')[0]
    imp = "8"
    sens = data['Sensitivity@1W,1m'].split(' ')[0]
    mag = data['Magnet'].split(' ')[0]
    reson = data['Resonance Frequency'].split(' ')[0]
    dcr = data['Voice Coil DC Resistance'].strip()

    li = soupmain.find("li",{'class':'gallery-slide'})
    img = li.find("a")['href']

    instruct = soupmain.find("div",{'class':'instructions'})
    freqres = "https://www.jensentone.com"+instruct.find("a")['href']
    
    out = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"%(name,"Jensen",size,power,imp,sens,mag,"","",reson,dcr,url,img,freqres)
    print out

'''
https://www.jensentone.com//vintage_alnico/p6v     P6V
Nominal Overall Diameter       6 in.
Nominal Voice Coil Diameter    1.00 in.
Magnet Weight                  4.16 oz
Overall Weight                 1.57 lbs
Flux Density                   1.00 T
Voice Coil DC Resistance       6.54 
Resonance Frequency            110.0 Hz
Mechanical Q Factor            10.52
Electrical Q Factor            1.09
Total Q Factor                 0.99
Mechanical Moving Mass         6.7 g
Mechanical Compliance          310 m/N
Force Factor                   5.29 Wb/m
Equivalent Acoustic Volume     6.6 lt.
Maximum Linear Displacement    0.50 mm
Reference Efficiency           0.77 %
Diaphragm Area                 122.7 cm2
Losses Electrical Resistance   59.2 
Voice Coil Inductance @ 1kHz   0.40 mH
Magnet                         Alnico
Voice Coil Winding             Copper
Voice Coil Former              Epotex
Cone Material                  Paper
Surround Material              Integrated Paper
Dust Dome Material             Non-treated Cloth
Basket Material                Pressed Sheet Steel
Nominal Impedance              8 
Rated Power                    20 W
Musical Power                  40 W
Sensitivity@1W,1m              91.9 dB
'''


for subnav in soupmain.findAll("div",{'class':'subnav'}):
    for list1 in subnav.findAll("div",{'class':'item-list'}):
        for ul in list1.findAll("ul"):
            for list in ul.findAll("div",{'class':'item-list'}):
                if str(list.text).count('Vintage Alnico') or str(list.text).count('Vintage Ceramic') or str(list.text).count('Jet Series') or str(list.text).count('Mod Series'):
                    for ul1 in list.findAll("ul"):
                        for li in ul1.findAll("li"):
                            for a in li.findAll("a"):
                                # print a['href'],hp.unescape(a.text)
                                url = "https://www.jensentone.com/"+a['href']
                                fn = "data/"+url.replace("/","_")
                                if os.path.exists(fn):
                                    doOne(url,hp.unescape(a.text),open(fn).read())
                                else:
                                    req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
                                    html = urllib2.urlopen(req).read()
                                    open(fn,'w').write(html)


