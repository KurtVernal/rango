import sys
import getopt
import json
import urllib, urllib2

def run_query(search_terms):
    root_url = 'https://api.datamarket.azure.com/Bing/Search/'
    source = 'Web'

    result_per_page = 10
    offset = 0

    query = "'{0}'".format(search_terms)
    query = urllib.quote(query)

    search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(
        root_url, source, result_per_page, offset, query)

    username = 'Dmitriy Velichko'
    bing_api_key = 'TMPDfEQ26vEvb56khRVoszeHLZk3R7i5Bg2kKaoPnBE'

    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, search_url, username, bing_api_key)
 
    results = []

    try:
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

        response = urllib2.urlopen(search_url).read()

        json_response = json.loads(response)

        for result in json_response['d']['results']:
            results.append({
                 'title': result['Title'],
                 'link': result['Url'],
                 'summary': result['Description']})

    except urllib2.URLError, e:
        print "Error when queryin the Bing API: ", e

    return results


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:", ["search"])
    except getopt.GetoptError:
        print 'bing_search.py -sch <search item>'
        sys.exit(2)

    for opt, arg in opts:
        print opt
        print arg
        if opt == '-h':
            print 'bing_search.py -sch <search item>'
            sys.exit()
        elif opt in ("-s", "--search"):
            print "arg=", arg
            result_list = run_query(arg)
            for result in result_list:
                print result['link'], result['title'], result['summary']
