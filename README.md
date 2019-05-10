# LofterCrawlerV2

```shell
>>> python loftercrawler.py -h
usage: loftercrawler.py [-h] [--start_page START_PAGE] [--end_page END_PAGE]
                        [--replace REPLACE] [--retry RETRY]
                        [--maxsize MAXSIZE] [--separate]
                        [--processes PROCESSES] [--timeout TIMEOUT]
                        [--chunksize CHUNKSIZE]
                        target

一个多线程 Lofter 爬虫

positional arguments:
  target                需要爬取的主页或贴子链接

optional arguments:
  -h, --help            输出帮助信息
  --start_page START_PAGE
                        起始页（默认 1）
  --end_page END_PAGE   结束页（默认 0，表示最后一页）
  --replace REPLACE     是否替换本地已有的同名图片
  --retry RETRY         重试次数（默认 2）
  --maxsize MAXSIZE     最大图片尺寸
  --separate            是否按贴子分文件夹进行存储
  --processes PROCESSES
                        进程数（默认 8）
  --timeout TIMEOUT     超时时间（默认 16 秒）
  --chunksize CHUNKSIZE
                        数据块大小（默认 1024KB）
  ```
