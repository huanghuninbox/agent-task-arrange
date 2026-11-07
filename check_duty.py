# -*- coding: utf-8 -*-
"""模块索引｜03_scripts/check_duty.py｜任务流转 CLI v2（少爷 2026-11-07 两维度模型）
验证方式｜py -3 03_scripts/check_duty.py
两维度模型（少爷口谕）｜端口=能力维度（队长/队员/临时工，能力大调配能力小，见 roster.json）；
  部门=管理维度（领域档案与记忆）。任务一律分配给【部门】；端口确认是哪个部门的任务后，
  自行代入该部门的工作（读其 现状/协同/台账）执行。端口不锁死角色：任何端口都可站 CEO 视点
  或各部门视点。codex 每 6 小时的 CEO 判断由少爷亲自驱动（四轮决断），本 CLI 不自动调用 codex。职责边界（少爷 2026-11-07）：zcode/管理端不代其他端口写入计划任务——「应该做什么」一律录成本台账任务单（--port 指定端口，缺省自由任务）；各端口读取台账后自行设定自己的定时任务，并按 GOV-20261106-03 在管理部登记簿登记。分配类型（少爷 2026-11-07）：--planned=计划分配（不紧急，端口侧计划任务低频来领，如 trae/codearts）；缺省=及时分配（立即派发）。派工原则：优先使用能连上的免费额度。省算力机制：duty_watcher 零算力扫描任务板（纯文件读取），有任务才唤醒对应端口——不设端口内高频轮询。分配类型（少爷 2026-11-07）：--planned=计划分配（不紧急，端口侧计划任务低频来领，如 trae/codearts）；缺省=及时分配（立即派发）。派工原则：优先使用能连上的免费额度。省算力机制：duty_watcher 零算力扫描任务板（纯文件读取），有任务才唤醒对应端口——不设端口内高频轮询。分配类型（少爷 2026-11-07）：--planned=计划分配（不紧急，端口侧计划任务低频来领，如 trae/codearts）；缺省=及时分配（立即派发）。派工原则：优先使用能连上的免费额度。省算力机制：duty_watcher 零算力扫描任务板（纯文件读取），有任务才唤醒对应端口——不设端口内高频轮询。分配类型（少爷 2026-11-07）：--planned=计划分配（不紧急，端口侧计划任务低频来领，如 trae/codearts）；缺省=及时分配（立即派发）。派工原则：优先使用能连上的免费额度。省算力机制：duty_watcher 零算力扫描任务板（纯文件读取），有任务才唤醒对应端口——不设端口内高频轮询。
用法｜
  --publish <部门> <标题>        发布任务单（CEO 视点动作：少爷四轮决断或 CEO 会话使用）
  --agent <端口名>               列出各部门待办（端口视角：按部门分组展示）
  --claim <单号> --by <端口名>   端口认领：确认部门后代入执行（写 executed_by）
  --report <单号> <汇报文本>     执行汇报（reported；含「待少爷/判断/请示」自动转 need_review）
  --review <单号> <意见>         CEO 视点审核（通过→closed，驳回→published）
  --escalate <单号>              判断类上浮 need_review（进少爷待审）
数据｜09_data/ledger/duty_board.json（事实源）+ invocations.jsonl（全部动作流水）
"""
import os, sys, json, datetime

DATA = os.environ.get('OPSHUB_DATA') or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '09_data')
BOARD = os.path.join(DATA, 'ledger', 'duty_board.json')
INV = os.path.join(DATA, 'ledger', 'invocations.jsonl')
DEPTS = ['dept_a', 'dept_b', 'dept_c']  # 按自己的组织结构修改（示例：三个部门）

def now():
    return datetime.datetime.now().isoformat(timespec='seconds')

def log_inv(actor, action, tid, detail=''):
    os.makedirs(os.path.dirname(INV), exist_ok=True)
    with open(INV, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'ts': now(), 'actor': actor, 'action': action,
                            'task': tid, 'detail': detail[:120]}, ensure_ascii=False) + '\n')

def load():
    return json.load(open(BOARD, encoding='utf-8'))

