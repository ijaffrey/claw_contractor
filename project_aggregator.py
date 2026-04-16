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