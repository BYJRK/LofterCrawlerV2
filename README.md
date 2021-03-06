# Lofter 爬虫 V2

## 查看帮助文档

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

## 简易操作指南

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

## 其他参数

`--replace` 参数表示是否覆盖本地已有的同名文件，默认为否；`--separate` 参数表示在批量下载某个主页下的所有贴子中的图片时，（默认）是将所有图片存放在一个目录下，还是根据贴子分别创建文件夹进行存储。

其他参数一般不需要进行调整，比如 `--timeout`，`--retry`，`--processes`，分别用来调整连接的超时时间，重试下载次数，以及进程数。这里是异步下载的进程数，并不是线程数，不需要小于等于 CPU 的核心数。

## 有关最大尺寸

这里解释一下 `--maxsize` 的原理。Lofter 上面的图片都保存在网易的图床中。在查看原图时，观察地址栏的参数不难发现，其中有一个参数用来控制展示图片的尺寸。举个例子：

http://imglf5.nosdn0.126.net/img/d0VyL3IzRngzRitTVW01Snl3TkVFM2FXUzJXVlRQa2JDZmk4MkM4SEhyd094cytyVjVTSmJRPT0.jpg?imageView&thumbnail=1680x0&quality=96&stripmeta=0&type=jpg

可以看到，参数中有 `thumbnail=1680x0` 字样。这里的 `1680` 指的就是图片的高度。

经测试，这里的尺寸并不一定是图片的最大尺寸。所以通过调整这个参数，有可能获得比查看原图更大的图片。默认下载的是查看原图所提供的图像大小。如果数值过大，比如大于服务器上存储的实际照片的尺寸，则会下载服务器上存储的最大尺寸。

因此这里可以给一个非常大的数字，比如超过 10000，并不会产生不良影响。
