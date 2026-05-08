#!/usr/bin/env python3
"""
Contact Page Scraper

Scrapes contact information from company websites by:
1. Trying common contact page paths (/contact, /contact-us, /about)
2. Extracting email addresses from page content
3. Filtering out generic addresses (info@, contact@, etc)
4. Rate limiting requests to 1 req/sec per domain
5. Handling HTTP errors and timeouts gracefully
"""

import requests
import re
import time
import logging
from typing import List, Dict, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

logger = logging.getLogger(__name__)


class ContactPageScraper:
    """
    Scraper for extracting contact information from company websites
    """
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """Initialize the contact page scraper
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
        # Set user agent to avoid bot blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting: track last request time per domain
        self.domain_last_request = {}
        self.rate_limit_delay = 1.0  # 1 second between requests per domain
        
        # Common contact page paths to try
        self.contact_paths = [
            '/contact',
            '/contact-us',
            '/contact_us',
            '/about',
            '/about-us',
            '/about_us',
            '/team',
            '/staff'
        ]
        
        # Generic email patterns to exclude
        self.generic_patterns = {
            r'^info@',
            r'^contact@',
            r'^support@',
            r'^help@',
            r'^sales@',
            r'^admin@',
            r'^webmaster@',
            r'^noreply@',
            r'^no-reply@',
            r'^donotreply@',
            r'^do-not-reply@',
            r'^hello@',
            r'^enquiry@',
            r'^enquiries@',
            r'^inquiry@',
            r'^inquiries@',
            r'^marketing@',
            r'^office@'
        }
    
    def _enforce_rate_limit(self, domain: str) -> None:
        """Enforce rate limiting for the given domain"""
        current_time = time.time()
        
        if domain in self.domain_last_request:
            time_since_last = current_time - self.domain_last_request[domain]
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        self.domain_last_request[domain] = time.time()
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL content with error handling and rate limiting
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content as string, or None if fetch failed
        """
        domain = urlparse(url).netloc.lower()
        self._enforce_rate_limit(domain)
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1})")
                response = self.session.get(
                    url, 
                    timeout=self.timeout, 
                    allow_redirects=True
                )
                
                # Check for successful response
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    logger.debug(f"Page not found: {url}")
                    return None
                elif response.status_code in [403, 401]:
                    logger.warning(f"Access denied for {url}: {response.status_code}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code} for {url}")
                    if attempt == self.max_retries - 1:
                        return None
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching {url} (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return None
                    
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error fetching {url} (attempt {attempt + 1})")
                if attempt == self.max_retries - 1:
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching {url}: {str(e)}")
                return None
            
            # Brief delay before retry
            if attempt < self.max_retries - 1:
                time.sleep(0.5)
        
        return None
    def _discover_contact_pages(self, base_url: str) -> List[str]:
        """Discover contact page URLs by trying common paths
        
        Args:
            base_url: Base URL of the website (e.g., https://example.com)
            
        Returns:
            List of URLs that returned successful responses
        """
        contact_urls = []
        
        for path in self.contact_paths:
            url = urljoin(base_url, path)
            content = self._fetch_url(url)
            if content:
                contact_urls.append(url)
                logger.debug(f"Found contact page: {url}")
        
        return contact_urls
    
    def _extract_emails_from_content(self, content: str) -> Set[str]:
        """Extract email addresses from page content using regex
        
        Args:
            content: HTML or text content to search
            
        Returns:
            Set of email addresses found
        """
        # Comprehensive email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Find all email matches
        emails = set(re.findall(email_pattern, content, re.IGNORECASE))
        
        # Clean up emails (remove surrounding punctuation, convert to lowercase)
        cleaned_emails = set()
        for email in emails:
            email = email.strip().lower()
            # Remove trailing punctuation that might be included by regex
            email = re.sub(r'[.,;:!?]+$', '', email)
            if '@' in email and '.' in email.split('@')[1]:
                cleaned_emails.add(email)
        
        return cleaned_emails
    def _filter_generic_emails(self, emails: Set[str]) -> Set[str]:
        """Filter out generic email addresses
        
        Args:
            emails: Set of email addresses to filter
            
        Returns:
            Set of non-generic email addresses
        """
        filtered_emails = set()
        
        for email in emails:
            is_generic = False
            for pattern in self.generic_patterns:
                if re.match(pattern, email, re.IGNORECASE):
                    is_generic = True
                    logger.debug(f"Filtering generic email: {email}")
                    break
            
            if not is_generic:
                filtered_emails.add(email)
        
        return filtered_emails
    
    def scrape_contact_info(self, base_url: str) -> Dict[str, any]:
        """Main method to scrape contact information from a website
        
        Args:
            base_url: Base URL of the website to scrape
            
        Returns:
            Dictionary containing:
                - contact_urls: List of contact page URLs found
                - emails: Set of non-generic email addresses
                - success: Boolean indicating if any contact info was found
        """
        try:
            # Ensure URL has protocol
            if not base_url.startswith(('http://', 'https://')):
                base_url = 'https://' + base_url
            
            logger.info(f"Scraping contact info from {base_url}")
            
            # Discover contact pages
            contact_urls = self._discover_contact_pages(base_url)
            
            # Extract emails from all contact pages
            all_emails = set()
            for url in contact_urls:
                content = self._fetch_url(url)
                if content:
                    page_emails = self._extract_emails_from_content(content)
                    all_emails.update(page_emails)
            
            # Also check the main page if no contact pages found
            if not contact_urls:
                logger.debug(f"No contact pages found, checking main page: {base_url}")
                main_content = self._fetch_url(base_url)
                if main_content:
                    main_emails = self._extract_emails_from_content(main_content)
                    all_emails.update(main_emails)
            
            # Filter out generic emails
            filtered_emails = self._filter_generic_emails(all_emails)
            
            result = {
                'base_url': base_url,
                'contact_urls': contact_urls,
                'emails': list(filtered_emails),  # Convert to list for JSON serialization
                'total_emails_found': len(all_emails),
                'filtered_emails_count': len(filtered_emails),
                'success': len(filtered_emails) > 0 or len(contact_urls) > 0
            }
            
            logger.info(f"Scraping complete: found {len(contact_urls)} contact pages, "
                       f"{len(filtered_emails)} valid emails (filtered {len(all_emails) - len(filtered_emails)} generic)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error scraping {base_url}: {str(e)}")
            return {
                'base_url': base_url,
                'contact_urls': [],
                'emails': [],
                'total_emails_found': 0,
                'filtered_emails_count': 0,
                'success': False,
                'error': str(e)
            }