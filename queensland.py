import json
import re
import traceback

from abodeapi.utils import read_json_file, read_file, get_url
from abodeapi.rental import Rental
from bs4 import BeautifulSoup
from abodeapi.api import upload_rental, add_user, find_rentaltypes, find_locations
from abodeapi import rentaltypes_dic, location
import requests



def process():

    count = 1
    errors = 0
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    for num in range(1, 70):
        r = requests.post("http://www.queensland.com/api/Search/ResultsList",
                          data=    {'TargetItemId':'7FA9F2AF451D4567B5BA31098E8ECB45',
                                    'PageItemId': 'D7016A9C180E4D34A038A7E17B46E154',
                                    'Page': num,
                                    'pageTotal': 70,
                                    'SearchGroups':'12156D00AAD1461DB7F463288C87555D',
                                    'OrderBy1': '',
                                    'PageSize':10,
                                    'searchPanelAnchor': '#spanel',
                                    'search-groups-mobile': 'accomm',
                                    'keywords':'',
                                    'categories':'selfc',
                                    'maxprice': 4000,
                                    'minprice': 1,
                                    'pricefrom': '',
                                    'priceto': '',
                                    'starratingfilter':'',
                                    'destinations':'',
                                    'locations':''},
                          headers=headers)

        json_response = json.loads(r.text)

        for response in json_response['Results']:

            print "[+][%s][%s][%s] Starting ..." % (num, count, errors)

            try:
                rental = get_rental(response)

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
                    print "[+][%s][%s][%s] Completed" % (num, count, rental_id)
                else:
                    print "[+][%s][%s][%s] is an hotel, motel or resort" % (num, count, rental.title)

            except Exception as e:
                print "[E][%s][%s][%s] Completed with Error !" % (num, count, errors)
                print e
                errors += 1
                tb = traceback.format_exc()
                print "Trace:"
                print tb


            count += 1

def get_rental(search):

    rental = Rental()

    url = "http://www.queensland.com/%s" % search['ReadMoreUrlMarket']
    rental.source = url

    print "[+] Fetching %s " % url

    # title
    rental.title = search["Title"]

    # lat, lng
    rental.lat = search["Locations"][0]['GeoLat']
    rental.long= search["Locations"][0]['GeoLng']

    # Rates
    rates_raw = search["Price"]
    rental.rates = re.match(".*AU\$(\d+).*", rates_raw).group(1)

    rental.description_about = search["Description"].encode('ascii', 'ignore')

    #html_doc = read_file("queensland/html/myella-farm-stay.html")
    html_doc, code = get_url(url)
    soup = BeautifulSoup(html_doc, 'html.parser')

    contact_details = soup.findAll("div", {"class", "contact-detail"})

    #print(contact_details)

    for contact_detail in contact_details:

        # get website
        try:
            on_click = str(contact_detail.findAll("a")[0]['onclick'])
            if on_click.find("Product Website Link") > -1 :
                rental.url = contact_detail.findAll("a")[0]['href']
        except:
            pass

        # get email
        try:
            on_click = str(contact_detail.findAll("a")[0]['onclick'])
            if on_click.find("Product Email Link") > -1:
                rental.email = contact_detail.findAll("a")[0]['href'].split(":")[1]
        except:
            pass

        # get phone
        try:
            on_click = str(contact_detail.findAll("a")[0]['onclick'])
            if on_click.find("Product Phone Link") > -1:
                rental.phone = contact_detail.findAll("a")[0]['href'].split(":")[1]
        except:
            pass


        # address
        try:
            rental.address = contact_detail.findAll("address")[0].text.split("\n")[1].strip()
        except:
            pass


    # lets figure out rentaltypes
    main_content_doc = (soup.findAll("div", {"class": "body-container"}))[0].text
    rental.rentaltype_id = find_rentaltypes(main_content_doc)
    rental.feature_ids = find_locations(main_content_doc)

    # pictures
    pictures_container = (soup.findAll("div", {"class": "atdw-product-multimedia-gallery"}))[0]
    pictures_raw = pictures_container.select('a[href^=https://assets.atdw-online.com]')

    for picture_raw in pictures_raw:
        href = picture_raw['href'].split('?')[0]
        rental.images.append(href)

    # features
    try:
        internets = (soup.findAll("div", {"class": "atdw-product-internet-points"}))[0].findAll("li")
        for internet in internets:
            rental.facilities.append(internet.text.strip().strip("\n"))
    except:
        print "[E] no internet available"

    features = (soup.findAll("div", {"class": "atdw-product-attributeListing"}))[0].findAll("li")
    for feature in features:
        rental.facilities.append(feature.text.strip().strip("\n"))

    return rental