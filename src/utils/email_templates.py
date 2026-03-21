"""
Email template utilities for contractor notifications and customer communications.

This module provides functions to generate professional HTML and text email templates
for various stages of the lead processing workflow.
"""

from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import base64
import os


def contractor_notification_template(lead_summary: Dict[str, Any], photos: List[Dict[str, str]]) -> Tuple[str, str]:
    """
    Generate contractor notification email template.
    
    Args:
        lead_summary: Dictionary containing lead information
        photos: List of photo dictionaries with 'filename' and 'data' keys
        
    Returns:
        Tuple of (html_content, text_content)
    """
    # Extract lead information with defaults
    customer_name = lead_summary.get('customer_name', 'Not provided')
    phone = lead_summary.get('phone', 'Not provided')
    email = lead_summary.get('email', 'Not provided')
    address = lead_summary.get('address', 'Not provided')
    service_type = lead_summary.get('service_type', 'General contracting')
    description = lead_summary.get('description', 'No description provided')
    urgency = lead_summary.get('urgency', 'Standard')
    budget = lead_summary.get('budget', 'Not specified')
    timeline = lead_summary.get('timeline', 'Flexible')
    lead_source = lead_summary.get('source', 'Website')
    created_at = lead_summary.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Generate HTML template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Lead Notification</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .lead-info {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 4px 4px 0;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .info-item {{
            background-color: #ffffff;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }}
        .info-label {{
            font-weight: 600;
            color: #495057;
            font-size: 14px;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .info-value {{
            color: #212529;
            font-size: 16px;
        }}
        .urgency {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .urgency-high {{
            background-color: #dc3545;
            color: white;
        }}
        .urgency-medium {{
            background-color: #fd7e14;
            color: white;
        }}
        .urgency-standard {{
            background-color: #28a745;
            color: white;
        }}
        .description-section {{
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 20px;
            margin: 20px 0;
        }}
        .photos-section {{
            margin: 30px 0;
        }}
        .photos-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .photo-item {{
            text-align: center;
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }}
        .cta-section {{
            text-align: center;
            padding: 30px 0;
            background-color: #f8f9fa;
            margin: 20px -30px -30px -30px;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            margin: 0 10px;
            transition: transform 0.2s;
        }}
        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 14px;
            background-color: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔔 New Lead Alert</h1>
            <p>A potential customer is interested in your services</p>
        </div>
        
        <div class="content">
            <div class="lead-info">
                <h2 style="margin-top: 0; color: #495057;">Lead Summary</h2>
                <p><strong>Lead Source:</strong> {lead_source} | <strong>Created:</strong> {created_at}</p>
                <span class="urgency urgency-{urgency.lower()}">{urgency} Priority</span>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Customer Name</div>
                    <div class="info-value">{customer_name}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Phone Number</div>
                    <div class="info-value">{phone}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Email Address</div>
                    <div class="info-value">{email}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Service Type</div>
                    <div class="info-value">{service_type}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Project Address</div>
                    <div class="info-value">{address}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Budget Range</div>
                    <div class="info-value">{budget}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Timeline</div>
                    <div class="info-value">{timeline}</div>
                </div>
            </div>
            
            <div class="description-section">
                <h3 style="margin-top: 0; color: #495057;">Project Description</h3>
                <p style="white-space: pre-wrap; margin: 0;">{description}</p>
            </div>
            
            {_generate_photos_section_html(photos)}
            
            <div class="cta-section">
                <h3 style="color: #495057;">Ready to Connect?</h3>
                <a href="tel:{phone}" class="cta-button">📞 Call Now</a>
                <a href="mailto:{email}" class="cta-button">✉️ Send Email</a>
            </div>
        </div>
        
        <div class="footer">
            <p>This lead was automatically processed by the Claw Contractor system.</p>
            <p>Please respond promptly to maximize conversion opportunities.</p>
        </div>
    </div>
</body>
</html>
    """
    
    # Generate text template
    text_content = f"""
NEW LEAD NOTIFICATION
====================

LEAD SUMMARY
------------
Lead Source: {lead_source}
Created: {created_at}
Priority: {urgency}

CUSTOMER INFORMATION
-------------------
Name: {customer_name}
Phone: {phone}
Email: {email}
Address: {address}

PROJECT DETAILS
--------------
Service Type: {service_type}
Budget Range: {budget}
Timeline: {timeline}

PROJECT DESCRIPTION
------------------
{description}

{_generate_photos_section_text(photos)}

NEXT STEPS
----------
1. Call the customer at {phone}
2. Send an email to {email}
3. Schedule a consultation if appropriate
4. Update the lead status in your system

This lead was automatically processed by the Claw Contractor system.
Please respond promptly to maximize conversion opportunities.
    """
    
    return html_content.strip(), text_content.strip()


def customer_handoff_template(customer_name: str, contractor_info: Dict[str, str], next_steps: List[str]) -> Tuple[str, str]:
    """
    Generate customer handoff email template.
    
    Args:
        customer_name: Name of the customer
        contractor_info: Dictionary containing contractor details
        next_steps: List of next steps for the customer
        
    Returns:
        Tuple of (html_content, text_content)
    """
    # Extract contractor information with defaults
    contractor_name = contractor_info.get('name', 'Your assigned contractor')
    contractor_phone = contractor_info.get('phone', 'Not provided')
    contractor_email = contractor_info.get('email', 'Not provided')
    company_name = contractor_info.get('company_name', 'Contractor Services')
    license_number = contractor_info.get('license_number', '')
    specialties = contractor_info.get('specialties', [])
    rating = contractor_info.get('rating', '')
    experience_years = contractor_info.get('experience_years', '')
    
    # Generate HTML template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>We Found Your Perfect Contractor!</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 700px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #495057;
            margin-bottom: 25px;
        }}
        .contractor-card {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
            padding: 25px;
            margin: 25px 0;
            border: 1px solid #dee2e6;
        }}
        .contractor-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .contractor-avatar {{
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
            margin-right: 20px;
        }}
        .contractor-name {{
            font-size: 24px;
            font-weight: 600;
            color: #212529;
            margin: 0;
        }}
        .company-name {{
            color: #6c757d;
            margin: 5px 0 0 0;
        }}
        .contractor-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .detail-item {{
            background-color: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }}
        .detail-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        .detail-value {{
            font-size: 16px;
            color: #212529;
            font-weight: 500;
        }}
        .specialties {{
            margin: 20px 0;
        }}
        .specialty-tag {{
            display: inline-block;
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 12px;
            margin: 3px;
            font-weight: 500;
        }}
        .rating-stars {{
            color: #ffc107;
            font-size: 18px;
        }}
        .contact-section {{
            background-color: #ffffff;
            border: 2px solid #28a745;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 25px 0;
        }}
        .contact-buttons {{
            margin: 20px 0;
        }}
        .contact-button {{
            display: inline-block;
            padding: 12px 24px;
            margin: 5px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
        }}
        .btn-secondary {{
            background-color: white;
            color: #28a745;
            border: 2px solid #28a745;
        }}
        .contact-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        }}
        .next-steps {{
            background-color: #f8f9fa;
            border-left: 4px solid #17a2b8;
            padding: 20px;
            margin: 25px 0;
            border-radius: 0 6px 6px 0;
        }}
        .step-list {{
            list-style: none;
            padding: 0;
        }}
        .step-item {{
            display: flex;
            align-items: flex-start;
            margin: 15px 0;
        }}
        .step-number {{
            background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        .step-content {{
            flex-grow: 1;
            padding-top: 5px;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 25px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
            border-top: 1px solid #dee2e6;
        }}
        .guarantee-badge {{
            background: linear-gradient(135deg, #ffc107 0%, #ff8f00 100%);
            color: #212529;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            display: inline-block;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Great News, {customer_name}!</h1>
            <p>We've found the perfect contractor for your project</p>
        </div>
        
        <div class="content">
            <div class="greeting">
                <p>Hi {customer_name},</p>
                <p>We're excited to connect you with a qualified professional who specializes in exactly what you need. Based on your project requirements, we've carefully selected the best contractor in your area.</p>
            </div>
            
            <div class="contractor-card">
                <div class="contractor-header">
                    <div class="contractor-avatar">
                        {contractor_name[0].upper() if contractor_name else 'C'}
                    </div>
                    <div>
                        <h2 class="contractor-name">{contractor_name}</h2>
                        <p class="company-name">{company_name}</p>
                    </div>
                </div>
                
                <div class="contractor-details">
                    {f'<div class="detail-item"><div class="detail-label">Phone</div><div class="detail-value">{contractor_phone}</div></div>' if contractor_phone != 'Not provided' else ''}
                    {f'<div class="detail-item"><div class="detail-label">Email</div><div class="detail-value">{contractor_email}</div></div>' if contractor_email != 'Not provided' else ''}
                    {f'<div class="detail-item"><div class="detail-label">License #</div><div class="detail-value">{license_number}</div></div>' if license_number else ''}
                    {f'<div class="detail-item"><div class="detail-label">Experience</div><div class="detail-value">{experience_years} years</div></div>' if experience_years else ''}
                    {f'<div class="detail-item"><div class="detail-label">Rating</div><div class="detail-value"><span class="rating-stars">{"★" * int(float(rating))}</span> {rating}/5</div></div>' if rating else ''}
                </div>
                
                {f'<div class="specialties"><h4 style="margin: 0 0 10px 0; color: #495057;">Specialties:</h4>{"".join([f"<span class='specialty-tag'>{spec}</span>" for spec in specialties])}</div>' if specialties else ''}
            </div>
            
            <div class="contact-section">
                <h3 style="margin-top: 0; color: #28a745;">Ready to Get Started?</h3>
                <div class="guarantee-badge">🛡️ Licensed & Insured Professional</div>
                <div class="contact-buttons">
                    <a href="tel:{contractor_phone}" class="contact-button btn-primary">📞 Call {contractor_name}</a>
                    <a href="mailto:{contractor_email}" class="contact-button btn-secondary">✉️ Send Email</a>
                </div>
                <p style="margin: 15px 0 0 0; color: #6c757d; font-size: 14px;">
                    Your contractor is expecting your call and ready to discuss your project!
                </p>
            </div>
            
            <div class="next-steps">
                <h3 style="margin-top: 0; color: #495057;">What Happens Next?</h3>
                <ul class="step-list">
                    {_generate_next_steps_html(next_steps)}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Need help or have questions?</strong></p>
            <p>Our team is here to support you throughout the entire process.</p>
            <p>Contact us anytime at support@clawcontractor.com</p>
            <br>
            <p style="font-size: 12px; color: #adb5bd;">
                This contractor has been pre-screened and meets our quality standards.
                All work should be discussed directly with your contractor.
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    # Generate text template
    specialties_text = ', '.join(specialties) if specialties else 'General contracting'
    
    text_content = f"""
GREAT NEWS, {customer_name.upper()}!
================================

We've found the perfect contractor for your project.

YOUR CONTRACTOR DETAILS
-----------------------
Name: {contractor_name}
Company: {company_name}
Phone: {contractor_phone}
Email: {contractor_email}
{f'License #: {license_number}' if license_number else ''}
{f'Experience: {experience_years} years' if experience_years else ''}
{f'Rating: {rating}/5 stars' if rating else ''}
Specialties: {specialties_text}

READY TO GET STARTED?
---------------------
📞 Call {contractor_name} at {contractor_phone}
✉️ Email {contractor_email}

🛡️ This is a licensed & insured professional who is expecting your call!

WHAT HAPPENS NEXT?
------------------
{_generate_next_steps_text(next_steps)}

NEED HELP?
----------
Our team is here to support you throughout the entire process.
Contact us anytime at support@clawcontractor.com

This contractor has been pre-screened and meets our quality standards.
All work should be discussed directly with your contractor.
    """
    
    return html_content.strip(), text_content.strip()


def lead_summary_template(lead_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generate lead summary email template.
    
    Args:
        lead_data: Dictionary containing comprehensive lead information
        
    Returns:
        Tuple of (html_content, text_content)
    """
    # Extract and organize lead data
    customer_info = lead_data.get('customer_info', {})
    project_info = lead_data.get('project_info', {})
    lead_metrics = lead_data.get('metrics', {})
    timeline = lead_data.get('timeline', {})
    photos = lead_data.get('photos', [])
    
    customer_name = customer_info.get('name', 'Unknown Customer')
    phone = customer_info.get('phone', 'Not provided')
    email = customer_info.get('email', 'Not provided')
    address = project_info.get('address', 'Not provided')
    service_type = project_info.get('service_type', 'General contracting')
    description = project_info.get('description', 'No description provided')
    budget = project_info.get('budget', 'Not specified')
    urgency = project_info.get('urgency', 'Standard')
    
    lead_score = lead_metrics.get('score', 'N/A')
    lead_source = lead_metrics.get('source', 'Unknown')
    conversion_probability = lead_metrics.get('conversion_probability', 'N/A')
    
    created_at = timeline.get('created', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    follow_up_date = timeline.get('follow_up', 'Not scheduled')
    
    # Generate HTML template
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lead Summary Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }}
        .card {{
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }}
        .card-header {{
            font-size: 14px;
            color: #6c757d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
            font-weight: 600;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 8px;
        }}
        .card-content {{
            color: #212529;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 5px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }}
        .score-high {{
            color: #28a745;
        }}
        .score-medium {{
            color: #ffc107;
        }}
        .score-low {{
            color: #dc3545;
        }}
        .priority-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .priority-high {{
            background-color: #dc3545;
            color: white;
        }}
        .priority-medium {{
            background-color: #fd7e14;
            color: white;
        }}
        .priority-standard {{
            background-color: #28a745;
            color: white;
        }}
        .description-section {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
            border-left: 4px solid #6c5ce7;
        }}
        .contact-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .contact-item {{
            background-color: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            text-align: center;
        }}
        .contact-icon {{
            font-size: 24px;
            margin-bottom: 10px;
        }}
        .contact-value {{
            font-weight: 600;
            color: #495057;
        }}
        .timeline-section {{
            background-color: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }}
        .timeline-item {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .timeline-icon {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            margin-right: 15px;
        }}
        .photos-preview {{
            margin: 25px 0;
        }}
        .photos-count {{
            background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
            color: white;
            padding: 10px 20px;
            