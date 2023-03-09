# ░▀█▀░█▄█░█▀█░█▀█░█▀▄░▀█▀░█▀▀
# ░░█░░█░█░█▀▀░█░█░█▀▄░░█░░▀▀█
# ░▀▀▀░▀░▀░▀░░░▀▀▀░▀░▀░░▀░░▀▀▀

import requests
import threading
from tqdm import tqdm

# ░█▀▀░█░█░█▀█░█▀▀░▀█▀░▀█▀░█▀█░█▀█░█▀▀
# ░█▀▀░█░█░█░█░█░░░░█░░░█░░█░█░█░█░▀▀█
# ░▀░░░▀▀▀░▀░▀░▀▀▀░░▀░░▀▀▀░▀▀▀░▀░▀░▀▀▀

def download_chunk(url, start, end, buffer, timeout, filename):
    headers = {'Range': f'bytes={start}-{end}'}
    response = requests.get(url, headers=headers, stream=True, timeout=timeout)

    with open(filename, 'r+b') as f:
        f.seek(start)
        for chunk in response.iter_content(chunk_size=buffer):
            if chunk:
                f.write(chunk)
                if bar:
                    bar.update()

def download_file(url: str, filename: str, num_threads = 8, chunk_size = 1024 * 1024 * 4, timeout = 10, display_bar = True):
    if chunk_size % 1024 != 0 or num_threads <= 0:
        return None

    response = requests.head(url)
    total_size = int(response.headers.get('content-length', 0))

    with open(filename, 'wb') as f:
        f.truncate(total_size)

    chunk_ranges = [(i*chunk_size, (i+1)*chunk_size-1) for i in range(num_threads)]
    chunk_ranges[-1] = (chunk_ranges[-1][0], total_size-1)

    global bar
    if display_bar:
        bar = tqdm(total = (total_size // chunk_size + 1), desc="Remaining parts", colour="yellow")
    else:
        bar = None

    threads = []
    for idx, (start, end) in enumerate(chunk_ranges):
        thread = threading.Thread(target=download_chunk, args=(url, start, end, chunk_size, timeout, filename))
        thread.start()
        threads.append(thread)

    # Wait for all threads to end
    thread: threading.Thread
    for thread in threads:
        thread.join()

    if bar:
        bar.close()
