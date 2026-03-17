"""
OpenClaw Test Scenarios - Core Test Library
Critical scenarios for conversation quality testing
"""

BUSINESSES = {
    'mikes_plumbing': {
        'name': "Mike's Plumbing",
        'trade_type': 'plumbing',
        'location': 'Brooklyn, NY',
        'brand_voice': "Friendly and direct, like a neighbor who knows their stuff. 20-year veteran who's seen it all. Brooklyn-based, no-nonsense but warm. Gets straight to the point.",
        'phone': '718-555-0142',
        'owner_name': 'Mike Rossi',
        'email': 'mike@mikesplumbing.com'
    },
    'summit_roofing': {
        'name': 'Summit Roofing',
        'trade_type': 'roofing',
        'location': 'Queens, NY',
        'brand_voice': "Professional and reassuring. 15 years in business. Handles insurance claims regularly. Warm but polished - like a contractor who's seen every type of roof damage and knows exactly what to do. Safety-conscious and detail-oriented.",
        'phone': '718-555-0283',
        'owner_name': 'Carlos Martinez',
        'email': 'carlos@summitroofing.com'
    },
    'brightline_electric': {
        'name': 'Brightline Electric',
        'trade_type': 'electrical',
        'location': 'Manhattan, NY',
        'brand_voice': "Calm, safety-focused, and precise. Licensed master electrician with 12 years experience. Takes electrical safety very seriously but explains things in plain English. Professional without being stiff. Thinks about code compliance and long-term solutions.",
        'phone': '212-555-0491',
        'owner_name': 'David Chen',
        'email': 'david@brightlineelectric.com'
    },
    'apex_construction': {
        'name': 'Apex Construction',
        'trade_type': 'general_contractor',
        'location': 'Tri-State Area',
        'brand_voice': "Polished and organized. 20+ years doing everything from small repairs to full gut renovations. Asks detailed questions upfront to understand scope. Friendly but businesslike - runs a tight ship. Good at setting realistic expectations for timelines and budgets.",
        'phone': '201-555-0847',
        'owner_name': 'Jennifer Okafor',
        'email': 'jen@apexconstruction.com'
    }
}

