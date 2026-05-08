#!/usr/bin/env python3
"""
Unit tests for ContactPageScraper
Tests happy path scenarios and network error handling
"""

import pytest
import requests
from unittest.mock import Mock, patch
from contact_page_scraper import ContactPageScraper


class TestContactPageScraper:
    """Test suite for ContactPageScraper"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scraper = ContactPageScraper(timeout=5, max_retries=2)
    
    def test_init_with_defaults(self):
        """Test initialization with default values"""
        scraper = ContactPageScraper()
        assert scraper.timeout == 10
        assert scraper.max_retries == 3
        assert scraper.rate_limit_delay == 1.0
        assert len(scraper.contact_paths) > 0
        assert '/contact' in scraper.contact_paths
    
    @patch('contact_page_scraper.requests.Session.get')
    def test_scrape_contact_info_happy_path(self, mock_get):
        """Test successful contact info scraping"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><h1>Contact</h1><p>Email: john@example.com</p></body></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_contact_info('https://example.com')
        
        assert result['success'] is True
        assert result['base_url'] == 'https://example.com'
        assert len(result['contact_urls']) > 0
    
    @patch('contact_page_scraper.requests.Session.get')
    def test_scrape_contact_info_network_timeout(self, mock_get):
        """Test handling of network timeout errors"""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        result = self.scraper.scrape_contact_info('https://example.com')
        
        assert result['success'] is False
        assert result['base_url'] == 'https://example.com'
        assert result['emails'] == []
        assert result['contact_urls'] == []
    
    @patch('contact_page_scraper.requests.Session.get')
    def test_scrape_contact_info_connection_error(self, mock_get):
        """Test handling of connection errors"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        result = self.scraper.scrape_contact_info('https://example.com')
        
        assert result['success'] is False
        assert result['emails'] == []
    
    def test_extract_emails_from_content_valid_emails(self):
        """Test email extraction from HTML content"""
        content = '<html><body><p>Contact: john.doe@company.com</p><p>Support: support@company.com</p></body></html>'
        
        emails = self.scraper._extract_emails_from_content(content)
        
        assert 'john.doe@company.com' in emails
        assert 'support@company.com' in emails
    
    def test_filter_generic_emails(self):
        """Test filtering of generic email addresses"""
        emails = {
            'info@company.com',
            'contact@company.com', 
            'john.doe@company.com',
            'jane@company.com'
        }
        
        filtered = self.scraper._filter_generic_emails(emails)
        
        # Generic emails should be filtered out
        assert 'info@company.com' not in filtered
        assert 'contact@company.com' not in filtered
        
        # Specific emails should remain
        assert 'john.doe@company.com' in filtered
        assert 'jane@company.com' in filtered
    
    def test_malformed_url_input(self):
        """Test handling of malformed URL inputs"""
        result = self.scraper.scrape_contact_info('not-a-valid-url')
        
        assert result['success'] is False
        assert result['emails'] == []
        assert result['contact_urls'] == []
