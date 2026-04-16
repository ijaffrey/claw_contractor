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
    def filter_high_value_projects(self, grouped_permits: Dict[str, List[Dict[str, Any]]], 
                                  min_value: Union[int, float, Decimal] = 50000) -> Dict[str, Dict[str, Any]]:
        """Filter projects with total value >= min_value (default $50k)."""
        high_value_projects = {}
        min_threshold = Decimal(str(min_value))
        
        for address, permits in grouped_permits.items():
            total_value = self.calculate_project_value(permits)
            
            if total_value >= min_threshold:
                high_value_projects[address] = {
                    'address': address,
                    'permits': permits,
                    'total_value': total_value,
                    'permit_count': len(permits),
                    'created_at': datetime.now().isoformat()
                }
        
        return high_value_projects
    
    def aggregate_projects(self, permits: Optional[List[Dict[str, Any]]] = None, 
                          min_value: Union[int, float, Decimal] = 50000) -> Dict[str, Dict[str, Any]]:
        """Main method to aggregate permits into high-value projects."""
        try:
            if permits is None:
                self.logger.info("No permits provided, using empty list for testing")
                permits = []
            
            if not permits:
                self.logger.warning("No permits found")
                return {}
            
            self.logger.info(f"Processing {len(permits)} permits")
            
            # Group permits by address
            grouped = self.group_permits_by_address(permits)
            self.logger.info(f"Grouped permits into {len(grouped)} unique addresses")
            
            # Filter for high-value projects
            high_value = self.filter_high_value_projects(grouped, min_value)
            self.logger.info(f"Found {len(high_value)} projects with value >= ${min_value}")
            
            return high_value
            
        except Exception as e:
            self.logger.error(f"Error aggregating projects: {e}")
            raise

def get_high_value_projects(min_value: Union[int, float, Decimal] = 50000) -> Dict[str, Dict[str, Any]]:
    """Convenience function to get high-value projects."""
    aggregator = ProjectAggregator()
    return aggregator.aggregate_projects(min_value=min_value)


if __name__ == '__main__':
    import sys
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Default to $50k threshold, allow command line override
        min_value = 50000
        if len(sys.argv) > 1:
            min_value = float(sys.argv[1])
        
        logger.info(f"Aggregating projects with minimum value: ${min_value:,.2f}")
        
        # Test with sample data since permit_store may not have data
        sample_permits = [
            {
                'address': '123 Main St Brooklyn NY',
                'estimated_job_costs': '75000',
                'job_type': 'Renovation'
            },
            {
                'address': '123 MAIN ST BROOKLYN NY',
                'estimated_job_costs': '25000',
                'job_type': 'Alteration'
            },
            {
                'address': '456 Oak Ave Queens NY',
                'estimated_job_costs': '30000',
                'job_type': 'New Building'
            }
        ]
        
        aggregator = ProjectAggregator()
        projects = aggregator.aggregate_projects(sample_permits, min_value=min_value)
        
        if projects:
            logger.info(f"\nFound {len(projects)} high-value projects:")
            for address, project in projects.items():
                logger.info(f"  {address}: ${project['total_value']:,.2f} ({project['permit_count']} permits)")
        else:
            logger.info("No high-value projects found")
            
        # Output JSON for programmatic use
        print(json.dumps({k: {**v, 'total_value': str(v['total_value'])} for k, v in projects.items()}, 
                        indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Failed to aggregate projects: {e}")
        sys.exit(1)