from newsapi import NewsApiClient

newsapi = NewsApiClient(api_key='2ed4a40b77fe4494b0021c0a391bfc7e')
top_headlines = newsapi.get_top_headlines(country='us')
print(top_headlines)
