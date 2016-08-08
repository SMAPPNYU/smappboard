'''
a model representing a permission object

http://api.mongodb.org/python/current/api/
http://stackoverflow.com/questions/12179271/python-classmethod-and-staticmethod-for-beginner

'''

import pymongo

class Permission(object):
	collection_name=''
	permitted_users=[]

	def __init__(self, host, collection_name, permitted_users):
		self.collection_name = collection_name
		self.permitted_users = permitted_users
		self.mongo = pymongo.MongoClient(host)

	def add_permission():
		pass
		