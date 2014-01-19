import psycopg2
from psycopg2.extras import DictCursor
import threading
import logging

logging.basicConfig(filename='search_engine.log', format='%(asctime)s %(levelname)s:%(message)s.\n', level=logging.DEBUG)

try:
	file = open('search_engine.log', 'w')
	file.write('')
	file.close()
except IOError as e:
	pass


class DatabaseError(Exception):
	pass

class Database(object):
	
	def __init__(self, host='127.0.0.1'):
		self.connection = psycopg2.connect('host=%s port=5432 dbname=search_engine user=spider password=spid3rp@ss'%host)
		
	def __del__(self):
		self.connection.close()

	def add_site(self, link, title, words):
		if link is None or title is None or words is None or len(words) == 0:
			raise DatabaseError('Not enough information to add site: link: %s title: %s words: %s' % (link, title, str(words)))
		else:
			cursor = None
			try:
			
				logging.debug('About to add site: link: %s title: %s words: %s' % (link, title, str(words)))
				cursor = self.connection.cursor(cursor_factory = DictCursor)
				
				cursor.execute("""insert into sites(link, title) values(%(link)s, %(title)s ) """, {'link':link, 'title':title})
				self.connection.commit()
				for word, frequency in words.items():
					try:
						try:
							cursor.execute("""insert into words(text) values(%(text)s)""", {'text':word})
							self.connection.commit()
						except Exception as e:
							self.connection.rollback()
						cursor.execute("""insert into contents(site_id, word_id, frequency) values((select id from sites where link = %(link)s), (select id from words where text = %(word)s), %(freq)s)""", {'link':link,'word':word,'freq':frequency})
						self.connection.commit()
					except Exception as e:
						self.connection.rollback()
						logging.error('Error: %s when inserting word: %s' %(str(e), word))
							
				logging.debug('Added site: link: %s title: %s words: %s' % (link, title, str(words)))
			except Exception as e:
				if self.connection is not None:
					self.connection.rollback()
				logging.error('Error Failed to add site:%s link: %s title: %s words: %s' % (str(e),link, title, str(words)))
			finally:
				if cursor is not None:
					cursor.close()
				
	def search(self, words, limit = 20):
		if words is None or len(words) == 0:
			raise DatabaseError('Not enough information to search: words: %s' % (str(words)))
		sites = []
		cursor = None
		
		# for performance
		self.remove_duplicates(words)
		try:

			cursor = self.connection.cursor(cursor_factory = DictCursor)
		
			# first select sites whose link contains the word
			for word in words:
				try:
					cursor.execute("""select link from sites where link ~* %(word)s""", {'word':'\w*'+word+'\w*'})
					rows = cursor.fetchall
					for row in rows:
						sites.extend([row['link']])
				except Exception as e:
					logging.error('Error: %s while searchcing for: %s' %(str(e), str(words)))

			# second select those whose title contains the word
			for word in words:
				try:
					cursor.execute("""select link from sites where title ~* %(title)s""", {'title':'\w*'+word+'\w*'})
					rows = cursor.fetchall()
					for row in rows:
						sites.extend([row['link']])		
				except Exception as e: 
					logging.error('Error: %s while searchcing for: %s' %(str(e), str(words)))
			
			# third select words
			for word in words:
				try:
					cursor.execute("""select sites.link from sites where id in (select site_id from contents where word_id = (select id from words where text = %(word)s))""", {'word':word})
					rows = cursor.fetchall()
					for row in rows:
						sites.extend([row['link']])
				except Exception as e:
					logging.error('Error: %s while searchcing for: %s' %(str(e), str(words)))

			
		except Exception as e:
			logging.error('Error: %s while searchcing for: %s' %(str(e), str(words)))
		finally:
			if cursor is not None:
				cursor.close()
			
			self.remove_duplicates(sites)
			return sites[:limit] if limit > 0 else sites
	

	def remove_duplicates(self,l):
		return [ x for idx, x in enumerate(l) if idx == l.index(x) ]	
