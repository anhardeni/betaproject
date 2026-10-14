#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime

try:
    import pymysql
except Exception:
    pymysql = None

STATUS_KEYS = [
    'Threads_running', 'Threads_connected', 'Questions', 'Queries', 'Uptime',
    'Slow_queries', 'Innodb_buffer_pool_reads', 'Innodb_buffer_pool_read_requests',
    'Innodb_rows_inserted', 'Innodb_rows_read', 'Innodb_row_lock_waits',
    'Innodb_row_lock_time', 'Innodb_os_log_written', 'Innodb_log_waits',
    'Created_tmp_disk_tables', 'Created_tmp_tables', 'Table_locks_waited',
    'Table_locks_immediate', 'Handler_write', 'Com_commit', 'Com_insert'
]

VARIABLE_KEYS = [
    'version', 'performance_schema', 'slow_query_log', 'long_query_time',
    'innodb_buffer_pool_size', 'innodb_flush_log_at_trx_commit', 'sync_binlog',
    'innodb_log_file_size', 'innodb_io_capacity', 'innodb_io_capacity_max',
    'userstat', 'autocommit', 'binlog_format'
]


def connect_from_env():
    if pymysql is None:
        raise RuntimeError('pymysql is not installed. Run: pip install pymysql')
    params = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', ''),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', ''),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True,
    }
    if not params['user']:
        raise RuntimeError('DB_USER environment variable is required')
    return pymysql.connect(**params)


def fetch_map(cur, sql, key_col, val_col):
    cur.execute(sql)
    rows = cur.fetchall()
    return {r[key_col]: r[val_col] for r in rows}


