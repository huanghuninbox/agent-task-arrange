# -*- coding: utf-8 -*-
"""port-waker · 零算力任务哨兵
原理｜纯文件读取任务板 JSON（毫秒级、零模型调用）——挂计划任务每 30 分钟跑也不消耗任何端口算力。
行为｜及时分配（immediate）未认领的任务 → 打印/记录提醒（指定自动端口的提示认领，GUI 端提示人工唤起）；
     计划分配（planned）→ 挂板不催（端口侧计划任务低频来领）。
用法｜python duty_watcher.py [--board data/duty_board.json] [--log watcher_alerts.jsonl]
"""
import os
import sys
import json
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO_PORTS = {'buddy', 'zcode', 'codex', 'workersai', 'glmfree'}  # 可程序唤醒的端口（按自己环境改）
GUI_PORTS = {'trae', 'codearts'}  # 需人工唤起（哨兵只提醒）


def main():
    board = os.path.join(HERE, 'data', 'duty_board.json')
    if '--board' in sys.argv:
        board = sys.argv[sys.argv.index('--board') + 1]
    logfile = os.path.join(HERE, 'watcher_alerts.jsonl')
    if '--log' in sys.argv:
        logfile = sys.argv[sys.argv.index('--log') + 1]
    if not os.path.exists(board):
        raise SystemExit('任务板不存在：' + board)
    b = json.load(open(board, encoding='utf-8'))
    alerts = []
    for t in b.get('tasks', []):
        if t.get('status') != 'published' or t.get('assign_type') == 'planned':
            continue
        port = t.get('port', '')
        if port in AUTO_PORTS:
            alerts.append('⚠️及时任务 ' + t['id'] + ' 指定自动端口[' + port + ']待认领：' + t.get('title', '')[:50])
        elif port in GUI_PORTS:
            alerts.append('🔔及时任务 ' + t['id'] + ' 需人工唤起[' + port + ']：' + t.get('title', '')[:50])
        elif not port:
            alerts.append('⚠️及时自由任务 ' + t['id'] + '（部门[' + str(t.get('dept', '?')) + '）待认领：' + t.get('title', '')[:50])
    now = datetime.datetime.now().isoformat(timespec='seconds')
    if alerts:
        with open(logfile, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': now, 'alerts': alerts}, ensure_ascii=False) + chr(10))
    for a in alerts:
        print(a)
    print('哨兵扫描完成：' + str(len(alerts)) + ' 条提醒（' + now + '）')


if __name__ == '__main__':
    main()
