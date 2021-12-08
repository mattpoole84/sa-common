import json
import re
import traceback

from abodeapi.utils import read_json_file, read_file, get_url
from abodeapi.rental import Rental
from bs4 import BeautifulSoup
from abodeapi.api import upload_rental, add_user, find_rentaltypes, find_locations, get_url_from_website
from abodeapi import rentaltypes_dic, location
import requests



def process():

    count = 1
    errors = 0
    #for num in range(1, 70):

    r = requests.get("http://localhost/api/atlas/products?key=0dfc86d738034026ba99a8c7407ab2fe&cla=APARTMENT,HOLHOUSE&out=json&size=7107")
    #r = requests.get("http://localhost/api/atlas/products?key=0dfc86d738034026ba99a8c7407ab2fe&cla=APARTMENT,HOLHOUSE&out=json&size=10")

    json_response = json.loads(r.text)

    #print(json_response)

    for response in json_response['products']:
        print "==========================="
        try:
            #print (response)
            #
            #print "[+][%s][%s][%s] Starting ..." % (num, count, errors)
            rental = get_rental(response)

            #print(rental)


            # create user
            add_user(rental)

            upload = True
            for banned in ["hotel", "motel", "resort"]:
                if banned in rental.title.lower():
                    upload = False
                    break

            # create accommodation
            if upload:
                rental_id = upload_rental(rental)
                print "[+][%s][%s][%s] Completed" % (count, errors, rental_id)
            else:
                print "[+][%s][%s][%s] is an hotel, motel or resort" % (count, errors, rental.title)
        except Exception as e:
            print "[E][%s][%s] Completed with Error !" % (count, errors)
            print e
            errors += 1
            tb = traceback.format_exc()
            print "Trace:"
            print tb
        count += 1

    # for response in json_response['Results']:
    #
    #     print "[+][%s][%s][%s] Starting ..." % (num, count, errors)
    #
    #     try:
    #         rental = get_rental(response)
    #
    #         # create user
    #         add_user(rental)
    #
    #
    #         upload = True
    #         for banned in ["hotel", "motel", "resort"]:
    #             if banned in rental.title.lower():
    #                 upload = False
    #                 break
    #
    #
    #         # create accommodation
    #         if upload:
    #             rental_id = upload_rental(rental)
    #             print "[+][%s][%s][%s] Completed" % (num, count, rental_id)
    #         else:
    #             print "[+][%s][%s][%s] is an hotel, motel or resort" % (num, count, rental.title)
    #
    #     except Exception as e:
    #         print "[E][%s][%s][%s] Completed with Error !" % (num, count, errors)
    #         print e
    #         errors += 1
    #         tb = traceback.format_exc()
    #         print "Trace:"
    #         print tb




