from urllib import request
from bs4 import BeautifulSoup
import re
import os
import urllib
import PyPDF2
import glob
import json
import shutil


#creation of a tmp dir
def create_dir(dirname):
	try:
		os.makedirs(dirname)
	except OSError:
		print ("Creation of the directory %s failed" % dirname)
	else:
		print ("Successfully created the directory %s" % dirname)

def delta(dicta):
	for region in dicta["data"]:
		current = float(dicta["data"][region]["current"])
		previous = float(dicta["data"][region]["previous"])
		dicta["data"][region]["delta"] = ""
		if current>previous:
			dicta["data"][region]["delta"]="+"
		elif current<previous:
			dicta["data"][region]["delta"]="-"
	return dicta

#Where store the files?
path = "/tmp/nuovi_rt"

#scrap first page
url="http://www.salute.gov.it/portale/nuovocoronavirus/archivioMonitoraggiNuovoCoronavirus.jsp"
response = request.urlopen(url).read()
soup= BeautifulSoup(response, "html.parser")  
links = soup.find_all('a')
clean = [x for x in links if x.string != None]
filtered_links = []
for link in clean:
	if "monitoraggio" in link.string.lower():
		filtered_links.append(link)
print ("Successfully got links for the Monitoraggio page")
#select first link of this type, should always appear as first
last_link=filtered_links[0]["href"]
previous_link=filtered_links[1]["href"]
####### Get Data From my page
# connect to website and get list of all pdfs
prefix = "http://www.salute.gov.it"
url_list=[prefix+last_link,prefix+previous_link]

pdf_list = {}
create_dir(path)
ultimoAggiornamento=""
italia_RT = {}
italia_RT["data"] = {}
for n,url in enumerate(url_list):
	response = request.urlopen(url).read()
	soup= BeautifulSoup(response, "html.parser")
	links = soup.find_all('a', href=re.compile(r'(egionale.pdf)'))

	# clean the pdf link names
	for el in links:
		regione = el["title"].replace(" ","").strip().replace("-","").lower()
		if "bolzano" in regione:
			regione = "bolzano"
		if "trento" in regione:
			regione = "trento"
		if "valle" in regione:
			regione = "valledaosta"
		if (el['href'].startswith('http')):
			pdf_list[regione] = el['href']
		else:
			pdf_list[regione] = "http://www.salute.gov.it" + el['href'] 
	
	# download the pdfs to a specified location
	for Region in pdf_list:
		#print(url)
		fullfilename = os.path.join(path, Region + ".pdf")
		#print(fullfilename)
		request.urlretrieve(pdf_list[Region], fullfilename)		

	# extract rt data
	files = glob.glob("{}/*.pdf".format(path))
	for pdf in files:
		Region = pdf.split("/")[-1].replace(".pdf","")
		if n == 0:
			Date = "current"
		else:
			Date = "previous"
		reader = PyPDF2.PdfFileReader(pdf)
		#print(pdf) 
		rt_value = reader.getPage(1).extractText().split("Rt:")[1].strip().split(" (CI")[0]
		if Region not in italia_RT["data"]:
			italia_RT["data"][Region] = {}
			italia_RT["data"][Region][Date] = rt_value
		else:
			italia_RT["data"][Region][Date] = rt_value			
	if n == 0:
		dadata = reader.getPage(0).extractText().split("aggiornati al")[1].strip().replace(")","").split("/")
		if '0' not in dadata[1] and len(dadata[1]) == 1:
			dadata[1] = '0'+dadata[1]
		italia_RT["ultimoAggiornamento"] = dadata[2].replace("\n","")+dadata[1].replace("\n","")+dadata[0].replace("\n","")
print ("Successfully got RT from PDF files")
#print(italia_RT)
#add delta info
delta(italia_RT)

# write a js 
with open('Rt_file.js', 'w') as outfile:
	json.dump(italia_RT, outfile)
print ("File Rt_file.js created")

#remove tmp file
shutil.rmtree(path)
