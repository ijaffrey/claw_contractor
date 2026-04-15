#!/usr/bin/env python3
import sys
sys.path.append('portal')
from leads_endpoint import get_leads_data

# Test data variety
data = get_leads_data()
boroughs = set(lead.get('borough') for lead in data.get('leads', []))
trades = set(lead.get('trade') for lead in data.get('leads', []))

print(f'Boroughs ({len(boroughs)}): {sorted(list(boroughs))}')
print(f'Trades ({len(trades)}): {sorted(list(trades))}')
