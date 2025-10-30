import requests
import os
import time
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import re
import sys # 導入 sys 模組以方便退出

# --- 配置 (v3 更新) ---
# [!! 重要 !!] 你必須在這裡填入你自己的 xeno-canto API Key
# 你可以登錄 xeno-canto.org 後在你的帳戶頁面找到它。
XC_API_KEY = "YOUR_API_KEY_HERE" 

BASE_OUTPUT_DIRECTORY = "downloaded_audio_data" # 主輸出目錄
REQUEST_DELAY_SECONDS = 1 # 每次 API 請求之間的延遲
MAX_COMPONENT_LENGTH = 80 # 單個檔名/目錄名組件的最大長度 (不含擴展名)

# --- Matplotlib 中文顯示配置 ---
# (此部分無需更改，保持原樣)
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
    plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    print(f"Warning: Could not set preferred CJK fonts. Chinese characters in plots might not display correctly. Error: {e}")
    print("Please ensure you have a CJK-compatible font installed and recognized by Matplotlib.")

# --- 輔助函數 ---
# (以下三個輔助函數無需更改，保持原樣)
def sanitize_filename_component(name, max_len=MAX_COMPONENT_LENGTH):
    """
    清理並縮短檔名/目錄名組件。
    1. 移除非法字元。
    2. 如果長度超過 max_len，則嘗試智能縮短或截斷。
    """
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    if len(name) > max_len:
        match = re.match(r"(XC\d+)-(\d{6})_.*?_([A-Za-z]{2}\.[A-Za-z]{3,5})", name)
        if match:
            xc_id, date_part, species_abbr = match.groups()
            short_name = f"{xc_id}_{date_part}_{species_abbr}"
            if len(short_name) <= max_len:
                print(f"  Shortened long name '{name}' to '{short_name}'")
                name = short_name
            else:
                name = name[:max_len]
                print(f"  Truncated long name to '{name}' (fallback)")
        else:
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
        y, sr = librosa.load(audio_path, sr=None)
        N_FFT = 2048
        HOP_LENGTH = 512
        N_MELS = 128
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH, n_mels=N_MELS, fmax=sr/2)
        S_DB = librosa.power_to_db(S, ref=np.max)
        plt.figure(figsize=(15, 6))
        librosa.display.specshow(S_DB, sr=sr, hop_length=HOP_LENGTH, x_axis='time', y_axis='mel', fmax=sr/2, cmap='magma')
        plt.colorbar(format='%+2.0f dB')
        title_text = f'鳥鳴頻譜圖 (Mel Spectrogram)\n{audio_filename_for_title}\n(sr={sr}Hz, n_fft={N_FFT}, hop={HOP_LENGTH}, n_mels={N_MELS})'
        plt.title(title_text)
        plt.tight_layout()
        plt.savefig(spectrogram_path, dpi=200)
        plt.close()
        print(f"  Generated spectrogram: {spectrogram_path} (sr={sr}Hz, n_fft={N_FFT}, hop={HOP_LENGTH}, n_mels={N_MELS})")
        return True
    except Exception as e:
        print(f"  Error generating spectrogram for {audio_path}: {e}")
        return False

