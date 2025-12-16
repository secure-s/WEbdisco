
from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from prometheus_client import Counter, generate_latest, REGISTRY, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('app_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'http_status'])

DB_HOST = os.getenv('DB_HOST', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'labdb')
DB_USER = os.getenv('DB_USER', 'labuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'labpass')


def get_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

@app.route('/')
def index():
    return 'DevOps Lab Demo App: Flask + PostgreSQL + Prometheus', 200

@app.route('/items', methods=['GET', 'POST'])
def items():
    status = 200
    try:
        conn = get_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('CREATE TABLE IF NOT EXISTS items (id SERIAL PRIMARY KEY, name TEXT NOT NULL);')
        conn.commit()
        if request.method == 'POST':
            data = request.get_json(force=True)
            cur.execute('INSERT INTO items (name) VALUES (%s) RETURNING id, name;', (data.get('name', 'unnamed'),))
            row = cur.fetchone()
            conn.commit()
            result = {'created': row}
        else:
            cur.execute('SELECT id, name FROM items ORDER BY id DESC;')
            result = {'items': cur.fetchall()}
        cur.close()
        conn.close()
        return jsonify(result), status
    except Exception as e:
        status = 500
        return jsonify({'error': str(e)}), status
    finally:
        REQUEST_COUNT.labels(method=request.method, endpoint='/items', http_status=str(status)).inc()

@app.route('/healthz')
def healthz():
    return 'ok', 200

@app.route('/metrics')
def metrics():
    # Expose default and custom metrics
    return generate_latest(REGISTRY), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
