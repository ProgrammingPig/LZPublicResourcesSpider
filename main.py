# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/7/18 18:32
# @Author  : Mikey Yang
# @File    : main.py
# @Software: PyCharm


import requests, re, json, time, pymongo
from lxml import etree


class LZPublicResourcesSpider():
    def __init__(self):
        self.start_url = "http://lzggzyjy.lanzhou.gov.cn/xqfzx/014001/{}.html"
        self.project_info_api = "http://lzggzyjy.lanzhou.gov.cn/detailjson/getallprocessdetailInfo/1{}.json"
        self.bidding_file_api1 = "http://lzggzyjy.lanzhou.gov.cn/detailjson/getallprocessdetailInfo/3{}.json"
        self.bidding_file_api2 = "http://lzggzyjy.lanzhou.gov.cn/EpointWebBuilder/BulletinWebServer.action?cmd=getallprocessdetailInfonew&infoid={}&strStep=3"
        self.project_info = []
        self.client = pymongo.MongoClient('localhost', 27017)  # 初始化MongoDB连接

    def get_project_id(self, url):
        res = requests.get(url)
        if res.status_code == 404:  # 若状态码为404则代表爬取完毕
            return '404'
        html = etree.HTML(res.content.decode())
        project_url_list = html.xpath("//div[@class='ewb-work-block l']/a/@href")
        for project_url in project_url_list:
            project_id = re.findall("/\d{8}/(.*?).html", project_url)
            self.get_project_info(project_id[0], project_url)

    def get_project_info(self, project_id, project_url):
        try:
            project_info = requests.get(self.project_info_api.format(project_id)).json()["ret"]
        except:
            pass
        else:
            try:
                res = requests.get(self.bidding_file_api1.format(project_id)).json()
            except Exception:
                res = requests.get("http://lzggzyjy.lanzhou.gov.cn" + project_url).content.decode()
                infoid = re.findall('<input type="hidden" id="ztbguid" value="(.*?)"/>', res)[0]
                res = requests.get(self.bidding_file_api2.format(infoid)).json()
                res = json.loads(res["custom"])
            self.project_info.append({
                "project_info": project_info,
                "project_bidding_info": res["ret"]
            })
        # time.sleep(0.5)

    def main(self):
        for i in range(1, 400):
            print("正在爬取第{}页".format(i))
            url = self.start_url.format(i)
            if self.get_project_id(url) == '404':
                break
        print("爬取完毕！")
        db = self.client.lz_public_resource  # 连接lz_public_resource数据库
        my_set = db.project_data  # 创建数据表
        my_set.insert_many(self.project_info)  # 一次写入所有数据
        print("写入数据库完毕")


if __name__ == '__main__':
    public_resource_spider = LZPublicResourcesSpider()
    public_resource_spider.main()
