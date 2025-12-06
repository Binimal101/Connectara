import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest import result
from bs4 import BeautifulSoup
from pathlib import Path
import requests, os

from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

def get_posts_similar_to_fullname(full_name: str):
    # Load the HTML dump
    url = "https://serpapi.com/search"
    query = 'site:linkedin.com inurl:"/posts/" intext:"' + full_name + '"'
    
    params = {
        'q': query,
        'api_key': os.getenv('SERP_TOKEN'), 
    }

    response = requests.get(url, params=params).json()

    with open("serp_result.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=2)

        all_posts = []
        first_page_results = response.get("organic_results", [])
        
        if "serpapi_pagination" in response:
            pagination = response["serpapi_pagination"]
            other_pages = pagination.get("other_pages") or {}
            
            if other_pages:
                api_key = params.get("api_key")
                page_results = {}
                
                def fetch_page(page_num: str, page_url: str):
                    query_params = {} if not api_key or "api_key=" in page_url else {"api_key": api_key}
                    page_response = requests.get(page_url, params=query_params, timeout=15)
                    page_response.raise_for_status()
                    data = page_response.json()
                    return int(page_num), data.get("organic_results", [])
                
                with ThreadPoolExecutor(max_workers=min(8, len(other_pages))) as executor:
                    futures = [
                        executor.submit(fetch_page, page_num, page_url)
                        for page_num, page_url in other_pages.items()
                    ]
                    
                    for future in as_completed(futures):
                        try:
                            page_num, organic_results = future.result()
                        except Exception:
                            continue
                        if organic_results:
                            page_results[page_num] = organic_results
                for page_index in sorted(page_results):
                    all_posts.extend(page_results[page_index])
            
        all_posts.extend(first_page_results)
        return [x["link"] for x in all_posts if x.get("link")]

def getPostDetails(html: str)-> tuple[str, str]:
    # Load the HTML dump
    soup = BeautifulSoup(html, "html.parser")

    # Find all sections with class 'mb-3'
    mb3_section = soup.find_all("section", class_="mb-3")[0]
    article = mb3_section.find_all("article")[0]
    p_tag = article.find("p")

    post_text = p_tag.get_text() if p_tag else None

    author_flexbox = article.find_all("div", class_ = "flex")[0]
    author_links = author_flexbox.find_all('a', attrs={'data-tracking-control-name': 'public_post_feed-actor-name'})
    author_name = author_links[0].get_text() if author_links else None

    if not all([post_text, author_name]):
        raise ValueError("Could not extract post details")
    else:
        return post_text, author_name # type: ignore

posts = get_posts_similar_to_fullname("Andres Campoverde")
print(f"Found {len(posts)} posts similar to the full name.")
pprint(posts)