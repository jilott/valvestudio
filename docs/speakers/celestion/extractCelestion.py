#!/usr/bin/env python

import BeautifulSoup,urllib2,re,traceback,pprint,sys,time,os

hreftext = re.compile('<a href.*>(.*?)\</a>', re.IGNORECASE)

if len(sys.argv) == 1:
    url = 'http://celestion.com/product/26/heritage_series_g1265/'
else:
    url = sys.argv[1]


def getInfo(labels,specs,label):
    i = 0
    for l in labels:
        if label == l.text:
            return specs[i].text
        i += 1 

out = ""
for url in open("list.txt").readlines():
    url = url.strip()
    # print url
    fn = "data/"+url.replace("/","_")
    if os.path.exists(fn):
        html = open(fn).read()
    else:
        req = urllib2.Request(url, headers={ 'User-Agent': 'Mozilla/5.0' })
        html = urllib2.urlopen(req).read()
        open(fn,'w').write(html)
    soup = BeautifulSoup.BeautifulSoup(html)

    labels = soup.findAll("div",{'class':'productspecblockleft'})
    specs = soup.findAll("div",{'class':'productspecblockright'})

    for name in soup.findAll("h2"):
        print name.text

    '''
    o = ""
    try:
        o += getInfo(labels,specs,"Nominal diameter").split('"')[0]+"\t"
    except:
        o += "\t"

    o += getInfo(labels,specs,"Power rating").split('W')[0]+"\t"

    try:
        o += str(getInfo(labels,specs,"Nominal impedance").encode('ascii','ignore')).replace("&Omega;","").strip()+"\t"
    except:
        o += "\t"
        

    o += getInfo(labels,specs,"Sensitivity").replace("dB","")+"\t"
    o += getInfo(labels,specs,"Magnet type")+"\t"
    freq = getInfo(labels,specs,"Frequency range").replace("Hz","").split('-')
    o += freq[0]+"\t"
    o += freq[1]+"\t"
    o += getInfo(labels,specs,"Resonance frequency, Fs").replace("Hz","")+"\t"
    try:
        o += getInfo(labels,specs,"DC resistance, Re").encode('ascii','ignore').split(' ',1)[1].replace("&Omega;","").replace(" or ",",")
    except:
        o += "\t"
    o += "\n"
    print o
    out += o
    '''


# open("out.csv","w").write(out)


