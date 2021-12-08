# Download from
# http://www.visitnsw.com/accommodation-self-contained
#
# curl 'http://www.visitnsw.com/dnsw_atlas/ajax/products' --data 'page_number=1&page_size=32&categories=ACCOMM&classifications=APARTMENT&region=NSW&alt_title=Self+Contained+Accommodation&order_by=random_20161104'

import re

from bs4 import BeautifulSoup

from abodeapi.api import upload_rental, add_user, find_rentaltypes, find_locations
from abodeapi.rental import Rental
import requests, json

from abodeapi.utils import get_url
import traceback

def process():
    count = 1
    errors = 0
    for num in range(1, 63):
        r = requests.post("http://www.visitnsw.com/dnsw_atlas/ajax/products",
                          data={'page_number': num, 'page_size': 32, 'categories': 'ACCOMM',
                                'classifications': 'APARTMENT', 'region': 'NSW',
                                'alt_title': 'Self+Contained+Accommodation', 'order_by': 'random_20161109'})
        json_response = json.loads(r.text)

        for response in json_response['json']:
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




# print(r.status_code, r.reason)
# print(r.text)

# print (search_response_raw['total'])
# print (search_response_raw['products'])
# print (search_response_raw['json'])

# URLS. Eg
#    {
#       "id": "56b244463ed14ca74532203e",
#       "name": "Beachfront Apartments",
#       "description": "<p itemprop=\"description\" class=\"prod-desc\"><span class=\"rates\">From $60 per night<\/span>Beachfront Apartments have eight fully self-contained two bedroom holiday units in a quiet section of the Fishpen. Each unit has full kitchen facilities, a bathroom with separate bath and separate toilet. There is...<\/p>\n",
#       "web_path": "beachfront-apartments",
#       "image": "https:\/\/assets.atdw-online.com.au\/images\/ATDW_Large_Landscape__9139429_FZ63_Garden_1_rq3rdlt.JPG?rect=0,0,800,600&w=280&h=210",
#       "type": "accommodation",
#       "product_type": "accommodation",
#       "lat": "-36.8978",
#       "long": "149.911972",
#       "region": "South Coast",
#       "area": "Merimbula And Sapphire Coast",
#       "town": "Merimbula",
#       "address1": "53 Ocean Drive",
#       "address2": "",
#       "suburb": "Merimbula",
#       "state": "NSW",
#       "postcode": "2548"
#       },
#
# Converts to http://www.visitnsw.com/destinations/south-coast/merimbula-and-sapphire-coast/merimbula/accommodation/beachfront-apartments
def get_accommodation_url(s):
    return "http://www.visitnsw.com/destinations/" + s['region'].lower().replace(" ", "-") + "/" + s['area'].lower().replace(" ", "-") + "/" + s[
        'town'].lower().replace(" ", "-") + "/" + s['type'] + "/" + \
           s['web_path']


#
# get details for first apartment
# print(get_url(get_accommodation_url(search_response_raw['json'][0])))
# write_file("html/accommodation_beachfront_apartments.html", get_url(get_accommodation_url(search_response_raw['json'][0])))
#


def get_rental(search):
    rental = Rental()

    # print
    # print "================================="
    # print "oldObject"
    # print rental
    # print "================================="
    # print

    url = get_accommodation_url(search)
    rental.source = url

    print "[+] Fetching %s " % url

    # Parse accommodation
    # html_doc = read_file("visitnsw/html/accommodation_beachfront_apartments.html")
    html_doc, code = get_url(url)
    soup = BeautifulSoup(html_doc, 'html.parser')

    # url
    try:
        rental.url = soup.findAll("a", {"itemprop", "url"})[0]['href']
    except:
        print "[E] no url available"

    # phone
    try:
        phone_raw = soup.findAll("span", {"class", "tel"})[0].text
        rental.phone = ''.join(c for c in phone_raw if c.isdigit())
    except:
        print "[W] Phone not found %s" % rental.url

    # lat, long
    rental.lat = search['lat']
    rental.long = search['long']

    # rates
    desc = BeautifulSoup(search['description'], 'html.parser')
    rates_raw = desc.findAll("span", {"class", "rates"})[0].text
    rental.rates = re.match(".*\$(\d+).*", rates_raw).group(1)

    # address
    rental.address = search['address1']

    # get title
    title_raw = soup.findAll("h1", {"class": "main-heading"})
    rental.title = title_raw[0].text.split("-")[0]

    # get about
    description_raw = soup.findAll("section", {"class": "about-block"})
    rental.description_about = description_raw[0].p.text

    # get facilities
    try:
        custom_details = soup.findAll("section", {"class": "content-widget custom-details"})
        facilities = custom_details[0].ul.findAll("li")
        for facility in facilities:
            rental.facilities.append(facility.text)

        # more random stuff
        # get more about
        custom_details_desc = custom_details[0].findAll("td", {"colspan": "2"})

        rental.description_about = rental.description_about + "<br><br>" + custom_details_desc[0].text

        facilities_raw = custom_details_desc[0].text.split("Facilities:")[1]
        rental.facilities = rental.facilities + re.split(r',|and', facilities_raw)
    except:
        print "[W] Problem with facilities, and extra description%s" % rental.url

    # images
    images = soup.findAll("div", {"class": "product-gallery"})[0].findAll("img")
    for image in images:
        rental.images.append(image['src'].split('?')[0])

    # email
    try:
        rental.email = soup.findAll("a", {"class": "ga_URL_lead_email"})[0]['href'].split(":")[1]
    except:
        print "[E] email not found, trying to get from url %s" % rental.url
        if rental.url is not None and rental.url != "":
            linked_doc, code = get_url(rental.url)
            linked_soup = BeautifulSoup(linked_doc, 'html.parser')
            mailtos = linked_soup.select('a[href^=mailto]')
            if len(mailtos) > 0:
                rental.email = mailtos[0]['href'].split(":")[1]

    # lets figure out rentaltypes
    main_content_doc = (soup.findAll("div", {"class": "product-detail"}))[0].text
    rental.rentaltype_id = find_rentaltypes(main_content_doc)
    rental.feature_ids = find_locations(main_content_doc)


    # print
    # print "================================="
    # print "newObject"
    # print rental
    # print "================================="
    # print

    return rental

# print
# print
# print rental
