import requests
import pandas as pd
import numpy as np
from StringIO import StringIO
from mpmath import isnan
import collections

from sympy import *
from IPython.display import display
init_printing(use_latex='mathjax')
import mpmath
mpmath.mp.dps = 15

def solve(key,debug=False,showcode=False,showequations=False):
    code = "from sympy import *\n\n"

    url = "https://docs.google.com/spreadsheets/d/%s/export?format=csv"%(key) # don't put the gid id in, then always returned the first sheet in tabs

    r = requests.get(url)
    data = r.content

    if debug:
        print data

    df = pd.read_csv(StringIO(data),header=-1)
    if debug:
        print df


    locInput = 1
    locName = 2
    locOutput = 3
    locRule = 0
    locSt = 0
    locGroup = 0

    parserState = None
    variables = []
    rules = []

    #print df.iloc[0,0]
    for i in range(0,len(df)):
        if df.iloc[i,locGroup] == 'st':
            continue
        if df.iloc[i,locGroup] == 'variables':
            parserState = 'inVariables'
            continue
        if parserState == 'inVariables':
            if pd.isnull(df.iloc[i,locName]):
                parserState = None
            else:
                variables.append({'st':df.iloc[i,locSt],
                                  'name':df.iloc[i,locName],
                                  'input':df.iloc[i,locInput],
                                 'row':i})

        if df.iloc[i,locGroup] == 'rules':
            parserState = 'inRules'
            continue
        if parserState == 'inRules':
            if pd.isnull(df.iloc[i,locRule]):
                parserState = None
                break
            else:
                rules.append(df.iloc[i,locRule])

    if debug:
        print variables
        print rules

    code += "# variables\n"
    initialGuess = 10000.1
    outputs = collections.OrderedDict()

    for v in variables:
        if len(v['name']) == 1:
            code += "%-5s = Symbol('%s')\n"%(v['name'],v['name'])
        else:
            code += "%-5s = Symbol('%c_%s')\n"%(v['name'],v['name'][0],v['name'][1:])

        if v['st'] =='g':
            outputs[v['name']] = float(v['input'])
        else:
            if isnan(v['input']):
                outputs[v['name']] = initialGuess
            else:
                code += "%-5s = %f\n"%(v['name'],float(v['input']))
    code += "\n"

    if debug:
        print code
        print outputs

    code += "# rules\n"
    ans = "ans = nsolve(("
    i = 1
    for r in rules:
        lhs,rhs = r.split('=',1)
        code += "e%d = Eq(   %10s,%-20s   )\n"%(i,lhs,rhs)
        if showequations:
            code += "display(e%d)\n"%i
        ans += "e%d,"%i
        i += 1



    code += "\n# solve\n"+ans[0:-1]+"),("+",".join(outputs.keys())+"),("
    code += ",".join(map(str,outputs.values()))+"),verify=True)"

    code += "\n\n# answers\n"

    i = 0
    if len(outputs.keys()) == 1:
        code += "print ans\n" 
    else:
        for k in outputs.keys():
            code += "print \"%-5s = %%14.6f\"%%ans[%d]\n"%(k,i)
            i += 1
        
    if debug or showcode:
        print code
        print 
        print "# ------------------------------------------------------------------\n\n"

    try:
        exec(code)
    except ValueError as msg:
        print msg
    except TypeError as msg:
        print msg
        print "modify initial values"
