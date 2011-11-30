import json, re, socket
from socket import gaierror

import lxml.etree, requests

from chii import command
ip_regex = re.compile(r'\d+-\d+-\d+-\d+')

def lookup_ip(host):
    # check if this is already an ip address
    try:
        socket.inet_aton(host)
        ip = host
    except socket.error:
        try:
            ip = socket.gethostbyaddr(host)[2][0]
        except gaierror:
            match = ip_regex.search(host)
            if match:
                ip = match.group().replace('-', '.')
            else:
                return "Sorry I can't seem to tell what planet you are from, specify your city/country"    
    api_key = 'bed6c8a08cd083d53f197053f1301829958c2f1caba64f2c764d1b8ce6e70709'
    url = 'http://api.ipinfodb.com/v3/ip-city/?key=%s&ip=%s&format=json'
    data = json.load(requests.get(url % (api_key, ip)))
    city, region, country = data['cityName'], data['regionName'], data['countryName']
    if city and region:
        return ', '.join([city, region])
    else:
        return ', '.join(x for x in [city, region, country] if x != '-')

@command('wz', 'weather')
def weather(self, channel, nick, host, *args):
    location = ' '.join(args)
    if not location:
        users = {
            'zk': 'Kansas city, KS',
            'kieran': 'Dublin, IE',
            'neoblaze': 'tonsberg, NO',
            'doomstalk': 'Boston, MA',
            'bunn': 'Vancouver, BC',
        }
        for u in users:
            if u in nick.lower():
                location = users[u]
                break
        else:
            location = lookup_ip(host.split('@')[1]).encode('ascii', 'ignore')
    url = 'http://www.google.com/ig/api?weather='
    try:
        tree = lxml.etree.parse(url + location)
        city = tree.xpath('//city')[0].get('data')
        date = tree.xpath('//forecast_date')[0].get('data')
        temp_f = tree.xpath('//temp_f')[0].get('data')
        temp_c = tree.xpath('//temp_c')[0].get('data')
        humidity = tree.xpath('//humidity')[0].get('data')
        wind_condition = tree.xpath('//wind_condition')[0].get('data')
        wz = '%s @ %s: %sf / %sc / %s / %s' % tuple(x.lower() for x in [city, date, temp_f, temp_c, humidity, wind_condition])
        return wz.encode('ascii', 'ignore')
    except:
        return 'fail'
