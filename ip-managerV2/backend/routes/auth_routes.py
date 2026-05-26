from flask import Blueprint, request, jsonify, current_app
from auth import verify_password, create_token, login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': '请提供用户名和密码'}), 400

    username = data.get('username', '')
    password = data.get('password', '')

    config = current_app.config['APP_CONFIG']
    if username != config['auth']['username']:
        return jsonify({'error': '用户名或密码错误'}), 401

    if not verify_password(password, config['auth']['password']):
        return jsonify({'error': '用户名或密码错误'}), 401

    token = create_token(
        username,
        config['auth']['jwt_secret'],
        config['auth']['token_expire_hours']
    )
    return jsonify({'token': token, 'username': username})


@auth_bp.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify({'username': request.current_user})
