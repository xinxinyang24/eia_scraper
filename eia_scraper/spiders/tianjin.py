import scrapy
from scrapy.mail import MailSender
import re
import os
from datetime import timezone
from datetime import timedelta
from datetime import datetime
from urllib.request import urlopen
from eia_scraper.items import EiaScraperItem

        
TIME_THRESHOLD = 21 # 15 days for now. 

class TianjinSpider(scrapy.Spider):
  name = 'tianjin'
  start_urls = ['http://sthj.tj.gov.cn/service_hall/approve_and_acceptance/approve_situation_notice/']
  path = './scraped_data/tianjin/'
  keywords = {'听证','报名', '环境影响报告', '环评', '用海批复', '用海申请', '用海规划', '海砂',  
    '开采', '功能区域区划', '海域使用权', '公报', '填海', '处罚', '罚款'}
  
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
            #urls_to_send = urls_to_send + title + ' (' + url + ')' + '; '
            urls_to_send += url +'; '
            break            
      else:
        exceeded_time_limit = True
        item['valid'] = False
      yield item    
    
    #yes_or_no = '有'
    yes_or_no = 'Yes'
    if urls_to_send == '':
      # urls_to_send = '本次无新链接。'
      urls_to_send = 'No new links.'
      yes_or_no = 'No'
    mailer = MailSender()
    # mailer.send(to=["simonfengqy@126.com"], subject="天津爬虫结果： " + yes_or_no, body=urls_to_send, 
    mailer.send(to=["simonfengqy@126.com"], subject="Tianjin spider results: " + yes_or_no, body=urls_to_send, 
      cc=["simonfengqy@gmail.com"])
    
    if not exceeded_time_limit:
      page_links = response.css('div[id="NPage"]')      
      next_page = page_links.xpath('//a[contains(text(), ">")]/@href').get()
      if next_page is not None:
        yield response.follow(next_page, self.parse)
    