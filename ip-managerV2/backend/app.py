import os
import sys
import yaml
from flask import Flask, send_from_directory
from flask_cors import CORS
from models import db_exists
from services.import_service import import_excel
from routes.auth_routes import auth_bp
from routes.ip_routes import ip_bp


def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def create_app():
    config = load_config()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.normpath(os.path.join(base_dir, config['data']['db_path']))
    excel_path = os.path.normpath(os.path.join(base_dir, config['data']['excel_path']))

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if not db_exists(db_path):
        if os.path.exists(excel_path):
            print(f"首次启动，正在从 Excel 导入数据...")
            total = import_excel(excel_path, db_path)
            print(f"导入完成，共 {total} 条IP记录")
        else:
            print(f"警告: Excel文件不存在 ({excel_path})，将创建空数据库")
            from models import init_db
            init_db(db_path)
    else:
        print(f"数据库已存在，跳过 Excel 导入")

    static_folder = os.path.normpath(os.path.join(base_dir, '..', 'frontend', 'dist'))

    app = Flask(__name__, static_folder=static_folder, static_url_path='')
    CORS(app)

    app.config['APP_CONFIG'] = config
    app.config['JWT_SECRET'] = config['auth']['jwt_secret']
    app.config['DB_PATH'] = db_path

    app.register_blueprint(auth_bp)
    app.register_blueprint(ip_bp)

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404)
    def fallback(e):
        index_path = os.path.join(app.static_folder, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(app.static_folder, 'index.html')
        return {'error': 'Not Found'}, 404

    return app


if __name__ == '__main__':
    app = create_app()
    config = app.config['APP_CONFIG']
    host = config['server']['host']
    port = config['server']['port']
    print(f"IP管理系统启动: http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
