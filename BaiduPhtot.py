import os
import json
import requests
from http.client import IncompleteRead
import time

class BaiduPhoto:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
        } 
        self.URL = "https://photo.baidu.com/youai/file/v2/download?clienttype={clienttype}&bdstoken={bdstoken}&fsid={fsid}"
        self.json_path = "./json/"
        self.save_path = "./BauduPhoto/"  # 保存图片的主目录
        self.clienttype = None
        self.bdstoken = None
        self.folder_names = []
        self.completed_files = self.load_completed_files()  # 加载已完成的文件

    def load_completed_files(self):
        """加载已下载的图片文件名"""
        downloaded_files = set()
        for root, dirs, files in os.walk(self.save_path):
            for file in files:
                downloaded_files.add(file)  # 将已下载的图片文件名加入集合
        return downloaded_files

    def sanitize_filename(self, filename):
        """对文件名进行清理，防止出现非法字符或路径问题"""
        return filename.replace(':', '-').replace('/', '_').replace('\\', '_').replace(' ', '_')

    def download_photo(self):
        files = os.listdir(self.json_path)  # 获取JSON文件列表
        for file in files:
            with open(self.json_path + file, 'r', encoding="utf-8") as f:
                json_data = json.load(f)
            
            # 获取图片信息
            date = json_data["extra_info"]["date_time"][:10].replace(':', '-')
            filename = self.sanitize_filename(json_data["path"][12:])  # 清理文件名
            fsid = json_data["fsid"]

            # 检查图片是否已下载
            if filename in self.completed_files:
                print(f"{filename} 已经下载，跳过...")
                continue

            # 创建日期文件夹，确保在 ./BauduPhoto/ 目录中
            if date not in self.folder_names:
                os.makedirs(os.path.join(self.save_path, date), exist_ok=True)
                self.folder_names.append(date)

            # 下载图片，添加重试机制和错误处理
            self.download_with_retry(date, filename, fsid)

    def download_with_retry(self, date, filename, fsid, retries=3, timeout=30):
        """下载图片并添加重试机制，处理 IncompleteRead 错误和超时"""
        for attempt in range(retries):
            try:
                # 获取下载链接
                response = requests.get(self.URL.format(clienttype=self.clienttype, bdstoken=self.bdstoken, fsid=fsid), headers=self.headers, timeout=timeout)
                
                if response.status_code == 200:
                    r_json = response.json()
                    download_url = r_json.get('dlink')

                    if download_url:
                        r_download = requests.get(download_url, headers=self.headers, timeout=timeout)
                        file_path = os.path.join(self.save_path, date, filename)  # 确保文件写入到正确的目录

                        # 写入文件
                        with open(file_path, 'wb') as f:
                            f.write(r_download.content)

                        print(f"{date}, {filename} 下载成功.")

                        # 将下载完成的文件名添加到 completed_files 中
                        self.completed_files.add(filename)
                        return  # 成功下载后返回，跳出重试循环

                else:
                    print(f"获取下载链接失败: {response.status_code}")

            except IncompleteRead as e:
                print(f"IncompleteRead 错误: {e}. 重试 {attempt + 1}/{retries} ...")
                time.sleep(5)  # 等待 5 秒后重试

            except requests.exceptions.RequestException as e:
                print(f"请求失败: {e}. 重试 {attempt + 1}/{retries} ...")
                time.sleep(5)  # 等待 5 秒后重试

        print(f"{filename} 下载失败，已达到最大重试次数.")

    def start(self):
        with open("settings.json", 'r') as f:
            json_data = json.load(f)
        self.clienttype = json_data["clienttype"]
        self.bdstoken = json_data["bdstoken"]
        self.headers["Cookie"] = json_data["Cookie"]

        self.download_photo()

if __name__ == "__main__":
    baidu_photo = BaiduPhoto()
    baidu_photo.start()