def save(b):
    b['updated_at'] = now()
    json.dump(b, open(BOARD, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

def argval(flag):
    return sys.argv[sys.argv.index(flag) + 1] if flag in sys.argv else None

def main():
    b = load()
    publish_dept, publish_title = argval('--publish'), None
    if publish_dept:
        publish_title = ' '.join(sys.argv[sys.argv.index('--publish') + 2:])
    agent, by, claim = argval('--agent'), argval('--by'), argval('--claim')
    report, review, escalate = argval('--report'), argval('--review'), argval('--escalate')

    if publish_dept:  # CEO 视点发布：任务分配给部门；--port 指定端口，缺省=自由任务
        port = argval('--port') or ''
        assign_type = 'planned' if '--planned' in sys.argv else 'immediate'
        tid = f"D-{datetime.date.today().strftime('%Y%m%d')}-{len([t for t in b['tasks'] if t['id'].startswith('D-' + datetime.date.today().strftime('%Y%m%d'))]) + 1:02d}"
        b['tasks'].append({'id': tid, 'round': b.get('round', ''), 'dept': publish_dept,
                           'title': publish_title[:120], 'assignee': publish_dept, 'executed_by': '',
                           'port': port, 'kind': '指定端口' if port else '自由任务',
                           'assign_type': assign_type,
                           'status': 'published', 'report': '', 'review': '',
                           'created': now(), 'closed': ''})
        save(b); log_inv('CEO视点', 'publish', tid, f'{publish_dept}｜{("指定" + port) if port else "自由"}｜{publish_title[:50]}')
        return print(f'{tid} 已发布 → 部门[{publish_dept}]｜{("指定端口[" + port + "]") if port else "自由任务"}｜{publish_title[:50]}')

    if claim:  # 端口认领：确认部门后代入
        who = by or agent or '?'
        for t in b['tasks']:
            if t['id'] == claim:
                if t['status'] not in ('published',):
                    return print(f"{claim} 状态为 {t['status']}，不可认领")
                if t.get('port') and t['port'] != who:
                    return print(f"{claim} 已指定端口 [{t['port']}]，{who} 不可认领")
                t['status'] = 'claimed'
                t['executed_by'] = who
                t['claimed_at'] = now()
                save(b); log_inv(who, 'claim', claim, f"代入部门[{t['dept']}]")
                print(f"{claim} 已认领｜部门[{t['dept']}]｜执行端口[{who}]")
                print(f"代入动作：读 {t['dept']} 的 现状.md / 协同.md / 00_台账 后再动手")
                print(f'汇报命令：py -3 03_scripts/check_duty.py --report {claim} "结果文本"')
                return
        return print(f'{claim} 不存在')

    if report:
        text = ' '.join(sys.argv[sys.argv.index('--report') + 2:])
        for t in b['tasks']:
            if t['id'] == report:
                t['report'] = text[:600]
                t['status'] = 'need_review' if any(k in text for k in ('待少爷', '判断', '请示')) else 'reported'
                t['reported_at'] = now()
                save(b); log_inv(t.get('executed_by') or '?', 'report', report, t['status'])
                return print(f'{report} → {t["status"]}（汇报已写回）')
        return print(f'{report} 不存在')

    if review:  # CEO 视点审核
        text = ' '.join(sys.argv[sys.argv.index('--review') + 2:])
        for t in b['tasks']:
            if t['id'] == review:
                ok = any(k in text for k in ('通过', 'OK', 'ok'))
                t['review'] = text[:400]
                t['status'] = 'closed' if ok else 'published'
                t['closed'] = now() if ok else ''
                save(b); log_inv('CEO视点', 'review', review, t['status'])
                return print(f'{review} → {t["status"]}（审核意见已写回）')
        return print(f'{review} 不存在')

    if escalate:
        for t in b['tasks']:
            if t['id'] == escalate:
                t['status'] = 'need_review'
                save(b); log_inv(t.get('executed_by') or '?', 'escalate', escalate, '上浮少爷待审')
                return print(f'{escalate} → need_review（已上浮少爷待审）')
        return print(f'{escalate} 不存在')

    # 查看模式
    if agent:  # 端口视角：按部门分组
        for dept in DEPTS:
            mine = [t for t in b['tasks'] if t.get('dept') == dept and t['status'] != 'closed']
            if mine:
                print(f'[{dept}]')
                for t in mine:
                    tag = f"（{t['executed_by']} 执行中）" if t['status'] == 'claimed' else ''
                    print(f"  {t['id']} [{t['status']}]{tag} {t['title'][:70]}")
        return
    for t in b['tasks']:  # 全景
        print(f"{t['id']} [{t['status']}] 部门[{t.get('dept', '?')}] 执行[{t.get('executed_by') or '—'}]｜{t['title'][:60]}")

if __name__ == '__main__':
    main()
