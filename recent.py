import requests
import json
import sys
import time

from login import login

'''
usage: python recent.py [username] [password]
or: python recent.py [cookie:SAAS_U]
'''

username = ""
password = ""
cookie = ""
use_cookie = False

if len(sys.argv) == 2:
    cookie = sys.argv[1]
    use_cookie = True
elif len(sys.argv) == 3:
    username = sys.argv[1]
    password = sys.argv[2]
else:
    print("Get recent daily health report result.")
    print("Usage: python recent.py [username] [password]")
    print("   or: python recent.py [cookie:SAAS_U]")
    sys.exit(1)

http_header = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/81.0.4044.138 Safari/537.36',
    'Referer': 'https://xmuxg.xmu.edu.cn/app/221'
}

# create session
session = requests.Session()

# login
login(session, username, password, cookie, use_cookie, http_header)

# get record business id
get_business_url = 'https://xmuxg.xmu.edu.cn/api/app/221/business/now'
resp = session.get(get_business_url, headers=http_header).text
business_id = json.loads(resp)['data'][0]['business']['id']

# get recent checkin status
recent_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/myFormInstance" % str(business_id)
resp = session.get(recent_url, headers=http_header).text
res_json = json.loads(resp)
form_data = res_json['data']['formData']
owner = res_json['data']['owner']['name']

# get recent result
record_data = []
for item in form_data:
    if "打卡详细情况" in item['title']:
        record_data = item['value']['tableValue']
        break

record_set = []
for item in record_data:
    raw = item['rowData']
    record = {
        "date": None,
        "heat": None,
        "promise": None,
        "syndrome": None
    }
    for v in raw:
        if "日期" in v['title']:
            record['date'] = v['value']['stringValue']
        elif "体温" in v['title']:
            record['heat'] = v['value']['stringValue']
        elif '本人承诺' in v['title']:
            record['promise'] = v['value']['stringValue']
        elif '症状' in v['title']:
            record['syndrome'] = v['value']['stringValue']
    record_set.append(record)

# get today's modification log

# get form id
now_url = "https://xmuxg.xmu.edu.cn/api/app/214/business/now"
resp = session.get(now_url).text
form_id = str(json.loads(resp)['data'][0]['business']['id'])

form_instance_url = "https://xmuxg.xmu.edu.cn/api/formEngine/business/%s/myFormInstance" % form_id
resp = session.get(form_instance_url, headers=http_header).text
form_json = json.loads(resp)["data"]
instance_id = form_json["id"]

changelog_url = "https://xmuxg.xmu.edu.cn/api/formEngine/formInstances/%s/changeLogs?playerId=owner&businessId=%s" \
                % (instance_id, form_id)
log_text = session.get(changelog_url).text
log_json = json.loads(log_text)['data']['logs']

result = {
    "owner": owner,
    "today": len(log_json) > 0,
    "payload": record_set
}
print(json.dumps(result, ensure_ascii=False, indent=4))