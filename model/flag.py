# -*- coding: utf-8 -*-

from datetime import datetime
from bson import ObjectId

from corelib.store import get_cursor
from model.photo import Photo
from model.user import User

STATUS_PENDING = 'pending'
STATUS_PASS = 'pass'
STATUS_DELETE = 'delete'


class Flag(object):

    table = "photo_flag"

    def __init__(self, id, photo_id, author_id, text, create_time, status):
        self.id = id
        self.photo_id = photo_id
        self.author_id = author_id
        self.text = text
        self.create_time = create_time
        self.status = status

    @property
    def photo(self):
        return self.photo_id and Photo.get(self.photo_id)

    @property
    def author(self):
        return self.author_id and User.get(self.author_id)

    @classmethod
    def new(cls, photo_id, author_id, text):
        item = {
            'photo_id': photo_id,
            'author_id': author_id,
            'text': text,
            'create_time': datetime.now()
        }
        id = get_cursor(cls.table).insert(item, safe=True)
        if id:
            return cls.get(id)
        return None

    @classmethod
    def initialize(cls, item):
        if not item:
            return None
        id = str(item.get('_id', ''))
        photo_id = item.get('photo_id')
        author_id = item.get('author_id')
        text = item.get('text')
        create_time = item.get('create_time')
        if not (id and photo_id and author_id):
            return None
        return cls(id, photo_id, author_id, text, create_time)

    @classmethod
    def get(cls, id):
        query = {'_id': ObjectId(id)}
        item = get_cursor(cls.table).find_one(query)
        return cls.initialize(item)

    @classmethod
    def gets(cls, status=STATUS_PENDING, start=0, limit=10):
        query = {}
        if status:
            query['status'] = status
        rs = get_cursor(cls.table).find(query).sort('create_time', 1)\
                                  .skip(start).limit(limit)
        return filter(None, [cls.initialize(r) for r in rs])

    @classmethod
    def get_count(cls, status=STATUS_PENDING):
        query = {}
        if status:
            query['status'] = status
        return get_cursor(cls.table).find(query).count()

    @classmethod
    def get_by_user_and_photo(cls, user_id, photo_id):
        query = {
            'photo_id': photo_id,
            'author_id': author_id
        }
        item = get_cursor(cls.table).find_one(query)
        return cls.initialize(item)

    def audit(self, status=STATUS_PASS):
        query = {'_id': ObjectId(self.id)}
        update = {'status': status}
        get_cursor(cls.table).update(query, {'$set': update}, safe=True)

