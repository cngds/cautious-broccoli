
#本py程序是抓取研招网的硕士专业目录的信息
import random
import time
import requests
import re
from lxml import etree
from pandas.core.frame import DataFrame

class Yanzhaowang:
    def __init__(self, search_data):
        self.head = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36"
        }
        
        #查询专业的url
        self.url = "https://yz.chsi.com.cn/zsml/queryAction.do"
        
        self.data = [["所在地", "招生单位", "考试方式", "院系所", "专业", "学习方式", "研究方向", "指导老师", "拟招人数", "备注", "考试范围"]]
        self.search_data = search_data
    
    def get_one_page_post(self, url, data):
        try :
            response = requests.post(url, data=data, headers=self.head)
            if response.status_code == 200:
                return response.text
            return None
        except RequestException:
            return None
        
    def get_one_page_get(self, url):
        try :
            response = requests.get(url, headers=self.head)
            if response . status_code == 200:
                return response.text
            return None
        except RequestException:
            return None
        
    def get_pages(self, text):
        '''获取页面的页数'''
        #测试1页的结果，以及多页的结果，取倒数第三个就是最大页数
        html = etree.HTML(text)
        result = html.xpath('//ul[@class="ch-page"]//text()')
        return result[-3]
    
    def get_school_url(self, text):
        """获取招生学校的信息"""
        #class="ch-table"院校列表
        html = etree.HTML(text)
        
        result_location = html.xpath('//table[@class="ch-table"]/tbody//tr//td[2]//text()')
        result_url = []
        r_url = html.xpath('//table[@class="ch-table"]/tbody//a/@href')
        for r in r_url:
            result_url.append("".join(["https://yz.chsi.com.cn",r]))
        result = zip(result_url, result_location)

        return list(result)

    def get_college_url(self, text):
        """返回一个学校详情的专业方向数据的网址"""
        _url = re.findall(
            '<td class="ch-table-center"><a href="(.*?)" target="_blank">查看</a>',
            text)
        colleges_url = []
        for r in _url:
            colleges_url.append("".join(["https://yz.chsi.com.cn",r]))
        return colleges_url

    def get_final_data(self, text):
        """输出一个学校一个学院一个专业的数据"""
        #class="zsml-summary"基本信息
        #class="zsml-bz"备注
        #class="zsml-res-items"考试范围，可能不止一个items
        result = []
        html = etree.HTML(text)
        
        result_inf = html.xpath('//td[@class="zsml-summary"]//text()')
        if len(result_inf) == 7:
            result_inf.insert(6, "")#指导老师栏目没有text,这里插入空值
            
        result_bz = html.xpath('//span[@class="zsml-bz"]//text()')

        res_items = html.xpath('//tbody[@class="zsml-res-items"]//td/text()')
        #清洗数据
        res_items.remove("\r\n                ")
        for i in range(len(res_items)):
            res_items[i] = res_items[i].replace("\r\n", "")
            res_items[i] = res_items[i].replace(" ", "")
 
        #合并元素，合并列表进去
        result = result_inf
        result.append(''.join(result_bz))
        result.append(''.join(res_items))

        return result

    def get_search_all_data(self):
        """获取最终网页（学校招生专业详情的网页）的数据"""
        
        html_text = self.get_one_page_post(self.url, self.search_data)
        pages = self.get_pages(html_text)
        for page in range(int(pages)):          
            self.search_data["pageno"] = page + 1
            html_text = self.get_one_page_post(self.url, self.search_data)
            print("开始查询……")
            
            urls = []
            #判断 高校名称 有没有，有的话，可能直接查的是学校学院专业数据。用get_college_url
            if self.search_data["dwmc"] == "":
                urls = self.get_school_url(html_text)
                
                for school_u in urls:
                    pages = self.get_pages(html_text)
                    for college_page in range(int(pages)):
                        
                        s_u = "".join([school_u[0], "&pageno=", str(college_page + 1)])
                        college_html_text = self.get_one_page_get(s_u)
                        college_url = self.get_college_url(college_html_text)
                        
                        for college_u in college_url:
                            print(college_u)
                            time.sleep(random.uniform(2, 6))
                            text = self.get_one_page_get(college_u)
                            temp = []
                            temp.append(school_u[1])
                            temp.extend(self.get_final_data(text))
                            self.data.append(temp)
                        
            else:
                urls = self.get_college_url(html_text)
                for college_u in urls:
                    print(college_u)
                    time.sleep(random.uniform(2, 6))
                    text = self.get_one_page_get(college_u)
                    temp = []
                    temp.append("")#不显示所在地
                    temp.extend(self.get_final_data(text))
                    self.data.append(temp)
                    
    def get_data_frame(self):
        """将列表形数据转化为数据框格式"""
        data = DataFrame(self.data)
        data.to_csv("查询招生信息的结果.csv", encoding="utf_8_sig")

if __name__ == '__main__': 
    search_data = {
        	"ssdm": "",#这里输入省市
            "dwmc": "",#这里输入高校名称
            "mldm": "08",#这里输入学科门类代码
            "mlmc": "",#不知道是啥，不用管先……
            "yjxkdm": "0808",#这里输入学科类别代码
            "zymc": "",#这里输入专业
            "xxfs": "",#这里输入学习方式
            "pageno": ""#这里输入查询的指定页数
        }
    spyder = Yanzhaowang(search_data)
    spyder.get_search_all_data()
    spyder.get_data_frame()
    print("OK,完成")
