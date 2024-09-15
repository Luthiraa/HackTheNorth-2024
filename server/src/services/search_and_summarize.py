import requests
import bs4
import urllib.parse
from groq import Groq
import logging

# Initialize the Groq API client
api_key = "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"
client = Groq(api_key=api_key)

# Function to extract the text from a webpage
def extract_page_text(page_url):
    try:
        page_response = requests.get(page_url)
        page_soup = bs4.BeautifulSoup(page_response.text, "html.parser")
        
        # Extract text from the page (within <p> tags)
        paragraphs = page_soup.find_all('p')
        page_text = " ".join([para.get_text() for para in paragraphs])
        return page_text
    except Exception as e:
        print(f"Error fetching {page_url}: {str(e)}")
        return ""

# Function to get top 5 Google search results
def google_search(query, num_results=5):
    url = 'https://google.com/search?q=' + urllib.parse.quote(query)
    request_result = requests.get(url)
    soup = bs4.BeautifulSoup(request_result.text, "html.parser")
    
    # Store top results
    results = []
    
    # Find all result divs, limit to top 5
    for g in soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:num_results]:
        title = g.get_text()
        parent_a_tag = g.find_parent('a')
        if parent_a_tag and 'href' in parent_a_tag.attrs:
            link = parent_a_tag['href']
            if link.startswith("/url?q="):
                link = link.split("/url?q=")[1].split("&")[0]  # Extract the actual URL
                link = urllib.parse.unquote(link)  # Decode the URL
            
            # Extract page text for the link
            page_text = extract_page_text(link)
            results.append({"title": title, "link": link, "text": page_text})
    
    return results

# Function to search Google Images and get the first image URL
def google_image_search(query):
    url = 'https://www.google.com/search?q=' + urllib.parse.quote(query) + '&tbm=isch'
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    html = response.text

    soup = bs4.BeautifulSoup(html, 'html.parser')
    images = soup.find_all('img')

    for img in images:
        img_url = img.get('src')
        if img_url and img_url.startswith('http'):
            return img_url
    return None

# Function to send the extracted text to the Groq LLM for summarization
def summarize_text(text):
    # Modify the prompt to include the image URL
    prompt = f"Summarize the following text and provide key takeaways. Make sure to return your answer in Markdown only. Format the bullet points, paragraphs, links, bold, etc., styling with appropriate tags. Make it look super pretty, readable, and well-formatted with spaces. Have extra links at the end too. Here is the text to summarize:\n\n{text}"
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# Function to extract important words from a query using Groq
def extract_important_words(query):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Extract the most important words from the following query, just give me the words straight up, ONLY THE WORDS, no other text:\n\n{query}"}
        ],
        max_tokens=50
    )
    important_words = response.choices[0].message.content.strip().split(' ')

    return important_words

# Main function to fetch top 5 results, process them, and send to Groq
def process_search_and_summarize(query):
    logging.basicConfig(level=logging.DEBUG)
    logging.debug(f"Processing query: {query}")
    
    important_words = extract_important_words(query)
    logging.debug(f"Important words: {important_words}")
    
    search_results = google_search(query)
    all_texts = ""
    resource_list = []

    # Combine all the text from the top 5 results
    for result in search_results:
        title = result['title']
        link = result['link']
        text = result['text']
        all_texts += f"\n\nFrom {title} ({link}):\n{text[:1000]}"  # Limit text from each source
        resource_list.append(link)

    logging.debug(f"Combined text: {all_texts[:500]}...")  # Print first 500 characters for brevity

    # Get image URL
    image_url = google_image_search(query)
    logging.debug(f"Image URL: {image_url}")

    # Send the combined text and image URL to Groq for summarization
    summary = summarize_text(all_texts)

    logging.debug(f"Summary from Groq: {summary}")

    # Return the summary and the resources
    return summary, resource_list, image_url


if __name__ == "__main__":
    query = "What is go fish hack the north?"
    summary, resources = process_search_and_summarize(query)
    important = extract_important_words(query)
    print("### Important Words ###")
    print(important)
    print("### Summary from Groq ###")
    print(summary)
    print("\n### Resources Used ###")
    for link in resources:
        print(link)
