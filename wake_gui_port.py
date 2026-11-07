# -*- coding: utf-8 -*-
"""port-waker · GUI 端标准唤醒器 v3（关闭重开=初始状态+固定步骤）
用法｜python wake_gui_port.py <端口名> <指令文本> [落档目录]
端口配置｜PORTS 字典（exe/proc/title_kw/input_rel）——按自己的客户端路径与界面实测坐标修改
验证过的组合｜trae（Trae CN：标题含 Agent，输入框相对位置 0.59,0.90）
链路｜①taskkill 关闭（初始状态）②启动 ③pygetwindow 定位 ④点击输入框（相对坐标，二次点击防弹窗）
     ⑤粘贴指令（自动附落档要求）⑥回车 ⑦轮询落档文件（2 轮重试）
红线｜只做系统/GUI 操作零模型调用；触发时占用鼠标键盘数秒。
"""
import os
import sys
import time
import datetime
import subprocess

PORTS = {
    'trae': {'exe': r'C:\Program Files\Trae CN\Trae CN.exe',
             'proc': 'Trae CN.exe', 'boot_wait': 25,
             'title_kw': 'Agent', 'input_rel': (0.59, 0.90)},
    # 按自己的客户端路径修改；更多端口照此添加
}
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wake.log')


def log(s):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(datetime.datetime.now().isoformat(timespec='seconds') + ' ' + s + '\n')


def find_win(title_kw):
    import pygetwindow as gw
    for w in gw.getAllWindows():
        if w.title and title_kw.lower() in w.title.lower() and w.width > 300 and w.height > 200:
            return w
    return None


def main():
    port, instruction = sys.argv[1], sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else RESULTS_DIR
    cfg = PORTS.get(port)
    if not cfg or not cfg['exe']:
        raise SystemExit('端口 ' + port + ' 未配置 GUI 通道（PORTS 字典按自己环境修改）')
    log('唤醒开始[' + port + ']（v3）：' + instruction[:50])

    # ① 关闭（初始状态）
    subprocess.run(['taskkill', '/IM', cfg['proc'], '/F'], capture_output=True)
    time.sleep(3)

    # ② 重新打开
    subprocess.Popen([cfg['exe']], shell=False)
    time.sleep(cfg['boot_wait'])

    # ③ 定位窗口
    win = None
    for attempt in range(5):
        win = find_win(cfg['title_kw'])
        if win:
            break
        log('窗口等待重试 ' + str(attempt + 1))
        time.sleep(6)
    if not win:
        log('❌ 窗口未找到——任务保持挂起')
        raise SystemExit('窗口未找到')
    log('窗口就位：(' + str(win.left) + ',' + str(win.top) + ' ' + str(win.width) + 'x' + str(win.height) + ')')

    # ④ 固定步骤：点击输入框 → 粘贴指令（含落档路径）→ 回车
    import pyautogui
    import pyperclip
    import re as _re
    rx, ry = cfg['input_rel']
    ix, iy = win.left + int(win.width * rx), win.top + int(win.height * ry)
    safe_name = _re.sub(r'[^\w\u4e00-\u9fff-]', '_', instruction[:16])
    out_path = os.path.join(out_dir, datetime.date.today().isoformat() + '_' + safe_name + '.md')
    full = (instruction + chr(10) + '完成后把结果写入 ' + out_path.replace(chr(92), '/')
            + '（目录不存在则创建），写完只回复：已完成')
    os.makedirs(out_dir, exist_ok=True)
    for attempt in range(2):
        pyautogui.click(ix, iy)
        time.sleep(1)
        pyautogui.click(ix, iy)
        time.sleep(0.8)
        pyperclip.copy(full)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(1.5)
        pyautogui.press('enter')
        log('第 ' + str(attempt + 1) + ' 次发送（落档：' + out_path[-40:] + '）')

        # ⑤ 轮询落档（2 轮重试）
        sent = False
        for _ in range(6):
            time.sleep(5)
            if os.path.exists(out_path):
                sent = True
                break
        if sent:
            log('✅ 结果已落档：' + out_path)
            print('✅ ' + port + ' 任务完成并落档：' + out_path)
            return
        log('第 ' + str(attempt + 1) + ' 次发送后 30 秒未见落档' + ('，重试' if attempt == 0 else '，放弃（任务保持挂起）'))
    print('⚠️ 两轮未落档，检查 ' + port + ' 界面')


if __name__ == '__main__':
    main()
