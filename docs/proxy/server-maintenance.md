# 服务端备份、升级与恢复

命令在服务端的完整私有工作区执行。真实路径、端口和备份标识只保存在私有手册与受保护材料中。服务状态以实际检查为准。

## 备份

```bash
sudo python3 scripts/proxy/backup-server.py
```

脚本通过 SQLite backup API 创建一致性副本，保存面板、核心、配置、systemd 与本方案主机配置，进行隔离解包、数据库完整性与摘要核对。备份不停止服务；期间避免同时在面板修改配置。目录 0700、归档 0600，包含秘密，不加入 Git 或发送到聊天。

隔离恢复校验不等于覆盖生产回退演练。防火墙快照仅用于审阅和针对性回退，不能直接恢复整机规则；云规则需另查。

## 升级与日志

沿用已核验的面板 v3.11.0、Xray 26.10.31 兼容基线，属于固定版本，本文不宣称它们是最新版本。升级前另行核对目标版本及兼容性，先备份并保持 SSH 恢复通道。通过面板管理核心，不同时升级面板、修改设备凭据或路由策略。

升级会中断代理连接，执行前应明确影响与回退。完成后运行：

```bash
sudo python3 scripts/proxy/audit-server.py
```

再从 Happ 核对连接、出口、代表目标、错误凭据拒绝与非公网目标阻断。

`configure-server-logging.py` 用于既定版本的日志轮转和 journal 速率限制，检查备份后修改配置并重启 x-ui；不是只读检查，不在日常诊断中自动执行。默认不长期保留访问日志，备份与日志均需受限权限。

## 回退

1. 选定已校验的私有备份，核对 verification.json，保留当前配置和核心。
2. 在新的 Root 专属临时目录安全解包，核对 checksums.json、SQLite integrity_check 和恢复后二进制。
3. 仅核心故障时，停止 x-ui，保留当前核心并恢复已验证旧核心，保留现有有效数据库。
4. 需要完整恢复时，停止 x-ui，分别保留当前安装和数据目录，再按备份结构恢复；不合并新旧 SQLite，不遗漏 WAL/SHM 一致性处理。
5. 仅恢复本方案相关的单元、环境文件、日志轮转和模块加载文件，不覆盖整个系统目录。必要时执行 daemon-reload。
6. 启动后核对服务、管理回环、订阅关闭、代理监听与语法，再用 Happ 验证。失败保留现场和恢复材料。

## 单入站 BBR 与重启

`prepare-inbound-bbr.py` 和 `persist-inbound-bbr.py` 用于模块准备和持久化，保留为既有部署维护工具。BBR 限定代理入站，不改变整机 TCP/qdisc；操作前备份，核对脚本前置条件。若需回退，在面板同一入站将 TCP Congestion 恢复原值并应用，再检查新连接。若不再使用 BBR，依据持久化脚本保存的 state.json 恢复本方案模块加载文件和单元顺序文件，执行 daemon-reload。不强卸载仍被 socket 使用的模块。

整机重启需另行安排可恢复维护窗口，不作为一般排障手段。`verify-after-reboot.py` 读取既有受保护基线，核对真实启动变化、自启动、监听、版本和 BBR；没有基线时不能将检查当作重启验收。重启后继续用 Happ 核对连接。

## 可选只读采样

```bash
bash scripts/proxy/proxyctl.sh sample 30 "$RESULT_DIR"
bash scripts/proxy/proxyctl.sh measure server-direct "$PROBE_DIR"
bash scripts/proxy/proxyctl.sh report "$PROBE_DIR/metrics.csv"
```

结果目录必须是新的私有绝对路径。资源采样限制为 4—600 秒；目标测量有超时与流量限制，只表示服务器直连请求，不证明客户端出口、代理吞吐或全部业务正常。日志和原始结果留在私有目录。
