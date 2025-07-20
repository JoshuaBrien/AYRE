import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

class WebContentHandler:
    def __init__(self, console):
        self.console = console
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def scrape_url(self, url):
        """Scrape content from a URL"""
        try:
            # Clean up URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            self.console.print(f"[cyan]🌐 Fetching content from: {url}[/cyan]")
            
            # Make request
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            title = self.extract_title(soup)
            description = self.extract_description(soup)
            
            # Extract main content
            content = self.extract_main_content(soup)
            
            # Extract links
            links = self.extract_links(soup, url)
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'links': links,
                'status': 'success'
            }
            
        except requests.exceptions.Timeout:
            return {'status': 'error', 'message': 'Request timed out'}
        except requests.exceptions.RequestException as e:
            return {'status': 'error', 'message': f'Network error: {str(e)}'}
        except Exception as e:
            return {'status': 'error', 'message': f'Parsing error: {str(e)}'}
    
    def extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Try h1 as fallback
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "No title found"
    
    def extract_description(self, soup):
        """Extract page description"""
        # Try meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            return text[:200] + "..." if len(text) > 200 else text
        
        return "No description found"
    
    def extract_main_content(self, soup):
        """Extract main text content from page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '#content', 
            '.post-content', '.entry-content', '.article-content'
        ]
        
        main_content = None
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            # Extract text and clean it up
            text = main_content.get_text()
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            # Limit length
            if len(text) > 5000:
                text = text[:5000] + "...\n[Content truncated for analysis]"
            return text
        
        return "No main content found"
    
    def extract_links(self, soup, base_url):
        """Extract important links from the page"""
        links = []
        for link in soup.find_all('a', href=True)[:10]:  # Limit to first 10 links
            href = link['href']
            text = link.get_text().strip()
            
            if href and text:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)
                links.append({'url': full_url, 'text': text})
        
        return links
    
    def format_web_content(self, data):
        """Format scraped content for display and analysis"""
        if data['status'] == 'error':
            return f"❌ Failed to scrape content: {data['message']}"
        
        formatted = f"""🌐 **Web Page Analysis**

**URL:** {data['url']}
**Title:** {data['title']}
**Description:** {data['description']}

**Main Content:**
{data['content']}
"""
        
        if data['links']:
            formatted += "\n**Important Links:**\n"
            for i, link in enumerate(data['links'][:5], 1):
                formatted += f"{i}. [{link['text']}]({link['url']})\n"
        
        return formatted
    
    def analyze_url_with_ai(self, url, user_question, message_history, gemini_model):
        """Scrape URL and analyze with AI"""
        # Scrape the content
        scraped_data = self.scrape_url(url)
        
        if scraped_data['status'] == 'error':
            self.console.print(f"[red]❌ Failed to analyze URL: {scraped_data['message']}[/red]")
            return None
        
        # Format content for AI
        web_content = self.format_web_content(scraped_data)
        
        # Display scraped content summary
        self.console.print(Panel(
            f"[green]✅ Successfully scraped: {scraped_data['title']}[/green]\n"
            f"Content length: {len(scraped_data['content'])} characters",
            title="Web Content Scraped",
            border_style="green"
        ))
        
        # Create AI prompt with web content
        if user_question:
            ai_prompt = f"Based on the following web page content, please answer this question: {user_question}\n\n{web_content}"
        else:
            ai_prompt = f"Please analyze and summarize the following web page content:\n\n{web_content}"
        
        # Add to message history and get AI response
        message_history.append({"role": "user", "content": ai_prompt})
        
        try:
            response = gemini_model.generate_content(ai_prompt)
            reply = response.text.strip()
            message_history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            error_msg = f"Error analyzing web content: {str(e)}"
            self.console.print(f"[red]❌ {error_msg}[/red]")
            return error_msg