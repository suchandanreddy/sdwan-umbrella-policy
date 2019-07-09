import requests
import json
import os
import tabulate
import time

from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

vmanage_host = os.environ.get("vmanage_host")
vmanage_port = os.environ.get("vmanage_port")
username = os.environ.get("username")
password = os.environ.get("password")
device_id = os.environ.get("device_id")
umbrella_key = os.environ.get("umbrella_key")
umbrella_secret = os.environ.get("umbrella_secret")
org_id = os.environ.get("org_id")


if vmanage_host is None or vmanage_port is None or username is None or password is None or device_id is None or umbrella_key is None or umbrella_secret is None or org_id is None:
    print("For Windows Workstation, vManage details must be set via environment variables using below commands")
    print("set vmanage_host=10.10.10.10")
    print("set vmanage_port=443")
    print("set username=admin")
    print("set password=admin")
    print("set device_id=1.1.1.6")
    print("set umbrella_key=<your-umbrella-key>")
    print("set umbrella_secret=<your-umbrella-secret>")
    print("set org_id=<your-org-id>")
    print("For MAC OSX Workstation, vManage details must be set via environment variables using below commands")
    print("export vmanage_host=10.10.10.10")
    print("export vmanage_port=443")
    print("export username=admin")
    print("export password=admin")
    print("export device_id=1.1.1.6")
    print("export umbrella_key=<your-umbrella-key>")
    print("export umbrella_secret=<your-umbrella-secret>")
    print("export org_id=<your-org-id>")
    exit()

requests.packages.urllib3.disable_warnings()

class rest_api_lib:
    def __init__(self, vmanage_host,vmanage_port, username, password):
        self.vmanage_host = vmanage_host
        self.vmanage_port = vmanage_port
        self.session = {}
        self.login(self.vmanage_host, username, password)

    def login(self, vmanage_host, username, password):

        """Login to vmanage"""

        base_url = 'https://%s:%s/'%(self.vmanage_host, self.vmanage_port)

        login_action = '/j_security_check'

        #Format data for loginForm
        login_data = {'j_username' : username, 'j_password' : password}

        #Url for posting login data
        login_url = base_url + login_action
        #url = base_url + login_url

        sess = requests.session()

        #If the vmanage has a certificate signed by a trusted authority change verify to True

        login_response = sess.post(url=login_url, data=login_data, verify=False)


        if b'<html>' in login_response.content:
            print ("Login Failed")
            sys.exit(0)

        self.session[vmanage_host] = sess

    def get_request(self, mount_point):
        """GET request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)
        #print(url)

        response = self.session[self.vmanage_host].get(url, verify=False)

        return response

    def post_request(self, mount_point, payload, headers={'Content-type': 'application/json', 'Accept': 'application/json'}):
        """POST request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)
        #print(url)
        payload = json.dumps(payload)
        #print (payload)

        response = self.session[self.vmanage_host].post(url=url, data=payload, headers=headers, verify=False)
        #print(response.text)
        #exit()
        #data = response
        return response

vmanage_session = rest_api_lib(vmanage_host, vmanage_port, username, password)

payload = {"query":{
           "condition":"AND","rules":
           [{"value":["10"],
           "field":"entry_time",
           "type":"date",
           "operator":"last_n_hours"},
           {"value":[device_id],
           "field":"vdevice_name",
           "type":"string",
           "operator":"in"},
           {"value":["umbrella"],
            "field":"type",
            "type":"string",
            "operator":"in"}]},
           "aggregation":
           {"metrics":[
               {"property":"redirect_pkts","type":"sum"}],
               "histogram":{"property":"entry_time",
                            "type":"minute",
                            "interval":60,
                            "order":"asc"}}}

umbrella_stats = vmanage_session.post_request("statistics/umbrella/aggregation",payload)

table = list()
headers = ["Time", "Redirect packets"]

items = umbrella_stats.json()['data']

for item in items:
    tr = [time.strftime('%m/%d/%Y %H:%M:%S',  time.gmtime(item['entry_time']/1000.)) + " UTC ",item['redirect_pkts']]
    table.append(tr)

try:
    print(tabulate.tabulate(table, headers, tablefmt="fancy_grid"))
except UnicodeEncodeError:
    print(tabulate.tabulate(table, headers, tablefmt="grid"))


destination_site = "toknowall.com"

print("\nUmbrella dashboard statistics for website toknowall.com\n")

url = "https://reports.api.umbrella.com/v1/organizations/%s/destinations/%s/activity?limit=1"%(org_id,destination_site)

tokno_umbrella_reports = requests.get(url,auth=HTTPBasicAuth(umbrella_key,umbrella_secret))

if tokno_umbrella_reports.status_code == 200:
    print(json.dumps(tokno_umbrella_reports.json(), indent=4, sort_keys=True))
else:
    print("\nError fetching reports from Umbrella")
    print(tokno_umbrella_reports.text)

destination_site = "facebook.com"

print("\nUmbrella dashboard statistics for website facebook.com\n")

url = "https://reports.api.umbrella.com/v1/organizations/%s/destinations/%s/activity?limit=1"%(org_id,destination_site)

fb_umbrella_reports = requests.get(url,auth=HTTPBasicAuth(umbrella_key,umbrella_secret))

if fb_umbrella_reports.status_code == 200:
    print(json.dumps(fb_umbrella_reports.json(), indent=4, sort_keys=True))
else:
    print("\nError fetching reports from Umbrella")
    print(fb_umbrella_reports.text)

destination_site = "ntp.ubuntu.com"

print("\nUmbrella dashboard statistics for website ntp.ubuntu.com\n")

url = "https://reports.api.umbrella.com/v1/organizations/%s/destinations/%s/activity?limit=1"%(org_id,destination_site)

ntp_umbrella_reports = requests.get(url,auth=HTTPBasicAuth(umbrella_key,umbrella_secret))

if ntp_umbrella_reports.status_code == 200:
    print(json.dumps(ntp_umbrella_reports.json(), indent=4, sort_keys=True))
else:
    print("\nError fetching reports from Umbrella")
    print(ntp_umbrella_reports.text)
