#!/usr/bin/env python3
import os
import json
import ast
from pathlib import Path

def analyze_test_coverage():
    """Analyze test coverage by examining test files and source files."""
    test_files = list(Path('.').glob('test*.py')) + list(Path('tests').glob('*.py'))
    source_files = [f for f in Path('.').glob('*.py') if not f.name.startswith('test') and f.name != 'validate_coverage.py']
    
    coverage_data = {
        'total_source_files': len(source_files),
        'total_test_files': len(test_files),
        'tested_modules': [],
        'untested_modules': [],
        'coverage_percentage': 0
    }
    
    # Analyze which modules have corresponding tests
    for source_file in source_files:
        module_name = source_file.stem
        has_test = any(f'test_{module_name}' in tf.name or f'{module_name}_test' in tf.name for tf in test_files)
        
        if has_test:
            coverage_data['tested_modules'].append(module_name)
        else:
            coverage_data['untested_modules'].append(module_name)
    
    if coverage_data['total_source_files'] > 0:
        coverage_data['coverage_percentage'] = (len(coverage_data['tested_modules']) / coverage_data['total_source_files']) * 100
    
    return coverage_data

if __name__ == '__main__':
    coverage = analyze_test_coverage()
    print(json.dumps(coverage, indent=2))
    
    if coverage['coverage_percentage'] >= 80:
        print('\n✅ Coverage target of 80% met!')
    else:
        print(f'\n❌ Coverage is {coverage["coverage_percentage"]:.1f}%, below 80% target')
        print('Untested modules:', coverage['untested_modules'])