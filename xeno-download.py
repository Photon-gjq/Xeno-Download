import requests
import os
import time
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import re

# --- 配置 ---
BASE_OUTPUT_DIRECTORY = "downloaded_audio_data" # 主輸出目錄
REQUEST_DELAY_SECONDS = 1 # 每次 API 請求之間的延遲
MAX_COMPONENT_LENGTH = 80 # 單個檔名/目錄名組件的最大長度 (不含擴展名)

# --- Matplotlib 中文顯示配置 ---
# 嘗試常用的中文字體，你需要確保你的系統上安裝了至少一個
# Windows: 'SimHei', 'Microsoft YaHei'
# macOS: 'Arial Unicode MS', 'PingFang SC' (可能需要指定完整字體檔案路徑)
# Linux: 'WenQuanYi Micro Hei', 'Noto Sans CJK SC' (可能需要安裝字體包)
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示為方塊的問題
except Exception as e:
    print(f"Warning: Could not set preferred CJK fonts. Chinese characters in plots might not display correctly. Error: {e}")
    print("Please ensure you have a CJK-compatible font installed and recognized by Matplotlib.")

# --- 輔助函數 ---
def sanitize_filename_component(name, max_len=MAX_COMPONENT_LENGTH):
    """
    清理並縮短檔名/目錄名組件。
    1. 移除非法字元。
    2. 如果長度超過 max_len，則嘗試智能縮短或截斷。
    """
    # 1. 移除 Windows/Linux 非法字元
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_") # 用下劃線替換空格

    # 2. 縮短 (如果需要)
    if len(name) > max_len:
        # 嘗試從 xeno-canto 格式提取關鍵部分
        # XC812465-230622_005_10.50_Ph.phoen
        match = re.match(r"(XC\d+)-(\d{6})_.*?_([A-Za-z]{2}\.[A-Za-z]{3,5})", name)
        if match:
            xc_id, date_part, species_abbr = match.groups()
            short_name = f"{xc_id}_{date_part}_{species_abbr}"
            if len(short_name) <= max_len:
                print(f"  Shortened long name '{name}' to '{short_name}'")
                name = short_name
            else:
                # 如果智能縮短後仍然太長，則直接截斷（保留開頭）
                name = name[:max_len]
                print(f"  Truncated long name to '{name}' (fallback)")
        else:
            # 如果不符合預期格式，直接截斷
            name = name[:max_len]
            print(f"  Truncated long name to '{name}'")
    return name

def download_file(url, local_path):
    """下載檔案到指定路徑"""
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"  Downloaded: {local_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  Error downloading {url}: {e}")
        return False
    except Exception as e:
        print(f"  An unexpected error occurred during download of {url}: {e}")
        return False

def create_spectrogram(audio_path, spectrogram_path, audio_filename_for_title):
    """為音訊檔案創建並保存頻譜圖"""
    try:
        y, sr = librosa.load(audio_path, sr=None) # sr=None 保留原始取樣率

        # --- 調整這些參數 ---
        N_FFT = 2048      # FFT 窗口大小，嘗試 1024, 2048, 4096
        HOP_LENGTH = 512  # 幀移，通常是 N_FFT / 4，嘗試 N_FFT / 8
        N_MELS = 128      # Mel 濾波器數量，嘗試 128, 256

        S = librosa.feature.melspectrogram(y=y, sr=sr,
                                           n_fft=N_FFT,
                                           hop_length=HOP_LENGTH,
                                           n_mels=N_MELS,
                                           fmax=sr/2) # 最高頻率，可設置為例如 8000 或 12000，或保持 sr/2
        S_DB = librosa.power_to_db(S, ref=np.max)

        plt.figure(figsize=(15, 6)) # 稍微增大圖像尺寸 (寬, 高) in inches
        librosa.display.specshow(S_DB, sr=sr,
                                 hop_length=HOP_LENGTH, # 確保 specshow 使用相同的 hop_length
                                 x_axis='time', y_axis='mel',
                                 fmax=sr/2, # 與 melspectrogram 中的 fmax 保持一致
                                 cmap='magma') # 嘗試不同的 colormap，如 'viridis', 'inferno', 'magma'

        plt.colorbar(format='%+2.0f dB')
        title_text = f'鳥鳴頻譜圖 (Mel Spectrogram)\n{audio_filename_for_title}\n(sr={sr}Hz, n_fft={N_FFT}, hop={HOP_LENGTH}, n_mels={N_MELS})'
        plt.title(title_text)
        plt.tight_layout()

        # --- 提高保存圖像的 DPI ---
        plt.savefig(spectrogram_path, dpi=200) # 嘗試 dpi=150, 200, 300
        plt.close()
        print(f"  Generated spectrogram: {spectrogram_path} (sr={sr}Hz, n_fft={N_FFT}, hop={HOP_LENGTH}, n_mels={N_MELS})")
        return True
    except Exception as e:
        print(f"  Error generating spectrogram for {audio_path}: {e}")
        # ... (原來的錯誤處理)
        return False

