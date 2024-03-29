import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import bridgedbpy

__author__ = 'Kozo Nishida'
__email__ = 'knishida@riken.jp'
__version__ = '0.0.1'
__license__ = 'MIT'

API_BASE = 'https://webservice.wikipathways.org/'

def wp2cyelements(identifier):
    gpml = requests.get(API_BASE + 'getPathway?pwId=' + identifier + '&format=json').content
    soup = BeautifulSoup(json.loads(gpml)['pathway']['gpml'], "xml")
    
    wpnodes = soup.find_all('DataNode')
    wpedges = soup.find_all('Interaction')

    cyelements = {}
    cynodes = []
    cyedges = []
    nodeids = []

    for wpn in wpnodes:
        if wpn['Type'] == "Metabolite":
            g = wpn.find('Graphics')
            
            data = {}
            data['id'] = wpn['GraphId']
            nodeids.append(wpn['GraphId'])
            data['label'] = wpn['TextLabel']
            data['x'] = float(g['CenterX'])
            data['y'] = float(g['CenterY'])
            data['width'] = g['Width']
            data['height'] = g['Height']

            xref = wpn.find('Xref')
            if xref is not None:
                data['database'] = xref['Database']
                data['xrefID'] = xref['ID']
                print(data['id'], data['label'], data['database'], data['xrefID'])
                data['KEGG'] = bridgedbpy.gpml2kegg(xref['Database'], xref['ID'])

        cynode = {"data":data, "position":{"x":float(g["CenterX"]), "y":float(g["CenterY"])}, "selected":"false"}
        cynodes.append(cynode)

    for wpe in wpedges:
        data = {}
        for point in wpe.find_all('Point'):
            if point.has_attr('GraphRef') and point.has_attr('ArrowHead'):
                if point['GraphRef'] in nodeids:
                    data['target'] = point['GraphRef']
            elif point.has_attr('GraphRef'):
                if point['GraphRef'] in nodeids:
                    data['source'] = point['GraphRef']
        if 'source' in data.keys() and 'target' in data.keys():
            cyedge = {"data":data}
            cyedges.append(cyedge)

    cyelements["nodes"] = cynodes
    cyelements["edges"] = cyedges
    return cyelements

def cynodes2df(cynodes):
    rows = []
    for cynode in cynodes:
        rows.append(pd.Series(cynode['data']))
    return pd.DataFrame(rows)

def cyelements2cyjs(cyelements, filename):
    d = {}
    d["elements"] = cyelements
    print(json.dumps(d, indent=4), file=open(filename,'w'))
    print("save cyelements as " + filename)
    
