import subprocess
from numpy import arange

count = 0

for window_size in [2, 4, 8, 16, 32]:
    for max_dupl_ack in range(8):
        for timer in arange(0.01, 0.1, 0.02):
            for _ in range(10):
                count += 1
print("On va faire %d tests" % count)