def table_exists(cur, schema_name, table_name):
    cur.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM information_schema.tables
        WHERE table_schema=%s AND table_name=%s
        """,
        (schema_name, table_name),
    )
    return cur.fetchone()['cnt'] > 0


def safe_query(cur, sql):
    try:
        cur.execute(sql)
        return cur.fetchall(), None
    except Exception as e:
        return None, str(e)


def bytes_to_mb(v):
    try:
        return round(int(v) / 1024 / 1024, 2)
    except Exception:
        return None


def analyze(status_map, variable_map, findings):
    notes = []

    bp_reads = int(status_map.get('Innodb_buffer_pool_reads', 0) or 0)
    bp_reqs = int(status_map.get('Innodb_buffer_pool_read_requests', 0) or 0)
    if bp_reqs > 0:
        miss_ratio = bp_reads / bp_reqs
        findings['buffer_pool_miss_ratio'] = miss_ratio
        if miss_ratio > 0.01:
            notes.append({
                'severity': 'high',
                'area': 'buffer_pool',
                'message': f'Buffer pool miss ratio terlihat tinggi ({miss_ratio:.4%}). Kandidat: innodb_buffer_pool_size terlalu kecil atau working set melebihi cache.'
            })
        else:
            notes.append({
                'severity': 'ok',
                'area': 'buffer_pool',
                'message': f'Buffer pool miss ratio rendah ({miss_ratio:.4%}). Tekanan read cache tampak sehat.'
            })

    log_waits = int(status_map.get('Innodb_log_waits', 0) or 0)
    if log_waits > 0:
        notes.append({
            'severity': 'high',
            'area': 'redo_log',
            'message': f'Innodb_log_waits = {log_waits}. Ini mengarah ke tekanan redo log atau flush yang menahan transaksi.'
        })

    row_lock_waits = int(status_map.get('Innodb_row_lock_waits', 0) or 0)
    row_lock_time = int(status_map.get('Innodb_row_lock_time', 0) or 0)
    if row_lock_waits > 0:
        notes.append({
            'severity': 'medium',
            'area': 'locking',
            'message': f'Row lock waits terdeteksi ({row_lock_waits}) dengan total wait time {row_lock_time} ms. Perlu audit transaksi panjang atau contention.'
        })

    slow_queries = int(status_map.get('Slow_queries', 0) or 0)
    if variable_map.get('slow_query_log', '').upper() in ('ON', '1'):
        notes.append({
            'severity': 'info',
            'area': 'slow_log',
            'message': f'Slow query log aktif. Counter Slow_queries saat ini = {slow_queries}.'
        })
    else:
        notes.append({
            'severity': 'medium',
            'area': 'slow_log',
            'message': 'Slow query log belum aktif; bukti query lambat belum akan terekam lengkap.'
        })

    trx_commit = str(variable_map.get('innodb_flush_log_at_trx_commit', ''))
    if trx_commit == '1':
        notes.append({
            'severity': 'info',
            'area': 'durability',
            'message': 'innodb_flush_log_at_trx_commit=1; durability kuat tetapi write cost lebih tinggi.'
        })
    elif trx_commit == '2':
        notes.append({
            'severity': 'info',
            'area': 'durability',
            'message': 'innodb_flush_log_at_trx_commit=2; write throughput bisa lebih baik, tetapi durability sedikit lebih longgar.'
        })

    if str(variable_map.get('performance_schema', '')).upper() not in ('ON', '1'):
        notes.append({
            'severity': 'medium',
            'area': 'observability',
            'message': 'performance_schema belum aktif; analisis wait/stage/detail statement akan terbatas.'
        })

    return notes


def main():
    result = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'connection': {},
        'variables': {},
        'status': {},
        'tables': {},
        'performance_schema': {},
        'analysis': [],
        'limitations': []
    }

    conn = connect_from_env()
    result['connection'] = {
        'host': os.getenv('DB_HOST', '127.0.0.1'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'database': os.getenv('DB_NAME', ''),
    }

    with conn.cursor() as cur:
        status_map = fetch_map(cur, 'SHOW GLOBAL STATUS', 'Variable_name', 'Value')
        variable_map = fetch_map(cur, 'SHOW GLOBAL VARIABLES', 'Variable_name', 'Value')

        result['status'] = {k: status_map.get(k) for k in STATUS_KEYS if k in status_map}
        result['variables'] = {k: variable_map.get(k) for k in VARIABLE_KEYS if k in variable_map}
        if 'innodb_buffer_pool_size' in result['variables']:
            result['variables']['innodb_buffer_pool_size_mb'] = bytes_to_mb(result['variables']['innodb_buffer_pool_size'])
        if 'innodb_log_file_size' in result['variables']:
            result['variables']['innodb_log_file_size_mb'] = bytes_to_mb(result['variables']['innodb_log_file_size'])

        if table_exists(cur, 'information_schema', 'USER_STATISTICS'):
            rows, err = safe_query(cur, 'SELECT * FROM information_schema.USER_STATISTICS ORDER BY BUSY_TIME DESC LIMIT 10')
            result['tables']['USER_STATISTICS'] = rows if rows is not None else {'error': err}
        else:
            result['limitations'].append('USER_STATISTICS tidak tersedia atau userstat belum aktif.')

        if table_exists(cur, 'information_schema', 'TABLE_STATISTICS'):
            rows, err = safe_query(cur, 'SELECT * FROM information_schema.TABLE_STATISTICS ORDER BY ROWS_CHANGED DESC LIMIT 10')
            result['tables']['TABLE_STATISTICS'] = rows if rows is not None else {'error': err}
        else:
            result['limitations'].append('TABLE_STATISTICS tidak tersedia atau userstat belum aktif.')

        if table_exists(cur, 'information_schema', 'INDEX_STATISTICS'):
            rows, err = safe_query(cur, 'SELECT * FROM information_schema.INDEX_STATISTICS ORDER BY QUERIES ASC LIMIT 20')
            result['tables']['INDEX_STATISTICS'] = rows if rows is not None else {'error': err}
        else:
            result['limitations'].append('INDEX_STATISTICS tidak tersedia atau userstat belum aktif.')

        if table_exists(cur, 'performance_schema', 'events_statements_summary_by_digest'):
            rows, err = safe_query(cur, """
                SELECT SCHEMA_NAME, DIGEST_TEXT, COUNT_STAR, SUM_TIMER_WAIT, AVG_TIMER_WAIT
                FROM performance_schema.events_statements_summary_by_digest
                ORDER BY SUM_TIMER_WAIT DESC
                LIMIT 10
            """)
            result['performance_schema']['events_statements_summary_by_digest'] = rows if rows is not None else {'error': err}
        else:
            result['limitations'].append('events_statements_summary_by_digest tidak tersedia; performance_schema mungkin belum aktif penuh.')

        if table_exists(cur, 'performance_schema', 'events_stages_history_long'):
            rows, err = safe_query(cur, """
                SELECT THREAD_ID, EVENT_NAME, TIMER_WAIT, WORK_COMPLETED, WORK_ESTIMATED
                FROM performance_schema.events_stages_history_long
                ORDER BY TIMER_WAIT DESC
                LIMIT 20
            """)
            result['performance_schema']['events_stages_history_long'] = rows if rows is not None else {'error': err}
        else:
            result['limitations'].append('events_stages_history_long tidak tersedia atau consumer stages belum aktif.')

        result['analysis'] = analyze(status_map, variable_map, result)

    print(json.dumps(result, indent=2, default=str))

if __name__ == '__main__':
    main()
