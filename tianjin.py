import scrapy
import re
from datetime import timezone
from datetime import timedelta
from datetime import datetime
 

class TianjinSpider(scrapy.Spider):
  name = 'Tianjin_spider'
  start_urls = ['http://sthj.tj.gov.cn/service_hall/approve_and_acceptance/approve_situation_notice/']
  TIME_THRESHOLD = 7 # 7 days for now.
  
  # TODO: unverified, probably has bugs.
  def parse(self, response):
    exceeded_time_limit = False
    ullist = response.css('ul.ullist')
    for url in ullist.css('a::attr("href")').getall():
      if exceeded_time_limit:
        break
      # Check whether the time is within the past TIME_THRESHOLD days.
      ma = re.search(r'/t.*_', url)
      date = re.search(r'\d+', ma.group(0)).group(0)
      # For example, the 'date' variable is a string "20190717".
      datetime_obj = datetime.strptime(date, '%Y%m%d').replace(tzinfo=timezone(timedelta(hours=8)))
      # Use Beijing time.
      current_datetime = datetime.now(tz=timezone(timedelta(hours=8)))
      if current_datetime <= datetime_obj + timedelta(days=TIME_THRESHOLD + 1):      
        # Plan: We can consider yielding a custom-defined Item. We should pass this url to 
        # the Item Pipeline or something like that: if the url's html content includes keywords,
        # we should copy the html to the local disk, otherwise throw a DropItem exception.
        yield {        
          'url': url,
          'valid': True,
        }
      else:
        exceeded_time_limit = True
        yield{
          'url': url,
          'valid': False,
        }          
    
    if not exceeded_time_limit:
      page_links = response.css('div[id="NPage"]')
      # Not quite sure whether this works or not.
      next_page = page_links.xpath('//a[contains(text(), ">")]/@href').get()
      if next_page is not None:
        yield response.follow(next_page, self.parse)
    