# --- 主處理函數 (v3 更新) ---
# --- 主處理函數 (v3 再次修正) ---
def fetch_and_process_recordings(species_list, country, quality_filter=""):
    """
    【已更新至 API v3 並修正查詢格式】
    查詢 xeno-canto API，下載音訊，並生成頻譜圖。
    quality_filter: 例如 "q:A" 代表 A 級錄音, "q_gt:B" 代表 B 級以上 (A,B)
    """
    if not XC_API_KEY or XC_API_KEY == "YOUR_API_KEY_HERE":
        print("錯誤：請在程式碼頂部的 XC_API_KEY 變數中設定您的 xeno-canto API Key。")
        sys.exit(1)

    if not os.path.exists(BASE_OUTPUT_DIRECTORY):
        os.makedirs(BASE_OUTPUT_DIRECTORY)

    API_ENDPOINT = "https://xeno-canto.org/api/3/recordings"

    for species_name in species_list:
        print(f"\nProcessing species: {species_name} in {country or 'any country'} (Quality: {quality_filter or 'any'})")
        sanitized_species_folder_name = sanitize_filename_component(species_name, max_len=50)
        species_output_dir = os.path.join(BASE_OUTPUT_DIRECTORY, sanitized_species_folder_name)
        if not os.path.exists(species_output_dir):
            os.makedirs(species_output_dir)

        # --- 【核心修改部分】 ---
        # 根據 API v3 的嚴格要求，將學名拆分為 gen 和 sp 標籤
        parts = species_name.strip().split()
        if len(parts) != 2:
            print(f"  錯誤：物種學名 '{species_name}' 格式不正確，應為 'Genus species'。已跳過此物種。")
            continue
        
        genus, species_epithet = parts
        
        # 使用一個列表來構建查詢標籤，這樣更清晰且不易出錯
        query_tags = [f"gen:{genus}", f"sp:{species_epithet}"]

        if country:
            query_tags.append(f"cnt:{country}")
        
        if quality_filter:
            query_tags.append(f"{quality_filter}")

        # 用空格將所有標籤連接成最終的查詢字串
        query = " ".join(query_tags)
        # --- 【修改結束】 ---
        
        current_page = 1
        total_pages = 1
        
        while current_page <= total_pages:
            payload = {
                'query': query,
                'key': XC_API_KEY,
                'page': current_page
            }

            try:
                print(f"Querying API page {current_page}/{total_pages}... Query: '{query}'")
                response = requests.get(API_ENDPOINT, params=payload, timeout=30)
                response.raise_for_status()
                data = response.json()

                if 'error' in data:
                    print(f"  API Error for {species_name}: {data['error']['message']}")
                    break

            except requests.exceptions.RequestException as e:
                print(f"  API request failed for {species_name} on page {current_page}: {e}")
                time.sleep(REQUEST_DELAY_SECONDS)
                break
            except requests.exceptions.JSONDecodeError:
                print(f"  Failed to decode JSON response for {species_name}. Response text: {response.text[:200]}...")
                time.sleep(REQUEST_DELAY_SECONDS)
                break
            
            if current_page == 1:
                total_pages = data.get('numPages', 1) # 預設為1以防萬一
                num_recordings_total = int(data.get('numRecordings', 0))
                if num_recordings_total == 0:
                    print(f"  No recordings found for query: '{query}'.")
                    break
                else:
                    print(f"  Found {num_recordings_total} recordings across {total_pages} page(s).")

            recordings_on_page = data.get('recordings', [])

            for i, recording in enumerate(recordings_on_page):
                xc_id = recording.get('id')
                audio_download_url = recording.get('file')
                if audio_download_url and audio_download_url.startswith("//"):
                    audio_download_url = "https:" + audio_download_url

                original_audio_filename = recording.get('file-name')

                if not xc_id or not audio_download_url or not original_audio_filename:
                    print(f"  Skipping recording due to missing ID, URL, or filename: {recording.get('id')}")
                    continue

                print(f"\n  Processing recording {xc_id}: {original_audio_filename}")
                
                # ...(後續的下載和頻譜圖生成邏輯無需改動)...
                original_audio_basename = os.path.splitext(original_audio_filename)[0]
                safe_base_for_folder_and_spectrogram = sanitize_filename_component(original_audio_basename)
                
                recording_subfolder = os.path.join(species_output_dir, safe_base_for_folder_and_spectrogram)
                if not os.path.exists(recording_subfolder):
                    os.makedirs(recording_subfolder)

                audio_local_path = os.path.join(recording_subfolder, original_audio_filename)
                spectrogram_filename = f"{safe_base_for_folder_and_spectrogram}_spectrogram.png"
                spectrogram_local_path = os.path.join(recording_subfolder, spectrogram_filename)

                if not os.path.exists(audio_local_path):
                    if not download_file(audio_download_url, audio_local_path):
                        time.sleep(REQUEST_DELAY_SECONDS)
                        continue
                else:
                    print(f"  Audio already exists: {audio_local_path}")

                if not os.path.exists(spectrogram_local_path):
                    create_spectrogram(audio_local_path, spectrogram_local_path, original_audio_filename)
                else:
                    print(f"  Spectrogram already exists: {spectrogram_local_path}")
                
                time.sleep(REQUEST_DELAY_SECONDS)
            
            current_page += 1

        print(f"Finished processing {species_name}.")
    print("\nAll species processed.")

# --- 主執行程序 ---
if __name__ == "__main__":
    target_species_sci = [
        "Otus spilocephalus",
        "Otus lettia",
        "Otus sunia" # 增加一個例子
    ]
    # 如果不指定國家，請留空
    target_country = "China" # 例如: "Germany", "United Kingdom", "France", "China", "Taiwan"
    
    # 可以添加錄音質量過濾，例如 "q:A" (僅A級), "q_gt:B" (B級以上), "" (不過濾)
    # q_gt:C 代表 B級和 A級
    quality_filter = "q:A"

    fetch_and_process_recordings(target_species_sci, target_country, quality_filter)
