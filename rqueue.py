'''
File: queue.py
Author: Andrei Ro
Description: 
'''



class Queue(object):
	"""Simple Queue class"""


	def __init__(self):
		super(Queue, self).__init__()
		self._queue = []

	def top(self):
		"""returns the first item to be removed"""
	
		if len(self._queue) <= 0:
			raise ValueError("Queue is empty. Cannot call top()!")
		else:
			return self._queue[0]

	def pop(self):
		"""removes the element on top"""
	
		if len(self._queue) <= 0:
			raise ValueError("Queue is empty. Cannot call remove")
	
		element = self._queue[0]
		del self._queue[0]
		
		return element

	def push(self, element):
		"""adds an item"""
		self._queue.append(element)

	def __len__(self):
		return len(self._queue)

	
	def contains(self, element):
		return element in self._queue

	def __repr__(self):
		print '['
		for element in self._queue:
			print element, ', '

		print ']'

	def __str__(self):
		s =  '['
		for element in self._queue:
			s += str(element) +  ', '

		s +=  ']'

		return s
