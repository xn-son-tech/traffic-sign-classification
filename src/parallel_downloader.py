import os
import urllib.request
import zipfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def download_chunk(url, start_byte, end_byte, chunk_idx, temp_dir):
    chunk_file = os.path.join(temp_dir, f"chunk_{chunk_idx}.part")
    
    # If already downloaded, skip
    if os.path.exists(chunk_file) and os.path.getsize(chunk_file) == (end_byte - start_byte + 1):
        return chunk_file
        
    req = urllib.request.Request(url)
    req.add_header("Range", f"bytes={start_byte}-{end_byte}")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(chunk_file, "wb") as f:
                    f.write(response.read())
            return chunk_file
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"\n[-] Error downloading chunk {chunk_idx}: {e}")
                raise e
            time.sleep(2 ** attempt)  # exponential backoff

def parallel_download(url, output_path, num_threads=32):
    print(f"\n[*] Starting parallel download of {url} using {num_threads} threads...")
    
    # 1. Get file size
    req = urllib.request.Request(url, method='HEAD')
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req) as resp:
        file_size = int(resp.headers.get("Content-Length", 0))
        
    if file_size == 0:
        raise ValueError("Could not retrieve file size. Server may not support range requests.")
        
    print(f"File Size: {file_size / (1024*1024):.2f} MB")
    
    # 2. Create temp directory for chunks
    temp_dir = output_path + "_temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    # 3. Calculate chunk boundaries
    chunk_size = file_size // num_threads
    chunks = []
    for i in range(num_threads):
        start_byte = i * chunk_size
        end_byte = (i + 1) * chunk_size - 1 if i < num_threads - 1 else file_size - 1
        chunks.append((start_byte, end_byte, i))
        
    # 4. Download chunks in parallel
    chunk_files = [None] * num_threads
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {
            executor.submit(download_chunk, url, start, end, idx, temp_dir): idx 
            for start, end, idx in chunks
        }
        
        with tqdm(total=num_threads, desc="Downloading chunks", unit="chunk") as pbar:
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    chunk_file = future.result()
                    chunk_files[idx] = chunk_file
                    pbar.update(1)
                except Exception as e:
                    print(f"[-] Chunk {idx} failed: {e}")
                    raise e
                    
    # 5. Merge chunks
    print(f"Merging {num_threads} chunks into {output_path}...")
    with open(output_path, "wb") as outfile:
        for chunk_file in chunk_files:
            if chunk_file and os.path.exists(chunk_file):
                with open(chunk_file, "rb") as infile:
                    outfile.write(infile.read())
                os.remove(chunk_file)  # clean up temp chunk
                
    # Remove temp dir
    try:
        os.rmdir(temp_dir)
    except:
        pass
        
    print(f"[+] Download complete: {output_path}")

def setup_gtsrb_dataset_parallel(data_dir="data", threads=32):
    os.makedirs(data_dir, exist_ok=True)
    
    urls = {
        "training": "https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Training_Images.zip",
        "test": "https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Test_Images.zip",
        "test_gt": "https://sid.erda.dk/public/archives/daaeac0d7ce1152aea9b61d9f1e19370/GTSRB_Final_Test_GT.zip"
    }
    
    for key, url in urls.items():
        filename = url.split('/')[-1]
        zip_path = os.path.join(data_dir, filename)
        
        extracted_folder = ""
        if key == "training":
            extracted_folder = os.path.join(data_dir, "GTSRB", "Final_Training")
        elif key == "test":
            extracted_folder = os.path.join(data_dir, "GTSRB", "Final_Test")
        elif key == "test_gt":
            extracted_folder = os.path.join(data_dir, "GT-final_test.csv")
            
        if os.path.exists(extracted_folder):
            print(f"[+] Component '{key}' is already downloaded and extracted.")
            continue
            
        # Download
        if not os.path.exists(zip_path):
            parallel_download(url, zip_path, num_threads=threads)
            
        # Extract
        print(f"Extracting {filename}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(data_dir)
        print(f"[+] Successfully extracted {filename}!")
        os.remove(zip_path)  # clean up zip

    print("[+] Parallel GTSRB Dataset setup complete!")

if __name__ == "__main__":
    setup_gtsrb_dataset_parallel()
