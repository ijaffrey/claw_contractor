"""
OpenClaw Test Scenarios - Comprehensive Test Library
50 scenarios covering diverse personalities, regions, and conversation patterns
"""

BUSINESSES = {
    "mikes_plumbing": {
        "name": "Mike's Plumbing",
        "trade_type": "plumbing",
        "location": "Brooklyn, NY",
        "brand_voice": "Friendly and direct, like a neighbor who knows their stuff. 20-year veteran who's seen it all. Brooklyn-based, no-nonsense but warm. Gets straight to the point.",
        "phone": "718-555-0142",
        "owner_name": "Mike Rossi",
        "email": "mike@mikesplumbing.com",
    },
    "summit_roofing": {
        "name": "Summit Roofing",
        "trade_type": "roofing",
        "location": "Queens, NY",
        "brand_voice": "Professional and reassuring. 15 years in business. Handles insurance claims regularly. Warm but polished - like a contractor who's seen every type of roof damage and knows exactly what to do. Safety-conscious and detail-oriented.",
        "phone": "718-555-0283",
        "owner_name": "Carlos Martinez",
        "email": "carlos@summitroofing.com",
    },
    "brightline_electric": {
        "name": "Brightline Electric",
        "trade_type": "electrical",
        "location": "Manhattan, NY",
        "brand_voice": "Calm, safety-focused, and precise. Licensed master electrician with 12 years experience. Takes electrical safety very seriously but explains things in plain English. Professional without being stiff. Thinks about code compliance and long-term solutions.",
        "phone": "212-555-0491",
        "owner_name": "David Chen",
        "email": "david@brightlineelectric.com",
    },
    "apex_construction": {
        "name": "Apex Construction",
        "trade_type": "general_contractor",
        "location": "Tri-State Area",
        "brand_voice": "Polished and organized. 20+ years doing everything from small repairs to full gut renovations. Asks detailed questions upfront to understand scope. Friendly but businesslike - runs a tight ship. Good at setting realistic expectations for timelines and budgets.",
        "phone": "201-555-0847",
        "owner_name": "Jennifer Okafor",
        "email": "jen@apexconstruction.com",
    },
    "lone_star_plumbing": {
        "name": "Lone Star Plumbing",
        "trade_type": "plumbing",
        "location": "Austin, TX",
        "brand_voice": "Friendly Texas charm with professional expertise. Family-owned for 15 years. Direct but personable - treats every home like it's their own. Experienced with Texas-specific issues like hard water and outdoor plumbing.",
        "phone": "512-555-0891",
        "owner_name": "Jake Miller",
        "email": "jake@lonestarplumbing.com",
    },
    "boston_roofing_pros": {
        "name": "Boston Roofing Pros",
        "trade_type": "roofing",
        "location": "Boston, MA",
        "brand_voice": "No-nonsense New England work ethic with deep expertise in harsh weather roofing. 25 years handling ice dams, nor'easters, and historic home roofing. Straightforward and honest - won't sugarcoat the situation.",
        "phone": "617-555-0234",
        "owner_name": "Patrick Sullivan",
        "email": "pat@bostonroofingpros.com",
    },
    "bay_area_electric": {
        "name": "Bay Area Electric",
        "trade_type": "electrical",
        "location": "San Francisco, CA",
        "brand_voice": "Tech-savvy and progressive. Specializes in EV charger installations, solar integration, and smart home systems. Licensed for 10 years. Professional but approachable - understands modern electrical needs.",
        "phone": "415-555-0672",
        "owner_name": "Sandra Patel",
        "email": "sandra@bayareaelectric.com",
    },
    "midwest_home_builders": {
        "name": "Midwest Home Builders",
        "trade_type": "general_contractor",
        "location": "Indianapolis, IN",
        "brand_voice": "Friendly Midwest hospitality with solid craftsmanship. Third-generation family business. Takes pride in quality work and building relationships. Down-to-earth and reliable - the kind of contractor who becomes a family friend.",
        "phone": "317-555-0445",
        "owner_name": "Tom Anderson",
        "email": "tom@midwesthomebuilders.com",
    },
}

