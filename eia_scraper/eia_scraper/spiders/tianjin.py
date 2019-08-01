import scrapy
from scrapy.mail import MailSender
import re
import os
from datetime import timezone
from datetime import timedelta
from datetime import datetime
from urllib.request import urlopen
from eia_scraper.items import EiaScraperItem
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

MAIL_HOST = 'smtp.sina.com'
MAIL_USER = 'shanahe'
MAIL_PASS = '******'
SENDER = 'shanahe@sina.com'
RECEIVERS = ['gloria6wzx@gmail.com', 'xinxin.yang@cecaprd.org']        
TIME_THRESHOLD = 15 # Can be adjusted. 

class TianjinSpider(scrapy.Spider):
  name = 'tianjin'

  start_urls = ['http://sthj.tj.gov.cn/service_hall/approve_and_acceptance/approve_situation_notice/']
  path = './scraped_data/tianjin/'
  keywords = {'听证','报名', '环境影响报告', '环评', '用海批复', '用海申请', '用海规划', '海砂',  
    '开采', '功能区域区划', '海域使用权', '公报', '填海', '处罚', '罚款'}
  eliminated_kwd = {'射线','放射'}
  
  def parse(self, response):
    exceeded_time_limit = False
    ullist = response.css('ul.ullist')
    urls_to_send = ''
    for url_selector in ullist.css('a'):      
      if exceeded_time_limit:
        break
      url = url_selector.css('*::attr("href")').get()
      # Check whether the time is within the past TIME_THRESHOLD days.
      ma = re.search(r'/t.*_', url)
      date = re.search(r'\d+', ma.group(0)).group(0)
      # For example, the 'date' variable is a string "20190717".
      datetime_obj = datetime.strptime(date, '%Y%m%d').replace(tzinfo=timezone(timedelta(hours=8)))
      # Use Beijing time.
      current_datetime = datetime.now(tz=timezone(timedelta(hours=8)))
      item = EiaScraperItem()
      item['url'] = url
      title = url_selector.css('*::text').get()
      if not os.path.exists(self.path):
        os.makedirs(self.path)
      item['path'] = self.path + date + '_' + title
            
      if current_datetime <= datetime_obj + timedelta(days=TIME_THRESHOLD + 1):          
        abs_url = response.urljoin(url)
        item['content'] = urlopen(abs_url).read().decode("utf-8") 
        item['valid'] = False
        for kwd in self.keywords:
          if re.search(kwd, item['content']) is not None:            
            item['valid'] = True           
            eliminated = True
            for e_kwd in self.eliminated_kwd:
              if re.search(e_kwd, item['content']) is not None:
            	  eliminated = False
            	  break

            if eliminated is True:
              urls_to_send = urls_to_send + '非缩水：' + title + ' (' + abs_url + ')' + '; ' + '\n'
              item['path'] = 'special_' + item['path']
            else:
              urls_to_send = urls_to_send + '缩水版：' + title + ' (' + abs_url + ')' + '; ' + '\n'       
            break            
      else:
        exceeded_time_limit = True
        item['valid'] = False
      yield item    
    
    yes_or_no = '有'    
    if urls_to_send == '':
      urls_to_send = '本次无新链接。'      
      yes_or_no = '无'    
    self.send_email('天津爬虫结果： ' + yes_or_no, urls_to_send)
    
    if not exceeded_time_limit:
      page_links = response.css('div[id="NPage"]')      
      next_page = page_links.xpath('//a[contains(text(), ">")]/@href').get()
      if next_page is not None:
        yield response.follow(next_page, self.parse)
        
        
  def send_email(self, email_title, email_body):
    message = MIMEMultipart()
    message['From'] = SENDER
    message['To'] = RECEIVERS[0]
    message['Subject'] = email_title
    #推荐使用html格式的正文内容，这样比较灵活，可以附加图片地址，调整格式等
    # with open('abc.html','r') as f:
        # content = f.read()
    #设置html格式参数
    # part1 = MIMEText(content,'html','utf-8')
    part1 = MIMEText(email_body,'plain','utf-8')
    #添加一个txt文本附件
    '''
    with open('abc.txt','r')as h:
        content2 = h.read()
    #设置txt参数
    part2 = MIMEText(content2,'plain','utf-8')
    #附件设置内容类型，方便起见，设置为二进制流
    part2['Content-Type'] = 'application/octet-stream'
    #设置附件头，添加文件名
    part2['Content-Disposition'] = 'attachment;filename="abc.txt"'
    '''
    #添加照片附件
    # with open('1.png','rb')as fp:
        # picture = MIMEImage(fp.read())        
        # picture['Content-Type'] = 'application/octet-stream'
        # picture['Content-Disposition'] = 'attachment;filename="1.png"'
    #将内容附加到邮件主体中
    message.attach(part1)
    # message.attach(part2)
    # message.attach(picture)

    #登录并发送
    try:
      smtpObj = smtplib.SMTP()
      smtpObj.connect(MAIL_HOST,25)
      smtpObj.login(MAIL_USER,MAIL_PASS)
      smtpObj.sendmail(
          SENDER,RECEIVERS,message.as_string())
      print('success')
      smtpObj.quit()
    except smtplib.SMTPException as e:
      print('error', e)
    