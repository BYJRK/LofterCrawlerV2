import datetime
import time


s1 = '302a9e_12e83e051'
d1 = datetime.datetime(2019, 4, 27)
s2 = '302a9e_12e88186a'
d2 = datetime.datetime(2019, 4, 28)
s3 = '1cb66dc4_12e89d634'
d3 = datetime.datetime(2019, 4, 29)


def s2t(s):
    s = s.split('_')[-1]
    n = int(s, base=16)
    # d = time.gmtime(n)
    return datetime.datetime.fromtimestamp(n)


print(s2t(s1) - d1)
print(s2t(s2) - d2)
print(s2t(s3) - d3)
