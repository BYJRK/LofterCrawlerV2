import lofter_utils
from lofter_utils import *
import pprint
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('target')
parser.add_argument('--start_page', type=int, default=1)
parser.add_argument('--end_page', type=int, default=0)
parser.add_argument('--replace', type=bool, default=True)
parser.add_argument('--retry', type=int, default=2)
parser.add_argument('--maxsize', type=int)
parser.add_argument('--separate', action='store_true')
parser.add_argument('--processes', type=int, default=8)
parser.add_argument('--timeout', type=int, default=16)

args = parser.parse_args()


def main():
    # target 可能是：
    # http://yurisa123.lofter.com/post/1cf5f941_12e0d2793
    # http://yurisa123.lofter.com/
    # yurisa123.lofter.com
    # yurisa123
    re_domain = re.compile(r'(?:http://)?([a-zA-Z0-9-]+)(?:\.\w+\.com.*)?')
    re_post = re.compile(r'[a-zA-Z0-9-]+\.lofter\.com/post/\w+_\w+')
    post = re_post.search(args.target)
    if post:
        post = post.group()
        download_post_mt(post)
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
    lofter_utils.REPLACE = args.replace
    lofter_utils.PROCESSES = args.processes
    lofter_utils.TIMEOUT = args.timeout
    lofter_utils.MAX_RETRY = args.retry
    main()