def fetch_and_process_recordings(species_list, country, quality_filter=""):
    """
    查詢 xeno-canto API，下載音訊，並生成頻譜圖。
    quality_filter: 例如 "q:A" 代表 A 級錄音, "q_gt:B" 代表 B 級以上 (A,B)
    """
    if not os.path.exists(BASE_OUTPUT_DIRECTORY):
        os.makedirs(BASE_OUTPUT_DIRECTORY)

    for species_name in species_list:
        print(f"\nProcessing species: {species_name} in {country} (Quality: {quality_filter or 'any'})")
        # 鳥種名本身可能包含中文，用於檔案夾時也需要清理
        sanitized_species_folder_name = sanitize_filename_component(species_name, max_len=50) # 物種檔案夾名可以短一些
        species_output_dir = os.path.join(BASE_OUTPUT_DIRECTORY, sanitized_species_folder_name)
        if not os.path.exists(species_output_dir):
            os.makedirs(species_output_dir)

        query_species = species_name.replace(" ", "+")
        query = f"{query_species}+cnt:{country}"
        if quality_filter:
            query += f"+{quality_filter}"

        api_url = f"https://xeno-canto.org/api/2/recordings?query={query}"

        try:
            print(f"Querying API: {api_url}")
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"  API request failed for {species_name}: {e}")
            time.sleep(REQUEST_DELAY_SECONDS)
            continue
        except requests.exceptions.JSONDecodeError:
            print(f"  Failed to decode JSON response for {species_name}. Response text: {response.text[:200]}...")
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        num_recordings = int(data.get('numRecordings', 0))
        recordings = data.get('recordings', [])

        if num_recordings == 0 or not recordings:
            print(f"  No recordings found for {species_name} in {country} with quality '{quality_filter}'.")
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        print(f"  Found {num_recordings} recordings for {species_name} in {country}.")

        for i, recording in enumerate(recordings):
            xc_id = recording.get('id')
            # audio_url = recording.get('file') # 完整的下載 URL
            # file_url 欄位通常是 https://xeno-canto.org/sounds/uploaded/HASH/XCID.mp3
            # 而 recording.get('file') 可能直接是 //xeno-canto.org/... 需要補齊 https:
            audio_download_url = recording.get('file')
            if audio_download_url.startswith("//"):
                audio_download_url = "https:" + audio_download_url

            original_audio_filename = recording.get('file-name') # API 提供的建議檔名

            if not xc_id or not audio_download_url or not original_audio_filename:
                print(f"  Skipping recording due to missing ID, URL, or filename: {recording.get('id')}")
                continue

            print(f"\n  Processing recording {i+1}/{num_recordings}: ID {xc_id}, Original Filename: {original_audio_filename}")

            # 從原始音訊檔名中獲取基礎名 (不含擴展名)
            original_audio_basename = os.path.splitext(original_audio_filename)[0]

            # 清理並可能縮短這個基礎名，用於創建子檔案夾名稱和頻譜圖檔名前綴
            safe_base_for_folder_and_spectrogram = sanitize_filename_component(original_audio_basename)

            # 創建子檔案夾 (使用清理/縮短後的名稱)
            recording_subfolder = os.path.join(species_output_dir, safe_base_for_folder_and_spectrogram)
            if not os.path.exists(recording_subfolder):
                os.makedirs(recording_subfolder)

            # 音訊檔案路徑 (使用原始 xeno-canto 檔名)
            audio_local_path = os.path.join(recording_subfolder, original_audio_filename)
            # 頻譜圖檔案路徑 (使用清理/縮短後的基礎名 + 後綴)
            spectrogram_filename = f"{safe_base_for_folder_and_spectrogram}_spectrogram.png"
            spectrogram_local_path = os.path.join(recording_subfolder, spectrogram_filename)


            if not os.path.exists(audio_local_path):
                if not download_file(audio_download_url, audio_local_path):
                    time.sleep(REQUEST_DELAY_SECONDS)
                    continue
            else:
                print(f"  Audio already exists: {audio_local_path}")

            if not os.path.exists(spectrogram_local_path):
                # 傳遞 original_audio_filename 給頻譜圖標題，以顯示完整資訊
                if not create_spectrogram(audio_local_path, spectrogram_local_path, original_audio_filename):
                    pass
            else:
                print(f"  Spectrogram already exists: {spectrogram_local_path}")

            time.sleep(REQUEST_DELAY_SECONDS)

        print(f"Finished processing {species_name}.")
    print("\nAll species processed.")

# --- 主執行程序 ---
if __name__ == "__main__":
    target_species_sci = [
        "Caprimulgus jotaka"
    ]
    target_country = "China" # 例如: "Germany", "United Kingdom", "France", "China"
    
    # 可以添加錄音質量過濾，例如 "q:A" (僅A級), "q_gt:B" (B級以上), "" (不過濾)
    quality_filter = "q_gt:B" # C級及以上

    # 使用學名列表進行查詢
    fetch_and_process_recordings(target_species_sci, target_country, quality_filter)

    # 如果你想用中文名作為檔案夾，可以這樣組織：
    # for cn_name, sci_name in zip(target_species_cn, target_species_sci):
    #     print(f"\n--- Processing {cn_name} ({sci_name}) ---")
    #     # 將 fetch_and_process_recordings 的物種名參數改為 sci_name
    #     # 並在創建 species_output_dir 時使用 cn_name
    #     # fetch_and_process_recordings_single_species(sci_name, target_country, quality_filter, cn_name_for_folder=cn_name)
    #     # 這需要稍微修改 fetch_and_process_recordings 函數的結構

