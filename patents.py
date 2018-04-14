import urllib2
import re
import datetime
import pprint
import codecs
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

cred = credentials.Certificate("./firekey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#Read user preferences
dbpreferences = db.collection(u'userpreferences').get()
userpreferences = {}
for dbpreference in dbpreferences:
    print dbpreference.to_dict()
    userpreferences[dbpreference.to_dict()['key']] = dbpreference.to_dict()['value']
#keyword
keyword = "ibm"
if(userpreferences.has_key('keyword')):
    keyword = userpreferences['keyword']
print keyword

start_date = "01/01/2018"
end_date = "01/01/2019"

def getPatentUrl(page):
	# Create Search Address with Correct Search Options
	search_address = "http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&u=/netahtml/PTO/search-adv.htm"
	options = "&r=0&p=%s&f=S&l=50&Query=ISD/%s->%s+AND+AANM/%s&d=PTXT" % (page, start_date, end_date, keyword)
	return search_address + options

def parsePatents(parsed_html, patents):
	for tr in parsed_html.body.findAll('tr'):
		patentNo = None
		patentTitle = None
		index = 0
		for td in tr.findAll("td"):
			if len(tr.findAll("td")) == 4:
				if index == 1:
					patentNo = td.text
				elif index == 3:
					patentTitle = td.text
			index += 1
		if patentNo != None:
			patents.append([patentNo, patentTitle])

try: 
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup

page = 1

the_add = getPatentUrl(page)

#+ISD/01/01/2017->06/01/2019+AND+AANM/ibm
#?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-adv.htm&r=0&f=S&l=50&d=PTXT&Query=ISD%2F01%2F01%2F2018-%3E06%2F01%2F2019+AND+AANM%2Fibm
# Query USPTO search
response = urllib2.urlopen(the_add)
html = response.read()

# Extract PatentCount and PageCount
patentCount = 0
search = re.findall(': (\d+) patents\.', html)
if len(search):
	patentCount = int((search[0]))


pageNo = (patentCount // 50) if (patentCount // 50) == 0 else ((patentCount // 50) + 1)
print "pageNo:"+str(pageNo)

#Extract patents
patents = []
parsed_html = BeautifulSoup(html)
parsePatents(parsed_html, patents)
print "patentsNo:"+str(len(patents))

#Iterate pages
for x in range(2, pageNo+1):
	the_add = getPatentUrl(x)
	response = urllib2.urlopen(the_add)
	html = response.read()
	parsed_html = BeautifulSoup(html)
	parsePatents(parsed_html, patents)
	print "x"+str(x)
	print "patentsNo:"+str(len(patents))

print len(patents)

#Save into Firestore
for patent in patents:
	try:                
	    results = db.collection(u'patentes').where(u'patentNo', u'==', patent[0]).get()                
	    #resultsit = itertools.tee(results)
	    if (sum(1 for x in results) == 0):
			print "new"
			print patent
			newPatent = {u"keyword": unicode(keyword),"patentNo": unicode(patent[0]), "patentTitle": unicode(patent[1])}
			doc_ref = db.collection(u'patentes').document()
			doc_ref.set(newPatent)
	    else: 
	    	print "no new"
	        print patent
	except Exception:
		print "err"


#Print out result
print "The Total Number of U.S. Patents issued is: %s" % str(patentCount)

