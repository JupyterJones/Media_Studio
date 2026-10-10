import requests

response = requests.get("http://localhost:11434/v1/models")
data = response.json()

models = [m['id'] for m in data['data']]
print(models)