# Core test scenarios covering key edge cases
SCENARIOS = {
    # ==================== EXISTING 24 SCENARIOS ====================
    "plumb_emergency_burst_pipe": {
        "business": "mikes_plumbing",
        "urgency": "emergency",
        "category": "plumbing",
        "description": "Emergency burst pipe - test brevity, no time commitment",
        "homeowner_persona": {
            "personality": "panicked",
            "communication_style": "urgent and breathless",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "EMERGENCY - burst pipe flooding basement",
            "from_name": "Jennifer Walsh",
            "from_email": "jwalsh42@gmail.com",
            "body": "We have a MAJOR emergency! Pipe burst in the basement and water is POURING out. We shut off the main valve but there's already 2 inches of water down there. Please help ASAP! Jennifer Walsh 347-555-8291 124 Prospect Ave, Brooklyn 11215",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Yes we got it shut off. It's the pipe coming from the water heater. Can you come right now??",
                "ai_should": [
                    "Be VERY brief",
                    "Validate they shut off water",
                    "Ask ONE question",
                    "Collect availability",
                ],
                "ai_must_not": [
                    "Re-ask for address",
                    "Promise specific time",
                    "Use clichés",
                    "Multiple questions",
                ],
            }
        ],
    },
    "plumb_medium_slow_drain": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Medium urgency - test tone matching, acknowledge DIY attempts",
        "homeowner_persona": {
            "personality": "relaxed and handy",
            "communication_style": "casual and conversational",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Kitchen sink draining slow",
            "from_name": "Robert Chen",
            "from_email": "robert.chen@gmail.com",
            "body": "Hey, my kitchen sink is draining really slow. Tried Drano twice, helped for a day then back to slow. Probably needs a snake? Not urgent but would like it fixed this week or next. Weekends work best.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Yeah, disposal on one side. Both sides drain slow though. House is about 40 years old if that matters.",
                "ai_should": [
                    "Match relaxed tone",
                    "Note house age",
                    "Acknowledge DIY without lecture",
                ],
                "ai_must_not": [
                    "Lecture about Drano",
                    "Be overly formal",
                    "Ask multiple questions",
                ],
            }
        ],
    },
    "plumb_edge_minimal_info": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Minimal info - test brevity matching",
        "homeowner_persona": {
            "personality": "no-nonsense",
            "communication_style": "terse and minimal",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Plumber needed",
            "from_name": "Chris",
            "from_email": "c.murphy@gmail.com",
            "body": "Need a plumber. Call me 555-0147.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Leaky faucet in bathroom. This week sometime.",
                "ai_should": ["Match terse style", "Ask ONE thing", "Keep VERY short"],
                "ai_must_not": [
                    "Send wall of text",
                    "Try to warm them up",
                    "Ask multiple questions",
                ],
            }
        ],
    },
    "plumb_edge_angry": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Angry customer - test direct confidence, no over-apologizing",
        "homeowner_persona": {
            "personality": "frustrated and skeptical",
            "communication_style": "direct and challenging",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Need reliable plumber",
            "from_name": "Steven Clark",
            "from_email": "sclark@yahoo.com",
            "body": "I need a plumber who actually shows up. Last guy was 3 hours late, charged me $400 to 'fix' a toilet that's STILL running, and won't return my calls. Can you fix a running toilet without screwing it up?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Just tell me yes or no - can you come this week and fix it properly?",
                "ai_should": [
                    "Be direct and confident",
                    "Match no-nonsense tone",
                    "Ask ONE thing",
                ],
                "ai_must_not": [
                    'Say "I\'m sorry you had that experience"',
                    "Badmouth previous contractor",
                    "Over-apologize",
                ],
            }
        ],
    },
    "plumb_edge_price_shopper": {
        "business": "mikes_plumbing",
        "urgency": "low",
        "category": "plumbing",
        "description": "Price shopper - test directness, minimal qualification",
        "homeowner_persona": {
            "personality": "budget-conscious",
            "communication_style": "direct and transactional",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Toilet install price",
            "from_name": "Mark Chen",
            "from_email": "markc@gmail.com",
            "body": "How much to install a toilet? Replacing existing one. Just need a straight answer on price.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Straight swap, same location. I already bought the toilet.",
                "ai_should": [
                    "Respect directness",
                    "Ask minimum needed",
                    "Keep SHORT (3 sentences max)",
                ],
                "ai_must_not": [
                    "Launch into full qualification",
                    "Try to warm them up",
                    "Give pricing",
                ],
            }
        ],
    },
    "plumb_not_lead_vendor": {
        "business": "mikes_plumbing",
        "urgency": "n/a",
        "category": "plumbing",
        "description": "Vendor email - should skip/not reply",
        "homeowner_persona": {
            "personality": "n/a",
            "communication_style": "vendor solicitation",
            "regional_flavor": "n/a",
        },
        "initial_email": {
            "subject": "Premium PEX Fittings - 20% Off",
            "from_name": "ProSupply Solutions",
            "from_email": "sales@prosupply.com",
            "body": "Dear Plumbing Professional, We're offering 20% off all PEX fittings this month! Stock up now.",
        },
        "expected_behavior": "SKIP - do not reply, this is vendor solicitation",
        "conversation_flow": [],
    },
    # ROOFING SCENARIOS
    "roof_emergency_storm_damage": {
        "business": "summit_roofing",
        "urgency": "emergency",
        "category": "roofing",
        "description": "Emergency storm damage - test photo request urgency",
        "homeowner_persona": {
            "personality": "anxious",
            "communication_style": "worried but detailed",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Emergency - tree fell on roof during storm",
            "from_name": "Maria Santos",
            "from_email": "msantos@gmail.com",
            "body": "A tree branch came down on our roof during the storm last night. There's a hole and it's supposed to rain again tomorrow. We need someone ASAP. 45 Oak Street, Queens 11375. Maria Santos 917-555-3821",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The hole is maybe 3 feet across. I can see into the attic. We put a tarp over it but wind keeps blowing it off.",
                "ai_should": [
                    "Acknowledge severity",
                    "Ask for photos",
                    "Keep very brief",
                ],
                "ai_must_not": [
                    "Promise specific time",
                    "Give advice on tarp",
                    "Ask multiple questions",
                ],
            }
        ],
    },
    "roof_medium_missing_shingles": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Medium urgency - test insurance question handling",
        "homeowner_persona": {
            "personality": "proactive and methodical",
            "communication_style": "thorough with questions",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Missing shingles after wind storm",
            "from_name": "Tom Bradley",
            "from_email": "tbradley44@yahoo.com",
            "body": "Hi, noticed we're missing some shingles after the windstorm last week. No leaks yet but want to get it fixed before we have problems. Does this work with insurance? How much does something like this usually cost?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Good question - I have State Farm. The roof is about 12 years old, asphalt shingles. How does the insurance thing work?",
                "ai_should": [
                    "Acknowledge insurance question without committing",
                    "Redirect to assessment",
                    "Ask for photos or location",
                ],
                "ai_must_not": [
                    "Give insurance advice",
                    "Quote pricing",
                    "Promise coverage",
                ],
            }
        ],
    },
    "roof_planning_full_replacement": {
        "business": "summit_roofing",
        "urgency": "low",
        "category": "roofing",
        "description": "Planning full replacement - test detailed scope questions",
        "homeowner_persona": {
            "personality": "planning-oriented",
            "communication_style": "organized and patient",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Need estimate for roof replacement",
            "from_name": "Patricia Wong",
            "from_email": "pwong@gmail.com",
            "body": "Looking to replace our roof this spring. Ranch house, about 1800 sq ft. Current roof is 20 years old. Want to understand the process and get some estimates. Not in a rush.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "We're in Flushing, Queens. One story ranch. Current roof is asphalt shingles, thinking about doing the same unless you recommend something else.",
                "ai_should": [
                    "Match relaxed planning tone",
                    "Ask for address or photos",
                    "Keep warm but professional",
                ],
                "ai_must_not": [
                    "Recommend materials",
                    "Give pricing",
                    "Be overly technical",
                ],
            }
        ],
    },
    "roof_wrong_trade_solar": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Wrong trade inquiry - test polite redirect",
        "homeowner_persona": {
            "personality": "curious and eco-conscious",
            "communication_style": "friendly",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Solar panel installation",
            "from_name": "Kevin Murphy",
            "from_email": "kmurphy@gmail.com",
            "body": "Hi, I'm looking to get solar panels installed on my roof. Do you do solar installations? Need a quote for a 2000 sq ft house.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Oh I see. Do you know anyone who does solar?",
                "ai_should": ["Polite redirect only", "Keep very brief"],
                "ai_must_not": [
                    "Try to qualify",
                    "Recommend specific companies",
                    "Upsell roofing",
                ],
            }
        ],
    },
    # ELECTRICAL SCENARIOS
    "elec_emergency_burning_smell": {
        "business": "brightline_electric",
        "urgency": "emergency",
        "category": "electrical",
        "description": "Emergency safety issue - test safety validation",
        "homeowner_persona": {
            "personality": "safety-conscious",
            "communication_style": "anxious but clear",
            "regional_flavor": "Manhattan",
        },
        "initial_email": {
            "subject": "URGENT - burning smell from outlet",
            "from_name": "Amanda Richardson",
            "from_email": "arichardson@gmail.com",
            "body": "There's a burning plastic smell coming from an outlet in our bedroom. I unplugged everything and the smell stopped but I'm worried. Is this dangerous? Can someone come look at it today? 234 W 18th St, Manhattan. Amanda 646-555-7392",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "We turned off the breaker for that room to be safe. The outlet looked a little discolored around the edges.",
                "ai_should": [
                    "Validate safety step",
                    "Acknowledge severity",
                    "Very brief",
                    "Collect availability",
                ],
                "ai_must_not": [
                    "Give technical diagnosis",
                    "Promise specific time",
                    "Downplay danger",
                ],
            }
        ],
    },
    "elec_medium_outlet_not_working": {
        "business": "brightline_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Medium urgency - test technical restraint",
        "homeowner_persona": {
            "personality": "practical",
            "communication_style": "matter-of-fact",
            "regional_flavor": "Manhattan",
        },
        "initial_email": {
            "subject": "Kitchen outlets stopped working",
            "from_name": "James Park",
            "from_email": "jpark@gmail.com",
            "body": "Half the outlets in my kitchen just stopped working. Checked the breaker and it's not tripped. What could cause this? Can you come take a look sometime this week?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's a condo in Manhattan, built in the 90s. The outlets on the left side of the kitchen work fine, but the right side is all dead.",
                "ai_should": [
                    "Acknowledge without diagnosing",
                    "Ask for location/address",
                    "Match medium urgency tone",
                ],
                "ai_must_not": [
                    "Give technical explanation (GFCI, etc)",
                    "Diagnose remotely",
                    "Ask multiple questions",
                ],
            }
        ],
    },
    "elec_planning_panel_upgrade": {
        "business": "brightline_electric",
        "urgency": "low",
        "category": "electrical",
        "description": "Planning major work - test scope understanding",
        "homeowner_persona": {
            "personality": "detail-oriented",
            "communication_style": "thorough and inquisitive",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Electrical panel upgrade quote",
            "from_name": "Robert Singh",
            "from_email": "rsingh@gmail.com",
            "body": "We're renovating our kitchen and the electrician said we need to upgrade our panel from 100 amp to 200 amp. Can you do this work and what's the ballpark cost?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's a house in Astoria, Queens. Current panel is original from the 1960s. Also planning to add a few circuits for the new kitchen.",
                "ai_should": [
                    "Acknowledge scope",
                    "Ask for location/timing",
                    "No pricing",
                ],
                "ai_must_not": [
                    "Give pricing estimates",
                    "Give technical advice",
                    "Recommend specific panel brands",
                ],
            }
        ],
    },
    "elec_edge_flickering_lights": {
        "business": "brightline_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Vague issue - test question focus",
        "homeowner_persona": {
            "personality": "busy and impatient",
            "communication_style": "terse",
            "regional_flavor": "Manhattan",
        },
        "initial_email": {
            "subject": "Lights flickering",
            "from_name": "Lisa",
            "from_email": "lisa.martinez@gmail.com",
            "body": "Lights keep flickering. Annoying.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "All over the apartment. Started a few days ago. Sometimes they dim, sometimes flicker.",
                "ai_should": [
                    "Match terse style",
                    "Ask ONE focused question",
                    "Very brief",
                ],
                "ai_must_not": [
                    "Ask multiple questions",
                    "Give technical explanation",
                    "Over-explain",
                ],
            }
        ],
    },
    # GENERAL CONTRACTOR SCENARIOS
    "gc_planning_kitchen_remodel": {
        "business": "apex_construction",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Major project planning - test scope questions",
        "homeowner_persona": {
            "personality": "excited and planning-oriented",
            "communication_style": "enthusiastic and detailed",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Kitchen remodel estimate",
            "from_name": "Michelle Davis",
            "from_email": "mdavis@gmail.com",
            "body": "Hi, we're looking to do a full kitchen renovation. Tear out everything and start fresh. About 200 sq ft. Looking for estimates and timeline. Located in Hoboken, NJ.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "We want new cabinets, countertops, appliances, flooring - the works. Hoping to start in the next few months. What's the typical timeline for something like this?",
                "ai_should": [
                    "Acknowledge scope",
                    "Ask for photos or more details",
                    "No timeline commitments",
                ],
                "ai_must_not": [
                    "Give timeline estimates",
                    "Give pricing",
                    "Recommend specific products",
                ],
            }
        ],
    },
    "gc_handyman_vs_major": {
        "business": "apex_construction",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Scope filtering - test handyman redirect",
        "homeowner_persona": {
            "personality": "practical",
            "communication_style": "casual and straightforward",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Need help with small projects",
            "from_name": "Steve Johnson",
            "from_email": "sjohnson@gmail.com",
            "body": "Looking for help with a few small things - fix a loose cabinet door, patch some drywall holes, replace a door handle. Can you help with this kind of stuff?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Just those three things. Probably a couple hours of work total. When could someone come out?",
                "ai_should": [
                    "Politely assess if too small",
                    "Either qualify or redirect",
                    "Be honest about scope fit",
                ],
                "ai_must_not": [
                    "Promise availability",
                    "Overcommit to small jobs",
                    "Be dismissive",
                ],
            }
        ],
    },
    "gc_multi_issue_list": {
        "business": "apex_construction",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Multiple issues - test prioritization",
        "homeowner_persona": {
            "personality": "organized and decisive",
            "communication_style": "systematic and clear",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Multiple repairs needed",
            "from_name": "Barbara Chen",
            "from_email": "bchen@yahoo.com",
            "body": "We need help with several things: bathroom shower is leaking, basement has water damage from a pipe leak last month (already fixed the pipe), and we want to add a half bath on the first floor. Can you handle all of this?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The shower leak is the most urgent - it's leaking through to the ceiling below. The basement water damage is contained, just needs cleanup and repair. The half bath is longer term.",
                "ai_should": [
                    "Acknowledge multiple items",
                    "Ask about location or priorities",
                    "Stay organized",
                ],
                "ai_must_not": [
                    "Ask about all three at once",
                    "Try to diagnose",
                    "Overwhelm with questions",
                ],
            }
        ],
    },
    "gc_commercial_property": {
        "business": "apex_construction",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Commercial vs residential - test clarification",
        "homeowner_persona": {
            "personality": "professional and deadline-oriented",
            "communication_style": "business-like",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Office renovation",
            "from_name": "Mark Stevens",
            "from_email": "mark@techstartup.com",
            "body": "We're expanding our office space and need to renovate about 2000 sq ft. New walls, electrical, flooring, paint. Do you do commercial projects?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's a tech office in Jersey City. Open floor plan, about 15 employees. Need it done by September.",
                "ai_should": [
                    "Clarify if they do commercial",
                    "Ask for location/timing",
                    "Professional tone",
                ],
                "ai_must_not": ["Commit to timeline", "Give pricing", "Over-promise"],
            }
        ],
    },
    "gc_edge_angry_previous_contractor": {
        "business": "apex_construction",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Angry about previous contractor - test professionalism",
        "homeowner_persona": {
            "personality": "frustrated and burned",
            "communication_style": "direct and skeptical",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Need a REAL contractor",
            "from_name": "Daniel Foster",
            "from_email": "dfoster@gmail.com",
            "body": "I hired a contractor to finish my basement 6 months ago. Paid him $15,000 and he disappeared after doing half the work. Drywall is up but nothing else. Can you finish what he started without screwing me over?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "I'm in Newark. The framing and drywall are done but no electrical, plumbing, or finishing work. Just want someone reliable to finish it.",
                "ai_should": [
                    "Professional empathy without over-apologizing",
                    "Focus on moving forward",
                    "Ask about scope",
                ],
                "ai_must_not": [
                    "Badmouth other contractor",
                    'Say "I understand your frustration"',
                    "Over-apologize",
                ],
            }
        ],
    },
    # Photo Request Test Scenarios
    "roof_photo_request_success": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Roofing lead - test photo request and receipt",
        "homeowner_persona": {
            "personality": "cooperative",
            "communication_style": "responsive and helpful",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Missing shingles after storm",
            "from_name": "Patricia Miller",
            "from_email": "pmiller@gmail.com",
            "body": "Had a bad storm last night and I noticed some shingles missing from my roof this morning. Not leaking yet but want to get it fixed before it does. House is in Astoria.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Not sure exactly how many. Maybe 5-6 shingles? On the south-facing side. This week would be great.",
                "ai_should": [
                    "Ask for photos (roofing ALWAYS needs photos)",
                    "Casual tone",
                    "ONE question",
                ],
                "ai_must_not": [
                    "Skip photo request",
                    'Formal language like "submit photographs"',
                    "Multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Sure, just sent you 3 photos from ground level showing the missing shingles.",
                "ai_should": [
                    "Acknowledge photos",
                    "Move to availability",
                    "Brief response",
                ],
                "ai_must_not": ["Re-ask for photos", "Give technical roof diagnosis"],
            },
        ],
    },
    "roof_photo_request_cant_access": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Roofing lead - test handling when customer cant provide photos",
        "homeowner_persona": {
            "personality": "concerned but limited mobility",
            "communication_style": "apologetic",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Roof leak in bedroom",
            "from_name": "Edward Kim",
            "from_email": "ekim@yahoo.com",
            "body": "I have water staining on my bedroom ceiling. Pretty sure it's a roof leak but haven't been up there to check. Need someone to come look. Flushing, Queens.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Just started noticing it last week. Stain is maybe 12 inches across, light brown. Happens when it rains.",
                "ai_should": [
                    "Ask for photos of CEILING stain (visible damage)",
                    "Casual phrasing",
                    "ONE question",
                ],
                "ai_must_not": [
                    "Ask to climb on roof",
                    "Diagnose leak source",
                    "Skip photo request entirely",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I can't really get up there to photograph the roof. I can send a pic of the ceiling stain if that helps?",
                "ai_should": [
                    "Accept ceiling photo gracefully",
                    "Move forward without making it awkward",
                    "Ask for availability",
                ],
                "ai_must_not": [
                    "Insist on roof photos",
                    "Make them feel bad",
                    "Over-explain why photos matter",
                ],
            },
        ],
    },
    "plumb_emergency_no_photos": {
        "business": "mikes_plumbing",
        "urgency": "emergency",
        "category": "plumbing",
        "description": "Plumbing emergency - test NO photo request (dont slow them down)",
        "homeowner_persona": {
            "personality": "panicked",
            "communication_style": "frantic and rushed",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "URGENT toilet overflowing",
            "from_name": "Sandra Lopez",
            "from_email": "slopez@gmail.com",
            "body": "My toilet is overflowing and won't stop! I shut off the valve behind it but there's water all over the bathroom floor. Please help! 917-555-4821",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Yes valve is off. It's the upstairs bathroom. Can someone come today??",
                "ai_should": [
                    "Be extremely brief",
                    "Validate shutoff",
                    "Ask availability",
                    "Skip photo request entirely",
                ],
                "ai_must_not": [
                    "Ask for photos (emergency!)",
                    "Multiple questions",
                    "Slow them down with photo request",
                ],
            }
        ],
    },
    "plumb_visible_damage_photos": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Plumbing visible damage - test photo request for ceiling stain",
        "homeowner_persona": {
            "personality": "observant and concerned",
            "communication_style": "detailed reporter",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Water stain on ceiling",
            "from_name": "Marcus Johnson",
            "from_email": "mjohnson84@gmail.com",
            "body": "I have a water stain on my kitchen ceiling. Not actively dripping right now but it's definitely getting worse over the past few weeks. Probably a pipe leak from the bathroom above? Park Slope area.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The stain is maybe 2 feet across, yellowish-brown. Bathroom is directly above the kitchen. Not dripping currently.",
                "ai_should": [
                    "Ask for photos (visible damage helps)",
                    "Casual tone",
                    "ONE question",
                ],
                "ai_must_not": [
                    "Skip photo request for visible damage",
                    "Diagnose the problem",
                    "Multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Just emailed you 2 photos - one of the ceiling stain, one showing where the bathroom is above it.",
                "ai_should": ["Acknowledge photos", "Move to availability", "Brief"],
                "ai_must_not": [
                    "Diagnose leak location",
                    "Give repair estimate",
                    "Re-ask for address",
                ],
            },
        ],
    },
    "gc_remodel_kitchen_photos": {
        "business": "apex_construction",
        "urgency": "planning",
        "category": "general_contractor",
        "description": "GC kitchen remodel - test photo request for current space",
        "homeowner_persona": {
            "personality": "design-conscious",
            "communication_style": "enthusiastic and detailed",
            "regional_flavor": "Manhattan",
        },
        "initial_email": {
            "subject": "Kitchen remodel quote",
            "from_name": "Rachel Goldstein",
            "from_email": "rgoldstein@gmail.com",
            "body": "We're looking to remodel our kitchen - new cabinets, countertops, possibly knock down a wall to open it up to the dining room. Looking for someone to come give us a quote and talk through options. Upper West Side.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Hoping to start in the next 2-3 months. Kitchen is about 10x12, galley style. Want to modernize everything.",
                "ai_should": [
                    "Ask for photos of current kitchen",
                    "Helps scope the project",
                    "ONE question",
                ],
                "ai_must_not": [
                    "Skip photo request for remodel",
                    "Give pricing guidance",
                    "Multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Sure! Just sent 4 photos - overall layout, the wall we want to remove, current cabinets, and appliances.",
                "ai_should": [
                    "Acknowledge photos",
                    "Move to availability for consultation",
                    "Professional tone",
                ],
                "ai_must_not": [
                    "Comment on current design",
                    "Estimate timeline",
                    "Give remodel advice",
                ],
            },
        ],
    },
    # ==================== NEW 26 SCENARIOS ====================
    # NEW PLUMBING SCENARIOS (6)
    "plumb_water_heater_not_heating": {
        "business": "lone_star_plumbing",
        "urgency": "urgent",
        "category": "plumbing",
        "description": "Water heater not heating - detail-oriented Boston homeowner",
        "homeowner_persona": {
            "personality": "detail-oriented and methodical",
            "communication_style": "thorough with specific observations",
            "regional_flavor": "Boston",
        },
        "initial_email": {
            "subject": "Water heater not producing hot water",
            "from_name": "Catherine O'Brien",
            "from_email": "cobrien@gmail.com",
            "body": "Our water heater stopped producing hot water yesterday morning. It's a gas unit, about 8 years old. The pilot light is on and I can hear it running, but the water only gets lukewarm at best. Located in South Boston. Need this fixed soon - we have young kids.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's a 50-gallon gas water heater, installed in 2017. No visible leaks. Temperature dial is set to 120 degrees like it's always been. The burner seems to ignite but water never gets truly hot.",
                "ai_should": [
                    "Match detail-oriented tone",
                    "Acknowledge observations",
                    "Ask ONE clarifying question",
                ],
                "ai_must_not": [
                    "Try to diagnose over email",
                    "Give DIY advice",
                    "Ask multiple technical questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "We tried turning it up to 140 but that didn't help. No error lights that I can see. Availability - I work from home so pretty flexible this week.",
                "ai_should": [
                    "Note troubleshooting attempts",
                    "Move toward scheduling",
                    "Brief response",
                ],
                "ai_must_not": [
                    "Continue technical diagnosis",
                    "Lecture about temperature settings",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Mornings work best, any day Monday through Friday. Address is 234 E 3rd St, South Boston 02127. Phone is 617-555-8834.",
                "ai_should": ["Confirm details", "Professional close"],
                "ai_must_not": ["Promise specific diagnosis", "Quote pricing"],
            },
            {
                "step": 4,
                "homeowner_reply": "Perfect, we'll be here. One more thing - should we keep using it or turn it off until you come?",
                "ai_should": ["Give simple safety guidance", "Very brief"],
                "ai_must_not": ["Over-explain", "Get overly technical"],
            },
            {
                "step": 5,
                "homeowner_reply": "Got it, thanks. See you Tuesday morning.",
                "ai_should": ["Simple confirmation", "Warm close"],
                "ai_must_not": ["Add unnecessary information"],
            },
        ],
    },
    "plumb_sewer_backup": {
        "business": "lone_star_plumbing",
        "urgency": "emergency",
        "category": "plumbing",
        "description": "Sewer backup - panicked Texas homeowner",
        "homeowner_persona": {
            "personality": "panicked and overwhelmed",
            "communication_style": "frantic and rambling",
            "regional_flavor": "Texas",
        },
        "initial_email": {
            "subject": "EMERGENCY sewage backing up into house!!!",
            "from_name": "Bobby Ray Tucker",
            "from_email": "btucker@yahoo.com",
            "body": "Oh Lord we got a MAJOR problem! Sewage is backing up into our downstairs bathroom and laundry room! Water's all over the floor and it STINKS something awful! We got guests coming tomorrow! This is in Austin off Highway 183. PLEASE HELP! Bobby Tucker 512-555-9021",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "We stopped using ALL the water in the house. It started this morning - toilet wouldn't flush and then... God, it just started coming up everywhere. The smell is making my wife sick!",
                "ai_should": [
                    "Stay VERY calm",
                    "Validate they stopped using water",
                    "Be brief",
                    "ONE question max",
                ],
                "ai_must_not": [
                    "Match panic tone",
                    "Multiple questions",
                    "Give DIY instructions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "It's affecting the toilet, shower drain, and the washing machine drain. All in that back bathroom. Rest of the house seems OK so far. When can you get here?!",
                "ai_should": [
                    "Acknowledge severity",
                    "Collect address/availability",
                    "Calm confidence",
                ],
                "ai_must_not": [
                    "Promise specific time without checking",
                    "Diagnose the issue",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "4523 Maple Ridge Drive, 78731. We're here all day, sooner the better obviously! What's this gonna cost?",
                "ai_should": [
                    "Focus on getting there",
                    "No pricing in emergency",
                    "Brief reassurance",
                ],
                "ai_must_not": [
                    "Give pricing estimates",
                    "Slow down with explanations",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "OK fine just get here please. Back door is easier to access that bathroom.",
                "ai_should": [
                    "Note access detail",
                    "Confirm arrival plan",
                    "Keep very brief",
                ],
                "ai_must_not": ["Add unnecessary info"],
            },
        ],
    },
    "plumb_outdoor_hose_frozen": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Outdoor hose bib frozen - casual Midwest homeowner",
        "homeowner_persona": {
            "personality": "laid-back and friendly",
            "communication_style": "casual and conversational",
            "regional_flavor": "Midwest",
        },
        "initial_email": {
            "subject": "Frozen outdoor faucet",
            "from_name": "Dave Nelson",
            "from_email": "dnelson@gmail.com",
            "body": "Hey there, we had that cold snap last week and I think my outdoor spigot froze. Forgot to disconnect the hose - yeah, I know, rookie mistake! Water won't come out and I'm worried the pipe might've burst inside the wall. House is in Park Slope. Not urgent but wanna get it checked before spring. Thanks!",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Nope, no leaks inside that I can see. It's on the side of the house, probably runs through the kitchen wall? Haven't tried forcing it or anything, just turned the handle and nothing came out.",
                "ai_should": [
                    "Match friendly casual tone",
                    "Acknowledge the mistake lightly",
                    "Ask ONE thing",
                ],
                "ai_must_not": [
                    "Lecture about winterizing",
                    "Be overly formal",
                    "Multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Yeah makes sense. I'm around most weekdays after 3pm and all weekend. Whatever works for you guys. Should I be worried about it bursting if I just leave it?",
                "ai_should": [
                    "Simple reassurance",
                    "Move toward scheduling",
                    "Keep conversational",
                ],
                "ai_must_not": [
                    "Get technical about freeze damage",
                    "Create unnecessary alarm",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Cool, that works. It's 445 8th Street, between 5th and 6th Ave. Park Slope 11215. Phone is 347-555-2109.",
                "ai_should": ["Confirm details", "Friendly close"],
                "ai_must_not": ["Over-formalize", "Add unnecessary warnings"],
            },
            {
                "step": 4,
                "homeowner_reply": "Perfect, see you Thursday! I'll make sure the side gate is unlocked.",
                "ai_should": ["Note gate detail", "Simple confirmation"],
                "ai_must_not": ["Over-communicate"],
            },
        ],
    },
    "plumb_garbage_disposal_jammed": {
        "business": "lone_star_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Garbage disposal jammed - budget-conscious California homeowner",
        "homeowner_persona": {
            "personality": "budget-conscious and DIY-attempted",
            "communication_style": "practical and cost-focused",
            "regional_flavor": "California",
        },
        "initial_email": {
            "subject": "Garbage disposal not working",
            "from_name": "Lisa Chen",
            "from_email": "lisa.chen.sf@gmail.com",
            "body": "My garbage disposal is jammed. I tried using the reset button and the hex wrench thing underneath but it's still not budging. Making a humming sound when I flip the switch. Before I call someone out, what do you charge for something like this? I'm in San Francisco, Sunset District.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "I tried the reset button twice and used the hex wrench to manually turn it - moved maybe a quarter turn then stuck again. There's definitely something stuck in there but I can't see what. Is this something that can be fixed or do I need a whole new disposal?",
                "ai_should": [
                    "Acknowledge DIY attempts positively",
                    "Respect budget concerns",
                    "Don't quote price",
                ],
                "ai_must_not": [
                    "Give pricing over email",
                    "Try to diagnose what's stuck",
                    "Upsell replacement",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "OK but ballpark - are we talking $100 or $500? Just want to know if I should even bother. The disposal is probably 10 years old.",
                "ai_should": [
                    "Redirect gently without pricing",
                    "Acknowledge the question",
                    "Short response",
                ],
                "ai_must_not": [
                    "Give specific pricing",
                    "Make them feel bad for asking",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Alright, fine. I can do afternoons this week. Wednesday or Friday after 2pm works. Address is 2847 Noriega St, SF 94122.",
                "ai_should": ["Move to scheduling", "Professional but warm"],
                "ai_must_not": ["Continue pricing discussion"],
            },
            {
                "step": 4,
                "homeowner_reply": "Friday at 3 works. Phone is 415-555-7623. Do I need to do anything before you come?",
                "ai_should": ["Simple prep guidance if needed", "Brief"],
                "ai_must_not": ["Over-explain"],
            },
            {
                "step": 5,
                "homeowner_reply": "Got it. See you Friday.",
                "ai_should": ["Simple confirmation"],
                "ai_must_not": ["Add unnecessary details"],
            },
        ],
    },
    "plumb_multiple_bathrooms_one_cold": {
        "business": "mikes_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Multiple bathrooms, one cold shower - systematic homeowner",
        "homeowner_persona": {
            "personality": "systematic and analytical",
            "communication_style": "organized with clear facts",
            "regional_flavor": "Brooklyn",
        },
        "initial_email": {
            "subject": "Hot water issue in master bathroom only",
            "from_name": "Richard Kowalski",
            "from_email": "rkowalski@gmail.com",
            "body": "We have a peculiar issue: the master bathroom shower only produces cold water, but the sink in the same bathroom gets hot water fine. All other bathrooms in the house have hot water in both sinks and showers. This started about a week ago. House is in Brooklyn, built in 1995. Three bathrooms total.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Correct - master bathroom sink: hot water works. Master bathroom shower: only cold. Guest bathroom and hall bathroom: all hot water works fine in both sink and shower. I've verified this multiple times.",
                "ai_should": [
                    "Acknowledge systematic approach",
                    "Match organized tone",
                    "ONE question",
                ],
                "ai_must_not": [
                    "Try to diagnose valve issue",
                    "Ask multiple questions",
                    "Get technical",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "It's a single-handle shower valve, about 10 years old. No visible leaks. I tried turning the handle all the way to hot - the water runs strong but completely cold. Temperature in other showers is normal.",
                "ai_should": [
                    "Note the details",
                    "Move toward scheduling",
                    "Professional tone",
                ],
                "ai_must_not": ["Diagnose cartridge problem", "Give DIY instructions"],
            },
            {
                "step": 3,
                "homeowner_reply": "I'm available weekday evenings after 6pm or Saturday mornings. Address is 722 Carroll Street, Brooklyn 11215. Would you need to access the wall behind the shower?",
                "ai_should": [
                    "Address access question simply",
                    "Confirm scheduling options",
                ],
                "ai_must_not": [
                    "Over-explain the repair process",
                    "Promise specific approach",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Understood. Saturday morning works best - 9 or 10am? Phone is 718-555-4401.",
                "ai_should": ["Confirm time and details", "Professional close"],
                "ai_must_not": ["Add unnecessary information"],
            },
            {
                "step": 5,
                "homeowner_reply": "Saturday at 9am confirmed. We'll have towels moved out of the way. Should we shut off water to that bathroom beforehand?",
                "ai_should": ["Simple guidance", "Brief and helpful"],
                "ai_must_not": ["Over-explain"],
            },
            {
                "step": 6,
                "homeowner_reply": "Perfect, thank you. See you Saturday.",
                "ai_should": ["Simple confirmation"],
                "ai_must_not": ["Over-communicate"],
            },
        ],
    },
    "plumb_sump_pump_failure_storm": {
        "business": "mikes_plumbing",
        "urgency": "emergency",
        "category": "plumbing",
        "description": "Sump pump failure during storm - anxious Northeast homeowner",
        "homeowner_persona": {
            "personality": "anxious and worried",
            "communication_style": "worried with lots of context",
            "regional_flavor": "Northeast",
        },
        "initial_email": {
            "subject": "Sump pump stopped working - basement flooding!",
            "from_name": "Ellen Shapiro",
            "from_email": "eshapiro@gmail.com",
            "body": "We're in the middle of this huge rainstorm and our sump pump just stopped working! The pit is filling up with water and starting to overflow onto the basement floor. We just finished the basement last year and I'm terrified of water damage! The pump was making a weird grinding noise and then just stopped. We're in Westchester. Please help! 914-555-7766",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's plugged in and I checked the breaker - that's fine. The float moves freely. There's about 6 inches of water in the pit already and it's rising. I can see maybe 2 inches on the basement floor now. The pump is maybe 5 years old?",
                "ai_should": [
                    "Stay calm and reassuring",
                    "Validate checks they did",
                    "Brief response",
                ],
                "ai_must_not": [
                    "Match anxious tone",
                    "Give DIY repair instructions",
                    "Multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Should we be doing anything right now? Moving stuff? We have our kids' playroom down there! How fast can someone get here?",
                "ai_should": [
                    "Simple protective advice if any",
                    "Address availability directly",
                    "Calming confidence",
                ],
                "ai_must_not": [
                    "Create more worry",
                    "Promise specific ETA without checking",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "OK we're moving furniture now. Address is 89 Sycamore Lane, Scarsdale NY 10583. We're home all day. Do you carry replacement pumps or do we need to buy one?",
                "ai_should": [
                    "Focus on getting there first",
                    "Brief response",
                    "Don't commit to solution",
                ],
                "ai_must_not": [
                    "Promise to fix vs replace",
                    "Talk pricing during emergency",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Alright, thank you. We'll keep moving things to higher ground. Please hurry if you can - it's still pouring outside.",
                "ai_should": ["Reassuring confirmation", "Very brief"],
                "ai_must_not": ["Add unnecessary information"],
            },
        ],
    },
    # NEW ROOFING SCENARIOS (6)
    "roof_hail_damage_insurance": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Hail damage insurance claim - formal Texas homeowner",
        "homeowner_persona": {
            "personality": "formal and process-oriented",
            "communication_style": "professional with insurance focus",
            "regional_flavor": "Texas",
        },
        "initial_email": {
            "subject": "Roof inspection for hail damage - insurance claim",
            "from_name": "Margaret Patterson",
            "from_email": "mpatterson@sbcglobal.net",
            "body": "We had a severe hailstorm in our area on March 10th. Several neighbors are filing insurance claims for roof damage. I need a professional inspection to document any damage for my insurance company (Allstate). The roof is 7 years old, composition shingles. Property is located in Plano, TX. Please advise on your inspection process and timeline.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Yes, I have not yet filed with insurance - I wanted to have documentation first. The adjuster from Allstate suggested I get a roofing contractor's assessment. Do you provide written reports that I can submit to insurance? What is your experience with hail damage claims?",
                "ai_should": [
                    "Acknowledge insurance question",
                    "Don't give insurance advice",
                    "Professional tone",
                ],
                "ai_must_not": [
                    "Promise insurance will cover it",
                    "Give detailed insurance process",
                    "Commit to specific documentation format",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "That's helpful. Do you charge for the initial inspection? Also, if there is damage, what is the typical timeline for insurance claim repairs?",
                "ai_should": [
                    "Address inspection fee policy clearly",
                    "No timeline commitments",
                    "Stay professional",
                ],
                "ai_must_not": [
                    "Give pricing details for repairs",
                    "Promise claim timeline",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Understood. I'd like to schedule an inspection. I'm available weekday afternoons after 4pm or weekend mornings. Address is 5634 Willow Creek Drive, Plano TX 75093. What information do you need from me?",
                "ai_should": [
                    "Outline any needed info simply",
                    "Professional scheduling",
                ],
                "ai_must_not": ["Ask for insurance details upfront", "Over-complicate"],
            },
            {
                "step": 4,
                "homeowner_reply": "This Saturday at 10am works well. My phone is 469-555-8891. Will you need access to the attic for the inspection?",
                "ai_should": ["Address attic access question", "Confirm appointment"],
                "ai_must_not": ["Give lengthy inspection procedure"],
            },
            {
                "step": 5,
                "homeowner_reply": "Perfect. I'll ensure the attic is accessible. How long should I expect the inspection to take?",
                "ai_should": ["Simple time estimate if typical", "Brief response"],
                "ai_must_not": ["Over-explain the inspection process"],
            },
            {
                "step": 6,
                "homeowner_reply": "Excellent. I'll have the roof photos I took ready as well. See you Saturday morning.",
                "ai_should": ["Acknowledge photos mention", "Professional close"],
                "ai_must_not": ["Request photos again if already mentioned"],
            },
        ],
    },
    "roof_flat_roof_ponding": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Flat roof ponding water - technical California homeowner",
        "homeowner_persona": {
            "personality": "technical and research-oriented",
            "communication_style": "detailed with technical terms",
            "regional_flavor": "California",
        },
        "initial_email": {
            "subject": "Flat roof drainage issue - ponding water",
            "from_name": "Dr. Alan Schwartz",
            "from_email": "aschwartz@gmail.com",
            "body": "I have a flat TPO roof on my mid-century modern home in Berkeley. After rain, water ponds in several areas for 48+ hours before evaporating. I understand ponding can reduce roof membrane lifespan. The roof is 6 years old. I'm looking for an assessment of the drainage issues and recommendations for correction. Do you have experience with flat roof re-sloping or drain installation?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The ponding areas are roughly 3-4 feet in diameter, maybe 2-3 inches deep at the center. There are three problem areas. No active leaks currently, but I'm concerned about long-term membrane degradation. Have you worked with TPO roofing systems specifically?",
                "ai_should": [
                    "Acknowledge technical knowledge",
                    "Don't get into technical back-and-forth",
                    "Professional tone",
                ],
                "ai_must_not": [
                    "Try to diagnose solution",
                    "Get into technical debate",
                    "Recommend specific approach",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I've done some research on tapered insulation systems versus additional drains. What's your typical approach for ponding remediation? Also, can you provide photos of previous flat roof work?",
                "ai_should": [
                    "Redirect to assessment first",
                    "Don't commit to approach",
                    "Professional",
                ],
                "ai_must_not": [
                    "Give technical recommendation",
                    "Promise portfolio via email",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "That makes sense - I'd prefer you assess in person. I can be available next week, Tuesday through Thursday. Address is 1847 Los Angeles Ave, Berkeley CA 94707. Will you need roof access? I have a ladder.",
                "ai_should": ["Address access question", "Move to scheduling"],
                "ai_must_not": ["Get back into technical discussion"],
            },
            {
                "step": 4,
                "homeowner_reply": "Wednesday at 2pm works. Phone is 510-555-3492. Should I take additional photos before you come, or will you document everything?",
                "ai_should": ["Simple guidance on photos", "Confirm appointment"],
                "ai_must_not": ["Over-explain documentation process"],
            },
            {
                "step": 5,
                "homeowner_reply": "Understood. I'll be here Wednesday. Looking forward to your assessment.",
                "ai_should": ["Professional confirmation"],
                "ai_must_not": ["Add unnecessary information"],
            },
        ],
    },
    "roof_ice_dam_winter_emergency": {
        "business": "boston_roofing_pros",
        "urgency": "emergency",
        "category": "roofing",
        "description": "Ice dam formation - worried Vermont homeowner",
        "homeowner_persona": {
            "personality": "worried and winter-weary",
            "communication_style": "concerned but detailed",
            "regional_flavor": "Vermont/New England",
        },
        "initial_email": {
            "subject": "URGENT: Ice dam causing water leak into house",
            "from_name": "Susan Bergeron",
            "from_email": "sbergeron@yahoo.com",
            "body": "We have a massive ice dam on our roof and it's causing water to leak into our upstairs bedroom! Icicles are 4 feet long along the gutters and we can see water coming in around the window frame. It's been below freezing for 2 weeks straight. We're in Burlington area. This is our first winter in this house and I'm terrified the whole roof is going to collapse! Please help! 802-555-6743",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The water is dripping down the wall near the window. We put towels down but they're soaked. The ice buildup on the edge of the roof must be 6-8 inches thick. We've been running space heaters but it's not helping. Is this dangerous? Should we evacuate?",
                "ai_should": [
                    "Stay calm and reassuring",
                    "Don't create panic",
                    "Address safety simply",
                ],
                "ai_must_not": [
                    "Match panicked tone",
                    "Give DIY ice removal advice",
                    "Overstate danger",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "OK we moved stuff away from the wall. The leak is just in that one bedroom so far. Should we be doing anything on the roof? My husband wants to chip away the ice but that seems dangerous.",
                "ai_should": [
                    "Advise against DIY if dangerous",
                    "Brief safety guidance",
                    "Focus on getting there",
                ],
                "ai_must_not": [
                    "Give detailed ice removal instructions",
                    "Multiple questions",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "We're home all day. Address is 4421 Mountain View Road, Burlington VT 05401. How do you even fix this? Do you steam it or something?",
                "ai_should": [
                    "Brief answer about approach",
                    "Don't over-explain",
                    "Confirm details",
                ],
                "ai_must_not": [
                    "Get technical about ice dam removal",
                    "Promise specific method",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Thank goodness. We'll be here. Should we turn off heat or keep it on? I've read conflicting things online.",
                "ai_should": ["Simple guidance on heat", "Calm and brief"],
                "ai_must_not": ["Get into attic ventilation lecture"],
            },
            {
                "step": 5,
                "homeowner_reply": "OK keeping heat normal. Thank you for coming quickly. This is so stressful.",
                "ai_should": ["Empathetic and reassuring", "Brief confirmation"],
                "ai_must_not": ["Dismiss their stress", "Over-explain"],
            },
        ],
    },
    "roof_chimney_flashing_leak": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Chimney flashing leak - older homeowner",
        "homeowner_persona": {
            "personality": "older and deliberate",
            "communication_style": "slow-paced and courteous",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Water leak near chimney",
            "from_name": "Robert Fitzgerald",
            "from_email": "rfitzgerald@aol.com",
            "body": "Hello, I have a small water leak in my attic near the chimney. I notice it after heavy rains. My neighbor suggested it might be the flashing around the chimney. I'm 72 years old and can't get up there to look myself. The house is in Forest Hills, Queens. The roof is about 15 years old. Not an emergency but I'd like to get it fixed before it becomes a bigger problem. Thank you.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The leak is small - I put a bucket up there and it catches maybe a cup of water during a rainstorm. I haven't noticed any staining on the ceiling below yet. The chimney is brick, we don't use the fireplace anymore but it's still there. How soon could someone come look?",
                "ai_should": [
                    "Match courteous, slower pace",
                    "Patient tone",
                    "ONE question",
                ],
                "ai_must_not": ["Rush them", "Be too casual", "Technical jargon"],
            },
            {
                "step": 2,
                "homeowner_reply": "Next week works fine, I'm retired so I'm home most days. Mornings are better for me - I have lunch with friends most afternoons. What day would work for you?",
                "ai_should": [
                    "Accommodate their schedule",
                    "Respectful tone",
                    "Clear about timing",
                ],
                "ai_must_not": [
                    "Be pushy about scheduling",
                    "Suggest inconvenient times",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Tuesday morning is perfect. Would 10 o'clock work? Address is 88-15 Yellowstone Boulevard, Forest Hills 11375. My phone number is 718-555-3021.",
                "ai_should": ["Confirm time and details", "Warm and respectful"],
                "ai_must_not": ["Be too brief", "Skip pleasantries"],
            },
            {
                "step": 4,
                "homeowner_reply": "Wonderful. Do you need me to do anything to prepare? Should I make sure the attic is accessible?",
                "ai_should": ["Simple preparation guidance", "Patient response"],
                "ai_must_not": ["Give complicated instructions"],
            },
            {
                "step": 5,
                "homeowner_reply": "That's easy enough. I'll have the attic stairs pulled down. Is there parking on the street or should I leave my driveway open?",
                "ai_should": ["Address parking question", "Courteous"],
                "ai_must_not": ["Dismiss the question as unnecessary"],
            },
            {
                "step": 6,
                "homeowner_reply": "Very good. I'll look for you Tuesday at 10. Thank you for your help.",
                "ai_should": ["Warm confirmation", "Match courteous tone"],
                "ai_must_not": ["Be too brief or casual"],
            },
        ],
    },
    "roof_skylight_leaking": {
        "business": "summit_roofing",
        "urgency": "urgent",
        "category": "roofing",
        "description": "Skylight leaking - impatient NYC homeowner",
        "homeowner_persona": {
            "personality": "impatient and busy",
            "communication_style": "rushed and direct",
            "regional_flavor": "NYC",
        },
        "initial_email": {
            "subject": "Skylight leak need fixed ASAP",
            "from_name": "Jordan Mitchell",
            "from_email": "jmitchell@gmail.com",
            "body": "Skylight in my bedroom is leaking. Dripping onto my bed when it rains. Need this fixed this week. Manhattan, UES. When can you come? Jordan 646-555-9034",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's the skylight above my bed. Started last month. Small drip during rain. Gets worse in heavy storms. Can you come Tuesday?",
                "ai_should": [
                    "Match direct, brief style",
                    "ONE question max",
                    "Very short",
                ],
                "ai_must_not": [
                    "Send long response",
                    "Ask multiple questions",
                    "Over-explain",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "245 E 78th St Apt 5C. Weekday mornings before 9am or after 7pm. Weekend mornings. Need it done this week.",
                "ai_should": [
                    "Acknowledge timeline pressure",
                    "Confirm if possible",
                    "Stay brief",
                ],
                "ai_must_not": ["Promise without checking", "Slow them down"],
            },
            {
                "step": 3,
                "homeowner_reply": "Wednesday 8am works. Don't be late, I have a meeting at 9:30. What's the cost?",
                "ai_should": ["Acknowledge timing", "No pricing", "Brief"],
                "ai_must_not": [
                    "Give pricing estimate",
                    "Get defensive about don't be late",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Fine. Wednesday 8am. Buzzer is broken, call when you arrive and I'll come down.",
                "ai_should": ["Note buzzer detail", "Simple confirmation"],
                "ai_must_not": ["Add unnecessary info"],
            },
        ],
    },
    "roof_full_replacement_quote_shopping": {
        "business": "boston_roofing_pros",
        "urgency": "low",
        "category": "roofing",
        "description": "Full roof replacement quote shopping - savvy Midwest homeowner",
        "homeowner_persona": {
            "personality": "savvy and comparison-shopping",
            "communication_style": "direct and evaluation-mode",
            "regional_flavor": "Midwest",
        },
        "initial_email": {
            "subject": "Roof replacement quote request",
            "from_name": "Karen Schultz",
            "from_email": "kschultz@gmail.com",
            "body": "I'm getting quotes for a full roof replacement. Colonial style home, approximately 2,400 sq ft, currently has asphalt shingles that are 23 years old. I'm getting 3-4 quotes before making a decision. What's your process for providing estimates? Located in Indianapolis. I've already had one company out but want to compare options and pricing before committing.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The first company quoted $14,500 for architectural shingles, 30-year warranty. They said 2-3 day job. What would your ballpark estimate be? I know you need to see it, but just generally speaking.",
                "ai_should": [
                    "Acknowledge other quotes",
                    "Don't give pricing",
                    "Respect shopping process",
                ],
                "ai_must_not": [
                    "Quote pricing without seeing it",
                    "Badmouth competitor pricing",
                    "Pressure them",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I understand. When could you come out for an estimate? And do you charge for estimates? The first company didn't charge. What questions should I be asking roofing contractors?",
                "ai_should": [
                    "Clear on estimate policy",
                    "Don't become their consultant",
                    "Professional",
                ],
                "ai_must_not": [
                    "Give lengthy advice on vetting contractors",
                    "Multiple questions",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "I can do Thursday or Friday afternoon this week, or next Monday. Address is 6834 Maple Grove Drive, Indianapolis 46220. How long does an estimate take?",
                "ai_should": [
                    "Typical estimate timeframe",
                    "Confirm scheduling",
                    "Professional",
                ],
                "ai_must_not": ["Over-explain estimate process"],
            },
            {
                "step": 4,
                "homeowner_reply": "Friday at 2pm works. Phone is 317-555-8802. Will you provide a written detailed estimate? The first company's was pretty vague.",
                "ai_should": ["Clarify estimate format", "Confirm appointment"],
                "ai_must_not": ["Criticize other company's estimate"],
            },
            {
                "step": 5,
                "homeowner_reply": "Good. I should have the other two estimates by next week so I can compare. Do you offer any warranties beyond the shingle manufacturer warranty?",
                "ai_should": ["Basic warranty info or defer to estimate", "Brief"],
                "ai_must_not": ["Get into detailed warranty comparison"],
            },
            {
                "step": 6,
                "homeowner_reply": "Sounds good. See you Friday at 2. I'll have my list of questions ready.",
                "ai_should": ["Welcome questions", "Professional confirmation"],
                "ai_must_not": ["Sound intimidated by their preparation"],
            },
        ],
    },
    # NEW ELECTRICAL SCENARIOS (6)
    "elec_ev_charger_panel_upgrade": {
        "business": "bay_area_electric",
        "urgency": "low",
        "category": "electrical",
        "description": "Panel upgrade for EV charger - tech-savvy California homeowner",
        "homeowner_persona": {
            "personality": "tech-savvy and detail-oriented",
            "communication_style": "technical and thorough",
            "regional_flavor": "California",
        },
        "initial_email": {
            "subject": "Electrical panel upgrade + Tesla charger installation",
            "from_name": "Michael Chen",
            "from_email": "mchen.sf@gmail.com",
            "body": "I'm getting a Tesla Model Y and need to install a Level 2 charger in my garage. My current panel is 100A service, and I understand I'll need to upgrade to 200A to support the 60A circuit for the charger plus my existing loads. House is in Palo Alto, built 1978. Also interested in future-proofing for solar if possible. What's involved in this upgrade? Permits? Timeline? Ballpark costs?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The panel is in the garage, original from 1978. I currently have electric dryer, electric stove, central AC, and standard 120V circuits. The charger would be wall-mounted about 15 feet from the panel. Tesla recommends 60A circuit. Do I need a load calculation first?",
                "ai_should": [
                    "Acknowledge technical knowledge",
                    "Don't quote pricing",
                    "Professional tone",
                ],
                "ai_must_not": [
                    "Get into detailed technical discussion",
                    "Recommend specific panel size",
                    "Give pricing",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Makes sense. For solar prep, I'm thinking 8-10kW system eventually. Should we run additional conduit during the panel upgrade? Also, who handles the PG&E coordination for the service upgrade?",
                "ai_should": [
                    "Acknowledge solar planning",
                    "Don't commit to specific approach",
                    "Defer details to assessment",
                ],
                "ai_must_not": [
                    "Design the system via email",
                    "Promise specific solar prep work",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Got it. When could you come assess the situation? I'm flexible most afternoons. Address is 2847 Waverley Street, Palo Alto 94301. How long does an assessment typically take?",
                "ai_should": [
                    "Typical assessment time",
                    "Move to scheduling",
                    "Professional",
                ],
                "ai_must_not": ["Continue technical discussion"],
            },
            {
                "step": 4,
                "homeowner_reply": "Tuesday at 3pm works great. Phone is 650-555-7734. Should I have my Tesla delivery date confirmed before we start work?",
                "ai_should": ["Address timing question", "Confirm appointment"],
                "ai_must_not": ["Over-explain project timeline"],
            },
            {
                "step": 5,
                "homeowner_reply": "Car arrives in 6 weeks so we have time. Will you provide a detailed written quote after the assessment? I need to submit it to my HOA for approval.",
                "ai_should": ["Clarify quote process", "Note HOA requirement"],
                "ai_must_not": [
                    "Promise specific quote format without knowing HOA requirements"
                ],
            },
            {
                "step": 6,
                "homeowner_reply": "Perfect. Looking forward to Tuesday. I'll have my panel photos and load info ready if that helps.",
                "ai_should": ["Welcome additional info", "Professional confirmation"],
                "ai_must_not": ["Request specific technical documentation"],
            },
        ],
    },
    "elec_partial_power_outage_elderly": {
        "business": "brightline_electric",
        "urgency": "urgent",
        "category": "electrical",
        "description": "Partial power outage - confused elderly Florida homeowner",
        "homeowner_persona": {
            "personality": "elderly and confused",
            "communication_style": "uncertain and needs patient explanation",
            "regional_flavor": "Florida",
        },
        "initial_email": {
            "subject": "Help - part of house has no power",
            "from_name": "Dorothy Williams",
            "from_email": "dwilliams52@aol.com",
            "body": "Hello, I'm having trouble with my electricity. Some rooms work but others don't. My bedroom and kitchen have power but the living room and bathroom are all dark. I checked the main breaker box in the garage and nothing looks tripped but I'm not sure what I'm looking for. I'm 78 and live alone. This is very concerning. I'm in Boca Raton, Florida. Can someone please help me? My phone is 561-555-8834.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Thank you for responding. The lights went out yesterday afternoon. I didn't do anything unusual - just turned on the bathroom light and it didn't work. Then I noticed the living room lamps don't work either. But my refrigerator is running fine. Is this dangerous? Should I call the electric company too?",
                "ai_should": [
                    "Very patient and clear",
                    "Reassuring tone",
                    "Simple guidance",
                ],
                "ai_must_not": [
                    "Use technical terms",
                    "Ask multiple questions",
                    "Rush them",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I called FPL and they said the power to my house is fine, it must be something inside. I'm worried about my bathroom - I can't see well in there at night without the light. Can someone come today? I'll be home all day.",
                "ai_should": [
                    "Acknowledge concern",
                    "Address availability clearly",
                    "Warm and patient",
                ],
                "ai_must_not": [
                    "Use jargon like GFCI or circuit",
                    "Make them feel foolish",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Oh that would be wonderful. My address is 4521 Cypress Point Drive, Boca Raton 33498. It's a single story house, the breaker box is in the garage. Should I leave the garage door open?",
                "ai_should": [
                    "Simple guidance on access",
                    "Clear about arrival",
                    "Patient",
                ],
                "ai_must_not": ["Give technical pre-diagnosis"],
            },
            {
                "step": 4,
                "homeowner_reply": "I'll leave it open then. What time should I expect you? And will you need to turn off all my power? I don't want my food to spoil.",
                "ai_should": [
                    "Clear about timing",
                    "Reassure about power",
                    "Simple explanation",
                ],
                "ai_must_not": [
                    "Be vague about timing",
                    "Over-explain the repair process",
                ],
            },
            {
                "step": 5,
                "homeowner_reply": "That's a relief. I'll be here. Thank you so much for your help, I was getting very worried.",
                "ai_should": ["Warm reassurance", "Confirm arrival"],
                "ai_must_not": ["Dismiss their concern"],
            },
        ],
    },
    "elec_smoke_detector_hardwiring": {
        "business": "brightline_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Smoke detector hardwiring - safety-conscious Boston parent",
        "homeowner_persona": {
            "personality": "safety-conscious parent",
            "communication_style": "concerned and thorough",
            "regional_flavor": "Boston",
        },
        "initial_email": {
            "subject": "Hardwire smoke detectors throughout house",
            "from_name": "Emily Kowalski",
            "from_email": "ekowalski@gmail.com",
            "body": "We just bought a house in Somerville and none of the smoke detectors are hardwired - they're all battery operated. We have two young kids and I want proper interconnected hardwired smoke alarms on all three floors. How many detectors do we need? What's involved in running the wiring? Can you also install carbon monoxide detectors? Safety is my top priority here.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The house is about 2,000 sq ft, three bedrooms upstairs, living/dining/kitchen first floor, finished basement. Currently there's one battery smoke alarm on each floor - clearly not enough. I've read we need them in each bedroom too. Is that code?",
                "ai_should": [
                    "Acknowledge safety concern",
                    "Don't give detailed code requirements",
                    "Professional",
                ],
                "ai_must_not": [
                    "Give specific code requirements",
                    "Quote detector quantities",
                    "Technical details",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I want to do this right the first time. Will you need to cut into walls and ceilings to run wires? We just painted and I'm trying to understand what we're getting into. Also, do the CO detectors need to be hardwired too?",
                "ai_should": [
                    "Honest about scope",
                    "No specific commitments",
                    "Understanding tone",
                ],
                "ai_must_not": [
                    "Promise no wall cutting",
                    "Get too technical about wiring paths",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "OK I appreciate the honesty. Can you come assess and give us a detailed quote? We'd want it done before the kids start sleeping here. We're available evenings or weekends. Address is 45 Morrison Ave, Somerville MA 02144.",
                "ai_should": [
                    "Acknowledge timeline concern",
                    "Move to scheduling",
                    "Professional and warm",
                ],
                "ai_must_not": ["Promise specific timeline", "Rush them"],
            },
            {
                "step": 4,
                "homeowner_reply": "Saturday morning works great. 10am? Phone is 617-555-6734. Should we have anything prepared for you to see?",
                "ai_should": ["Simple prep guidance", "Confirm appointment"],
                "ai_must_not": ["Request complicated preparations"],
            },
            {
                "step": 5,
                "homeowner_reply": "Perfect. We really appreciate you taking this seriously. See you Saturday at 10.",
                "ai_should": ["Reinforce safety importance", "Professional close"],
                "ai_must_not": ["Downplay their concern"],
            },
        ],
    },
    "elec_ceiling_fan_diy_failed": {
        "business": "lone_star_plumbing",
        "urgency": "medium",
        "category": "electrical",
        "description": "Ceiling fan installation - DIY-attempted Texas homeowner",
        "homeowner_persona": {
            "personality": "handy but got in over their head",
            "communication_style": "sheepish and frustrated",
            "regional_flavor": "Texas",
        },
        "initial_email": {
            "subject": "Need help finishing ceiling fan install",
            "from_name": "Tyler Morrison",
            "from_email": "tmorrison@gmail.com",
            "body": "So... I tried installing a ceiling fan myself and I think I screwed something up. I got the fan mounted but the wiring isn't working right - when I flip the switch the light comes on but the fan doesn't spin. Or sometimes the fan spins but the light doesn't work. I'm pretty handy but electrical isn't my thing. Can you come fix my mess? I'm in Austin. Already spent 6 hours on this thing and I'm done!",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's a new fan with light kit, replacing an old light fixture. There were three wires in the ceiling - black, white, and bare copper. The fan has four wires - black, white, blue, and green. I connected black to black, white to white, green and copper together, but I'm not sure about the blue wire. That's probably where I messed up, huh?",
                "ai_should": [
                    "Sympathetic to DIY attempt",
                    "Don't diagnose wiring",
                    "Light and friendly",
                ],
                "ai_must_not": [
                    "Give wiring instructions",
                    "Lecture about DIY electrical",
                    "Make them feel stupid",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Yeah, I figured it might be a switch thing too but I don't want to mess with it more and make it worse. How much do you charge to come fix this? I know I should've called you first.",
                "ai_should": ["Empathetic", "Don't quote price", "Casual Texas tone"],
                "ai_must_not": [
                    "Say I told you so",
                    "Give pricing",
                    "Be condescending",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Fair enough. I'm available weeknights after 5 or weekends. Address is 8834 Ranch Road, Austin 78749. This week would be great - my wife is not happy with me right now!",
                "ai_should": ["Light humor OK", "Move to scheduling", "Friendly"],
                "ai_must_not": ["Make jokes at their expense"],
            },
            {
                "step": 4,
                "homeowner_reply": "Thursday at 6 works perfect. Phone is 512-555-4401. Should I disconnect everything before you come or leave it how it is?",
                "ai_should": ["Simple safety guidance", "Confirm appointment"],
                "ai_must_not": ["Give complicated instructions"],
            },
        ],
    },
    "elec_gfci_bathroom_reno": {
        "business": "brightline_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "GFCI outlets for bathroom reno - contractor-savvy NYC homeowner",
        "homeowner_persona": {
            "personality": "contractor-savvy and knows the lingo",
            "communication_style": "direct with industry terms",
            "regional_flavor": "NYC",
        },
        "initial_email": {
            "subject": "Bathroom reno - GFCI outlets and fan",
            "from_name": "Alex Russo",
            "from_email": "arusso@gmail.com",
            "body": "Renovating a bathroom in my Astoria apartment. Need GFCI outlets installed per code - looks like I need two outlets and they have to be GFCI within 6 feet of water source. Also need exhaust fan wired. Current bathroom has one non-GFCI outlet and no fan. My contractor is doing the tile and plumbing but said I need to hire the electrical separately. Can you coordinate with another contractor? Timing needs to work with the tile guy's schedule.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Tile guy will be done with walls next Friday. After that you can do your thing, then he'll finish the floor. I need electrical rough-in done before tile, then final install after tile. You good with that sequence?",
                "ai_should": [
                    "Acknowledge contractor coordination",
                    "Professional tone",
                    "Clear about coordination",
                ],
                "ai_must_not": [
                    "Overcomplicate the staging",
                    "Promise specific timeline",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Perfect. For rough-in I need outlet boxes placed at 42 inches height, GFCI by sink and shower areas. Fan will be centered over shower. Do you need me there or can you coordinate directly with my tile guy Marco?",
                "ai_should": [
                    "Clarify coordination preference",
                    "Professional",
                    "ONE question",
                ],
                "ai_must_not": ["Get into technical placement details via email"],
            },
            {
                "step": 3,
                "homeowner_reply": "Cool. I'll connect you with Marco. Address is 31-15 23rd Avenue, Astoria 11105. Apartment 3R. Can you give me a quote before you start? Need it for my building's permit application.",
                "ai_should": [
                    "Address quote timing",
                    "Note permit requirement",
                    "Professional",
                ],
                "ai_must_not": [
                    "Give quote without seeing scope",
                    "Promise instant quote",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Can you come by this week to measure and quote? I'm there Wednesday and Thursday evenings after 7. Marco is there during days if you need to see it with him.",
                "ai_should": ["Scheduling options", "Confirm approach"],
                "ai_must_not": ["Over-explain the quoting process"],
            },
            {
                "step": 5,
                "homeowner_reply": "Thursday at 7:30 works. Phone is 718-555-9021. Marco's number is 917-555-3401 if you need to coordinate. Bring a quote sheet or whatever you need.",
                "ai_should": [
                    "Note both contacts",
                    "Confirm appointment",
                    "Professional",
                ],
                "ai_must_not": ["Over-communicate"],
            },
        ],
    },
    "elec_outdoor_security_lighting": {
        "business": "brightline_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Outdoor lighting for security - concerned homeowner",
        "homeowner_persona": {
            "personality": "concerned about safety",
            "communication_style": "direct with security focus",
            "regional_flavor": "Queens",
        },
        "initial_email": {
            "subject": "Install outdoor security lighting",
            "from_name": "Sharon Baptiste",
            "from_email": "sbaptiste@gmail.com",
            "body": "We've had some break-ins in our neighborhood recently and I want to install motion-sensor security lights around our house. Need lighting on the driveway, back yard, and both side entrances. Currently we only have one light by the front door. What's involved in running power to these locations? Do you install the lights too or just the wiring? Located in Jamaica, Queens.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Ideally I want motion-sensor LED floods. Driveway and back yard are priority - those are completely dark right now. How many lights would you recommend? Also, can they connect to a timer or smart control?",
                "ai_should": [
                    "Acknowledge security concern",
                    "Don't recommend specific quantities",
                    "Professional",
                ],
                "ai_must_not": [
                    "Design the system via email",
                    "Recommend specific products",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "That makes sense. When could you come assess? I work during the week but I'm home after 6pm or weekends. Address is 178-24 Dalton Avenue, Jamaica 11432. How long does installation typically take?",
                "ai_should": [
                    "Move to scheduling",
                    "General timeline if typical",
                    "Professional",
                ],
                "ai_must_not": [
                    "Promise specific timeline",
                    "Get into technical installation details",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Saturday afternoon works. 3pm? Phone is 718-555-7812. Should I buy the lights first or wait until you assess?",
                "ai_should": ["Guidance on purchasing", "Confirm appointment"],
                "ai_must_not": ["Be vague about who provides fixtures"],
            },
            {
                "step": 4,
                "homeowner_reply": "Good to know. I'll wait for your recommendation. Do you have experience with Ring or other smart security lights?",
                "ai_should": [
                    "Brief response on smart systems",
                    "Don't commit to specific brands",
                ],
                "ai_must_not": ["Get into product comparison"],
            },
            {
                "step": 5,
                "homeowner_reply": "Perfect. See you Saturday at 3. Really appreciate the help - this has been worrying me.",
                "ai_should": ["Empathetic acknowledgment", "Confirm appointment"],
                "ai_must_not": ["Dismiss their security concern"],
            },
        ],
    },
    # NEW GENERAL CONTRACTOR SCENARIOS (8)
    "gc_basement_waterproofing_finish": {
        "business": "midwest_home_builders",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Basement waterproofing and finish - detailed Pennsylvania homeowner",
        "homeowner_persona": {
            "personality": "detail-oriented and project-planning",
            "communication_style": "thorough with many questions",
            "regional_flavor": "Pennsylvania",
        },
        "initial_email": {
            "subject": "Basement waterproofing + finishing project",
            "from_name": "Christine Wallace",
            "from_email": "cwallace@gmail.com",
            "body": "We have a partially finished basement that gets damp in heavy rains. Want to properly waterproof it and then finish it as a family room + guest bedroom. About 900 sq ft total. Currently has concrete floors, exposed studs on two walls, foundation walls on other two. Need waterproofing, insulation, drywall, flooring, electrical, bathroom addition. This is a big project and I want to understand the full scope before committing. Located in Pittsburgh area.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The water issue is primarily on the north wall - we get dampness and some seepage where the wall meets the floor during heavy rain. I've had two waterproofing companies out and got quotes for interior drain tile system. Should I do that waterproofing first before you start the finishing work?",
                "ai_should": [
                    "Acknowledge waterproofing priority",
                    "Don't give specific sequencing yet",
                    "Professional",
                ],
                "ai_must_not": [
                    "Recommend specific waterproofing approach",
                    "Commit to project sequence",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "That makes sense. For the finish work, I'm envisioning: family room area with LVP flooring and recessed lighting, a guest bedroom with closet and egress window, and a 3/4 bathroom. Do you handle everything including the plumbing and electrical or do I need separate contractors?",
                "ai_should": [
                    "Clarify trade coverage",
                    "Ask for photos or site visit",
                    "Professional",
                ],
                "ai_must_not": ["Give detailed scope breakdown", "Quote pricing"],
            },
            {
                "step": 3,
                "homeowner_reply": "Good to know you handle all trades. Budget-wise we're thinking $50-70k total. Is that realistic? And what's a typical timeline for a project like this? We're not in a rush but want to plan around the holidays.",
                "ai_should": [
                    "Acknowledge budget question without committing",
                    "No timeline commitment",
                    "Need site visit",
                ],
                "ai_must_not": [
                    "Validate or reject their budget",
                    "Give project timeline",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "Understood. When could you come walk through and assess? We're available most evenings and weekends. Address is 4521 Denniston Street, Pittsburgh PA 15217. Should I have anything prepared - measurements, plans, waterproofing quotes?",
                "ai_should": [
                    "Helpful guidance on preparation",
                    "Move to scheduling",
                    "Organized tone",
                ],
                "ai_must_not": ["Require extensive prep work", "Over-complicate"],
            },
            {
                "step": 5,
                "homeowner_reply": "Saturday morning at 10 works great. Phone is 412-555-8901. Will you be able to give us a detailed written estimate after the walkthrough? And how long until we'd get that estimate?",
                "ai_should": [
                    "Clear about estimate process and timing",
                    "Confirm appointment",
                ],
                "ai_must_not": ["Promise instant estimate", "Be vague about process"],
            },
            {
                "step": 6,
                "homeowner_reply": "Perfect. We'll have our ideas and questions ready. Looking forward to Saturday. Thanks for the thorough responses.",
                "ai_should": ["Professional and warm close", "Confirm details"],
                "ai_must_not": ["Over-promise on the project"],
            },
        ],
    },
    "gc_deck_replacement_materials": {
        "business": "midwest_home_builders",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Deck replacement wood vs composite - indecisive homeowner",
        "homeowner_persona": {
            "personality": "indecisive and deliberating",
            "communication_style": "back-and-forth with lots of what-ifs",
            "regional_flavor": "Midwest",
        },
        "initial_email": {
            "subject": "Replace old deck - need advice on materials",
            "from_name": "Brian Patterson",
            "from_email": "bpatterson@gmail.com",
            "body": "Our deck is 20 years old and falling apart. Need to replace it but can't decide between wood and composite. I've read so many reviews and forums and I'm just more confused. Wood is cheaper but needs maintenance. Composite is expensive but lasts longer. But some composites get hot in the sun. And some look fake. What do most of your customers do? The deck is about 300 sq ft, ground level. Indianapolis area.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Yeah I know I need to decide. Part of me thinks just go with pressure-treated wood since it's half the cost. But then I think about staining it every few years and I hate maintenance. How much more is composite really? Like double? And does composite hold up in midwest winters?",
                "ai_should": [
                    "Patient tone",
                    "Don't give pricing",
                    "Don't push them to decide",
                ],
                "ai_must_not": [
                    "Give specific pricing comparison",
                    "Recommend one over the other",
                    "Show impatience",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "But if I go composite, which brand? Trex? TimberTech? They're all so expensive and they seem pretty similar. Do you have a preference? What if I do wood deck boards but composite railing? Is that weird?",
                "ai_should": [
                    "Acknowledge questions",
                    "Redirect to site visit",
                    "Patient",
                ],
                "ai_must_not": [
                    "Recommend specific brands",
                    "Get into detailed material comparison",
                    "Rush them",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "OK yeah that makes sense. Can you show me samples when you come? And maybe show me pictures of decks you've done in both materials? That might help me visualize it better.",
                "ai_should": [
                    "Willing to show examples",
                    "Move to scheduling",
                    "Helpful tone",
                ],
                "ai_must_not": ["Complicate with too many options"],
            },
            {
                "step": 4,
                "homeowner_reply": "I'm free next Saturday or the following weekend. Either works. Address is 7823 Brookside Avenue, Indianapolis 46220. Should my wife be there too? She might have different opinions than me.",
                "ai_should": [
                    "Encourage both homeowners present",
                    "Confirm scheduling",
                    "Friendly",
                ],
                "ai_must_not": ["Show concern about indecisiveness"],
            },
            {
                "step": 5,
                "homeowner_reply": "Next Saturday at 11 then. Phone is 317-555-6701. Do I need to have the old deck torn down first or do you handle that too? And what if we decide to make it bigger while we're at it?",
                "ai_should": ["Address demo question", "Keep options open", "Patient"],
                "ai_must_not": ["Get frustrated with more questions"],
            },
            {
                "step": 6,
                "homeowner_reply": "Alright, we'll talk it all through Saturday. I promise I'll make a decision after we meet. My wife says I overthink everything!",
                "ai_should": ["Warm and understanding", "Light humor OK", "Confirm"],
                "ai_must_not": ["Agree that they overthink in a critical way"],
            },
        ],
    },
    "gc_bathroom_gut_reno": {
        "business": "apex_construction",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Bathroom gut renovation - impatient NYC homeowner",
        "homeowner_persona": {
            "personality": "impatient and deadline-driven",
            "communication_style": "rushed and results-focused",
            "regional_flavor": "NYC",
        },
        "initial_email": {
            "subject": "Full bathroom renovation - start ASAP",
            "from_name": "Lauren Goldberg",
            "from_email": "lgoldberg@gmail.com",
            "body": "Need to gut renovate my master bathroom. Everything goes - tub, tile, vanity, toilet, all of it. Want to start ASAP, ideally within 2 weeks. How fast can you do a bathroom? I'm talking full demo to finished in like 3-4 weeks max. UWS Manhattan. Need someone who works FAST. Lauren 212-555-8834",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's about 8x7 feet. Tub/shower combo along one wall, vanity, toilet. Want to do walk-in shower, floating vanity, new tile floor to ceiling, better lighting. Nothing crazy fancy but quality materials. Can you do it in a month?",
                "ai_should": [
                    "Don't commit to timeline",
                    "Match directness",
                    "Professional",
                ],
                "ai_must_not": [
                    "Promise 4-week timeline",
                    "Be overly cautious about timeline",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I get that. When can you come see it? I need to get this moving. Available tomorrow afternoon or Thursday morning. 245 W 104th St Apt 8B. How long after you see it before I get a quote?",
                "ai_should": [
                    "Match urgency in scheduling",
                    "Clear about quote timing",
                    "Professional",
                ],
                "ai_must_not": [
                    "Slow them down unnecessarily",
                    "Promise instant quote",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Thursday at 10 works. 212-555-8834. I'll have photos of bathrooms I like for reference. Can you send me examples of your work before Thursday?",
                "ai_should": [
                    "Address portfolio request",
                    "Confirm appointment",
                    "Brief",
                ],
                "ai_must_not": ["Over-promise on portfolio", "Sound defensive"],
            },
            {
                "step": 4,
                "homeowner_reply": "Thanks. And to be clear - I need reliable contractors who show up every day and finish on time. I work from home and can't have this dragging on forever. That won't be a problem, right?",
                "ai_should": [
                    "Confident but realistic",
                    "Don't over-promise",
                    "Professional",
                ],
                "ai_must_not": [
                    "Say anything that sounds like excuse-making",
                    "Guarantee no delays",
                ],
            },
            {
                "step": 5,
                "homeowner_reply": "Good. See you Thursday at 10. Don't be late, I have a call at 11.",
                "ai_should": ["Simple confirmation", "Note their schedule"],
                "ai_must_not": ["Get defensive about don't be late", "Over-explain"],
            },
        ],
    },
    "gc_kitchen_island_addition": {
        "business": "apex_construction",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Kitchen island addition - planning California homeowner",
        "homeowner_persona": {
            "personality": "planning-oriented and measuring",
            "communication_style": "detailed with dimensions",
            "regional_flavor": "California",
        },
        "initial_email": {
            "subject": "Add kitchen island with electrical",
            "from_name": "Priya Sharma",
            "from_email": "psharma.ca@gmail.com",
            "body": "We want to add an island to our kitchen. Current kitchen is 14x16 feet with an open layout to dining. I've measured and we have room for approximately a 4x6 foot island with 42 inches clearance on all sides per what I've read online. Would need electrical outlets, pendant lights above, and we're thinking quartz countertop. Nothing structural - just building the island and finishing it. Located in San Jose, CA. What's involved in a project like this?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Good questions. We want seating on one side - probably 3 stools. Base cabinets for storage on the other sides. I've been looking at IKEA cabinets but open to other options if you have suggestions. The electrical is the part I'm fuzzy on - we'd need outlets on the side for appliances and wiring for pendant lights above. Is that complicated?",
                "ai_should": [
                    "Acknowledge planning",
                    "Don't get into electrical technical details",
                    "Professional",
                ],
                "ai_must_not": [
                    "Recommend specific cabinet sources",
                    "Diagnose electrical complexity",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I have sketches and measurements. The current flooring is hardwood that we'd want to match or we could do tile under the island - haven't decided. Do you handle the electrical or do I need a separate electrician? And do you source the countertop or do I?",
                "ai_should": [
                    "Clarify what's included in scope",
                    "Professional",
                    "Ask to see plans",
                ],
                "ai_must_not": [
                    "Commit to specific scope without seeing it",
                    "Give pricing",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Great. When could you come by? Evenings after 6 or weekends work for us. Address is 2941 Meridian Avenue, San Jose CA 95124. I'll have my sketches and measurements ready. Should I have anything else prepared?",
                "ai_should": [
                    "Helpful on what to prepare",
                    "Scheduling",
                    "Organized tone",
                ],
                "ai_must_not": ["Require extensive prep"],
            },
            {
                "step": 4,
                "homeowner_reply": "Saturday at 2pm perfect. Phone is 408-555-7123. Budget-wise we're hoping to stay under $15k for everything. Is that doable? I know quartz is expensive.",
                "ai_should": [
                    "Acknowledge budget without committing",
                    "Need to see scope first",
                ],
                "ai_must_not": ["Validate or reject budget", "Quote pricing"],
            },
            {
                "step": 5,
                "homeowner_reply": "Understood. I'll have my inspiration photos and material samples ready too. We're not in a huge rush but would like to get started within the next couple months.",
                "ai_should": ["Note timing", "Confirm appointment", "Professional"],
                "ai_must_not": ["Commit to start date"],
            },
            {
                "step": 6,
                "homeowner_reply": "Perfect. See you Saturday at 2. Really looking forward to finally having an island!",
                "ai_should": ["Warm and professional close"],
                "ai_must_not": ["Over-promise on the project"],
            },
        ],
    },
    "gc_exterior_door_accessibility": {
        "business": "midwest_home_builders",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Exterior door replacement - elderly homeowner accessibility",
        "homeowner_persona": {
            "personality": "elderly with mobility concerns",
            "communication_style": "deliberate and accessibility-focused",
            "regional_flavor": "Midwest",
        },
        "initial_email": {
            "subject": "Replace back door - accessibility needed",
            "from_name": "George Henderson",
            "from_email": "ghenderson@aol.com",
            "body": "I'm 76 and recently had hip surgery. My back door has a 6-inch step down to the patio that's becoming difficult for me to navigate. I'd like to replace the door and possibly add a ramp or eliminate the step somehow. The door itself is also old and hard to open. Looking for someone who understands accessibility modifications. Located in Indianapolis. Would this be something you could help with?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Thank you. It's a standard exterior door, 36 inches wide. The threshold has that 6-inch drop to the concrete patio. My physical therapist suggested getting a ramp but I don't know if that's the best option or if there's a better way. I use a cane currently but may need a walker in the future.",
                "ai_should": [
                    "Compassionate and patient",
                    "Don't recommend specific solution",
                    "Respectful",
                ],
                "ai_must_not": [
                    "Get technical about accessibility codes",
                    "Rush them",
                    "Recommend without seeing it",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "That would be helpful. I also need the door handle to be a lever style instead of a knob - knobs are hard for me to grip now. And the door is heavy to push open. Are there easier doors for seniors?",
                "ai_should": [
                    "Acknowledge needs",
                    "Don't give product recommendations",
                    "Patient",
                ],
                "ai_must_not": ["Recommend specific door products", "Over-complicate"],
            },
            {
                "step": 3,
                "homeowner_reply": "I'd like that. I'm home most days. Mornings are best for me - I get tired in the afternoons. Would sometime next week work? Address is 4521 Willow Street, Indianapolis 46208.",
                "ai_should": [
                    "Accommodate their schedule",
                    "Respectful and patient",
                    "Clear timing",
                ],
                "ai_must_not": ["Suggest inconvenient times"],
            },
            {
                "step": 4,
                "homeowner_reply": "Tuesday at 10 is perfect. Phone is 317-555-4402. Should I have my daughter here? She helps me make decisions on bigger things like this.",
                "ai_should": ["Welcome daughter's presence", "Supportive tone"],
                "ai_must_not": ["Discourage family involvement"],
            },
        ],
    },
    "gc_drywall_repair_water_damage": {
        "business": "apex_construction",
        "urgency": "medium",
        "category": "general_contractor",
        "description": "Drywall repair from water damage - insurance claim",
        "homeowner_persona": {
            "personality": "insurance-claim focused",
            "communication_style": "process-oriented with insurance questions",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Drywall repair - insurance claim from pipe burst",
            "from_name": "Kevin Walsh",
            "from_email": "kwalsh@gmail.com",
            "body": "We had a pipe burst in February that caused water damage to two rooms - bedroom ceiling and hallway wall. Insurance (State Farm) has approved the claim and I need to get the drywall repaired and repainted. The water remediation company already removed the damaged sections. Do you work with insurance claims? Do you bill the insurance directly or do I pay and get reimbursed? Located in Montclair, NJ.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The adjuster estimated about 60 sq ft of ceiling drywall and 40 sq ft of wall to be replaced, plus painting both rooms. I have the insurance estimate - should I send that to you? Does your estimate need to match theirs or can it be different?",
                "ai_should": [
                    "Clarify insurance process",
                    "Professional",
                    "Don't over-commit on process",
                ],
                "ai_must_not": [
                    "Promise to match insurance estimate",
                    "Give insurance billing advice",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "That makes sense. The damaged areas are currently just open - you can see the studs and insulation. Everything is dry now. When could you come assess and give me a quote? I need to get this done soon because we have family visiting in a month.",
                "ai_should": ["Move to scheduling", "Note deadline", "Professional"],
                "ai_must_not": [
                    "Promise to meet their deadline",
                    "Rush the assessment",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "This week would be great. I work from home so I'm flexible. Address is 234 Valley Road, Montclair NJ 07042. Should I have the insurance paperwork ready for you to see?",
                "ai_should": ["Helpful on what to have ready", "Confirm scheduling"],
                "ai_must_not": ["Require extensive insurance documentation upfront"],
            },
            {
                "step": 4,
                "homeowner_reply": "Thursday at 2 works. Phone is 862-555-7734. For the painting, do I need to pick the paint colors beforehand or can we do that later?",
                "ai_should": [
                    "Simple guidance on paint selection",
                    "Confirm appointment",
                ],
                "ai_must_not": ["Over-explain the process"],
            },
            {
                "step": 5,
                "homeowner_reply": "Perfect. I'll have the insurance docs and photos of the damage ready. See you Thursday.",
                "ai_should": ["Professional confirmation"],
                "ai_must_not": ["Over-communicate"],
            },
        ],
    },
    "gc_attic_conversion_office": {
        "business": "apex_construction",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Attic conversion to office - remote worker detailed requirements",
        "homeowner_persona": {
            "personality": "remote worker with specific needs",
            "communication_style": "detailed about workspace requirements",
            "regional_flavor": "New Jersey",
        },
        "initial_email": {
            "subject": "Attic conversion to home office",
            "from_name": "Jessica Nguyen",
            "from_email": "jnguyen@gmail.com",
            "body": "I'm a full-time remote software engineer and need to convert our attic into a proper home office. Currently it's unfinished - insulated but no drywall, flooring is plywood. About 400 sq ft. Need: good insulation for HVAC, electrical outlets (lots of them), ethernet wiring, possibly a half bath, good lighting, and noise insulation from kids below. Also concerned about egress window requirements. This needs to be a real workspace. Located in Hoboken. What's your experience with attic conversions?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "The attic has 8-foot ceilings in the center, slopes down to 4 feet on the sides. Current access is pull-down stairs - would probably need real stairs for regular office use. I'm on video calls 4-5 hours a day so soundproofing from downstairs is critical. Kids are loud. Do you handle the HVAC extension too?",
                "ai_should": [
                    "Acknowledge complex requirements",
                    "Don't commit to specific scope",
                    "Professional",
                ],
                "ai_must_not": [
                    "Try to scope entire project via email",
                    "Give technical advice",
                    "Quote pricing",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "For the half bath, I know that's a big add. Maybe that's phase 2. The office workspace is priority - I literally work up there 8 hours a day so it needs to be comfortable. What about HVAC? Does heat rise enough or do I need a mini-split?",
                "ai_should": [
                    "Acknowledge phasing",
                    "Don't give HVAC advice",
                    "Redirect to assessment",
                ],
                "ai_must_not": [
                    "Design the HVAC system",
                    "Recommend specific approach",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Makes sense. Timeline-wise I'd want to start in the next 2-3 months and I'm hoping it takes 4-6 weeks total. Is that realistic? I can work from a coffee shop during construction but not for months.",
                "ai_should": [
                    "No timeline commitment",
                    "Honest about complexity",
                    "Professional",
                ],
                "ai_must_not": [
                    "Commit to 4-6 week timeline",
                    "Dismiss their concerns",
                ],
            },
            {
                "step": 4,
                "homeowner_reply": "OK, when can you come by? I'm pretty flexible - I work from home so just about any day works. Address is 523 Garden Street, Hoboken NJ 07030. Should I have anything specific ready - measurements, codes, inspiration photos?",
                "ai_should": ["Helpful preparation guidance", "Move to scheduling"],
                "ai_must_not": ["Require extensive prep work"],
            },
            {
                "step": 5,
                "homeowner_reply": "Next Tuesday at 5 works. Phone is 551-555-8901. Budget-wise I'm thinking $40-60k depending on whether we do the bathroom. Am I in the ballpark?",
                "ai_should": [
                    "Acknowledge budget without committing",
                    "Need assessment first",
                ],
                "ai_must_not": ["Validate or reject budget", "Give pricing guidance"],
            },
            {
                "step": 6,
                "homeowner_reply": "Got it. I'll have my requirements doc ready - I'm an engineer, I made a spreadsheet. See you Tuesday!",
                "ai_should": ["Welcome their preparation", "Professional and warm"],
                "ai_must_not": ["Be intimidated by spreadsheet"],
            },
        ],
    },
    "gc_multiroom_paint_trim": {
        "business": "midwest_home_builders",
        "urgency": "low",
        "category": "general_contractor",
        "description": "Multi-room paint and trim work - budget-conscious homeowner",
        "homeowner_persona": {
            "personality": "budget-conscious and comparing quotes",
            "communication_style": "practical and cost-focused",
            "regional_flavor": "Midwest",
        },
        "initial_email": {
            "subject": "Interior painting - 5 rooms plus trim",
            "from_name": "Mike and Sarah Kowalski",
            "from_email": "mkowalski@gmail.com",
            "body": "Need interior painting for 5 rooms - living room, dining room, kitchen, and two bedrooms. Also want to repaint all the trim throughout the house - it's currently cream and we want bright white. Total house is about 2,000 sq ft. Getting multiple quotes to compare. What's your price per sq ft or per room? We're in Indianapolis and hoping to keep the total under $5,000. Possible?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Rooms are all standard size, 8-foot ceilings. Walls are in decent shape - some small holes to patch but nothing major. We're providing the paint - already picked colors and planning to buy. Just need labor. Does that affect your price?",
                "ai_should": [
                    "Acknowledge DIY paint supply",
                    "Don't quote pricing",
                    "Professional",
                ],
                "ai_must_not": [
                    "Give per sq ft pricing",
                    "Commit to their budget",
                    "Discourage them from buying paint",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "I've gotten one quote so far for $6,200 including paint. Seems high? That's why I'm shopping around. Can you give me at least a ballpark range so I know if it's worth having you come out?",
                "ai_should": [
                    "Respect budget concern",
                    "Don't quote pricing",
                    "Redirect to assessment",
                ],
                "ai_must_not": [
                    "Compare to other quote",
                    "Give range",
                    "Make them feel bad for asking",
                ],
            },
            {
                "step": 3,
                "homeowner_reply": "Alright, I get it. When could you come by? We're available evenings or weekends. Address is 7234 Brookside Avenue, Indianapolis 46220. How long does a walkthrough take?",
                "ai_should": [
                    "Move to scheduling",
                    "Typical walkthrough time",
                    "Professional",
                ],
                "ai_must_not": ["Continue pricing discussion"],
            },
            {
                "step": 4,
                "homeowner_reply": "Saturday at 11 works. Phone is 317-555-6623. Do we need to have furniture moved already or will you account for that in the quote?",
                "ai_should": ["Address furniture question", "Confirm appointment"],
                "ai_must_not": ["Over-explain the painting process"],
            },
            {
                "step": 5,
                "homeowner_reply": "OK good to know. And timeline - how long would this take once you start? We're flexible but curious.",
                "ai_should": ["General timeline if typical", "Defer to quote", "Brief"],
                "ai_must_not": ["Commit to specific timeline"],
            },
        ],
    },
    # ========================================
    # PHOTO REQUEST/ACKNOWLEDGMENT SCENARIOS
    # Testing photo request logic and phrasing
    # ========================================
    "plumb_photo_water_heater": {
        "business": "miller_plumbing",
        "urgency": "medium",
        "category": "plumbing",
        "description": "Plumbing - water heater issue, bot should ask for EQUIPMENT photo with specific guidance",
        "homeowner_persona": {
            "personality": "practical and helpful",
            "communication_style": "cooperative",
            "regional_flavor": "Austin, TX",
        },
        "initial_email": {
            "from_name": "Mike Chen",
            "from_email": "mike.chen@email.com",
            "subject": "Water heater not heating",
            "body": "Hi, my water heater stopped making hot water yesterday. It's a gas unit in the garage, pilot light is on but no hot water. Can you come take a look?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Started yesterday morning. I tried the reset button but nothing changed. How soon can someone come out?",
                "ai_should": [
                    "Ask for photo of water heater label",
                    "Specify WHAT to photograph (manufacturer label)",
                    "Explain WHY (helps know what parts to bring)",
                    "Casual tone",
                ],
                "ai_must_not": [
                    'Generic "send photos of the issue"',
                    "Skip photo request for EQUIPMENT",
                    "Ask multiple questions",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Sure, just sent 2 photos of the label. Address is 4521 Riverside Drive. When works for you?",
                "ai_should": [
                    "Acknowledge photos received",
                    "Move to availability",
                    "Brief",
                ],
                "ai_must_not": ["Ignore that photos were sent", "Ask for more photos"],
            },
        ],
    },
    "elec_photo_panel": {
        "business": "bay_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Electrical - panel upgrade, bot should ask for EQUIPMENT photo (panel with door open)",
        "homeowner_persona": {
            "personality": "detail-oriented",
            "communication_style": "thorough",
            "regional_flavor": "Portland, OR",
        },
        "initial_email": {
            "from_name": "Sarah Martinez",
            "from_email": "sarah.m@email.com",
            "subject": "Need panel upgrade quote",
            "body": "Looking to upgrade my electrical panel to 200 amp. Current panel seems old and we're adding EV charger. What do you need from me to provide a quote?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "It's in the basement. Not sure of the brand, kind of old looking. What info do you need?",
                "ai_should": [
                    "Ask for photo of panel with door open",
                    "Specify WHAT (panel with door open showing brand/breakers)",
                    "Explain WHY (know what replacement is needed)",
                ],
                "ai_must_not": ["Skip photo request", 'Vague "send some photos"'],
            },
            {
                "step": 2,
                "homeowner_reply": 'Just emailed you a photo. I see it says "Federal Pacific" on it. Address is 823 NW Maple Street.',
                "ai_should": [
                    "Acknowledge photo",
                    "Continue with next qualification step",
                ],
                "ai_must_not": [
                    "Provide technical assessment of Federal Pacific",
                    "Diagnose safety issue",
                ],
            },
        ],
    },
    "roof_photo_storm": {
        "business": "summit_roofing",
        "urgency": "urgent",
        "category": "roofing",
        "description": "Roofing - ALWAYS needs photos, bot should ask even for urgent scenarios",
        "homeowner_persona": {
            "personality": "stressed but organized",
            "communication_style": "efficient",
            "regional_flavor": "Oklahoma City",
        },
        "initial_email": {
            "from_name": "Tom Bradley",
            "from_email": "tom.bradley@email.com",
            "subject": "Storm damage - need inspection",
            "body": "Had bad storms last night. Got some shingles blown off and water stain appearing on bedroom ceiling. Need someone out ASAP.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Not actively dripping but the stain is growing. Maybe 10-12 shingles missing from what I can see from the ground. When can you come?",
                "ai_should": [
                    "Ask for photos (roof surface AND interior damage)",
                    "ROOFING always needs photos",
                    "Acknowledge urgency but still request photos",
                ],
                "ai_must_not": [
                    "Skip photos because it's urgent",
                    "Just ask for address without photos",
                ],
            }
        ],
    },
    "gc_photo_kitchen_remodel": {
        "business": "pacific_builders",
        "urgency": "planning",
        "category": "general_contractor",
        "description": "GC - remodel project, should ask for CURRENT SPACE photos with layout/condition",
        "homeowner_persona": {
            "personality": "enthusiastic planner",
            "communication_style": "detailed",
            "regional_flavor": "San Diego",
        },
        "initial_email": {
            "from_name": "Jennifer Park",
            "from_email": "jpark@email.com",
            "subject": "Kitchen remodel quote request",
            "body": "Want to remodel our dated 90s kitchen. New cabinets, counters, flooring, the works. Looking for a ballpark quote to start planning. Space is about 12x14.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Late summer or early fall. We're flexible on timing but want to get the budget nailed down first. What else do you need?",
                "ai_should": [
                    "Ask for photos of current kitchen",
                    "Specify WHAT (layout and current cabinets/condition)",
                    "Explain WHY (helps scope the project)",
                ],
                "ai_must_not": [
                    "Skip photo request for REMODEL project",
                    "Generic photo request",
                ],
            }
        ],
    },
    "plumb_no_photo_slow_drain": {
        "business": "miller_plumbing",
        "urgency": "low",
        "category": "plumbing",
        "description": "Plumbing - slow drain, bot should NOT ask for photos (invisible issue)",
        "homeowner_persona": {
            "personality": "practical",
            "communication_style": "brief",
            "regional_flavor": "Austin, TX",
        },
        "initial_email": {
            "from_name": "Dan Wilson",
            "from_email": "dan.w@email.com",
            "subject": "Slow kitchen drain",
            "body": "Kitchen sink draining really slow. Tried Drano, didn't help. Need a plumber to snake it out.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Just the kitchen sink. Been slow for about 2 weeks, getting worse. 1823 Oak Street. When could you come by?",
                "ai_should": [
                    "NOT ask for photos",
                    "Move to availability",
                    "Slow drain = invisible issue = no photos useful",
                ],
                "ai_must_not": ["Ask for photos of drain", "Request photos"],
            }
        ],
    },
    "elec_no_photo_flickering": {
        "business": "bay_electric",
        "urgency": "medium",
        "category": "electrical",
        "description": "Electrical - flickering lights, bot should NOT ask for photos (invisible issue)",
        "homeowner_persona": {
            "personality": "concerned homeowner",
            "communication_style": "detailed",
            "regional_flavor": "Seattle",
        },
        "initial_email": {
            "from_name": "Amy Tran",
            "from_email": "amy.tran@email.com",
            "subject": "Lights flickering in living room",
            "body": "All the lights in our living room flicker when we turn on the TV. Worried it's a wiring issue. Can you diagnose this?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Started about a month ago. Only happens in the living room, rest of house is fine. 6634 Pine Avenue. Available most afternoons.",
                "ai_should": [
                    "NOT ask for photos",
                    "Move to scheduling",
                    "Flickering = invisible issue = nothing to photograph",
                ],
                "ai_must_not": [
                    "Ask for photos",
                    "Request pictures of flickering lights",
                ],
            }
        ],
    },
    "plumb_photo_visible_damage": {
        "business": "miller_plumbing",
        "urgency": "urgent",
        "category": "plumbing",
        "description": "Plumbing - visible water damage, should ask for DAMAGE photos",
        "homeowner_persona": {
            "personality": "stressed",
            "communication_style": "urgent",
            "regional_flavor": "Houston",
        },
        "initial_email": {
            "from_name": "Carlos Rivera",
            "from_email": "crivera@email.com",
            "subject": "Water leak - ceiling damage",
            "body": "Got a water stain on the ceiling under the upstairs bathroom. Seems to be getting worse. Need help ASAP.",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "About 2 feet across, brownish stain. Not dripping but definitely wet. 9234 Westheimer Road. Can you come today?",
                "ai_should": [
                    "Ask for photo of ceiling damage",
                    "Visible DAMAGE = photos helpful",
                    "Keep it brief given urgency",
                ],
                "ai_must_not": [
                    "Skip photo request for visible damage",
                    "Lengthy photo instructions when urgent",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "[Attaches 2 photos of ceiling stain] Here you go. Phone is 281-555-4433.",
                "ai_should": ["Acknowledge photos", "Proceed to handoff"],
                "ai_must_not": ["Ignore photo acknowledgment"],
            },
        ],
    },
    "roof_photo_acknowledge": {
        "business": "summit_roofing",
        "urgency": "medium",
        "category": "roofing",
        "description": "Roofing - customer proactively sends photos, bot should acknowledge them",
        "homeowner_persona": {
            "personality": "organized and proactive",
            "communication_style": "efficient",
            "regional_flavor": "Denver",
        },
        "initial_email": {
            "from_name": "Linda Hayes",
            "from_email": "lhayes@email.com",
            "subject": "Roof inspection - photos attached",
            "body": "Need a roof inspection. I've attached 3 photos showing some shingles that look damaged on the south-facing slope. Can you give me an estimate for repair?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "House is about 15 years old. This is the original roof. 4422 Mountain View Drive. When could someone come by?",
                "ai_should": [
                    "Acknowledge photos were already provided",
                    "NOT ask for more photos",
                    "Move to availability",
                ],
                "ai_must_not": [
                    "Ask for photos they already sent",
                    "Ignore that photos were attached initially",
                ],
            }
        ],
    },
    "plumb_photo_fixture_matching": {
        "business": "miller_plumbing",
        "urgency": "low",
        "category": "plumbing",
        "description": "Plumbing - fixture replacement where matching matters, should ask for FIXTURE photo",
        "homeowner_persona": {
            "personality": "detail-oriented",
            "communication_style": "specific",
            "regional_flavor": "Austin",
        },
        "initial_email": {
            "from_name": "Rachel Green",
            "from_email": "rgreen@email.com",
            "subject": "Replace bathroom faucets",
            "body": "Want to replace all three bathroom faucets - they're old and corroded. Would like to keep a similar style if possible. Can you do this?",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "All three bathrooms. Chrome finish, two-handle style. They all match currently. 5521 River Oaks Boulevard. What's your availability?",
                "ai_should": [
                    "Ask for photo of current faucets",
                    "FIXTURE replacement where matching matters = ask for photo",
                    "Explain WHY (helps match style)",
                ],
                "ai_must_not": [
                    "Skip photo request when matching is mentioned",
                    "Generic photo ask",
                ],
            }
        ],
    },
    "elec_photo_scorched_outlet": {
        "business": "bay_electric",
        "urgency": "urgent",
        "category": "electrical",
        "description": "Electrical - visible damage (scorched outlet), should ask for DAMAGE photo",
        "homeowner_persona": {
            "personality": "safety-concerned",
            "communication_style": "worried",
            "regional_flavor": "Phoenix",
        },
        "initial_email": {
            "from_name": "Brad Thompson",
            "from_email": "bthompson@email.com",
            "subject": "URGENT - Outlet looks burned",
            "body": "One of the outlets in my home office has black marks around it and smells like burning plastic. Unplugged everything and flipped the breaker off. Need an electrician ASAP!",
        },
        "conversation_flow": [
            {
                "step": 1,
                "homeowner_reply": "Good question - no. I shut off the whole circuit. 8823 Desert Vista Lane. How soon can you get here?",
                "ai_should": [
                    "Ask for photo of outlet damage",
                    "Visible DAMAGE = photo helpful even when urgent",
                    "Safety issue but still get photo",
                ],
                "ai_must_not": [
                    "Skip photo because of urgency",
                    "Provide safety instructions about breakers",
                ],
            },
            {
                "step": 2,
                "homeowner_reply": "Just sent a close-up photo. Phone is 602-555-7788. Standing by.",
                "ai_should": ["Acknowledge photo", "Move to handoff"],
                "ai_must_not": ["Diagnose from photo", "Give technical assessment"],
            },
        ],
    },
}

# Export in format expected by test_harness.py
BUSINESS_PROFILES = BUSINESSES

# Convert scenarios dict to list format expected by test_harness
ALL_SCENARIOS = []
for scenario_id, scenario_data in SCENARIOS.items():
    scenario = {
        "id": scenario_id,
        "name": scenario_data["description"],
        "business": scenario_data["business"],
        "urgency": scenario_data.get("urgency"),
        "category": scenario_data.get("category"),
        "description": scenario_data["description"],
        "homeowner_persona": scenario_data.get("homeowner_persona", {}),
        "initial_email": {
            "from": f"{scenario_data['initial_email']['from_name']} <{scenario_data['initial_email']['from_email']}>",
            "subject": scenario_data["initial_email"]["subject"],
            "body": scenario_data["initial_email"]["body"],
        },
        "conversation_flow": scenario_data.get("conversation_flow", []),
    }

    # Add expected_behavior for non-leads
    if "expected_behavior" in scenario_data:
        scenario["expected_behavior"] = scenario_data["expected_behavior"]

    ALL_SCENARIOS.append(scenario)
