from lofter_utils import *
import pprint
import argparse

# parser = argparse.ArgumentParser()
# parser.add_argument()
# args = parser.parse_args()


if __name__ == "__main__":
    # pp = pprint.PrettyPrinter(indent=4, depth=2)
    # post1 = 'http://hiroron.lofter.com/post/302a9e_12e83e051'
    # post2 = 'http://shorthairgirls.lofter.com/post/3e5460_12e8c81e6'
    # post3 = 'http://gx-bhmt.lofter.com/post/1cb66dc4_12e89d634'
    # post4 = 'http://hiroron.lofter.com/post/302a9e_12e611a5c'
    # post5 = 'http://yurisa123.lofter.com/post/1cf5f941_12e0d2793'
    # post = get_post_info(
    #     'http://hiroron.lofter.com/post/302a9e_b8b9399')
    # download_post_mt(post, maxsize=6000)
    url = 'yurisa123.lofter.com'
    domain = re.search(
        r'(?:http://)?([a-zA-Z0-9-]+)(?:\.\w+\.com.*)?', url).group(1)
    gather_image_links(domain)