def get_rental(search):

    rental = Rental()

    url = "http://localhost/api/atlas/product?key=0dfc86d738034026ba99a8c7407ab2fe&productId=" + search["productId"] + "&out=json"
    rental.source = url

    print "[+] Fetching %s " % url

    rental_raw = requests.get(url)
    rentaldata = json.loads(rental_raw.text)

    #print ("rental json_response")
    #print (rental_raw.text)

    # title
    rental.title = rentaldata["productName"]

    # lat, lng
    rental.lat = rentaldata["addresses"][0]['geocodeGdaLatitude']
    rental.long= rentaldata["addresses"][0]['geocodeGdaLongitude']

    # Rates
    rental.rates = rentaldata["rates"][0]["priceFrom"].encode('ascii', 'ignore').decode('ascii')

    rental.description_about = rentaldata["productDescription"].encode('ascii', 'ignore').decode('ascii')

    rental.address = rentaldata["addresses"][0]["addressLine1"] + "  " + rentaldata["addresses"][0]["addressLine2"]

    for facility in rentaldata["attributes"]:
        rental.facilities.append(facility["attributeIdDescription"].encode('ascii', 'ignore').decode('ascii'))


    for mutimedia in rentaldata["multimedia"]:
        if mutimedia["attributeIdMultimediaContent"] == "IMAGE":
            image_path = mutimedia["serverPath"].split('?')[0]
            if image_path not in rental.images:
                rental.images.append(mutimedia["serverPath"].split('?')[0])

    for internet in rentaldata["internetPoints"]:
        rental.facilities.append(internet["attributeIdAddressDescription"].encode('ascii', 'ignore').decode('ascii'))

    for service in rentaldata["services"]:
        rental.description_about += "\n\n"
        rental.description_about += service["serviceName"].encode('ascii', 'ignore').decode('ascii')
        rental.description_about += "\n\n"
        rental.description_about += service["serviceDescription"].encode('ascii', 'ignore').decode('ascii')

        # facilities
        for facility in service["serviceAttribute"]:
            rental.facilities.append(facility["attributeIdDescription"].encode('ascii', 'ignore').decode('ascii'))

        # facilities
        for mutimedia in service["serviceMultimedia"]:
            if mutimedia["attributeIdMultimediaContent"] == "IMAGE":
                image_path = mutimedia["serverPath"].split('?')[0]
                if image_path not in rental.images:
                    rental.images.append(mutimedia["serverPath"].split('?')[0])

    for producttype in rentaldata["verticalClassifications"]:
        rentaltype_id = find_rentaltypes(producttype["productTypeId"])
        if rentaltype_id != -1:
            rental.rentaltype_id = rentaltype_id

    for communication in rentaldata["communication"]:

        if rental.phone == "" and communication["attributeIdCommunication"] == "CAMBENQUIR":
            rental.phone = communication["communicationDetail"]

        if rental.phone == "" and communication["attributeIdCommunication"] == "CAPHENQUIR":
            rental.phone = communication["communicationDetail"]

        if rental.email == "" and communication["attributeIdCommunication"] == "CAEMENQUIR":
            rental.email = communication["communicationDetail"]

        if rental.url == "" and communication["attributeIdCommunication"] == "CAURENQUIR":
            rental.url = communication["communicationDetail"]
            if rental.url[0:7] <> "http://":
                rental.url = "http://" + rental.url

    if rental.email == "" and rental.url <> "":
        print "[E] email not found, trying to get from url %s" % rental.url
        rental.email = get_url_from_website(rental.url)

    #
    # #html_doc = read_file("queensland/html/myella-farm-stay.html")
    # html_doc, code = get_url(url)
    # soup = BeautifulSoup(html_doc, 'html.parser')
    #
    # contact_details = soup.findAll("div", {"class", "contact-detail"})
    #
    # #print(contact_details)
    #
    # for contact_detail in contact_details:
    #
    #     # get website
    #     try:
    #         on_click = str(contact_detail.findAll("a")[0]['onclick'])
    #         if on_click.find("Product Website Link") > -1 :
    #             rental.url = contact_detail.findAll("a")[0]['href']
    #     except:
    #         pass
    #
    #     # get email
    #     try:
    #         on_click = str(contact_detail.findAll("a")[0]['onclick'])
    #         if on_click.find("Product Email Link") > -1:
    #             rental.email = contact_detail.findAll("a")[0]['href'].split(":")[1]
    #     except:
    #         pass
    #
    #     # get phone
    #     try:
    #         on_click = str(contact_detail.findAll("a")[0]['onclick'])
    #         if on_click.find("Product Phone Link") > -1:
    #             rental.phone = contact_detail.findAll("a")[0]['href'].split(":")[1]
    #     except:
    #         pass
    #
    #
    #     # address
    #     try:
    #         rental.address = contact_detail.findAll("address")[0].text.split("\n")[1].strip()
    #     except:
    #         pass
    #
    #
    # # lets figure out rentaltypes
    # main_content_doc = (soup.findAll("div", {"class": "body-container"}))[0].text
    # rental.rentaltype_id = find_rentaltypes(main_content_doc)
    # rental.feature_ids = find_locations(main_content_doc)
    #
    # # pictures
    # pictures_container = (soup.findAll("div", {"class": "atdw-product-multimedia-gallery"}))[0]
    # pictures_raw = pictures_container.select('a[href^=https://assets.atdw-online.com]')
    #
    # for picture_raw in pictures_raw:
    #     href = picture_raw['href'].split('?')[0]
    #     rental.images.append(href)
    #
    # # features
    # try:
    #     internets = (soup.findAll("div", {"class": "atdw-product-internet-points"}))[0].findAll("li")
    #     for internet in internets:
    #         rental.facilities.append(internet.text.strip().strip("\n"))
    # except:
    #     print "[E] no internet available"
    #
    # features = (soup.findAll("div", {"class": "atdw-product-attributeListing"}))[0].findAll("li")
    # for feature in features:
    #     rental.facilities.append(feature.text.strip().strip("\n"))

    return rental


def find_rentaltypes(hmtl_doc):
    rentaltype_id = -1
    for rentaltype in rentaltypes_dic.keys():
        if re.search(r"\b" + re.escape(rentaltype) + r"\b", hmtl_doc, re.IGNORECASE):
            rentaltype_id = rentaltypes_dic[rentaltype]
            break

    return rentaltype_id