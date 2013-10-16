# -*- coding: utf-8 -*-

import bson.objectid
import datetime
import logging
import os
import re
import StringIO
from bson.objectid import ObjectId

import Image
import pymongo

def get_good_image_ids():
    db = pymongo.MongoClient().kuke
    ids = set()
    for thing in db.things.find():
        for image_id in thing['image_ids']:
            ids.add(image_id)
    print 'good record', len(ids)
    return ids

def filter_good(good_set):
    file_remove_count = 0
    record_count = 0
    record_remove_count = 0

    bad_set = set()
    db = pymongo.MongoClient().kuke
    for image in db.images.find():
        record_count += 1
        if image['_id'] not in good_set:
            bad_set.add(image['_id'])

            try:
                os.remove('../static/data/%s%s' % (str(image['_id']), image['ext']))
                file_remove_count += 1
            except:
                pass

            try:
                os.remove('../static/data/%s.min.jpg' % str(image['_id']))
                file_remove_count += 1
            except:
                pass

    db.images.remove({'_id': {'$in': list(bad_set)}})

    print 'total record', record_count
    print 'record remove', record_remove_count
    print 'file remove', file_remove_count

def main():
    good_set = get_good_image_ids()
    filter_good(good_set)

if __name__ == '__main__':
    main()
