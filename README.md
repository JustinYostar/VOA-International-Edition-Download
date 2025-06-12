# VOA International Edition 批量下载器

> 版本：**1.1**
> 更新日期：2025-06-12
> 作者：Justin Yo

## 🧩 项目简介

该程序是一款专为 [VOA International Edition](https://www.voanews.com/z/7104) 节目设计的**可视化批量下载器**，通过自动翻页抓取节目详情页、提取音频链接（优先高质量 `_hq.mp3`），实现便捷、可控的日期范围批量下载。


## ✨ 功能特点

* 📅 **按日期范围遍历**：自定义开始和结束日期，精确筛选节目。
* 🔗 **三级下载链接提取机制**：

  1. `<a download>` 标签中的链接（优先 `_hq.mp3`）
  2. `<audio src="...">` 标签中的链接
  3. HTML 中的 `.mp3` 正则直链
* 🧠 **智能命名**：文件保存为 `日期_节目标题_质量.mp3` 格式。
* 📂 **自动建目录**：按 `年/月` 结构组织文件夹。
* 🧵 **多线程下载**：支持并发池，默认 4 个线程同时下载。
* 🛑 **可中止下载**：运行中点击“停止”按钮立即终止所有下载。
* 📋 **日志可视化**：GUI 实时显示抓取和下载进度。
* 🧪 **测试遍历**：预览抓取到的节目链接，便于校验范围。



## 📷 界面预览

> GUI 界面包括：

* 参数配置区（日期、保存目录）
* 操作按钮（测试遍历、开始下载、停止）
* 下载进度条
* 日志输出框



## 🛠️ 环境依赖

请确保已安装以下 Python 库：

```bash
pip install requests beautifulsoup4 python-dateutil orjson
```

* **Tkinter**：Python GUI 标准库，Windows/macOS 默认内置。
* **Playwright（可选）**：如需处理 JS 渲染页面：

```bash
pip install playwright
playwright install
```



## 🚀 启动方式

在命令行中运行主程序：

```bash
python download.py
```



## 📁 下载结果示例

目录结构如下所示：

```
downloads/
├── 2025/
│   ├── 03/
│   │   ├── 2025-03-13_Biden’s Middle East Visit_hq.mp3
│   │   └── 2025-03-14_World News Brief_normal.mp3
```



## 📌 常见问题

* **无法运行 GUI？**

  * 请检查 tkinter 是否正确安装或使用支持 GUI 的 Python 版本。
* **找不到 \_hq 音频？**

  * 程序自动回退至普通质量 `.mp3` 链接。



## 📄 授权许可

本项目为个人学习与非商业使用开发，遵循 MIT 协议。



