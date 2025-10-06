import getpass
import json
from urllib.parse import quote
import uuid
import anthropic
import os
import requests
import pandas as pd


username = input("Enter your ETS username: ")
password = getpass.getpass("Enter your ETS password: ")


loginUrl = "https://ets-prod-100.epsilontg.com/etsauth/user/login"
headers = {
    "accept": "*/*",
    "Content-Type": "application/json"
}
payload = {
    "username": username,
    "password": password
}

response = requests.post(loginUrl, headers=headers, json=payload)
#print("Login status code:", response.status_code)
#print("Login response text:\n", response.text)

token = response.text.strip()


auth_headers = {
    "accept": "*/*",
    "Authorization": f"Bearer {token}"
}

NLPPrompt = input("Enter your query: ")

with open('anthropicPrompt.txt', 'r', encoding='utf-8') as f:
    anthropicPrompt = f.read()
    prompt = anthropicPrompt + NLPPrompt


client = anthropic.Anthropic(api_key = "")

response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens = 1024,
        messages = [ {"role": "user", "content": prompt} ]
)

anthropicResult = response.content[0].text

#-------------------------------------------------
for i in range(3):
    filter_json = json.loads(anthropicResult)

    

    try:
        predicates = filter_json["expression"]["predicates"]
        readable_filters = []
        for pred in predicates:
            attr = pred.get("attributeName", "")
            sign = pred.get("sign", "")
            value = pred.get("value", "")
            readable_filters.append(f"{attr} {sign} {value}")
        query_display = " AND ".join(readable_filters)
    except Exception as e:
        query_display = ""

    #if query_display is empty, ask again


    feedbackString = "What would you like to change or clarify about the filters?: "
    if (query_display == ""):
        feedbackString = "Sorry, unable to retrieve proper filters, please enter your query again: "
        response = ""
    else:
        response = input("Is [" + query_display + "] good?: ")


    if response == "yes":
        break
    else:
        if i == 2:
            print("Too many failed attempts to get valid filters. Exiting.")
            exit(1)
            
        user_feedback = input(feedbackString)
        full_prompt = f"""{anthropicPrompt}
        Original query: "{NLPPrompt}"
        Previous filters returned: {query_display}
        User feedback: "{user_feedback}"
        Please revise the filter expression accordingly."""

        response = client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens = 1024,
        messages = [ {"role": "user", "content": prompt} ])

        anthropicResult = response.content[0].text



#---------------------------------------







#filter_json = {"expression":{"predicates":[{"attributeName":"Amount","sign":"=","value":10,"valueType":{"dataType":"NUMBER","fieldFormat":"TEXT","fieldType":"TEXT_BOX","isRel":False},"isRel":False}]}}
filter_json = json.loads(anthropicResult)
filter_str = json.dumps(filter_json, separators=(',', ':'))
#print(filter_str)

filter_param = quote(filter_str)
request_id = str(uuid.uuid4())


get_url = f"https://ets-prod-100.epsilontg.com/etsserver/Accounting/getJournalEntries?filter={filter_param}&requestId={request_id}"
response = requests.get(get_url, headers=auth_headers)




#print("Status Code:", response.status_code)
#print("Response JSON:", response.text)

data = response.json()
df = pd.DataFrame(data)
csv_filename = "journal_entries.csv"
df.to_csv(csv_filename, index=False)

#Add feature later to go through all the queries


try:
    predicates = filter_json["expression"]["predicates"]
    readable_filters = []
    for pred in predicates:
        attr = pred.get("attributeName", "")
        sign = pred.get("sign", "")
        value = pred.get("value", "")
        readable_filters.append(f"{attr} {sign} {value}")
    query_display = " AND ".join(readable_filters)
except Exception as e:
    query_display = "[Unable to parse filter expression]"


print(f"Results for [" + query_display + "] are saved to {csv_filename}")
