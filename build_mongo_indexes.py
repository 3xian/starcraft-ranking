import pymongo

def main():
    db = pymongo.MongoClient().kuke
    db.users.ensure_index('uid')
    db.things.ensure_index([('date', pymongo.DESCENDING)])
    db.things.ensure_index([('visit', pymongo.DESCENDING)])
    db.things.ensure_index([('favor', pymongo.DESCENDING)])
    db.things.ensure_index([('tags', pymongo.ASCENDING), ('date', pymongo.DESCENDING)])
    db.comments.ensure_index([('tid', pymongo.ASCENDING), ('date', pymongo.DESCENDING)])

if __name__ == '__main__':
    main()
