import functools
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import request, jsonify, current_app


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def create_token(username, secret, expire_hours):
    payload = {
        'sub': username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=expire_hours),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def decode_token(token, secret):
    return jwt.decode(token, secret, algorithms=['HS256'])


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.args.get('token')

        if not token:
            return jsonify({'error': '未登录'}), 401

        try:
            payload = decode_token(token, current_app.config['JWT_SECRET'])
            request.current_user = payload['sub']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的Token'}), 401

        return f(*args, **kwargs)

    return decorated
