import urllib2

import requests, json



def post_url(url, payload, file = None):
    headers = {
        "apikey": "4242424242IUYE"
    }
    #print "URL: %s" % url
    #print "PARAMS: %s" % payload
    if file is not None:
        r = requests.post(url, params=payload, headers=headers, files=file)
    else:
        r = requests.post(url, params=payload, headers=headers)
    #print "CODE: %s" % r.status_code
    #print "TEXT: %s" % r.text

    return r.text, r.status_code


def put_url(url, payload):
    headers = {
        "apikey": "4242424242IUYE"
    }
    #print "URL: %s" % url
    #print "PARAMS: %s" % payload
    r = requests.put(url, params=payload, headers=headers)
    #print "CODE: %s" % r.status_code
    #print "TEXT: %s" % r.text

    return r.text, r.status_code


def get_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0',
        # 'From': 'youremail@domain.com'  # This is another valid field
    }
    r = requests.get(url, headers=headers)
    return r.text, r.status_code


def download_file(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0',
        # 'From': 'youremail@domain.com'  # This is another valid field
    }
    request = urllib2.Request(url, headers=headers)
    f = urllib2.urlopen(request)
    return f.read()


def read_json_file(path):
    with open(path) as json_data:
        d = json.load(json_data)
        return d


def read_file(path):
    file = open(path, 'r')
    return file.read()


def write_file(path, content):
    file = open(path, "w")
    file.write(content)
    file.close()


def write_bin_file(path, content):
    file = open(path, "wb")
    file.write(content)
    file.close()

