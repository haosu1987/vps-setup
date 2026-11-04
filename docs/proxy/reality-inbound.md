# REALITY 入站与设备节点

配置由 3X-UI 面板管理。管理面只监听回环，经 SSH 隧道访问，不直接覆盖生产 JSON 或数据库。

## 入站与独立凭据

沿用 VLESS + TCP/RAW + REALITY + Vision 基线：VLESS decryption 为 none，客户端 Flow 为 `xtls-rprx-vision`，不额外叠加其他传输。代理监听端口以私有手册为准。

REALITY 目标与允许的 SNI 对齐部署参数；VPS 连接地址与 SNI 是不同字段。密钥及 short ID 由面板生成，公钥供客户端使用，私钥只留服务端。Mac 和 iPhone 分别创建独立客户端，便于单独撤销。

在既有 v3.11.0 界面中，入站安全页的 `SNI` 对应 `serverNames`；输入后确认成为标签再保存。客户端管理在独立页面，选择关联入站后在凭据页核对 UUID 和 Flow。若 Flow 不显示，先确认关联入站已保存为 VLESS + TCP/RAW + REALITY，再刷新。

## Happ 导入

通过面板导出对应设备的节点链接或二维码并导入 Happ，核对服务器地址、端口、UUID、Vision、REALITY 公钥、short ID 与 SNI。节点链接和二维码包含秘密，不发到聊天或在线转换站。

分流与 DNS 在 Happ 中管理；导入节点不等于完成国内直连配置。调整后用实际目标核对连接、出口和国内访问。本仓库不生成 Happ 策略，不将旧客户端测试作为 Happ 的验收。

## 服务端出口保护

面板 Xray 配置的 RoutingStrategy 对应 `routing.domainStrategy`，保持 `IPOnDemand`；与 FreedomStrategy 分开。保留非公网目标阻断，覆盖私网、回环、链路本地与元数据地址，也覆盖域名解析后指向这些地址的请求。

变更后运行 `audit-server.py` 检查配置和语法，再按授权范围核对真实连接、错误凭据拒绝与出口保护。结构审计不代替实际拒绝测试。
