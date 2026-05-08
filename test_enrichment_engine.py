#!/usr/bin/env python3
"""
Unit tests for EnrichmentEngine
Tests cache hit/miss scenarios and malformed data handling
"""

import pytest
from unittest.mock import Mock
from enrichment.enrichment_engine import EnrichmentEngine, EnrichmentResult


class TestEnrichmentEngine:
    """Test suite for EnrichmentEngine"""
    
    def setup_method(self):
        """Setup test fixtures with mocked dependencies"""
        self.mock_cache = Mock()
        self.mock_scraper = Mock()
        self.engine = EnrichmentEngine(
            cache_manager=self.mock_cache,
            contact_scraper=self.mock_scraper
        )
    
    def test_enrich_contractor_cache_hit(self):
        """Test successful cache hit scenario"""
        # Setup cache hit
        cached_data = {
            'website': 'https://example.com',
            'email': 'contact@example.com',
            'phone': '555-1234'
        }
        self.mock_cache.get.return_value = cached_data
        
        contractor = {'company_name': 'Test Company', 'license_number': 'LIC123'}
        result = self.engine.enrich_contractor(contractor)
        
        assert isinstance(result, EnrichmentResult)
        assert result.cache_hit is True
        assert result.company_name == 'Test Company'
        assert result.website == 'https://example.com'
        
        # Verify cache was checked
        self.mock_cache.get.assert_called_once_with('Test Company', 'LIC123')
        
        # Verify scraper was not called on cache hit
        self.mock_scraper.scrape_contact_info.assert_not_called()
    
    def test_enrich_contractor_cache_miss_with_scraping(self):
        """Test cache miss with successful website scraping"""
        # Setup cache miss
        self.mock_cache.get.return_value = None
        
        # Setup successful scraping
        scrape_result = {
            'success': True,
            'emails': ['info@example.com', 'john@example.com'],
            'phone_numbers': ['555-1234'],
            'contact_urls': ['https://example.com/contact']
        }
        self.mock_scraper.scrape_contact_info.return_value = scrape_result
        
        contractor = {
            'company_name': 'Test Company',
            'license_number': 'LIC123',
            'website': 'https://example.com'
        }
        
        result = self.engine.enrich_contractor(contractor)
        
        assert isinstance(result, EnrichmentResult)
        assert result.cache_hit is False
        assert result.scraped_successfully is True
        assert result.website == 'https://example.com'
        
        # Verify scraper was called
        self.mock_scraper.scrape_contact_info.assert_called_once_with('https://example.com')
    
    def test_enrich_contractor_scraping_failure(self):
        """Test cache miss with failed website scraping"""
        # Setup cache miss
        self.mock_cache.get.return_value = None
        
        # Setup failed scraping
        scrape_result = {
            'success': False,
            'emails': [],
            'phone_numbers': [],
            'contact_urls': []
        }
        self.mock_scraper.scrape_contact_info.return_value = scrape_result
        
        contractor = {
            'company_name': 'Test Company',
            'license_number': 'LIC123',
            'website': 'https://badwebsite.com'
        }
        
        result = self.engine.enrich_contractor(contractor)
        
        assert isinstance(result, EnrichmentResult)
        assert result.cache_hit is False
        assert result.scraped_successfully is False
        assert result.email is None
    
    def test_malformed_contractor_data(self):
        """Test handling of malformed contractor data"""
        # Setup cache miss
        self.mock_cache.get.return_value = None
        
        # Test with missing fields
        contractor = {'license_number': 'LIC123'}
        result = self.engine.enrich_contractor(contractor)
        
        assert isinstance(result, EnrichmentResult)
        assert result.company_name == ''
        
        # Test with None values
        contractor = {'company_name': None, 'license_number': None}
        result = self.engine.enrich_contractor(contractor)
        
        assert result.company_name == ''
        assert result.license_number == ''
    
    def test_empty_contractor_data(self):
        """Test handling of empty contractor data"""
        self.mock_cache.get.return_value = None
        
        result = self.engine.enrich_contractor({})
        
        assert isinstance(result, EnrichmentResult)
        assert result.company_name == ''
        assert result.cache_hit is False
