from re import match
from urllib2 import urlopen, Request, HTTPError
from urllib import urlencode
from simplejson import loads
 
username = "zeekay"
api_key  = "R_de915cb44ad6b8aaf74d3c55832829a8"
 
def expand(url):
    try:
        params = urlencode({'shortUrl': url, 'login': username, 'apiKey': api_key, 'format': 'json'})
        req = Request("http://api.bit.ly/v3/expand?%s" % params)
        response = urlopen(req)
        j = loads(response.read())
        if j['status_code'] == 200:
            return j['data']['expand'][0]['long_url']
        raise Exception('%s'%j['status_txt'])
    except HTTPError, e:
        raise('HTTP Error%s'%e.read())
 
def shorten(url):
    try:
        params = urlencode({'longUrl': url, 'login': username, 'apiKey': api_key, 'format': 'json'})
        req = Request("http://api.bit.ly/v3/shorten?%s" % params)
        response = urlopen(req)
        j = loads(response.read())
        if j['status_code'] == 200:
            return j['data']['url']
        raise Exception('%s'%j['status_txt'])
    except HTTPError, e:
        raise('HTTP error%s'%e.read())
    
