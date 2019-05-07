import web_utils
from web_utils import *
import pprint
import argparse

parser = argparse.ArgumentParser(description='一个多线程 Lofter 爬虫', add_help=False)
parser.add_argument('target', help='需要爬取的主页或贴子链接')
parser.add_argument('-h', '--help', action='help', help='输出帮助信息')
parser.add_argument('--start_page', type=int, default=1, help='起始页（默认 1）')
parser.add_argument('--end_page', type=int, default=0, help='结束页（默认 0，表示最后一页）')
parser.add_argument('--replace', type=bool, default=True, help='是否替换本地已有的同名图片')
parser.add_argument('--retry', type=int, default=2, help='重试次数（默认 2）')
parser.add_argument('--maxsize', type=int, help='最大图片尺寸')
parser.add_argument('--separate', action='store_true', help='是否按贴子分文件夹进行存储')
parser.add_argument('--processes', type=int, default=8, help='进程数（默认 8）')
parser.add_argument('--timeout', type=int, default=16, help='超时时间（默认 16 秒）')

args = parser.parse_args()


def main():
    # target 可能是：
    # http://yurisa123.lofter.com/post/1cf5f941_12e0d2793
    # http://yurisa123.lofter.com/
    # yurisa123.lofter.com
    # yurisa123
    re_domain = re.compile(r'(?:http://)?([a-zA-Z0-9-]+)(?:\.\w+\.com.*)?')
    re_post = re.compile(r'http://[a-zA-Z0-9-]+\.lofter\.com/post/\w+_\w+')
    post = re_post.search(args.target)
    if post:
        post = post.group()
        post_info = get_post_info(post)
        image_links = gather_image_links(post_info, args.separate)
        download_images_mt(image_links)
        return
    domain = re_domain.search(args.target)
    if domain:
        domain = domain.group(1)
        post_infos = gather_post_infos(domain, args.start_page, args.end_page)
        image_links = gather_image_links(post_infos, args.separate)
        download_images_mt(image_links, args.maxsize)


if __name__ == "__main__":
    # post1 = 'http://hiroron.lofter.com/post/302a9e_12e83e051'
    # post2 = 'http://shorthairgirls.lofter.com/post/3e5460_12e8c81e6'
    # post3 = 'http://gx-bhmt.lofter.com/post/1cb66dc4_12e89d634'
    # post4 = 'http://hiroron.lofter.com/post/302a9e_12e611a5c'
    web_utils.REPLACE = args.replace
    web_utils.PROCESSES = args.processes
    web_utils.TIMEOUT = args.timeout
    web_utils.MAX_RETRY = args.retry
    main()
