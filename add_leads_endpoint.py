#!/usr/bin/env python3
"""Script to add the leads endpoint to portal/app.py"""

# Read the existing portal/app.py content
with open('portal/app.py', 'r') as f:
    app_content = f.read()

# Read the endpoint code
with open('portal/leads_endpoint.py', 'r') as f:
    endpoint_code = f.read()

# Find the last @app.route to insert after it
last_route_pos = app_content.rfind('@app.route')
if last_route_pos == -1:
    print('No @app.route found in portal/app.py')
    exit(1)

# Find the end of that route function
next_line = app_content.find('\n', last_route_pos)
next_func = app_content.find('\n@app.route', next_line)
if next_func == -1:
    # If no next route, look for 'if __name__'
    next_func = app_content.find('\nif __name__', next_line)
    if next_func == -1:
        # Insert at end of file
        next_func = len(app_content)

# Insert the new endpoint
new_content = app_content[:next_func] + '\n\n' + endpoint_code + '\n' + app_content[next_func:]

# Write back to portal/app.py
with open('portal/app.py', 'w') as f:
    f.write(new_content)

print('Successfully added /api/leads endpoint to portal/app.py')