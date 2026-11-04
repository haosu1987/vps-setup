# 服务端维护者指南

真实部署参数保存在 `.private/deployment.json`，权限必须为 0600，私有目录为 0700。新参数格式见 [deployment.example.json](../../config/deployment.example.json)，只要求服务端与管理字段。旧客户端字段可省略；已有完整私有配置继续兼容，旧字段仍经输入校验，不影响生成的服务端代码。无需改写现有私有资料。

## 准备私有部署参数

公开模板不包含真实部署值。使用已有受保护参数渲染全新的私有目录：

```bash
python3 tools/render-deployment.py --profile .private/deployment.json --output .private/server-workspace
```

渲染不激活服务、不改变 DNS 或路由、不下载依赖。仅显式 `--fetch-vendor` 下载并校验固定安装器；已有生产服务不得重复安装。

```bash
python3 tools/test-render-deployment.py
python3 tools/check-public-tree.py --profile .private/deployment.json --worktree
```

修改模板后同时验证合成参数与已有私有参数。发布前检查暂存树与将发布历史，不提交生成物、配置、备份或日志。服务端升级、覆盖和恢复前保留私有备份。

## 目录与运行环境

`templates/scripts/proxy/` 是可维护服务端源码，`templates/deploy/proxy/` 仅存配置说明模板，`tools/` 是本地渲染和隐私检查工具。`.private/` 保存真实参数及渲染产物；忽略的 `scripts/`、`deploy/` 不是公开源码。

本地使用已有 Python 3 和 Bash，不需要 Node 或新依赖。Linux 端按脚本使用现有 Python 3、systemd、curl、SQLite、归档及系统工具；缺工具时先核对环境，不自动安装。完整工作区中的 `toolset.sha256` 固定校验控制器、测量、报告和目标清单，分发时保持同次生成。

当前操作文档集中在本目录，旧客户端文档、测量和规划材料已删除。
