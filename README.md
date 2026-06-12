# Icomon 智能体脂秤 - Home Assistant 集成

[![Buy Me A Coffee](https://img.shields.io/badge/请我喝杯咖啡-Buy_Me_A_Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://www.buymeacoffee.com/genelee26)

通过 BLE Proxy 连接 Icomon (沃莱) 体脂秤，支持多用户按需测量，15 项体成分指标。

## 功能

- **多用户支持** — 最多 5 个用户，每人独立传感器和历史记录
- **按需测量** — 每个用户有"开始测量"按钮，按下后才连接秤
- **15 项体成分指标** — 体重、BMI、体脂率、水分率、骨骼肌率、骨骼率、蛋白质率、肌肉率、内脏脂肪指数、皮下脂肪率、去脂体重、基础代谢、身材评价、阻抗、测量状态
- **BIA 公式校准** — 基于 ha-miscale2 BIA 公式，经 Icomon App 数据校准，体脂率误差 < 0.2%

## 前提条件

- ESPHome BLE Proxy（需支持 active 扫描和 GATT 连接）
- Icomon 体脂秤（已测试 MY_SCALE，服务 UUID `0000FFB0`）

## 安装

### HACS 安装（推荐）

1. 在 HACS 中添加自定义仓库：`https://github.com/genelee26/icomon_scale`
2. 搜索 "Icomon" 并安装
3. 重启 Home Assistant

### 手动安装

将 `custom_components/icomon_scale` 目录复制到 HA 的 `config/custom_components/` 下，重启 HA。

## 配置

1. 设置 → 设备与服务 → 添加集成 → 搜索 "Icomon"
2. 第 1 步：填写秤的 MAC 地址和用户数量
3. 第 2 步起：为每个用户填写姓名、身高、年龄、性别

## 使用

1. 在 HA 中按下对应用户的 **"开始测量"** 按钮
2. 60 秒内站上秤，等待数字稳定
3. 数据自动写入该用户的传感器

## 协议说明

| 字段 | 字节位置 | 说明 |
|------|---------|------|
| 包头 | byte[0] | 固定 0xAC |
| 体重 | byte[3:5] | 24 位大端整数，`(val - 9175040) / 1000` = kg |
| 阻抗 | byte[17:18] | 大端 16 位，`raw / 5.532` = Ω |

## 赞赏支持

纯业余时间做着玩的开源项目，免费、而且会一直免费。要是它帮你省了心、或者让你会心一笑，
欢迎请我喝杯咖啡 ☕ —— 纯属鼓励，绝不影响任何功能。

[![Buy Me A Coffee](https://img.shields.io/badge/请我喝杯咖啡-Buy_Me_A_Coffee-FFDD00?logo=buymeacoffee&logoColor=black)](https://www.buymeacoffee.com/genelee26)

国内的同道也可以微信赞赏，扫下面这个码就行：

<img src="images/wechat_pay.png" width="280" alt="微信赞赏码">

谢谢每一位同道中人的鼓励 🙏

## License

MIT
