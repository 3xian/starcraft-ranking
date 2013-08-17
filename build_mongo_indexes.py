import pymongo

def main():
    db = pymongo.MongoClient().kuke
    db.users.ensure_index('uid')
    db.things.ensure_index([('date', pymongo.DESCENDING)])
    db.things.ensure_index([('tags', pymongo.ASCENDING), ('date', pymongo.DESCENDING)])

if __name__ == '__main__':
    main()
