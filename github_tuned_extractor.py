#!/usr/bin/env python3
"""
TUNED GitHub Extractor for LLM Consumption
Handles bot detection, extracts structured data, returns clean JSON/markdown
"""

import json
import re
import sys
from html.parser import HTMLParser

class GitHubProfileParser(HTMLParser):
    """Parse GitHub profile HTML into structured data for LLMs"""
    
    def __init__(self):
        super().__init__()
        self.data = {
            "profile": {},
            "repositories": [],
            "meta": {
                "extractor_version": "2.0",
                "optimized_for": "LLM_consumption",
                "format": "structured_json"
            }
        }
        self.current_tag = None
        self.in_repo_card = False
        self.repo_buffer = {}
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self.current_tag = tag
        
        # Detect bot/captcha pages
        if tag == 'div' and 'captcha' in attrs_dict.get('class', ''):
            self.data["error"] = "Bot detection page encountered"
            return
            
        # Profile avatar
        if tag == 'img' and 'avatar' in attrs_dict.get('class', ''):
            self.data["profile"]["avatar"] = attrs_dict.get('src', '')
            
        # Repository links
        if tag == 'a' and '/m5it/' in attrs_dict.get('href', ''):
            repo_name = attrs_dict['href'].split('/')[-1]
            if repo_name and repo_name not in [r.get('name') for r in self.data["repositories"]]:
                self.repo_buffer = {"name": repo_name, "url": "https://github.com" + attrs_dict['href']}
                self.in_repo_card = True
                
    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
            
        # Extract profile name (first h1 or vcard-fullname)
        if self.current_tag in ['h1', 'span', 'div']:
            if 'full' in text.lower() or not self.data["profile"].get("name"):
                if len(text) < 100 and not text.startswith('http'):
                    self.data["profile"]["name"] = text
                    
        # Repository description
        if self.in_repo_card and self.current_tag == 'p':
            self.repo_buffer["description"] = text
            
        # Language/stars extraction via pattern matching
        if re.match(r'^[A-Z][a-z]+$', text) and len(text) < 20:
            self.repo_buffer["language"] = text
            
    def handle_endtag(self, tag):
        if tag == 'a' and self.in_repo_card and self.repo_buffer:
            self.data["repositories"].append(self.repo_buffer)
            self.repo_buffer = {}
            self.in_repo_card = False
            
    def get_structured_output(self):
        """Return LLM-optimized format"""
        # Deduplicate repos
        seen = set()
        unique_repos = []
        for repo in self.data["repositories"]:
            if repo.get("name") and repo["name"] not in seen:
                seen.add(repo["name"])
                unique_repos.append(repo)
        self.data["repositories"] = unique_repos
        
        # Add summary for quick LLM parsing
        self.data["summary"] = {
            "total_repos": len(unique_repos),
            "has_profile_data": bool(self.data["profile"]),
            "repo_names": [r["name"] for r in unique_repos[:5]]
        }
        
        return json.dumps(self.data, indent=2, ensure_ascii=False)

def extract_from_html(html_content):
    """Main extraction function"""
    parser = GitHubProfileParser()
    
    # Check for common bot blocks
    if any(x in html_content for x in ['captcha', 'robot', ' rate limit', '403']):
        return json.dumps({
            "error": "Bot detection or rate limit",
            "suggestion": "Try authenticated requests or API endpoints",
            "raw_snippet": html_content[:500]
        }, indent=2)
    
    parser.feed(html_content)
    return parser.get_structured_output()

if __name__ == "__main__":
    # Read from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            html = f.read()
    else:
        html = sys.stdin.read()
        
    print(extract_from_html(html))
