import requests
from rqueue import Queue
from rdatabase import Database
import re
import threading
import logging

logging.basicConfig(filename='search_engine.log', format='%(asctime)s %(levelname)s:%(message)s.\n', level=logging.DEBUG)

try:
	file = open('search_engine.log', 'w')
	file.write('')
	file.close()
except IOError as e:
	pass


def get_base_link(link):
	base_regex = re.compile('http[s]{0,1}://[a-zA-Z0-9\._\-]+/')
	return re.findall(base_regex, link)[0]




class SiteError(Exception):
	pass



class Site(object):

	HTTP_PROXY_URL	  = 'http://222.87.129.30:80'
	RELATIVE_REGEX    = re.compile('href="(?!http[s]{0,1}://|.*\.js|.*\.css).*?"')
	ABSOLUTE_REGEX    = re.compile('href="http[s]{0,1}://.+?"')
	#DESCRIPTION_REGEX = re.compile('(<meta\s*name="[Dd]escription"\s*content="*."\s*[/>]+|<meta\s*name="[kK]eywords"\s*content="*."\s*[/>]+|<title>.*</title>)')
	DESCRIPTION_REGEX = re.compile('(<title\s*>.*</title\s*>)')
	REPLACE_REGEX     = re.compile('<title\s*>|</title\s*>')
	SENTENCE_REGEX    = re.compile('(?!script|title)([^><]*)>(?u)\w+</')
	WORD_REGEX        = re.compile('(?u)\w+')  

	def __init__(self, link, anonimously = False):
		super(Site, self).__init__()
		self.link = link
		self.content      = ''
		self.content_type = ''
		self.headers = {'User-Agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.1.7pre) Gecko/20070815 Firefox/2.0.0.6 Navigator/9.0b3'}
		self.relative_links = []
		self.absolute_links = []
		self.description    = ''
		self.anonimously    = anonimously
		self.words          = {}	

	def load(self):
		try:
			logging.debug('Starting to load url:%s' % self.link)
			response = None
			if self.anonimously is True:
				response = requests.get(self.link, headers=self.headers, proxies={'http' : Site.HTTP_PROXY_URL})
			else:
				response = requests.get(self.link, headers=self.headers)

			if response.status_code == 200 and response.headers['content-type'].startswith('text/html'):
				
				self.content      = response.content			
		
				try:
					response.content = unicode(response.content, "UTF-8")
					self.description = re.findall(Site.DESCRIPTION_REGEX, response.content)
					self.description = self.description[0] if len(self.description) > 0 else ''
					self.description = re.sub(Site.REPLACE_REGEX, '', self.description)			
				except Exception as e:
					print e
					logging.error('Error: %s while looking for description...' % str(e))
				relative_links = re.findall(Site.RELATIVE_REGEX, response.content)
			
				# remove href=" and "
				relative_links = map(lambda x: x[6:-1], relative_links)
						
				# remove forward slash if any eg. /download
				for idx,link2 in enumerate(relative_links):
					while link2.startswith('/'):
						link2 = link2[1:]
					relative_links[idx] = link2
			
				# add base url eg http://www.base.ro/ + download 
				base_link = get_base_link(self.link)
				relative_links = map(lambda x: base_link + x, relative_links)
	
				# check for absolute links
				absolute_links = re.findall(Site.ABSOLUTE_REGEX, response.content)

				del_idx = []			
				for idx, link in enumerate(absolute_links):

					if len(re.findall(link, base_link)) > 0:
						if link not in relative_links:
							relative_links.append(link)
						del_idx.append(idx)	
	
				for idx in del_idx:
					del absolute_links[idx]
		
				self.relative_links = relative_links
				self.absolute_links = absolute_links	
				logging.info('Url: %s loaded succesfully!' % self.link)
		
				#handle words
				sentences = re.findall(Site.SENTENCE_REGEX, response.content, "UTF-8")
				words = []

				for sentence in sentences:
					re.sub(r'(.*>|</.*)', sentence, '')
					words.extend(re.findall(Site.WORD_REGEX, sentence))

				for word in words:
					if word in self.words.keys():
						self.words[word] += 1
					else:
						self.words[word] = 1
				
				# set frequency
				for word in self.words.keys():
					self.words[word] = int( ( self.words[word]/float(len(words)) )*100)
					if self.words[word] == 0:	
						self.words[word] = 1	
			else:
				logging.error('Error while loading url: %s' % self.link)
				raise SiteError({'message':'There was a problem loading the site', 'link':self.link})
		except Exception as e:
			raise SiteError(e)
			logging.error('Error while loading url: %s' % self.url)



