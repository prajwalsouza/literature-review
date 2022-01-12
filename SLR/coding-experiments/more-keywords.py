import requests
import json
import time
import re
import pickle

searchString = 'title-abs-key(\'citizen science games\')'

apiKey = 'scopus key' 
# https://dev.elsevier.com/apikey/manage


print(searchString)

def getSearchPage(pageNum):
	response = requests.get('https://api.elsevier.com/content/search/scopus?query=' + searchString + '&apiKey=' + apiKey + '&start=' + str(pageNum*200) + '&sort=citedby-count&count=200')
	recievedSearchData = {}
	if response.status_code == 200:
		pageContent = json.loads(response.content)
		recievedSearchData['totalResults'] = pageContent['search-results']['opensearch:totalResults']
		recievedSearchData['perPageResults'] = pageContent['search-results']['opensearch:itemsPerPage']
		entries = pageContent['search-results']['entry']
		recievedSearchData['articles'] = []
		entryCount = 0
		for entry in entries:
			article = {}
			article['scopusId'] = entry['dc:identifier'].split('SCOPUS_ID:')[1]
			article['title'] = entry['dc:title']
			article['citationCount'] = entry['citedby-count']

			recievedSearchData['articles'].append(article)
	else:
		print("Error with the page")
		print(response.status_code)

	return recievedSearchData

try:
	with open(searchString + '.p', 'rb') as handle:
		searchData = pickle.load(handle)
except:
	searchData = {}

	firstPageSearchData = getSearchPage(0)

	totalResults = int(firstPageSearchData['totalResults'])
	perPageResults = int(firstPageSearchData['perPageResults'])
	pagesCount = int(totalResults*1.0/perPageResults) + 1

	searchData['totalResults'] = totalResults
	searchData['perPageResults'] = perPageResults
	searchData['pagesCount'] = pagesCount

	print(totalResults)

	searchData['articles'] = firstPageSearchData['articles']

	for pageNumber in range(1, pagesCount):
		time.sleep(1)
		searchResults = getSearchPage(pageNumber)
		searchData['articles'] = searchData['articles'] + searchResults['articles']


	with open(searchString + '.p', 'wb') as handle:
		pickle.dump(searchData, handle, protocol=pickle.HIGHEST_PROTOCOL)


try:
	with open('keywords.p', 'rb') as handle:
		keywords = pickle.load(handle)
except:
	keywords = {}

def getKeywords(scopus_id):
	try:
		return keywords[scopus_id]
	except:
		time.sleep(0.2)
		response = requests.get("https://api.elsevier.com/content/abstract/scopus_id/" + scopus_id + "?field=authkeywords&apiKey=913df200a0d9b596664aa9ce90a6e0f4")
		if response.status_code == 200:
			pageContent = response.content.decode('utf-8')
			keywordsForArticle = re.findall(r"<author-keyword>(.*?)</author-keyword>", pageContent)
			keywords[scopus_id] = keywordsForArticle

			with open('keywords.p', 'wb') as handle:
				pickle.dump(keywords, handle, protocol=pickle.HIGHEST_PROTOCOL)

			return keywords[scopus_id]

keys = []
for article in searchData['articles']:
	keysFromArticle = getKeywords(article['scopusId'])
	keys = keys + keysFromArticle 
	

keywordCount = {}
avoidChar = ['-']

for keyword in keys:
	word = keyword.lower()
	for char in avoidChar:
		word = word.replace(char, '')
	try:
		keywordCount[word] = keywordCount[word] + 1
	except:
		keywordCount[word] = 1


keywordCount = dict(sorted(keywordCount.items(), key=lambda item: item[1], reverse=True))

print(keywordCount)

