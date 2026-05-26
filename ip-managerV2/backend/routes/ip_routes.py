import io
from flask import Blueprint, request, jsonify, current_app, send_file
from auth import login_required
from services.ip_service import (
    get_all_subnets, get_subnet_ips, get_ip_detail,
    occupy_ip, release_ip, update_ip, search_ips, export_excel
)

ip_bp = Blueprint('ip', __name__)


def _db():
    return current_app.config['DB_PATH']


@ip_bp.route('/api/subnets', methods=['GET'])
@login_required
def list_subnets():
    subnets = get_all_subnets(_db())
    return jsonify(subnets)


@ip_bp.route('/api/subnets/<int:subnet_id>/ips', methods=['GET'])
@login_required
def list_ips(subnet_id):
    ips = get_subnet_ips(_db(), subnet_id)
    return jsonify(ips)


@ip_bp.route('/api/ips/<int:ip_id>', methods=['GET'])
@login_required
def ip_detail(ip_id):
    ip = get_ip_detail(_db(), ip_id)
    if not ip:
        return jsonify({'error': 'IP不存在'}), 404
    return jsonify(ip)


@ip_bp.route('/api/ips/<int:ip_id>/occupy', methods=['PUT'])
@login_required
def occupy(ip_id):
    data = request.get_json() or {}
    ok, msg = occupy_ip(_db(), ip_id, data)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'message': msg})


@ip_bp.route('/api/ips/<int:ip_id>/release', methods=['PUT'])
@login_required
def release(ip_id):
    ok, msg = release_ip(_db(), ip_id)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'message': msg})


@ip_bp.route('/api/ips/<int:ip_id>', methods=['PUT'])
@login_required
def edit_ip(ip_id):
    data = request.get_json() or {}
    ok, msg = update_ip(_db(), ip_id, data)
    if not ok:
        return jsonify({'error': msg}), 400
    return jsonify({'message': msg})


@ip_bp.route('/api/search', methods=['GET'])
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    results = search_ips(_db(), q)
    return jsonify(results)


@ip_bp.route('/api/export', methods=['GET'])
@login_required
def export():
    wb = export_excel(_db())
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='IP地址信息汇总_导出.xlsx'
    )


@ip_bp.route('/api/reimport', methods=['POST'])
@login_required
def reimport():
    """手动重新导入 Excel 数据（会覆盖现有数据）"""
    import os
    from services.import_service import import_excel

    config = current_app.config['APP_CONFIG']
    excel_path = config['data']['excel_path']
    db_path = config['data']['db_path']

    if not os.path.exists(excel_path):
        return jsonify({'error': f'Excel文件不存在: {excel_path}'}), 400

    if os.path.exists(db_path):
        os.remove(db_path)

    total = import_excel(excel_path, db_path)
    return jsonify({'message': f'重新导入成功，共 {total} 条IP记录'})
