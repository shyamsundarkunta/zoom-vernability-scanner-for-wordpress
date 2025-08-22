#!/usr/bin/env python

# Required modules
import argparse
import requests
import re
import json
import sys
from DNSDumpsterAPI import DNSDumpsterAPI

# Just some colors and shit bro
white = '\033[97m'
green = '\033[1;32m'
red = '\033[1;31m'
yellow = '\033[1;33m'
end = '\033[1;m'
info = '\033[1;33m[!]\033[1;m'
que =  '\033[1;34m[?]\033[1;m'
bad = '\033[1;31m[-]\033[1;m'
good = '\033[1;32m[+]\033[1;m'
run = '\033[1;97m[~]\033[1;m'

# Fix for line 25 / cross-version input()
try:
    input = raw_input  # Python 2 compatibility
except NameError:
    pass  # Python 3 already has input()

parser = argparse.ArgumentParser()  # defines the parser
parser.add_argument('-u', '--url', help='Target wordpress website', dest='url')
parser.add_argument('--auto', help='Automatic mode', dest='auto', action='store_true')
args = parser.parse_args()  # Parsing the arguments

print ('''%s  ____                
 /_  / ___  ___  ____ 
  / /_/ %s_ \/ _%s \/    \\
 /___/\\___%s/\\%s___/_/_/_%s\n''' % (yellow, white, yellow, white, yellow, end))

usernames = []  # List for storing found usernames
subdomains = set()  # List for storing subdomains

def metagenerator(url):
    response = requests.get(url).text
    match = re.search(r'<meta name="generator" content="WordPress .*" />', response)
    if match:
        version_dec = match.group().split('<meta name="generator" content="WordPress ')[1][:-4]
        return [version_dec.replace('.', ''), version_dec]
    else:
        print('%s Target doesn\'t seem to use WordPress' % bad)

def version_vul(version, version_dec):
    response = requests.get(
        'https://wpvulndb.com/api/v3/wordpresses/%s' % version,
        headers={'Authorization': 'Token token=pTs1OAhcDTJxOVjava5usL9lGpDHbIanuluU1CpoXzs'}
    ).text
    jsoned = json.loads(response)
    if not jsoned[version_dec]['vulnerabilities']:
        print('%s No vulnerabilities found' % bad)
    else:
        print('')
        print(( '%s-%s' % (red, end) ) * 50)
        for vulnerability in jsoned[version_dec]['vulnerabilities']:
            print('%s %s' % (good, vulnerability['title']))
            for reference in vulnerability['references']['url']:
                print('    ' + reference)
            print('')
        print(( '%s-%s' % (red, end) ) * 50)

def iswordpress(url):
    try:
        response = requests.get(url, timeout=2).text
        if 'content="WordPress' in response:
            return True
        else:
            return False
    except Exception:
        return False

def source_dig(url, domain):
    print('%s Finding subdomains' % run)
    response = requests.get(url).text
    matches = re.findall(r'//[^"\']*\.%s' % domain, response)
    for match in matches:
        clean = match.split('/')[2]
        if clean.endswith(domain):
            subdomains.add(clean)
    for subdomain in subdomains:
        print(subdomain)

def dnsdump(domain):
    res = DNSDumpsterAPI(False).search(domain)
    for entry in res['dns_records']['host']:
        subdomain = '{domain}'.format(**entry).replace('HTTP:', '').replace('SSH:', '').replace('FTP:', '')
        subdomains.add(subdomain)
        print(subdomain)

def automatic(url, domain):
    source_dig(url, domain)
    dnsdump(domain)
    progress = 1
    choice = input('%s Store subdomains in a text file for further processing? [y/N]' % que).lower()
    if choice == 'y':
        with open('%s.txt' % domain.split('.')[0], 'w+') as f:
            for x in subdomains:
                f.write(x + '\n')
    for subdomain in subdomains:
        sys.stdout.write('\r%s Subdomains scanned: %i/%i' % (run, progress, len(subdomains)))
        sys.stdout.flush()
        if iswordpress('http://' + subdomain):
            print('\n%s %s seems to use WordPress' % (good, subdomain))
            version = metagenerator('http://' + subdomain)
            version_vul(version[0], version[1])
            manual('http://' + subdomain)
        progress = progress + 1
    print('')

def manual(url):
    print('%s Extracting usernames' % run)
    for number in range(1, 9999):
        response = requests.get(
            url + '/?d3v=x&author=' + str(number),
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'}
        ).text  # Makes request to webpage
        match = re.search(r'/author/(.*?)"', response)  # Regular expression to extract username
        if match:
            username = match.group(1).split('/')[0]  # Taking what we need from the regex match
            print(username.replace('/feed', ''))  # Print the username without '/feed', if present
            usernames.append(username)  # Appending the username to usernames list
        else:
            if number - len(usernames) > 20:  # A simple logic to be on the safe side
                if len(usernames) > 0:
                    print('%s Looks like Zoom has found all the users.' % info)
                    if args.auto:
                        break
                    else:
                        quit()
                else:
                    print('%s Looks like there\'s some security measure in place.' % bad)
                    if args.auto:
                        break
                    else:
                        quit()

if args.url:
    url = args.url  # args.url contains value of -u option
    if 'http' not in url:
        url = 'http://' + url
    if url.endswith('/'):
        url = url[:-1]
    domain = url.replace('http://', '').replace('https://', '').replace('www', '')
else:
    parser.print_help()

if args.url and args.auto:
    automatic(url, domain)
else:
    try:
        version = metagenerator(url)
        version_vul(version[0], version[1])
        manual(url)
    except Exception as e:
        print('%s %s doesn\'t seem to use Wordpress.' % (bad, domain))          
