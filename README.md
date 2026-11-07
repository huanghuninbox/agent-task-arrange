# port-waker

> AI 端口（agent/CLI/GUI 工具）的**统一唤醒与任务执行层**：没任务零消耗，有任务才唤醒对应端口并把指令送进去，干完活结果自动落档。
>
> English: A unified wake-up & task-execution layer for AI agents. Zero-cost sentinel watches a task board; only when a task exists does it wake the target port (CLI headless or GUI automation), deliver the instruction, and enforce result archiving.

## 核心：三层分离（省算力架构）

```
哨兵层（每 30 分钟计划任务）   本地 python 读任务板 JSON —— 纯文件读取，毫秒级，零模型调用
        ↓ 发现任务才触发
唤醒层                        系统级操作：启动进程/激活窗口/剪贴板粘贴指令 —— 零模型调用
        ↓ 端口收到指令开始处理
干活层                        端口自己消耗自己的积分（此刻才花钱）
```

**没有任务时端口永远不会被启动**——调度全程零算力，这是整套设计的目的。

## 各端口怎么唤醒（实测结论，2026-11）

| 端口类型 | 唤醒方式 | 要点与坑 |
|---|---|---|
| **CLI headless 型**（CodeBuddy/Codex/智谱等） | `subprocess` 直接调 CLI：`codebuddy --model <档> -p "指令"` | 模型档位=积分开关（免费档省积分、付费档吃池）；选档按任务需要 |
| **GUI IDE 型**（Trae/CodeArts Agent 等） | `wake_gui_port.py`：关闭重开=初始状态 → pygetwindow 定位窗口 → **坐标点击聊天输入框** → 剪贴板粘贴指令 → 回车 | ①关闭重开比「激活已有窗口」可靠（多实例/最小化/遮挡全是坑）②**粘贴前必须验证焦点**（否则贴进用户正在打字的窗口）③快捷键（Ctrl+L 等）不可靠，用窗口相对坐标 ④窗口标题可能不含产品名（Trae 的标题是「Agent」），按实测标题匹配 |
| **纯 GUI 无自动化通道型** | 哨兵只提醒（系统通知），人工唤起 | 逆向协议不采用（条款+封号风险） |

### GUI 唤醒五连教训（每条都是实测踩出来的）

1. `SetForegroundWindow` 会被 Windows 前台锁定策略拒绝——**关闭重开**比「激活已有窗口」省掉一整类问题
2. 粘贴前不验证焦点 = 内容可能贴进用户正在打字的窗口（真实事故）
3. Electron 应用的弹窗（会员促销等）会在粘贴瞬间抢焦点——**二次点击输入框** + 粘贴后验证
4. 最小化窗口的 `GetWindowRect` 返回幽灵坐标（-32000），点击会触发 pyautogui FailSafe——`pygetwindow.restore()` 先行
5. 窗口标题按实测写（Trae 的标题是「Agent」不是「TRAE CN」）

## 快速开始

```bash
# 1. 任务板（JSON，示例见 data/duty_board.example.json）
#    每单：id/dept/assign_type(immediate|planned)/port/status/report/review

# 2. 发布任务（CLI）
python check_duty.py --publish <部门> <标题> [--port <端口名>] [--planned]
#    缺省=及时分配+自由任务；--port 指定端口专属；--planned=计划分配（端口侧计划任务低频来领）

# 3. 端口认领执行
python check_duty.py --claim <单号> --by <端口名>

# 4. GUI 端唤醒（示例：唤醒 trae 查天气，结果自动落档 results/）
python wake_gui_port.py trae "帮我查一下上海明天的天气，简短总结"

# 5. 零算力哨兵（挂计划任务，每 30 分钟）
python duty_watcher.py    # 读任务板：及时单提醒认领/唤起；计划单挂板不催
```

## 结果落档

GUI 端的每条指令自动附加落档要求：

```
完成后把结果写入 results/<日期>_<任务>.md（目录不存在则创建），写完只回复：已完成
```

端口是 IDE agent 时（有文件写入能力）会自己落档——**「结果保存到哪里」由指令模板强制规定，不靠端口自觉**。

## 目录结构

```
wake_gui_port.py     # GUI 端标准唤醒器（v3 固定流程：关闭重开+坐标点击+落档模板）
check_duty.py        # 任务板 CLI（发布/认领/汇报/审核/上浮）
duty_watcher.py      # 零算力哨兵（扫描及时任务→提醒；计划任务→挂板）
data/duty_board.example.json   # 任务板示例（脱敏）
```

## License

[MIT](LICENSE)
