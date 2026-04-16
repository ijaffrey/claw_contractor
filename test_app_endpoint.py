from portal.app import app
import json

def test_leads_endpoint():
    with app.test_client() as client:
        response = client.get('/api/leads')
        print('Status:', response.status_code)
        data = response.get_json()
        print('Lead count:', data['count'] if data else 'No data')
        if data and data.get('data'):
            sample_lead = data['data'][0]
            print('Sample lead fields:', list(sample_lead.keys()))
            print('Sample lead:', json.dumps(sample_lead, indent=2))
        return data

if __name__ == '__main__':
    test_leads_endpoint()