# Core test scenarios covering key edge cases
SCENARIOS = {
    'plumb_emergency_burst_pipe': {
        'business': 'mikes_plumbing',
        'urgency': 'emergency',
        'category': 'plumbing',
        'description': 'Emergency burst pipe - test brevity, no time commitment',
        'initial_email': {
            'subject': 'EMERGENCY - burst pipe flooding basement',
            'from_name': 'Jennifer Walsh',
            'from_email': 'jwalsh42@gmail.com',
            'body': "We have a MAJOR emergency! Pipe burst in the basement and water is POURING out. We shut off the main valve but there's already 2 inches of water down there. Please help ASAP! Jennifer Walsh 347-555-8291 124 Prospect Ave, Brooklyn 11215"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Yes we got it shut off. It's the pipe coming from the water heater. Can you come right now??",
                'ai_should': ['Be VERY brief', 'Validate they shut off water', 'Ask ONE question', 'Collect availability'],
                'ai_must_not': ['Re-ask for address', 'Promise specific time', 'Use clichés', 'Multiple questions']
            }
        ]
    },
    
    'plumb_medium_slow_drain': {
        'business': 'mikes_plumbing',
        'urgency': 'medium',
        'category': 'plumbing',
        'description': 'Medium urgency - test tone matching, acknowledge DIY attempts',
        'initial_email': {
            'subject': 'Kitchen sink draining slow',
            'from_name': 'Robert Chen',
            'from_email': 'robert.chen@gmail.com',
            'body': "Hey, my kitchen sink is draining really slow. Tried Drano twice, helped for a day then back to slow. Probably needs a snake? Not urgent but would like it fixed this week or next. Weekends work best."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Yeah, disposal on one side. Both sides drain slow though. House is about 40 years old if that matters.",
                'ai_should': ['Match relaxed tone', 'Note house age', 'Acknowledge DIY without lecture'],
                'ai_must_not': ['Lecture about Drano', 'Be overly formal', 'Ask multiple questions']
            }
        ]
    },
    
    'plumb_edge_minimal_info': {
        'business': 'mikes_plumbing',
        'urgency': 'medium',
        'category': 'plumbing',
        'description': 'Minimal info - test brevity matching',
        'initial_email': {
            'subject': 'Plumber needed',
            'from_name': 'Chris',
            'from_email': 'c.murphy@gmail.com',
            'body': "Need a plumber. Call me 555-0147."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Leaky faucet in bathroom. This week sometime.",
                'ai_should': ['Match terse style', 'Ask ONE thing', 'Keep VERY short'],
                'ai_must_not': ['Send wall of text', 'Try to warm them up', 'Ask multiple questions']
            }
        ]
    },
    
    'plumb_edge_angry': {
        'business': 'mikes_plumbing',
        'urgency': 'medium',
        'category': 'plumbing',
        'description': 'Angry customer - test direct confidence, no over-apologizing',
        'initial_email': {
            'subject': 'Need reliable plumber',
            'from_name': 'Steven Clark',
            'from_email': 'sclark@yahoo.com',
            'body': "I need a plumber who actually shows up. Last guy was 3 hours late, charged me \$400 to 'fix' a toilet that's STILL running, and won't return my calls. Can you fix a running toilet without screwing it up?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Just tell me yes or no - can you come this week and fix it properly?",
                'ai_should': ['Be direct and confident', 'Match no-nonsense tone', 'Ask ONE thing'],
                'ai_must_not': ['Say "I\'m sorry you had that experience"', 'Badmouth previous contractor', 'Over-apologize']
            }
        ]
    },
    
    'plumb_edge_price_shopper': {
        'business': 'mikes_plumbing',
        'urgency': 'low',
        'category': 'plumbing',
        'description': 'Price shopper - test directness, minimal qualification',
        'initial_email': {
            'subject': 'Toilet install price',
            'from_name': 'Mark Chen',
            'from_email': 'markc@gmail.com',
            'body': "How much to install a toilet? Replacing existing one. Just need a straight answer on price."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Straight swap, same location. I already bought the toilet.",
                'ai_should': ['Respect directness', 'Ask minimum needed', 'Keep SHORT (3 sentences max)'],
                'ai_must_not': ['Launch into full qualification', 'Try to warm them up', 'Give pricing']
            }
        ]
    },
    
    'plumb_not_lead_vendor': {
        'business': 'mikes_plumbing',
        'urgency': 'n/a',
        'category': 'plumbing',
        'description': 'Vendor email - should skip/not reply',
        'initial_email': {
            'subject': 'Premium PEX Fittings - 20% Off',
            'from_name': 'ProSupply Solutions',
            'from_email': 'sales@prosupply.com',
            'body': "Dear Plumbing Professional, We're offering 20% off all PEX fittings this month! Stock up now."
        },
        'expected_behavior': 'SKIP - do not reply, this is vendor solicitation',
        'conversation_flow': []
    },

    # ROOFING SCENARIOS
    'roof_emergency_storm_damage': {
        'business': 'summit_roofing',
        'urgency': 'emergency',
        'category': 'roofing',
        'description': 'Emergency storm damage - test photo request urgency',
        'initial_email': {
            'subject': 'Emergency - tree fell on roof during storm',
            'from_name': 'Maria Santos',
            'from_email': 'msantos@gmail.com',
            'body': "A tree branch came down on our roof during the storm last night. There's a hole and it's supposed to rain again tomorrow. We need someone ASAP. 45 Oak Street, Queens 11375. Maria Santos 917-555-3821"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "The hole is maybe 3 feet across. I can see into the attic. We put a tarp over it but wind keeps blowing it off.",
                'ai_should': ['Acknowledge severity', 'Ask for photos', 'Keep very brief'],
                'ai_must_not': ['Promise specific time', 'Give advice on tarp', 'Ask multiple questions']
            }
        ]
    },

    'roof_medium_missing_shingles': {
        'business': 'summit_roofing',
        'urgency': 'medium',
        'category': 'roofing',
        'description': 'Medium urgency - test insurance question handling',
        'initial_email': {
            'subject': 'Missing shingles after wind storm',
            'from_name': 'Tom Bradley',
            'from_email': 'tbradley44@yahoo.com',
            'body': "Hi, noticed we're missing some shingles after the windstorm last week. No leaks yet but want to get it fixed before we have problems. Does this work with insurance? How much does something like this usually cost?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Good question - I have State Farm. The roof is about 12 years old, asphalt shingles. How does the insurance thing work?",
                'ai_should': ['Acknowledge insurance question without committing', 'Redirect to assessment', 'Ask for photos or location'],
                'ai_must_not': ['Give insurance advice', 'Quote pricing', 'Promise coverage']
            }
        ]
    },

    'roof_planning_full_replacement': {
        'business': 'summit_roofing',
        'urgency': 'low',
        'category': 'roofing',
        'description': 'Planning full replacement - test detailed scope questions',
        'initial_email': {
            'subject': 'Need estimate for roof replacement',
            'from_name': 'Patricia Wong',
            'from_email': 'pwong@gmail.com',
            'body': "Looking to replace our roof this spring. Ranch house, about 1800 sq ft. Current roof is 20 years old. Want to understand the process and get some estimates. Not in a rush."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "We're in Flushing, Queens. One story ranch. Current roof is asphalt shingles, thinking about doing the same unless you recommend something else.",
                'ai_should': ['Match relaxed planning tone', 'Ask for address or photos', 'Keep warm but professional'],
                'ai_must_not': ['Recommend materials', 'Give pricing', 'Be overly technical']
            }
        ]
    },

    'roof_wrong_trade_solar': {
        'business': 'summit_roofing',
        'urgency': 'medium',
        'category': 'roofing',
        'description': 'Wrong trade inquiry - test polite redirect',
        'initial_email': {
            'subject': 'Solar panel installation',
            'from_name': 'Kevin Murphy',
            'from_email': 'kmurphy@gmail.com',
            'body': "Hi, I'm looking to get solar panels installed on my roof. Do you do solar installations? Need a quote for a 2000 sq ft house."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Oh I see. Do you know anyone who does solar?",
                'ai_should': ['Polite redirect only', 'Keep very brief'],
                'ai_must_not': ['Try to qualify', 'Recommend specific companies', 'Upsell roofing']
            }
        ]
    },

    # ELECTRICAL SCENARIOS
    'elec_emergency_burning_smell': {
        'business': 'brightline_electric',
        'urgency': 'emergency',
        'category': 'electrical',
        'description': 'Emergency safety issue - test safety validation',
        'initial_email': {
            'subject': 'URGENT - burning smell from outlet',
            'from_name': 'Amanda Richardson',
            'from_email': 'arichardson@gmail.com',
            'body': "There's a burning plastic smell coming from an outlet in our bedroom. I unplugged everything and the smell stopped but I'm worried. Is this dangerous? Can someone come look at it today? 234 W 18th St, Manhattan. Amanda 646-555-7392"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "We turned off the breaker for that room to be safe. The outlet looked a little discolored around the edges.",
                'ai_should': ['Validate safety step', 'Acknowledge severity', 'Very brief', 'Collect availability'],
                'ai_must_not': ['Give technical diagnosis', 'Promise specific time', 'Downplay danger']
            }
        ]
    },

    'elec_medium_outlet_not_working': {
        'business': 'brightline_electric',
        'urgency': 'medium',
        'category': 'electrical',
        'description': 'Medium urgency - test technical restraint',
        'initial_email': {
            'subject': 'Kitchen outlets stopped working',
            'from_name': 'James Park',
            'from_email': 'jpark@gmail.com',
            'body': "Half the outlets in my kitchen just stopped working. Checked the breaker and it's not tripped. What could cause this? Can you come take a look sometime this week?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "It's a condo in Manhattan, built in the 90s. The outlets on the left side of the kitchen work fine, but the right side is all dead.",
                'ai_should': ['Acknowledge without diagnosing', 'Ask for location/address', 'Match medium urgency tone'],
                'ai_must_not': ['Give technical explanation (GFCI, etc)', 'Diagnose remotely', 'Ask multiple questions']
            }
        ]
    },

    'elec_planning_panel_upgrade': {
        'business': 'brightline_electric',
        'urgency': 'low',
        'category': 'electrical',
        'description': 'Planning major work - test scope understanding',
        'initial_email': {
            'subject': 'Electrical panel upgrade quote',
            'from_name': 'Robert Singh',
            'from_email': 'rsingh@gmail.com',
            'body': "We're renovating our kitchen and the electrician said we need to upgrade our panel from 100 amp to 200 amp. Can you do this work and what's the ballpark cost?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "It's a house in Astoria, Queens. Current panel is original from the 1960s. Also planning to add a few circuits for the new kitchen.",
                'ai_should': ['Acknowledge scope', 'Ask for location/timing', 'No pricing'],
                'ai_must_not': ['Give pricing estimates', 'Give technical advice', 'Recommend specific panel brands']
            }
        ]
    },

    'elec_edge_flickering_lights': {
        'business': 'brightline_electric',
        'urgency': 'medium',
        'category': 'electrical',
        'description': 'Vague issue - test question focus',
        'initial_email': {
            'subject': 'Lights flickering',
            'from_name': 'Lisa',
            'from_email': 'lisa.martinez@gmail.com',
            'body': "Lights keep flickering. Annoying."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "All over the apartment. Started a few days ago. Sometimes they dim, sometimes flicker.",
                'ai_should': ['Match terse style', 'Ask ONE focused question', 'Very brief'],
                'ai_must_not': ['Ask multiple questions', 'Give technical explanation', 'Over-explain']
            }
        ]
    },

    # GENERAL CONTRACTOR SCENARIOS
    'gc_planning_kitchen_remodel': {
        'business': 'apex_construction',
        'urgency': 'low',
        'category': 'general_contractor',
        'description': 'Major project planning - test scope questions',
        'initial_email': {
            'subject': 'Kitchen remodel estimate',
            'from_name': 'Michelle Davis',
            'from_email': 'mdavis@gmail.com',
            'body': "Hi, we're looking to do a full kitchen renovation. Tear out everything and start fresh. About 200 sq ft. Looking for estimates and timeline. Located in Hoboken, NJ."
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "We want new cabinets, countertops, appliances, flooring - the works. Hoping to start in the next few months. What's the typical timeline for something like this?",
                'ai_should': ['Acknowledge scope', 'Ask for photos or more details', 'No timeline commitments'],
                'ai_must_not': ['Give timeline estimates', 'Give pricing', 'Recommend specific products']
            }
        ]
    },

    'gc_handyman_vs_major': {
        'business': 'apex_construction',
        'urgency': 'medium',
        'category': 'general_contractor',
        'description': 'Scope filtering - test handyman redirect',
        'initial_email': {
            'subject': 'Need help with small projects',
            'from_name': 'Steve Johnson',
            'from_email': 'sjohnson@gmail.com',
            'body': "Looking for help with a few small things - fix a loose cabinet door, patch some drywall holes, replace a door handle. Can you help with this kind of stuff?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "Just those three things. Probably a couple hours of work total. When could someone come out?",
                'ai_should': ['Politely assess if too small', 'Either qualify or redirect', 'Be honest about scope fit'],
                'ai_must_not': ['Promise availability', 'Overcommit to small jobs', 'Be dismissive']
            }
        ]
    },

    'gc_multi_issue_list': {
        'business': 'apex_construction',
        'urgency': 'medium',
        'category': 'general_contractor',
        'description': 'Multiple issues - test prioritization',
        'initial_email': {
            'subject': 'Multiple repairs needed',
            'from_name': 'Barbara Chen',
            'from_email': 'bchen@yahoo.com',
            'body': "We need help with several things: bathroom shower is leaking, basement has water damage from a pipe leak last month (already fixed the pipe), and we want to add a half bath on the first floor. Can you handle all of this?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "The shower leak is the most urgent - it's leaking through to the ceiling below. The basement water damage is contained, just needs cleanup and repair. The half bath is longer term.",
                'ai_should': ['Acknowledge multiple items', 'Ask about location or priorities', 'Stay organized'],
                'ai_must_not': ['Ask about all three at once', 'Try to diagnose', 'Overwhelm with questions']
            }
        ]
    },

    'gc_commercial_property': {
        'business': 'apex_construction',
        'urgency': 'low',
        'category': 'general_contractor',
        'description': 'Commercial vs residential - test clarification',
        'initial_email': {
            'subject': 'Office renovation',
            'from_name': 'Mark Stevens',
            'from_email': 'mark@techstartup.com',
            'body': "We're expanding our office space and need to renovate about 2000 sq ft. New walls, electrical, flooring, paint. Do you do commercial projects?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "It's a tech office in Jersey City. Open floor plan, about 15 employees. Need it done by September.",
                'ai_should': ['Clarify if they do commercial', 'Ask for location/timing', 'Professional tone'],
                'ai_must_not': ['Commit to timeline', 'Give pricing', 'Over-promise']
            }
        ]
    },

    'gc_edge_angry_previous_contractor': {
        'business': 'apex_construction',
        'urgency': 'medium',
        'category': 'general_contractor',
        'description': 'Angry about previous contractor - test professionalism',
        'initial_email': {
            'subject': 'Need a REAL contractor',
            'from_name': 'Daniel Foster',
            'from_email': 'dfoster@gmail.com',
            'body': "I hired a contractor to finish my basement 6 months ago. Paid him $15,000 and he disappeared after doing half the work. Drywall is up but nothing else. Can you finish what he started without screwing me over?"
        },
        'conversation_flow': [
            {
                'step': 1,
                'homeowner_reply': "I'm in Newark. The framing and drywall are done but no electrical, plumbing, or finishing work. Just want someone reliable to finish it.",
                'ai_should': ['Professional empathy without over-apologizing', 'Focus on moving forward', 'Ask about scope'],
                'ai_must_not': ['Badmouth other contractor', 'Say "I understand your frustration"', 'Over-apologize']
            }
        ]
    }
}

# Export in format expected by test_harness.py
BUSINESS_PROFILES = BUSINESSES

# Convert scenarios dict to list format expected by test_harness
ALL_SCENARIOS = []
for scenario_id, scenario_data in SCENARIOS.items():
    scenario = {
        'id': scenario_id,
        'name': scenario_data['description'],
        'business': scenario_data['business'],
        'urgency': scenario_data.get('urgency'),
        'category': scenario_data.get('category'),
        'description': scenario_data['description'],
        'initial_email': {
            'from': f"{scenario_data['initial_email']['from_name']} <{scenario_data['initial_email']['from_email']}>",
            'subject': scenario_data['initial_email']['subject'],
            'body': scenario_data['initial_email']['body']
        },
        'conversation_flow': scenario_data.get('conversation_flow', []),
    }

    # Add expected_behavior for non-leads
    if 'expected_behavior' in scenario_data:
        scenario['expected_behavior'] = scenario_data['expected_behavior']

    ALL_SCENARIOS.append(scenario)
