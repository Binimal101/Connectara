from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import pathlib
from bs4 import BeautifulSoup
from typing import Any, List
import os, json, requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

from src import env_path

load_dotenv(env_path)
assert os.getenv("SERP_TOKEN") is not None, "SERP_TOKEN not set in environment"
"""
1) Get posts similar to the name    
2) validate for each post that the author is the same as the name as the initial target
3) return post details for validated posts
"""

def get_all_post_details(name: str) -> List[str]:
    post_urls = get_posts_similar_to_fullname(name)

    valid_posts = []
    for url in post_urls:
        try:
            post_text, author_name = headless_browse(url)
            if author_name.lower() == name.lower():
                valid_posts.append(post_text)
        
        except Exception as e:
            print(f"[error] Failed to process {url}: {e}")
    return valid_posts


def headless_browse(url: str, screenshot_name: str | None = None):
    if screenshot_name is None:
        screenshot_name = f"screenshot_{int(time.time())}.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 720},
        )

        page = context.new_page()

        print(f"Navigating to: {url}")
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)

        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PlaywrightTimeoutError:
            print("[warn] networkidle not reached, continuing anyway...")

        page.wait_for_timeout(750)

        # Try to dismiss the modal; if it fails, just log and continue
        # try:
        #     page.click("button[aria-label='Dismiss']", timeout=3_000, force=True)
        # except Exception as e:
        #     print(f"[warn] Failed to click dismiss button: {e}")

        # Save HTML from the current DOM
        html = page.content()
        
        title = page.title()
        browser.close()
        return getPostDetails(html) 

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
        print("found post details:", post_text, author_name, "\n\n")
        return post_text, author_name # type: ignore
    
posts = get_all_post_details("Andres Campoverde")
with open("posts.json", "w", encoding="utf-8") as f:
    for post in posts:
        f.write(post + "\n")