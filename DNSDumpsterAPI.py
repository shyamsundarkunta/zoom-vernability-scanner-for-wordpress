"""
This is the (unofficial) Python API for dnsdumpster.com Website.
Using this code, you can retrieve subdomains

"""
from __future__ import print_function

import requests
import re
import sys

from bs4 import BeautifulSoup


class DNSDumpsterAPI(object):

    """DNSDumpsterAPI Main Handler"""

    def __init__(self, verbose=False):
        self.verbose = verbose

    def display_message(self, s):
        if self.verbose:
            print('[verbose] %s' % s)


    def retrieve_results(self, table):
        res = []
        trs = table.findAll('tr')
        for tr in trs:
            tds = tr.findAll('td')
            domain = tds[0].text.replace('\n', '').split(' ')[0]
            data = {'domain': domain}
            res.append(data)
        return res

    def retrieve_txt_record(self, table):
        res = []
        for td in table.findAll('td'):
            res.append(td.text)
        return res


    def search(self, domain):
        dnsdumpster_url = 'https://dnsdumpster.com/'
        s = requests.session()

        req = s.get(dnsdumpster_url)
        soup = BeautifulSoup(req.content, 'html.parser')
        csrf_middleware = soup.findAll('input', attrs={'name': 'csrfmiddlewaretoken'})[0]['value']
        self.display_message('Retrieved token: %s' % csrf_middleware)

        cookies = {'csrftoken': csrf_middleware}
        headers = {'Referer': dnsdumpster_url}
        data = {'csrfmiddlewaretoken': csrf_middleware, 'targetip': domain}
        req = s.post(dnsdumpster_url, cookies=cookies, data=data, headers=headers)

        if req.status_code != 200:
            print(
                u"Unexpected status code from {url}: {code}".format(
                    url=dnsdumpster_url, code=req.status_code),
                file=sys.stderr,
            )
            return []

        if 'error' in req.content.decode('utf-8'):
            print("There was an error getting results", file=sys.stderr)
            return []

        soup = BeautifulSoup(req.content, 'html.parser')
        tables = soup.findAll('table')

        res = {}
        res['domain'] = domain
        res['dns_records'] = {}
        res['dns_records']['host'] = self.retrieve_results(tables[3])
        return res