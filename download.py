# -*- coding: utf-8 -*-
"""
VOA International Edition 批量下载器  (2025-06-12 / 1.1d)
=================================================

* 针对 `https://www.voanews.com/z/7104`（International Edition 列表页），自动翻页。
* GUI 允许设置 **开始 / 结束日期**（YYYY-MM-DD），在遍历时即按范围过滤并提前停止，避免无效请求。
* 下载链接三级回退：
  1. `<a download ... .mp3>`，优先 _hq 版本
  2. `<audio src="...mp3">`
  3. 正则检索 HTML 中直链 `.mp3`。
* 保存时按日期在目标目录下建立 `年/月` 两级子目录。
* 遍历测试功能后台线程执行并显示进度，界面不阻塞。
* 多线程下载支持（线程池控制）。
* 文件名格式：日期_节目标题_质量.mp3
* 依赖：`requests`, `beautifulsoup4`, `python-dateutil`, `orjson`, `tkinter`; 若需 JS 渲染再装 `playwright` 并 `playwright install`。
"""

import os
import re
import threading
import requests
from datetime import date, datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import messagebox

import orjson
from bs4 import BeautifulSoup
from dateutil import parser as dtparser
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

BASE_URL = "https://www.voanews.com"
LIST_URL = "https://www.voanews.com/z/7104"
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome"}

STATIC_SEL = "a[href^='/a/'][href$='.html']"
DOWNLOAD_SEL = "a[download][href$='.mp3']"


def fetch_html(url, use_browser):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def _fallback_mp3_regex(html):
    return re.findall(r"https?://[^\"']+?\.mp3", html)


def iter_detail_links(use_browser, date_from=None, date_to=None):
    page_idx = 0
    seen = set()
    while True:
        url = LIST_URL if page_idx == 0 else f"{LIST_URL}?p={page_idx}"
        html = fetch_html(url, use_browser)
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.select(STATIC_SEL):
            dt_val = _parse_date(" ".join(a.parent.stripped_strings))
            if dt_val:
                full_url = BASE_URL + a.get("href", "")
                if full_url not in seen:
                    seen.add(full_url)
                    links.append((dt_val, full_url))
        if not links:
            break
        stop = False
        for dt_val, link in links:
            if date_to and dt_val > date_to:
                continue
            if date_from and dt_val < date_from:
                stop = True
                break
            yield dt_val, link
        if stop:
            break
        page_idx += 1


def _parse_date(text):
    m = re.search(r"([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
    if not m:
        return None
    try:
        return dtparser.parse(m.group(1)).date()
    except:
        return None


def safe_filename(name):
    return re.sub(r"[\\/:*?<>|]+", "_", name)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VOA 下载器 1.1d")
        self.geometry("900x700")
        self._stop_flag = threading.Event()

        self.var_from = tk.StringVar()
        self.var_to = tk.StringVar()
        self.var_dir = tk.StringVar(value=os.path.abspath("downloads"))
        self.var_browser = tk.BooleanVar(value=False)

        frm = ttk.LabelFrame(self, text="参数设置")
        frm.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(frm, text="开始日期:").grid(row=0, column=0)
        ttk.Entry(frm, textvariable=self.var_from).grid(row=0, column=1, sticky="we")
        ttk.Label(frm, text="结束日期:").grid(row=1, column=0)
        ttk.Entry(frm, textvariable=self.var_to).grid(row=1, column=1, sticky="we")

        ttk.Label(frm, text="保存目录:").grid(row=2, column=0)
        ttk.Entry(frm, textvariable=self.var_dir, width=70).grid(row=2, column=1, sticky="we")
        ttk.Button(frm, text="选择…", command=self._choose_dir).grid(row=2, column=2)

        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=10)
        ttk.Button(bar, text="测试遍历", command=self._test_range).pack(side=tk.LEFT)
        ttk.Button(bar, text="开始下载", command=self._start).pack(side=tk.LEFT)
        ttk.Button(bar, text="停止", command=self._stop).pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.pack(fill=tk.X, padx=10, pady=5)

        self.log_box = scrolledtext.ScrolledText(self, font=("Consolas", 10))
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _choose_dir(self):
        p = filedialog.askdirectory()
        if p:
            self.var_dir.set(p)

    def _log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    def _stop(self):
        self._stop_flag.set()
        self._log("[中止] 请求停止…")

    def _test_range(self):
        try:
            d_from = datetime.strptime(self.var_from.get(), "%Y-%m-%d").date()
            d_to = datetime.strptime(self.var_to.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("日期错误", "格式应为 YYYY-MM-DD")
            return
        threading.Thread(target=self._run_test_range, args=(d_from, d_to), daemon=True).start()

    def _run_test_range(self, d_from, d_to):
        self._log("[测试遍历] 开始抓取...")
        count = 0
        seen = set()
        for dt_val, url in iter_detail_links(self.var_browser.get(), d_from, d_to):
            if url in seen:
                continue
            seen.add(url)
            self._log(f"{dt_val} -> {url}")
            count += 1
        self._log(f"[测试遍历] 完成，共 {count} 条唯一节目")

    def _start(self):
        try:
            d_from = datetime.strptime(self.var_from.get(), "%Y-%m-%d").date()
            d_to = datetime.strptime(self.var_to.get(), "%Y-%m-%d").date()
        except:
            messagebox.showerror("日期错误", "格式应为 YYYY-MM-DD")
            return
        self._stop_flag.clear()
        threading.Thread(target=self._run, args=(d_from, d_to), daemon=True).start()

    def _run(self, d_from, d_to):
        self._log("[下载] 启动线程...")
        seen = set()
        all_links = [(dt_val, url) for dt_val, url in iter_detail_links(self.var_browser.get(), d_from, d_to) if url not in seen and not seen.add(url)]
        self.progress.config(maximum=len(all_links), value=0)
        self._log(f"[下载] 总共 {len(all_links)} 条任务")

        def download_one(dt_val, url):
            try:
                html = fetch_html(url, self.var_browser.get())
                mp3s = _fallback_mp3_regex(html)
                if not mp3s:
                    return f"{dt_val} 无音频"
                mp3 = next((m for m in mp3s if '_hq' in m), mp3s[0])
                quality = "hq" if '_hq' in mp3 else "normal"

                title_tag = BeautifulSoup(html, "html.parser").find("title")
                title = title_tag.get_text(strip=True).split("|")[0] if title_tag else "voa"

                year_dir = os.path.join(self.var_dir.get(), str(dt_val.year))
                month_dir = os.path.join(year_dir, f"{dt_val.month:02d}")
                os.makedirs(month_dir, exist_ok=True)
                fname = safe_filename(f"{dt_val}_{title}_{quality}.mp3")
                path = os.path.join(month_dir, fname)
                with requests.get(mp3, headers=HEADERS, stream=True, timeout=30) as r:
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(8192):
                            f.write(chunk)
                return f"{dt_val} 下载完成: {fname}"
            except Exception as e:
                return f"{dt_val} 下载失败: {e}"

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {pool.submit(download_one, dt_val, url): (dt_val, url) for dt_val, url in all_links}
            for i, future in enumerate(as_completed(futures)):
                if self._stop_flag.is_set():
                    self._log("[下载] 中止请求已触发")
                    break
                msg = future.result()
                self._log(msg)
                self.progress.step()

        self._log("[下载] 任务全部结束")


if __name__ == '__main__':
    App().mainloop()
