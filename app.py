from flask import Flask, request, jsonify, session, render_template
import os
import logging
from datetime import timedelta, datetime
from services.auth_service import AuthService
from services.query_service import QueryService
from models.database import SnowflakeConnection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log', mode='a')
    ]
)

app = Flask(__name__)
app.config.from_object('config.Config')

# Configure built-in Flask sessions (simpler and more reliable)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

# Initialize services
auth_service = AuthService()
query_service = QueryService()

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    return render_template('dashboard.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    
    user = auth_service.authenticate(username, password)
    if user:
        regions = auth_service.get_user_regions(user.user_id)
        
        session['user_id'] = user.user_id
        session['username'] = user.username
        session['full_name'] = user.full_name
        session['regions'] = [region.to_dict() for region in regions]
        session.permanent = True
        
        return jsonify({
            'success': True,
            'user': {
                'username': user.username,
                'full_name': user.full_name,
                'regions': session['regions']
            }
        })
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username'],
        'full_name': session['full_name'],
        'regions': session['regions']
    })

@app.route('/api/query/ask', methods=['POST'])
def ask_question():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    question = data.get('question')
    
    if not question or not question.strip():
        return jsonify({'error': 'Question is required'}), 400
    
    try:
        # Set user context in Snowflake session
        user_context = {
            'current_user_id': session['user_id'],
            'accessible_regions': session['regions'],
            'is_admin': False
        }
        
        result = query_service.process_question(question.strip(), user_context)
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Query processing error for user {session['user_id']}: {str(e)}")
        return jsonify({'error': 'An error occurred while processing your question. Please try again.'}), 500

@app.route('/api/query/feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    request_id = data.get('request_id')
    positive = data.get('positive')
    feedback_message = data.get('feedback_message', '')
    
    if not request_id or positive is None:
        return jsonify({'error': 'Request ID and positive feedback flag are required'}), 400
    
    try:
        result = query_service.submit_feedback(request_id, positive, feedback_message)
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Feedback submission error: {str(e)}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        db = SnowflakeConnection()
        success, message = db.test_connection()
        
        if success:
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': message,
                'timestamp': datetime.utcnow().isoformat()
            }), 503
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host=app.config['HOST'], port=app.config['PORT'])
