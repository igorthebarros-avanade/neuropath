import os
import requests

endpoint = "https://ricar-mb5f5eic-australiaeast.cognitiveservices.azure.com"
api_key = "4PDlfnRLCS43XJaWDOUGTjSrxILu0hFuF9T3I6zrkRFyzhZ7x7HqJQQJ99BEACL93NaXJ3w3AAAAACOGAkGH"

url = f"{endpoint}/openai/deployments/dall-e-3/images/generations?api-version=2024-02-01"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

data = {
    "model": "dall-e-3",
    "prompt": "A photograph of a red fox in an autumn forest",
    "size": "1024x1024",
    "style": "vivid",
    "quality": "standard",
    "n": 1
}

response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print(response.json())
else:
    print("Error:", response.status_code, response.text)
