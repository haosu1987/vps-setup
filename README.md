# VPS 代理服务端

本仓库维护 3X-UI / Xray 服务端，使用 VLESS + REALITY + Vision。Mac 和 iPhone 使用 Happ，分别导入面板创建的独立客户端节点；分流与 DNS 由 Happ 管理。

自写 Mac 客户端、TUN、DNS 控制、launchd 托管及配套验收脚本已取消并移除，不再部署或测试。

## 服务端操作

- [安装面板](docs/proxy/server-install.md)
- [配置入站和设备凭据](docs/proxy/reality-inbound.md)
- [备份、日志与维护](docs/proxy/server-maintenance.md)
- [私有工作区生成](docs/proxy/maintainer.md)

面板只监听回环，经 SSH 隧道管理；不开放公网面板或订阅。保留现有生产服务，不因仓库清理而升级或重启。

公开源码保留占位符，真实参数只存受保护私有文件。先渲染新的私有工作区，再按生成的 OPERATIONS.md 操作；不要直接执行 `.in` 模板。

## 目录

| 目录 | 用途 |
| --- | --- |
| `templates/` | 带占位符的服务端源码与私有操作手册 |
| `config/` | 无真实部署值的参数示例 |
| `tools/` | 私有渲染、渲染验证与隐私检查 |
| [docs/proxy/](docs/proxy/README.md) | 当前服务端操作与故障诊断 |
| `.private/` | 被 Git 忽略的参数、渲染产物及恢复材料 |

本地整理只运行渲染、语法、链接和隐私检查；不运行网络验收或自动部署。已有生产服务和 Happ 配置独立于仓库变更。
