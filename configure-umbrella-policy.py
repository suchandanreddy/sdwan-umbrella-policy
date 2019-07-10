import requests
import json
import os

from requests.packages.urllib3.exceptions import InsecureRequestWarning

vmanage_host = os.environ.get("vmanage_host")
vmanage_port = os.environ.get("vmanage_port")
username = os.environ.get("username")
password = os.environ.get("password")
device_template_name = os.environ.get("device_template_name")


if vmanage_host is None or vmanage_port is None or username is None or password is None or device_template_name is None :
    print("For Windows Workstation, vManage details must be set via environment variables using below commands")
    print("set vmanage_host=198.18.1.10")
    print("set vmanage_port=443")
    print("set username=admin")
    print("set password=admin")
    print("set device_template_name=BR2-CSR-1000v")
    print("For MAC OSX Workstation, vManage details must be set via environment variables using below commands")
    print("export vmanage_host=198.18.1.10")
    print("export vmanage_port=443")
    print("export username=admin")
    print("export password=admin")
    print("export device_template_name=BR2-CSR-1000v")
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

        login_action = 'j_security_check'

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
            exit(0)

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

    def put_request(self, mount_point, payload, headers={'Content-type': 'application/json', 'Accept': 'application/json'}):
        """POST request"""
        url = "https://%s:%s/dataservice/%s"%(self.vmanage_host, self.vmanage_port, mount_point)
        #print(url)
        payload = json.dumps(payload)
        #print (payload)

        response = self.session[self.vmanage_host].put(url=url, data=payload, headers=headers, verify=False)
        #print(response.text)
        #exit()
        #data = response
        return response




vmanage_session = rest_api_lib(vmanage_host, vmanage_port, username, password)

#Fetching list of device templates

template_id_response = vmanage_session.get_request("template/device")

if template_id_response.status_code == 200:
    items = template_id_response.json()['data']
    template_found=0
    print("\nFetching Template uuid of %s"%device_template_name)
    for item in items:
        if item['templateName'] == device_template_name:
            device_template_id = item['templateId']
            template_found=1
            break
    if template_found==0:
        print("\nDevice Template is not found")
        exit()
else:
    print("\nError fetching list of templates")
    exit()

#Fetching feature templates associated with Device template. 

print("\nFetching feature templates associated with %s device template"%device_template_name)

template_response = vmanage_session.get_request("template/device/object/%s"%(device_template_id))

if template_response.status_code == 200:
    feature_template_ids=template_response.json()
else:
    print("\nError fetching feature template ids")
    exit()

#Fetch Umbrella Token

print("\nFetching Umbrella Token list-id")

umbrella_token_response = vmanage_session.get_request("template/policy/list/umbrelladata/")

if umbrella_token_response.status_code==200:
    umbrella_token_listid=umbrella_token_response.json()["data"][0]["listId"]

else:
    print('\nError fetching Umbrella token')
    exit()


#Create DNS Security/Umbrella policy 

print("\nCreating DNS Security policy")

dnssecurity_policy_name="DNS-Security-BR-2-API-call"

dns_security_payload = {"name":dnssecurity_policy_name,
           "type":"DNSSecurity",
           "description":dnssecurity_policy_name,
           "definition":{"localDomainBypassList":{},
           "matchAllVpn":True,
           "umbrellaDefault":True,
           "localDomainBypassEnabled":False,
           "dnsCrypt":True,
           "umbrellaData":
           {"ref":umbrella_token_listid}}}

dnssecurity_response = vmanage_session.post_request("template/policy/definition/dnssecurity",dns_security_payload)

if dnssecurity_response.status_code==200:
    dnssecurity_uuid=dnssecurity_response.json()["definitionId"]
else:
    print("\nError creating dns security policy\n")
    print(dnssecurity_response.text)
    exit()

#Creating Security Policy

print("\nCreating Security Policy")

security_policy_name="BR2-Security-Policy-API"

security_payload = {"policyDescription": security_policy_name,
           "policyType": "feature",
           "policyName": security_policy_name,
           "policyUseCase": "custom",
           "policyDefinition": {
           "assembly": [
                {
                "definitionId": dnssecurity_uuid,
                "type": "DNSSecurity"
                }
            ],
            "settings": {}
            },
            "isPolicyActivated": False
            }

security_policy_res = vmanage_session.post_request("template/policy/security/",security_payload)

if not (security_policy_res.status_code == 200):
    print("\nCreating security policy failed")

#Fetching Security Policy uuid

security_policy_uuid_res = vmanage_session.get_request("template/policy/security/")

if security_policy_uuid_res.status_code == 200:
    items = security_policy_uuid_res.json()['data']
    for item in items:
        if item['policyName'] == security_policy_name:
            security_policy_uuid = item['policyId']
            break
else:
    print("\nFetching Security Policy uuid failed\n")
    print(security_policy_uuid_res.text)
    
print("\nsecurity policy uuid: %s"%security_policy_uuid)

#Edit Device Template

payload = {"templateId":device_template_id,"templateName":device_template_name,
           "templateDescription":feature_template_ids["templateDescription"],"deviceType":feature_template_ids["deviceType"],
           "configType":"template","factoryDefault":False,
           "policyId":feature_template_ids["policyId"],
           "featureTemplateUidRange":[],"connectionPreferenceRequired":True,
           "connectionPreference":True,"policyRequired":True,
           "generalTemplates":feature_template_ids["generalTemplates"],
            "securityPolicyId":security_policy_uuid}

device_template_edit_res = vmanage_session.put_request("template/device/%s"%device_template_id,payload)

if device_template_edit_res.status_code == 200:
    device_uuid = device_template_edit_res.json()['data']['attachedDevices'][0]['uuid']
    template_pushid = device_template_edit_res.json()['data']['processId']
else:
    print("\nError editing device template\n")
    print(device_template_edit_res.text)

print("\nDevice uuid: %s"%device_uuid)

# Fetching Device csv values

print("\nFetching device csv values")

payload = {"templateId":device_template_id,
           "deviceIds":[device_uuid],
           "isEdited":False,"isMasterEdited":False}

device_csv_res = vmanage_session.post_request("template/device/config/input/",payload)

if device_csv_res.status_code == 200:
    device_csv_values = device_csv_res.json()['data'][0]
else:
    print("\nError getting device csv values\n")
    print(device_csv_res.text)

# Attaching new Device template

print("\nAttaching new device template")

payload = {"deviceTemplateList":[{"templateId":device_template_id,
           "device":[device_csv_values],
           "isEdited":True,"isMasterEdited":False}]}

attach_template_res = vmanage_session.post_request("template/device/config/attachfeature",payload)

if attach_template_res.status_code == 200:
    attach_template_pushid = attach_template_res.json()['id']
else:
    print("\nattaching device template failed\n")
    print(attach_template_res.text)
    exit()

# Fetch the status of template push

while(1):
    template_status_res = vmanage_session.get_request("device/action/status/%s"%attach_template_pushid)
    if template_status_res.status_code == 200:
        if template_status_res.json()['summary']['status'] == "done":
            print("\nTemplate push status is done")
            break
        else:
            continue
    else:
        print("\nFetching template push status failed\n")
        print(template_status_res.text)
        exit()

