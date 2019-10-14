# Lofter 爬虫 V2

在控制台中可以查看该脚本的简易帮助文档：

```shell
>>> python loftercrawler.py -h
usage: loftercrawler.py [-h] [--start_page START_PAGE] [--end_page END_PAGE]
                        [--replace] [--retry RETRY] [--maxsize MAXSIZE]
                        [--separate] [--processes PROCESSES]
                        [--timeout TIMEOUT] [--chunksize CHUNKSIZE]
                        target

一个多线程 Lofter 爬虫

positional arguments:
  target                需要爬取的主页或贴子链接

optional arguments:
  -h, --help            输出帮助信息
  --start_page START_PAGE
                        起始页（默认 1）
  --end_page END_PAGE   结束页（默认 0，表示最后一页）
  --replace             是否替换本地已有的同名图片
  --retry RETRY         重试次数（默认 2）
  --maxsize MAXSIZE     最大图片尺寸（默认为网页上的查看原图）
  --separate            是否按贴子分文件夹进行存储
  --processes PROCESSES
                        进程数（默认 8）
  --timeout TIMEOUT     超时时间（默认 16 秒）
  --chunksize CHUNKSIZE
                        数据块大小（默认 1024KB）
```

你可以用如下几种方式来快速使用本爬虫工具：

```shell
# 爬取 yurisa123.lofter.com 的所有贴子，并将所有图片下载到本地
python loftercrawler.py yurisa123
# 同上，但是并不需要输入完整的网址
python loftercrawler.py yurisa213.lofter.com
python loftercrawler.py http://yurisa213.lofter.com
# 爬取前 5 页的所有贴子并下载
python loftercrawler.py yurisa123 --end_page 5
# 爬取某个贴子
python loftercrawler.py http://yurisa123.lofter.com/post/1cf5f941_1c6be7500
```

其他参数一般不需要进行调整，比如 `--timeout`，`--retry`，`--processes`，分别用来调整连接的超时时间，重试下载次数，以及进程数。这里是异步下载的进程数，并不是线程数，不需要小于等于 CPU 的核心数。

这里解释一下 `--maxsize` 的原理。其实 Lofter 上面的图片都保存在网易的图床中。在查看原图时，观察地址栏的参数不难发现，其中有一个参数用来控制展示图片的尺寸。经过测试，这里的尺寸并不一定是图片的最大尺寸。所以通过调整这个参数，有可能获得比查看原图更大的图片。默认下载的是查看原图所提供的图像大小。可以尝试调整为更大的数值（如 3840）。如果图片最大大小小于这个数值，则会下载提供的最大尺寸。因此这里可以给一个非常大的数字，比如超过 10000，并不会产生任何不良影响。
