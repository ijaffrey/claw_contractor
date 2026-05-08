"""Enrichment engine for contractor data."""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

from cache_manager import CacheManager
from contact_page_scraper import ContactPageScraper

logger = logging.getLogger(__name__)


@dataclass
class EnrichmentResult:
    """Result of contractor enrichment process."""
    company_name: str
    license_number: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    business_description: Optional[str] = None
    social_media: Optional[Dict[str, str]] = None
    cache_hit: bool = False
    scraped_successfully: bool = False
    error_message: Optional[str] = None


class EnrichmentEngine:
    """Orchestrates cache lookup, scraping, and result merging for contractor data."""
    
    def __init__(self, cache_manager: CacheManager = None, contact_scraper: ContactPageScraper = None):
        self.cache_manager = cache_manager or CacheManager()
        self.contact_scraper = contact_scraper or ContactPageScraper()
        self.logger = logging.getLogger(__name__)
    
    def enrich_contractor(self, contractor: Dict[str, Any]) -> EnrichmentResult:
        """Main enrichment method - checks cache, scrapes on miss, returns structured result."""
        try:
            company_name = contractor.get('company_name', '')
            license_number = contractor.get('license_number', '')
            
            # Check cache first using CacheManager's compound key interface
            cached_data = self.cache_manager.get(company_name, license_number)
            if cached_data:
                self.logger.info(f"Cache hit for contractor: {company_name}")
                result = self._merge_results(contractor, cached_data)
                result.cache_hit = True
                return result
            
            # Cache miss - scrape website if available
            website = contractor.get('website')
            scraped_data = None
            
            if website:
                self.logger.info(f"Cache miss - scraping website for: {company_name}")
                try:
                    scraped_data = self.contact_scraper.scrape_contact_page(website)
                    
                    # Cache the results if scraping was successful
                    if scraped_data and scraped_data.get('success'):
                        self.cache_manager.set(company_name, license_number, scraped_data)
                        self.logger.info(f"Cached new data for: {company_name}")
                        
                except Exception as scrape_error:
                    self.logger.error(f"Scraping failed for {website}: {str(scrape_error)}")
                    scraped_data = None
            else:
                self.logger.warning(f"No website available for contractor: {company_name}")
            
            result = self._merge_results(contractor, scraped_data)
            return result
            
        except Exception as e:
            self.logger.error(f"Enrichment failed for contractor {contractor.get('company_name', 'Unknown')}: {str(e)}")
            result = EnrichmentResult(
                company_name=contractor.get('company_name', ''),
                license_number=contractor.get('license_number'),
                website=contractor.get('website'),
                error_message=str(e)
            )
            return result

    def _merge_results(self, contractor: Dict[str, Any], scraped_data: Optional[Dict[str, Any]]) -> EnrichmentResult:
        """Merge original contractor data with scraped results."""
        result = EnrichmentResult(
            company_name=contractor.get('company_name', ''),
            license_number=contractor.get('license_number'),
            website=contractor.get('website'),
            cache_hit=False,
            scraped_successfully=scraped_data is not None and scraped_data.get('success', False)
        )
        
        if scraped_data and scraped_data.get('success'):
            # Update with scraped data, preserving original values where not found
            result.email = scraped_data.get('email') or scraped_data.get('emails', [None])[0] or contractor.get('email')
            result.phone = scraped_data.get('phone') or contractor.get('phone')
            result.address = scraped_data.get('address') or contractor.get('address')
            result.contact_name = scraped_data.get('contact_name') or contractor.get('contact_name')
            result.business_description = scraped_data.get('business_description') or contractor.get('business_description')
            result.social_media = scraped_data.get('social_media') or contractor.get('social_media')
        else:
            # No scraped data - use original contractor data
            result.email = contractor.get('email')
            result.phone = contractor.get('phone')
            result.address = contractor.get('address')
            result.contact_name = contractor.get('contact_name')
            result.business_description = contractor.get('business_description')
            result.social_media = contractor.get('social_media')
        
        return result
