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
		dicta["data"][region]["delta"] = "="
		if current>previous:
			dicta["data"][region]["delta"]="+"
		elif current<previous:
			dicta["data"][region]["delta"]="-"
	return dicta

#Where store the files?
path = "/tmp/nuovi_rt"

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
last_link=filtered_links[0]["href"]
previous_link=filtered_links[1]["href"]
####### Get Data From my page
# connect to website and get list of all pdfs
prefix = "http://www.salute.gov.it"
url_list=[prefix+last_link,prefix+previous_link]

pdf_list = []
direct_links_pdf=[]
create_dir(path)
ultimoAggiornamento=""
for n,url in enumerate(url_list):
	response = request.urlopen(url).read()
	soup= BeautifulSoup(response, "html.parser")
	links = soup.find_all('a', href=re.compile(r'(.pdf)'))

	# clean the pdf link names
	for el in links:
		if (el['href'].startswith('http')):
			pdf_list.append(el['href'])
		else:
			pdf_list.append("http://www.salute.gov.it" + el['href'])
	for cc in pdf_list:
		if 'Epi_aggiornam' in cc:
			direct_links_pdf.append(cc)
			if n==0:
				ultimoAggiornamento=cc.split("_")[-1].strip(".pdf")
	
	# download the pdfs to a specified location
	for direct in direct_links_pdf:
	    #print(url)
	    fullfilename = os.path.join(path, direct.replace("http://www.salute.gov.it/portale/news/documenti/Epi_aggiornamenti/", ""))
	    #print(fullfilename)
	    request.urlretrieve(direct, fullfilename)

	# extract rt data
	files = glob.glob("{}/*.pdf".format(path))
	italia_RT = {}
	italia_RT["data"] = {}
	for pdf in files:
		Date=pdf.split("_")[-1].strip(".pdf")
		if Date == ultimoAggiornamento:
			Date = "current"
		else:
			Date = "previous"
		reader = PyPDF2.PdfFileReader(pdf)
		#print(pdf) 
		Region = pdf.split("Epi_aggiornamento_")[-1].lower().replace("-","")[:-13].replace("_","")
		rt_value = reader.getPage(1).extractText().split("Rt:")[1].strip().split(" (CI")[0]
		if Region not in italia_RT["data"]:
			italia_RT["data"][Region] = {}
			italia_RT["data"][Region][Date] = rt_value
		else:
			italia_RT["data"][Region][Date] = rt_value			
	italia_RT["ultimoAggiornamento"] = ultimoAggiornamento
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