class SiteSpider(threading.Thread):
	
	def __init__(self, link, anonimously = False, base = True):
		super(SiteSpider, self).__init__()
		self.link = link	

		if not self.link.endswith('/'):
			self.link = self.link + '/'
	 
		try:
			base_link = get_base_link(self.link)
		except Exception as e:
			logging.critical('Error when getting link: %s' % link)
			base_link = 'http://bad_url'

		self.database = Database()

		
		self.to_visit = Queue()
		if base:
			self.to_visit.push(base_link)
		self.to_visit.push(self.link)
		self.visited  = Queue()
	
		self.relative_links = []
		self.absolute_links = []
	
		self.anonimously = anonimously
		
	def load(self):
		try:		
			while len(self.to_visit) > 0:
				l = self.to_visit.top()
				self.load_page(l)
				self.visited.push(l)
				self.to_visit.pop()
			
		except Exception as e:
			print 'Error: ', e
			logging.critical('Error: %s while initiaing crawling')
		finally:
			self.relative_links = self.visited
			


	def load_page(self, link):

		try:
			site = Site(link, anonimously=self.anonimously)	
			site.load()

			
			relative_links = site.relative_links
			absolute_links = site.absolute_links			

			for link2 in relative_links:
				if self.visited.contains(link2) or self.to_visit.contains(link2):
					continue
				else:
					self.to_visit.push(link2)

			for link2 in absolute_links:
			
				if link2 not in self.absolute_links:
					self.absolute_links.append(link2)
			print link
			self.database.add_site(link=site.link, title=site.description, words=site.words)
			
		except SiteError as e:
			print 'Error!', e
			logging.error("Error:%s while loading link: %s" % (e.args, link))	


		
	def run(self):
		logging.debug('Starting to crawl site: %s' % self.link)
		self.load()

	def __del__(self):
		del self.database

class WebSpider(object):

	LINK_REGEX = 'http[s]{0,1}://.*'
	
	def __init__(self, max_threads=10):
		super(WebSpider, self).__init__()
		self.max_threads = max_threads

	def load(self, **kwargs):
		logging.info('Starting webspider...')
		urls = Queue()
		spiders = []
		absolute_urls = []

		if 'url' in kwargs:
			absolute_urls = re.findall(WebSpider.LINK_REGEX, kwargs['url'])	
		elif 'file' in kwargs:
			try:
				file = open(kwargs['file'], 'r')
				absolute_urls = re.findall(WebSpider.LINK_REGEX, file.read())
			except IOError as e:
				logging.error(e.message)
			finally:
				file.close()
		
		if len(absolute_urls) < 0:
			logging.critical('No valid links found.... (...closing...)')	
		else:
			logging.info('Found links: %s' % absolute_urls)	
			for url in absolute_urls:
				urls.push(url)

			while len(urls) > 0 or self.has_alive_spiders(spiders):
				if len(spiders) < self.max_threads:
					while len(spiders) < 10 and len(urls) > 0:
						spider = SiteSpider(urls.pop())
						spider.start()
						spiders.append(spider)
				
				for idx, spider in enumerate(spiders):					
					if spider.isAlive():
						continue
					else:
						logging.debug('Spider finished')		
						logging.debug('Found absolutes: %s from link: %s' % (str(spider.absolute_links), spider.link))
						print 'Found absolutes: %s from link: %s' % (str(spider.absolute_links), spider.link)			
	
						for url in spider.absolute_links:
							urls.push(url)
						try:	
							spiders[idx] = SiteSpider(urls.pop())
							spiders[idx].start()
						except Exception as e:
							logging.error(e)
									
	def has_alive_spiders(self, spiders):
		for spider in spiders:
			if spider.isAlive():
				return True
		return False
