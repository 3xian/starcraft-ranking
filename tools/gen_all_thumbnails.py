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
import qrcode

def main():
    db = pymongo.MongoClient().kuke
    for image in db.images.find():
        image_id = str(image['_id'])
        img = Image.open('../static/data/%s%s' % (image_id, image['ext']))
        width, height = img.size
        logging.info('image size: (%d, %d)' % (width, height))
        if width > 300:
            try:
                new_width = 300
                new_height = height * new_width / width
                logging.info('thumbnail size: (%d, %d)' % (new_width, new_height))
                min_image_path = os.path.join('../static/data', image_id+'.min.png')
                img.resize((new_width, new_height)).save(min_image_path, 'PNG')
                db.images.update({'_id': image['_id']}, {'$set': {'thumbnail': 1}})
            except:
                logging.warning('fail to convert %s', str(image))

if __name__ == '__main__':
    main()
