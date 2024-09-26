import os
import json
import requests
from http.client import IncompleteRead
import time

class FindPhotoList:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        }
        self.path = "./json/"
        self.completed_file = "completed.json"  # 已爬取文件的索引
        self.clienttype = None
        self.bdstoken = None
        self.need_thumbnail = None
        self.need_filter_hidden = None
        self.flag = True
        self.i_num = 1  # 初始化计数器
        self.completed = self.load_completed()  # 加载已完成的列表
        self.scan_existing_files()  # 扫描已存在的文件，并将其加入索引

    def load_completed(self):
        """加载已完成的文件列表"""
        if os.path.exists(self.completed_file):
            with open(self.completed_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))  # 用集合来存储已完成文件的路径，方便快速查找
        return set()

    def save_completed(self):
        """保存已完成的文件列表"""
        with open(self.completed_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.completed), f, ensure_ascii=False, indent=4)

    def scan_existing_files(self):
        """扫描已经爬取的 JSON 文件并加入索引"""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                            if "path" in data:
                                self.completed.add(data["path"])  # 将文件的路径加入已完成列表
                        except json.JSONDecodeError:
                            print(f"无法解析文件: {file_path}")
        self.save_completed()  # 将已爬取部分保存到索引中

    def save_json(self, photo_list):
        for photo in photo_list:
            if photo["path"] not in self.completed:  # 检查是否已爬取
                file_name = self.path + photo["path"][12:] + ".json"
                os.makedirs(os.path.dirname(file_name), exist_ok=True)
                with open(file_name, "w", encoding="utf-8") as f:
                    json.dump(photo, f, ensure_ascii=False, indent=4)
                self.completed.add(photo["path"])  # 将新的文件路径加入已完成的列表
                self.save_completed()  # 保存已完成的列表

    def crawler(self, URL, retries=3, timeout=30):
        """
        爬虫请求函数，增加了重试机制，处理IncompleteRead错误，并设置了超时时间。
        :param URL: 请求的URL
        :param retries: 最大重试次数
        :param timeout: 请求超时时间
        :return: 返回光标以便获取下一页
        """
        for attempt in range(retries):
            try:
                response = requests.get(URL, headers=self.headers, timeout=timeout)
                print(f"ID:{self.i_num}\tStatus:{response.status_code}")
                self.i_num += 1  # 每次成功请求后递增计数器
                response.raise_for_status()  # 检查请求是否成功
                data = response.json()

                photo_list = data.get("list", [])
                if not photo_list:  # 爬取完毕
                    self.flag = False
                    return
                self.save_json(photo_list)

                cursor = data.get("cursor")
                return cursor

            except IncompleteRead as e:
                print(f"IncompleteRead 错误: {e}. 正在重试 {attempt + 1}/{retries} ...")
                time.sleep(5)  # 等待 5 秒后重试

            except requests.exceptions.RequestException as e:
                print(f"请求失败: {e}. 正在重试 {attempt + 1}/{retries} ...")
                time.sleep(5)  # 等待 5 秒后重试

        self.flag = False
        return None

    def func(self):
        URL = f"https://photo.baidu.com/youai/file/v1/list?clienttype={self.clienttype}&bdstoken={self.bdstoken}&need_thumbnail={self.need_thumbnail}&need_filter_hidden={self.need_filter_hidden}"
        cursor = self.crawler(URL)
        while self.flag and cursor:
            URL = f"https://photo.baidu.com/youai/file/v1/list?clienttype={self.clienttype}&bdstoken={self.bdstoken}&cursor={cursor}&need_thumbnail={self.need_thumbnail}&need_filter_hidden={self.need_filter_hidden}"
            cursor = self.crawler(URL)

    def start(self):
        with open("settings.json", 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        self.clienttype = json_data["clienttype"]
        self.bdstoken = json_data["bdstoken"]
        self.need_thumbnail = json_data["need_thumbnail"]
        self.need_filter_hidden = json_data["need_filter_hidden"]
        self.headers["Cookie"] = json_data["Cookie"]

        os.makedirs(self.path, exist_ok=True)
        self.func()

if __name__ == "__main__":
    find_photo_list = FindPhotoList()
    find_photo_list.start()
