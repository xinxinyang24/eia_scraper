# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

class EiaScraperPipeline(object):
    def process_item(self, item, spider):
        url = item['url']
        if not item['valid']:
            raise DropItem('The URL {0} does not correspond to a wanted webpage.'.format(url))
        
        f_name = item['path'] + '.html'        
        with open(f_name, 'w', encoding='utf-8') as f:
            f.write(item['content'])          
        return item

        