@app.route('/campaigns')
def campaigns():
    try:
        session, engine = _get_db()
        result = engine.execute(text("""
            SELECT id, name, angle, trade, borough, 
                   lead_count, enriched_count, proposals_sent, 
                   replies, interested, created_at
            FROM campaigns 
            ORDER BY created_at DESC
        """))
        campaigns_data = [dict(row) for row in result]
        session.close()
        return render_template('campaigns.html', campaigns=campaigns_data)
    except Exception as e:
        logger.error(f'Error fetching campaigns: {e}')
        return render_template('campaigns.html', campaigns=[], error=str(e))

@app.route('/campaigns/create', methods=['POST'])
def create_campaign():
    try:
        data = request.get_json()
        session, engine = _get_db()
        engine.execute(text("""
            INSERT INTO campaigns (name, angle, trade, borough)
            VALUES (:name, :angle, :trade, :borough)
        """), {
            'name': data['name'],
            'angle': data['angle'],
            'trade': data['trade'],
            'borough': data['borough']
        })
        session.close()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error creating campaign: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500