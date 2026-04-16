import logging
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from collections import defaultdict
from decimal import Decimal


class ProjectAggregator:
    """Groups permits by address and calculates total project values."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def group_permits_by_address(self, permits: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group permits by exact address match."""
        grouped = defaultdict(list)
        
        for permit in permits:
            address = self._normalize_address(permit.get('address', ''))
            if address:
                grouped[address].append(permit)
        
        return dict(grouped)
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for consistent grouping."""
        if not address:
            return ''
        
        # Basic normalization - remove extra spaces, convert to uppercase
        return ' '.join(address.strip().upper().split())

    def calculate_project_value(self, permits: List[Dict[str, Any]]) -> Decimal:
        """Calculate total project value from permits."""
        total_value = Decimal('0')
        
        for permit in permits:
            value = self._extract_permit_value(permit)
            if value is not None:
                total_value += value
        
        return total_value
    
    def _extract_permit_value(self, permit: Dict[str, Any]) -> Optional[Decimal]:
        """Extract numeric value from permit data."""
        # Try common field names for permit values based on NYC DOB permit structure
        value_fields = ['estimated_job_costs', 'estimated_cost', 'initial_cost', 'job_cost', 'cost', 'value']
        
        for field in value_fields:
            if field in permit and permit[field]:
                try:
                    # Handle string values with $ and commas
                    value_str = str(permit[field]).replace('$', '').replace(',', '').strip()
                    if value_str and value_str.replace('.', '').replace('-', '').isdigit():
                        return Decimal(value_str)
                except (ValueError, TypeError, AttributeError):
                    continue
        
        return None