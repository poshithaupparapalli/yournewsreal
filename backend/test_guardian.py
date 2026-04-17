"""                                                                                                                    
  test_guardian.py                                                                                                       
                                                                                                                         
  Tests the Guardian API and shows you exactly what we get back.                                                       
  Run with: python3 test_guardian.py                                                                                     
  """                                                                                                                    
   
import requests                                                                                                        
import os                                                                                                            
from dotenv import load_dotenv

  # Load the API key from your .env file                                                                                 
load_dotenv()
API_KEY = os.getenv("GUARDIAN_API_KEY")                                                                                
                                                                                                                         
  # ─────────────────────────────────────────────────────
  # The topics we want to pull articles for                                                                              
  # These map directly to Guardian sections                                                                              
  # ─────────────────────────────────────────────────────
TOPICS = [                                                                                                             
      "technology",                                                                                                    
      "science",                                                                                                         
      "business",                                                                                                      
      "world",
      "environment",
  ]
                                                                                                                         
def fetch_articles(topic, num_articles=5):
      """                                                                                                                
      Calls the Guardian API for a given topic.                                                                        
      show-fields=bodyText tells the API to include the full article text.                                               
      Without that parameter you only get the headline.                                                                  
      """                                                                                                                
      url = "https://content.guardianapis.com/search"                                                                    
                                                                                                                         
      params = {                                                                                                         
          "section": topic,           # which topic section to pull from
          "show-fields": "bodyText,trailText,byline",  # fields we want back                                             
          "page-size": num_articles,  # how many articles                                                                
          "order-by": "newest",       # latest first                                                                     
          "api-key": API_KEY                                                                                             
      }                                                                                                                  
                                                                                                                         
      response = requests.get(url, params=params)                                                                      
      return response.json()

def main():
      print("\n" + "="*60)
      print("GUARDIAN API TEST")                                                                                         
      print("="*60)
                                                                                                                         
      for topic in TOPICS:                                                                                             
          print(f"\n\n── TOPIC: {topic.upper()} ──────────────────────────")
                                                                                                                         
          data = fetch_articles(topic, num_articles=3)
          articles = data.get("response", {}).get("results", [])                                                         
                                                                                                                         
          if not articles:
              print("  No articles returned")                                                                            
              continue                                                                                                 

          for i, article in enumerate(articles, 1):                                                                      
              title = article.get("webTitle", "No title")
              date = article.get("webPublicationDate", "")                                                               
              url = article.get("webUrl", "")                                                                            
              fields = article.get("fields", {})
              body = fields.get("bodyText", "")                                                                          
              summary = fields.get("trailText", "")                                                                      
              author = fields.get("byline", "Unknown")
                                                                                                                         
              print(f"\n  [{i}] {title}")                                                                                
              print(f"      Date:    {date}")
              print(f"      Author:  {author}")                                                                          
              print(f"      URL:     {url}")                                                                           
              print(f"      Summary: {summary[:150]}...")                                                                
              print(f"      Body:    {body[:300]}...")
              print(f"      Body length: {len(body)} chars")                                                             
                                                                                                                       
      print("\n\n" + "="*60)                                                                                             
      print("DONE — if you see body text above, the API is working")                                                   
      print("="*60)                                                                                                      
  
if __name__ == "__main__":                                                                                             
      main()