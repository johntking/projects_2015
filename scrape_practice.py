from bs4 import BeautifulSoup
import urllib.request
from collections import defaultdict
import numpy as np
import json

"""
'zip_codes_states.csv' from https://www.gaslampmedia.com/download-zip-code-latitude-longitude-city-state-county-csv/
"""


def get_stabbs():
	with open('stabbs.json','r') as F:
		D = json.load(F)
	return D

def get_wiki_data():
	wiki = "http://en.wikipedia.org/wiki/List_of_United_States_counties_and_county_equivalents"
	#header = {'User-Agent': 'Mozilla/5.0'} #Needed to prevent 403 error on Wikipedia .. in py2?
	page = urllib.request.urlopen(wiki)
	soup = BeautifulSoup(page)
	table = soup.find("table", { "class" : "wikitable sortable" })
	output = []
	for row in table.findAll("tr"):
		cells = row.findAll("td")
		#For each "tr", assign each "td" to a variable.
		if len(cells)!= 7: 
			#print(cells)
			continue
		county = cells[1].find(text=True)
		state = cells[2].find(text=True)
		population = int(cells[4].find(text=True).replace(',',''))
		output.append({'c':county,'s':state,'p':population})
	return output

def get_zip_data():
	output = []
	with open('zip_codes_states.csv','r') as F:
		for i,l0 in enumerate(F):
			l1 = [x.strip('"\n') for x in l0.split(',')]
			if i!=0 and l1[1]!='' and l1[2]!='':
				l2 = {'ll':(float(l1[1]),float(l1[2])),'s':l1[4],'c':l1[5],'z':int(l1[0])}
				output.append(l2)
	return output

stabbs = get_stabbs()
output_wiki = get_wiki_data()
output_zip = get_zip_data()
# manual corrections:
output_zip.append({'z':00000,'ll':(21.192587, -156.964330),'s':"HI",'c':"Kalawao"})
zc_corrections = {
	80020:'Broomfield',
	24422:'Alleghany',
	99929:'Wrangell',
	99833:'Petersburg',
	99820:'Hoonah Angoon',
	99840:'Skagway',
}

rev_stabb_dict = {y:x for x,y in stabbs.items()}
rev_stabb_dict.update({'district of columbia':'DC','hawai':'HI'})
# excludes {'AS', 'FM', 'GU', 'MH', 'MP', 'PR', 'PW', 'VI'}:
states = {x for x,y in stabbs.items()}

misc_state_corr = {
	'lasalle':'la salle',
	'obrien':"o'brien",
	'carson city':'carson',
	'st. louis city':'st. louis',
	'st. marys':"st. mary's",
	'queen annes':"queen anne's",
	'prince georges':"prince george's",
	'du page':'dupage',
	'de kalb':'dekalb',
	'de witt':'dewitt',
	'dona ana':'doña ana',
	'de soto':'desoto',
	'la porte':'laporte',
	'prince wales ketchikan':'prince of wales – hyder',
}

def get_cou_simple_form(c):
	c = c.lower()
	for a,b in [('saint','st.'),('sainte','ste.'),('st','st.')]:
		if c.startswith(a+' '):
			c = c.replace(a,b)
	for jetsom in [' county',', city of',' parish', ' borough',' census area',
		', municipality of',', city and of',', city and  of',
		', consolidated municipality of',' city',', city and county of',
		', town and county of',', city and borough of']:
		if c.endswith(jetsom):
			c = c[:-len(jetsom)]
	if c in misc_state_corr:
		c = misc_state_corr[c]
	c = c.strip(' .').replace('–',' ').replace('-',' ')
	return c

def clean_cou_wiki_form(c):
	for jetsom in [' County',', City of',' Parish', ' Borough',' Census Area',
		', Municipality of',', City and of',', City and  of',
		', Consolidated Municipality of',' City',', City and County of',
		', Town and County of',', City and Borough of']:
		if c.endswith(jetsom):
			c = c[:-len(jetsom)]
		return c


scp_dict = {s:{} for s in states}
county_orig_wiki = {}
for d in output_wiki:
	s = rev_stabb_dict[d['s'].lower()]
	if s not in states: continue
	c = get_cou_simple_form(d['c'])
	county_orig_wiki[(s,c)] = d['c']
	scp_dict[s][c] = d['p']

scz_dict = {s:{} for s in states}
#county_orig_zip = {}
for d in output_zip:
	s = d['s']
	if s not in states: continue
	z = d['z']
	if z not in zc_corrections:
		c = get_cou_simple_form(d['c'])
	else:
		c = get_cou_simple_form(zc_corrections[z])
	#county_orig_zip[(s,c)] = d['c']
	if c not in scz_dict[s]:
		scz_dict[s][c] = []
	scz_dict[s][c].append((d['z'],d['ll']))

#for s in states:
#	cc1 = set(scz_dict[s])
#	cc2 = set(scp_dict[s])
#	shared = cc1 & cc2
#	unac1 = cc1 - cc2
#	unac2 = cc2 - cc1
#	if unac1!=set() or unac2!=set():
#		print('\n'+s)
#		for c in unac1:
#			print(' 1',c)
#		for c in unac2:
#			print(' 2',c)
# for now it includes a few zips that are rep'd:
# they were part of census areas that were split.

main_dict = {}
for s in scp_dict:
	main_dict[s] = {}
	for c in scp_dict[s]:
		lon = np.mean([ll[0] for z,ll in scz_dict[s][c]])
		lat = np.mean([ll[1] for z,ll in scz_dict[s][c]])
		sc_subdict = {'pop':scp_dict[s][c],'lat':lat,'lon':lon}
		c_clean = clean_cou_wiki_form(county_orig_wiki[(s,c)])
		main_dict[s][c_clean] = sc_subdict


def test_plot():
	figure(figsize=(15,10))
	colors = {s:random.random(size=3) for s in main_dict}
	dd = [(s,d) for s,dd in main_dict.items() for c,d in dd.items() if s not in ('AK','HI')]
	xx = np.array([d['lat'] for s,d in dd])
	yy = np.array([d['lon'] for s,d in dd])
	pp = np.array([d['pop'] for s,d in dd])**.5/2
	col = np.array([colors[s] for s,d in dd])
	scatter(xx,yy,s=pp,color=col,alpha=.25)
	xlim(-126,-66)
	ylim(24,50)
	subplots_adjust(0,0,1,1)
	gca().tick_params(axis='both',left='off',right='off',top='off',bottom='off')










