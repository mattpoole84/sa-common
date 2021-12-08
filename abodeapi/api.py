import re

from bs4 import BeautifulSoup
import requests

from abodeapi.utils import post_url, put_url, get_url, write_bin_file, download_file
import json

from abodeapi import rentaltypes_dic, location



def add_user(rental):
    params = {
        "inputName": rental.email.split("@")[0],
        "inputEmail": rental.email.strip(),
        "inputPassword": "auto"
    }
    text, code = post_url("http://localhost:8080/api/v1/user", params)


def get_url_from_website(url):
        linked_doc, code = get_url(url)
        linked_soup = BeautifulSoup(linked_doc, 'html.parser')
        mailtos = linked_soup.select('a[href^=mailto]')
        if len(mailtos) > 0:
            return mailtos[0]['href'].split(":")[1]
        else:
            return ""


def upload_rental(rental):

    rental_id = _upload_basic(rental)
    print '[+] Rental ID: %s ' % rental_id
    if rental_id is not None:
        _upload_descriptions(rental, rental_id)
        _upload_images_aync(rental, rental_id)
        _upload_features(rental, rental_id)
        _upload_location(rental, rental_id)
        _update_status(rental_id)
    else:
        print '[E] Accommodation %s error uploading source ' % rental.source

    return rental_id

def _upload_basic(rental):
    #
    # basic accommodation
    #
    params = {
        "inputType": rental.rentaltype_id,
        "inputOwneremail": rental.email.strip(),
        "inputRentalemail": rental.email.strip(),
        "inputRentalphone": rental.phone.strip(),
        "inputUrl": rental.url.strip(),
        "inputSource": rental.source,
        "inputRateRaw": rental.rates

    }

    text, code = post_url("http://localhost:8080/api/v1/rental", params)
    if code != 201:
        print "[E] OBJECT NOT CREATED"
        print "url"
        print "http://localhost:8080/api/v1/rental"
        print "Params"
        print params
        print "Response"
        print code
        print text
        rental_id = None
    else:
        rentaljson = json.loads(text)
        rental_id = rentaljson['id']
    return rental_id


def _upload_images_aync(rental, rental_id):
    #
    # Upload images
    #
    for image in rental.images:
        #print "UPLOADING ASYNC IMAGE:" + image
        params = {
            "rental_id": rental_id,
            "url": image
        }
        text, code = post_url("http://localhost:8080/api/v1/rental/%s/picture_async" % rental_id, params)

        if code != 200:
            print "[E] OBJECT NOT UPDATED"
            print "url"
            print "http://localhost:8080/api/v1/rental/%s/picture" % rental_id
            print "Params"
            print params
            print "Response"
            print code
            print text


def _upload_images(rental, rental_id):
    #
    # Upload images
    #
    for image in rental.images:
        data = download_file(image)
        filename = image.split('/')[-1]
        write_bin_file("/tmp/%s" % filename, data)
        files = {'file': open("/tmp/%s" % filename, 'rb')}

        params = {
            "rental_id": rental_id
        }
        text, code = post_url("http://localhost:8080/api/v1/rental/%s/picture" % rental_id, params, file=files)

        if code != 200:
            print "[E] OBJECT NOT UPDATED"
            print "url"
            print "http://localhost:8080/api/v1/rental/%s/picture" % rental_id
            print "Params"
            print params
            print "Response"
            print code
            print text


def _upload_descriptions(rental, rental_id):
    #
    # descriptions
    #
    params = {
        "langPosition": 0,
        "inputSummary": rental.title,
        "inputTexts[1]": rental.description_about,
        "inputTexts[2]": rental.description_surrounds
    }

    text, code = put_url("http://localhost:8080/api/v1/rental/%s/description" % rental_id, params)
    if code != 200:
        print "[E] OBJECT NOT UPDATED"
        print "url"
        print "http://localhost:8080/api/v1/rental/%s/description" % rental_id
        print "Params"
        print params
        print "Response"
        print code
        print text

def _upload_features(rental, rental_id):
    #
    # descriptions
    #

    params = {}

    # feature raw
    count = 0
    for feature_raw in rental.facilities:
        params['inputFeatureraw[%s]' % count] = feature_raw
        count +=1


    # feature id
    for feature_id in rental.feature_ids:
        params['inputFeature[%s]' % feature_id] = 1


    text, code = put_url("http://localhost:8080/api/v1/rental/%s/feature" % rental_id, params)
    if code != 200:
        print "[E] OBJECT NOT UPDATED"
        print "url"
        print "http://localhost:8080/api/v1/rental/%s/feature" % rental_id
        print "Params"
        print params
        print "Response"
        print code
        print text

def _upload_location(rental, rental_id):
    #
    # locations
    #

    # march agains the region
    text_json, code = get_url("http://localhost:8080/api/region/geo?lng=%s&lat=%s" % (rental.long, rental.lat))
    region = json.loads(text_json);

    #
    params = {
         "inputRegion": region['id'],
         "inputAddress": rental.address,
         "inputLatitude": rental.lat,
         "inputLongitude": rental.long,
         "inputShowPublicLocation": 1
      }

    text, code = put_url("http://localhost:8080/api/v1/rental/%s/location" % rental_id, params)
    if code != 200:
        print "[E] OBJECT NOT UPDATED"
        print "url"
        print "http://localhost:8080/api/v1/rental/%s/location" % rental_id
        print "Params"
        print params
        print "Response"
        print code
        print text


def _update_status(rental_id):
    #
    # status
    #

    params = {
        # "rentalstatus_id": 4 # active
        "rentalstatus_id": 7  # paused
    }

    text, code = put_url("http://localhost:8080/api/v1/rental/%s/status" % rental_id, params)
    if code != 200:
        print "[E] OBJECT NOT UPDATED"
        print "url"
        print "http://localhost:8080/api/v1/rental/%s/status" % rental_id
        print "Params"
        print params
        print "Response"
        print code
        print text


def find_rentaltypes(hmtl_doc):
    rentaltype_id = -1
    for rentaltype in rentaltypes_dic.keys():
        if re.search(r"\b" + re.escape(rentaltype) + r"\b", hmtl_doc, re.IGNORECASE):
            rentaltype_id = rentaltypes_dic[rentaltype]
            break

    return rentaltype_id

def find_locations(hmtl_doc):
    feature_ids = []
    for location_key in location.keys():
        if re.search(r"\b" + re.escape(location_key) + r"\b", hmtl_doc, re.IGNORECASE):
            #rental.feature_ids.append(location[location_key])
            feature_ids.append(location[location_key])
    return feature_ids