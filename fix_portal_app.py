#!/usr/bin/env python3
"""
Fix indentation error in portal/app.py at line 747
"""

import re

def fix_portal_app():
    """Fix the indentation error in portal/app.py"""
    
    with open('portal/app.py', 'r') as f:
        lines = f.readlines()
    
    # Find and fix the problematic line around 747
    for i, line in enumerate(lines, 1):
        if i == 747:  # Line 747 has unexpected indent
            # Check if it's the misplaced SQL query
            if 'FROM campaigns' in line:
                # This line should be part of a function, likely the previous route
                # Remove the extra indentation or move it to proper place
                # Looking at context, it seems like orphaned SQL that should be removed
                print(f"Removing orphaned SQL at line {i}: {line.strip()}")
                lines[i-1] = ''  # Remove the problematic line
            elif 'ORDER BY name' in line:
                print(f"Removing orphaned SQL at line {i}: {line.strip()}")
                lines[i-1] = ''
    
    # Write the fixed file
    with open('portal/app.py', 'w') as f:
        f.writelines(lines)
    
    print("Fixed portal/app.py indentation error")

if __name__ == '__main__':
    fix_portal_app()