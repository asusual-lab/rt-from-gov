from urllib import request
from bs4 import BeautifulSoup
import re
import os
import urllib
import PyPDF2
import glob
import json
import shutil

#scrap first page
url="http://www.salute.gov.it/portale/nuovocoronavirus/dettaglioContenutiNuovoCoronavirus.jsp?area=nuovoCoronavirus&id=5351&lingua=italiano&menu=vuoto"
response = request.urlopen(url).read()
soup= BeautifulSoup(response, "html.parser")  
links = soup.find_all('a')
clean = [x for x in links if x.string != None]
filtered_links = []
for link in clean:
	if "MONITORAGGIO" in link.string:
		filtered_links.append(link)
print ("Successfully got links for the Monitoraggio page")
#select first link of this type, should always appear as first
myurl=filtered_links[0]["href"]
####### Get Data From my page
# connect to website and get list of all pdfs
url="http://www.salute.gov.it"+myurl

response = request.urlopen(url).read()
soup= BeautifulSoup(response, "html.parser")
links = soup.find_all('a', href=re.compile(r'(.pdf)'))

# clean the pdf link names
url_list = []
for el in links:
	if (el['href'].startswith('http')):
		url_list.append(el['href'])
	else:
		url_list.append("http://www.salute.gov.it" + el['href'])
url_clean=[]
for cc in url_list:
	if 'Epi_aggiornam' in cc:
		url_clean.append(cc)
#print(url_clean)


#creation of a tmp dir
path = "/tmp/nuovi_rt"

try:
    os.makedirs(path)
except OSError:
    print ("Creation of the directory %s failed" % path)
else:
    print ("Successfully created the directory %s" % path)

# download the pdfs to a specified location
for url in url_clean:
    #print(url)
    fullfilename = os.path.join('/tmp/nuovi_rt', url.replace("http://www.salute.gov.it/portale/news/documenti/Epi_aggiornamenti/", ""))
    #print(fullfilename)
    request.urlretrieve(url, fullfilename)


# extract rt data
files = glob.glob("{}/*.pdf".format(path))
italia_reg = {}
italia_reg["data"] = {}
for url in files:
	reader = PyPDF2.PdfFileReader(url)
	region = url.split("_")[-2]
	rt = reader.getPage(1).extractText().split("Rt:")[1].strip().split(" (CI")[0]
	italia_reg["data"][region] = rt
italia_reg["ultimo_aggiornamento"] = url.split("_")[-1].strip(".pdf")
print ("Successfully got RT from PDF files")

# write a js 
with open('Rt_file.js', 'w') as outfile:
	json.dump(italia_reg, outfile)
print ("File Rt_file.js created")

#remove tmp file
shutil.rmtree(path)