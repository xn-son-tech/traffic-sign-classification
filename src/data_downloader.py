import os
from src.parallel_downloader import setup_gtsrb_dataset_parallel

def setup_gtsrb_dataset(data_dir="data"):
    # Call our ultra high-speed multi-threaded parallel downloader
    # Using 32 threads to bypass academic server bandwidth throttling!
    setup_gtsrb_dataset_parallel(data_dir, threads=32)

if __name__ == "__main__":
    setup_gtsrb_dataset()
