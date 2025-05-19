# Xeno-Canto 鳥鳴音訊下載與頻譜圖生成器 (Xeno-Canto Audio Downloader & Spectrogram Generator)

這是一個 Python 腳本，用於從 [xeno-canto.org](https://xeno-canto.org) API 直接下載指定鳥種在特定國家的鳥鳴音訊，並為每個音訊檔案生成對應的頻譜圖。腳本會自動為每個音訊創建一個子檔案夾，其中包含音訊檔案 (.mp3) 和其頻譜圖 (.png)。

## 功能特性

*   **直接下載**: 無需手動處理 JSON，直接輸入鳥種（學名）和國家即可下載。
*   **批量處理**: 支持一次輸入多個鳥種。
*   **質量過濾**: 可以根據 xeno-canto 的錄音質量評級 (A, B, C, D, E) 進行篩選。
*   **頻譜圖生成**: 自動為每個下載的音訊生成梅爾頻譜圖 (Mel Spectrogram)。
*   **檔案組織**:
    *   在指定的基礎輸出目錄下，為每個鳥種創建一個子目錄。
    *   在每個鳥種目錄下，為每個錄音創建一個以其（經處理的）檔名命名的子目錄。
    *   每個錄音子目錄包含原始 `.mp3` 檔案和對應的 `_spectrogram.png` 頻譜圖。
*   **檔名處理**: 自動處理和縮短過長的檔名/目錄名，以避免作業系統限制。
*   **中文支持**: 頻譜圖標題中的中文字元可以正常顯示（需系統安裝支持中文的字體）。
*   **API 友好**: 在請求之間加入延遲，以尊重 xeno-canto API 的使用。

## 先決條件

1.  **Python**: 建議使用 Python 3.7 或更高版本。
2.  **Pip**: Python 包安裝器。
3.  **必要的 Python 庫**:
    *   `requests`: 用於發送 HTTP 請求。
    *   `librosa`: 用於音訊分析和頻譜圖生成。
    *   `matplotlib`: 用於繪製和保存頻譜圖。
    *   `numpy`: `librosa` 的依賴庫。
4.  **FFmpeg (推薦)**: `librosa` 在後台可能需要 `ffmpeg` 來解碼某些音訊格式（尤其是 MP3）。請確保已安裝 `ffmpeg` 並將其添加到了系統的 PATH 環境變數中。
    *   下載與安裝指南: [FFmpeg Download](https://ffmpeg.org/download.html)
5.  **中文字體 (用於頻譜圖標題)**: 為了在頻譜圖標題中正確顯示中文，你的系統需要安裝至少一種支持中文的字體，並且 `matplotlib` 能夠找到它。腳本中預設嘗試了常見的中文字體如 `'SimHei'`, `'Microsoft YaHei'` 等。如果中文仍顯示為方框，請參考腳本開頭的 `plt.rcParams['font.sans-serif']` 部分，並將其修改為你系統上已安裝的中文字體名稱。

## 安裝依賴

打開終端或命令提示符，運行以下命令安裝所需的 Python 庫：

```bash
pip install requests librosa matplotlib numpy
```

## 如何使用

1.  **下載/克隆腳本**:
    將 `xc_downloader.py` (或你命名的腳本檔案) 下載到你的本地電腦。

2.  **配置腳本**:
    打開 `xc_downloader.py` 檔案，找到以下主要配置區域並進行修改：

    *   **腳本頂部常量**:
        *   `BASE_OUTPUT_DIRECTORY`: 主輸出目錄，所有下載的數據將保存在此目錄下。預設為 `"downloaded_audio_data"`。
        *   `REQUEST_DELAY_SECONDS`: 每次 API 請求之間的延遲（秒）。建議保持 `1` 秒或以上，以避免對 API 造成過大負擔。預設為 `1`。
        *   `MAX_COMPONENT_LENGTH`: 檔名/目錄名單個組件的最大長度（不含擴展名），用於防止檔名過長。預設為 `80`。

    *   **`if __name__ == "__main__":` 區塊 (腳本末尾)**:
        *   `target_species_sci`: 一個 Python 列表，包含你想要下載音訊的**鳥類學名** (Scientific Names)。
            ```python
            target_species_sci = [
                "Phoenicurus phoenicurus", # 例如：普通紅尾鴝
                "Sylvia atricapilla"      # 例如：黑頂林鶯
                # 添加更多學名...
            ]
            ```
        *   `target_country`: 一個字串，指定你感興趣的**國家名 (英文)**。xeno-canto API 使用英文國家名。
            ```python
            target_country = "Poland" # 例如: "Germany", "United Kingdom", "China"
            ```
        *   `quality_filter`: 一個字串，用於篩選錄音質量。留空 (`""`) 表示下載所有質量的錄音。一些示例：
            *   `"q:A"`: 只下載 A 級錄音。
            *   `"q_gt:C"`: 下載 C 級及以上質量的錄音 (即 A, B, C)。
            *   `"q_lt:B"`: 下載 B 級以下質量的錄音 (即 C, D, E, no-quality-assigned)。
            ```python
            quality_filter = "q_gt:C" # 例如，獲取 C 級及以上的錄音
            ```

3.  **運行腳本**:
    配置完成後，在終端或命令提示符中，導航到腳本所在的目錄，然後運行：
    ```bash
    python xc_downloader.py
    ```

4.  **查看結果**:
    腳本運行完成後，你可以在 `BASE_OUTPUT_DIRECTORY` 設定的目錄下找到下載的音訊和生成的頻譜圖。檔案結構如下：

    ```
    <BASE_OUTPUT_DIRECTORY>/
    └── <處理後的物種名1>/
    |   └── <處理後的音訊基礎名1>/
    |   |   ├── <原始音訊檔名1>.mp3
    |   |   └── <處理後的音訊基礎名1>_spectrogram.png
    |   └── <處理後的音訊基礎名2>/
    |       ├── <原始音訊檔名2>.mp3
    |       └── <處理後的音訊基礎名2>_spectrogram.png
    └── <處理後的物種名2>/
        └── ...
    ```

## 可調整參數 (進階)

除了上述主要配置外，你還可以調整腳本中的其他參數以滿足特定需求：

*   **中文字體配置 (`plt.rcParams['font.sans-serif']`)**:
    位於腳本開頭。如果預設字體無法顯示中文，你可以修改此列表，加入你系統上已安裝的中文字體名稱。
    ```python
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
    ```

*   **頻譜圖參數 (在 `create_spectrogram` 函數中)**:
    *   `n_mels`: 梅爾濾波器的數量。預設為 `128`。
    *   `fmax`: 顯示的最高頻率。預設為音訊取樣率的一半 (`sr/2`)，即奈奎斯特頻率。你可以設置為一個固定值，例如 `8000` (Hz)。
    *   `plt.figure(figsize=(12, 5))`: 頻譜圖圖片的尺寸。

*   **檔名清理邏輯 (`sanitize_filename_component` 函數)**:
    如果預設的檔名縮短邏輯不符合你的需求，你可以修改此函數中的正則表達式或截斷邏輯。

## 注意事項與故障排除

*   **API 使用條款**: 請遵守 [xeno-canto API 的使用條款](https://xeno-canto.org/article/153) 和 [robots.txt](https://xeno-canto.org/robots.txt)。不要過於頻繁地請求。
*   **FFmpeg 未安裝或未在 PATH 中**: 如果 `librosa.load()` 失敗並提示無法解碼音訊檔案，很可能是因為缺少 `ffmpeg` 或者 `ffmpeg` 不在系統 PATH 中。
*   **中文字體問題**: 如果頻譜圖標題中的中文顯示為方框，請檢查你的系統是否安裝了腳本中指定的任一中文字體，或修改腳本以使用你系統上存在的其他中文字體。
*   **網路問題**: 下載過程依賴穩定的網路連接。
*   **處理時間**: 如果請求的鳥種和國家組合包含大量錄音，腳本可能需要較長時間來下載和處理所有檔案。
*   **磁碟空間**: 大量高質量音訊檔案會佔用 considerable 的磁碟空間。


## 致謝

*   本腳本使用了 [xeno-canto.org](https://xeno-canto.org) 提供的公共 API。感謝 xeno-canto 社區的貢獻。

---
```
MIT License

Copyright (c) [年份] [你的名字或組織名]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
將 `[年份]` 和 `[你的名字或組織名]` 替換為實際資訊。
