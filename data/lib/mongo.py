import os
import motor
import functools
import tornado.gen

from pymongo import MongoClient


mongo_user  = os.getenv('MONGO_USER')
mongo_pass  = os.getenv('MONGO_PASSWORD')
mongo_host  = os.getenv('MONGO_HOST')
mongo_port  = os.getenv('MONGO_PORT')
mongo_db    = os.getenv('MONGO_DB')
mongo_limit = int(os.getenv('MONGO_LIMIT'))

mongo_uri = "mongodb://%s:%s@%s:%s/%s" % (mongo_user, mongo_pass,
        mongo_host, mongo_port, mongo_db)

def mongo_aync():
    return motor.MotorClient(host=mongo_uri).open_sync()[mongo_db]

def mongo_sync():
    return MongoClient(mongo_uri)[mongo_db]

class MongoQuery:
    def __init__(self, model=None, model_functions=None):
        self.collection = mongo_aync()[model.get_collection()]
        self.model = model
        self.model_functions = model_functions

    @tornado.gen.engine
    def execute(self, args, page=0, limit=mongo_limit, callback=None):

        arguments = self.build_mongo_query(args)
        cursor = self.collection.find(arguments)
        if not 0 < limit < mongo_limit:
            limit = mongo_limit
        cursor.limit(limit).skip(limit * page)
        results = []
        # I don't like the generator model here ... It hides what
        # the code is doing which is an async callback on the ioloop...
        # But can't see a good way to handle it with current callback model
        while (yield cursor.fetch_next):
            results.append(cursor.next_object())
        response = [self.model.build_response_dict(result) for result in results]
        callback(response)

    def build_mongo_query(self, arguments):
        # slug is a list, each with (key, value)
        if [func for func in dir(self.model_functions) if not "__" in func]:
            slug = {}
            for key, value in arguments.iteritems():
                new_key, new_value = self.attr_func_wrap(key, value)
                if new_key in slug:
                    slug[new_key].update(new_value)
                else:
                    slug[new_key] = new_value
            return slug
        return arguments
    
    def attr_func_wrap(self, key, value):
        func = getattr(self.model_functions, key)
        key, value = func(value)
        return key, value
