def get_search_results(search_term):
    url = f"https://serpapi.com/search.json?q={search_term}&api_key={SERP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data['organic_results']
