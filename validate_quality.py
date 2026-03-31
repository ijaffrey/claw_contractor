#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

def validate_code_quality():
    """Validate code quality against defined standards."""
    quality_results = {
        'syntax_check': False,
        'import_check': False,
        'test_structure': False,
        'documentation': False,
        'overall_pass': False
    }
    
    # Check syntax of all Python files
    try:
        result = subprocess.run(['python3', '-m', 'py_compile'] + [str(f) for f in Path('.').glob('*.py')], 
                              capture_output=True, text=True)
        quality_results['syntax_check'] = result.returncode == 0
    except:
        quality_results['syntax_check'] = False
    
    # Check if test files can be imported
    test_files = list(Path('.').glob('test*.py'))
    import_success = 0
    for test_file in test_files:
        try:
            module_name = test_file.stem
            __import__(module_name)
            import_success += 1
        except:
            pass
    
    quality_results['import_check'] = import_success == len(test_files) if test_files else True
    
    # Check test structure exists
    required_files = ['test_strategy.md', 'quality_gates_definition.md', 'run_basic_tests.py']
    quality_results['test_structure'] = all(Path(f).exists() for f in required_files)
    
    # Check documentation completeness
    doc_files = list(Path('.').glob('*.md')) + list(Path('docs').glob('*.md'))
    quality_results['documentation'] = len(doc_files) >= 3
    
    # Overall pass requires all checks to pass
    quality_results['overall_pass'] = all([
        quality_results['syntax_check'],
        quality_results['import_check'], 
        quality_results['test_structure'],
        quality_results['documentation']
    ])
    
    return quality_results

if __name__ == '__main__':
    results = validate_code_quality()
    print(json.dumps(results, indent=2))
    
    if results['overall_pass']:
        print('\n✅ All quality gates passed!')
    else:
        print('\n❌ Quality validation failed:')
        for check, passed in results.items():
            if check != 'overall_pass' and not passed:
                print(f'  - {check}: FAILED')