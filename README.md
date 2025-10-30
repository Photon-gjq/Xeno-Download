# Xeno-Canto 鳥鳴音訊下載與頻譜圖生成器 (v3)

這是一個 Python 腳本，用於從 [xeno-canto.org](https://xeno-canto.org) **最新的 API v3** 直接下載指定鳥種在特定國家的鳥鳴音訊，並為每個音訊檔案生成對應的頻譜圖。腳本會自動為每個音訊創建一個子檔案夾，其中包含音訊檔案 (.mp3) 和其頻譜圖 (.png)。

## 功能特性

*   **支持 API v3**: 已完全適配 xeno-canto 最新的 API v3 規範。
*   **直接下載**: 無需手動處理 JSON，直接輸入鳥種（學名）和國家即可下載。
*   **批量處理**: 支持一次輸入多個鳥種。
*   **質量過濾**: 可以根據 xeno-canto 的錄音質量評級 (A, B, C 等) 進行篩選。
*   **分頁處理**: **自動處理 API v3 的分頁機制，確保下載所有符合條件的錄音，而不僅僅是第一頁。**
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
5.  **中文字體 (用於頻譜圖標題)**: 為了在頻譜圖標題中正確顯示中文，你的系統需要安裝至少一種支持中文的字體，並且 `matplotlib` 能夠找到它。腳本中預設嘗試了常見的中文字體如 `'SimHei'`, `'Microsoft YaHei'` 等。如果中文仍顯示為方框，請參考腳本開頭的 `plt.rcParams['font.sans-serif']` 部分。

## 安裝依賴

打開終端或命令提示符，運行以下命令安裝所需的 Python 庫：

```bash
pip install requests librosa matplotlib numpy
```

## 如何使用

1.  **下載/克隆腳本**:
    將 `xc_downloader.py` (或你命名的腳本檔案) 下載到你的本地電腦。

2.  **獲取 Xeno-Canto API Key**:
    **API v3 要求所有請求都必須包含一個 API Key。**
    *   如果你還沒有帳戶，請先在 [xeno-canto.org](https://xeno-canto.org/contribute) 註冊。
    *   登錄後，訪問你的**帳戶頁面** (點擊右上角你的用戶名 -> Account)。
    *   在頁面上你會找到你的 API Key。它是一長串字母和數字。請複製它。

3.  **配置腳本**:
    打開 `xc_downloader.py` 檔案，找到以下主要配置區域並進行修改：

    *   **腳本頂部常量**:
        *   **`XC_API_KEY`**: **這是最重要的步驟！** 將你剛剛複製的 API Key 粘貼到這裡。
            ```python
            # [!! 重要 !!] 你必須在這裡填入你自己的 xeno-canto API Key
            XC_API_KEY = "YOUR_API_KEY_HERE" 
            ```
        *   `BASE_OUTPUT_DIRECTORY`: 主輸出目錄，所有下載的數據將保存在此目錄下。預設為 `"downloaded_audio_data"`。
        *   `REQUEST_DELAY_SECONDS`: 每次 API 請求/下載之間的延遲（秒）。建議保持 `1` 秒或以上。預設為 `1`。
        *   `MAX_COMPONENT_LENGTH`: 檔名/目錄名單個組件的最大長度。預設為 `80`。

    *   **`if __name__ == "__main__":` 區塊 (腳本末尾)**:
        *   `target_species_sci`: 一個 Python 列表，包含你想要下載音訊的**鳥類學名** (Scientific Names)，每個學名由屬名和種名組成，用空格隔開。
            ```python
            target_species_sci = [
                "Otus spilocephalus", # 例子：黃嘴角鴞
                "Glaucidium brodiei"  # 例子：鵂鶹
                # 添加更多學名...
            ]
            ```
        *   `target_country`: 一個字串，指定你感興趣的**國家名 (英文)**。
            ```python
            target_country = "Taiwan" # 例如: "Germany", "United Kingdom", "China"
            ```
        *   `quality_filter`: 一個字串，用於篩選錄音質量。**API v3 嚴格使用標籤格式**。留空 (`""`) 表示下載所有質量的錄音。一些示例：
            *   `"q:A"`: 只下載 A 級錄音。
            *   `"q_gt:C"`: 下載 C 級及以上質量的錄音 (即 A, B)。
            *   `"q:no"`: 下載未評級的錄音。
            ```python
            quality_filter = "q_gt:C" # 獲取 B 級及以上的錄音
            ```

4.  **運行腳本**:
    配置完成後，在終端或命令提示符中，導航到腳本所在的目錄，然後運行：
    ```bash
    python xc_downloader.py
    ```

5.  **查看結果**:
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

*   **頻譜圖參數 (在 `create_spectrogram` 函數中)**:
    *   `N_FFT`, `HOP_LENGTH`, `N_MELS`: 這些參數決定了頻譜圖的時間和頻率解析度。你可以嘗試不同的值來觀察效果。
    *   `cmap`: 頻譜圖的顏色映射，例如 `'magma'`, `'viridis'`, `'inferno'`。

*   **檔名清理邏輯 (`sanitize_filename_component` 函數)**:
    如果預設的檔名縮短邏輯不符合你的需求，你可以修改此函數中的正則表達式或截斷邏輯。

## 注意事項與故障排除

*   **API Key 錯誤**: 如果程式提示 API 錯誤或請求失敗，請首先檢查你的 `XC_API_KEY` 是否正確填寫。
*   **API 使用條款**: 請遵守 [xeno-canto API 的使用條款](https://xeno-canto.org/explore/api)。**不要分享你的 API Key**。負責任地使用 API。
*   **FFmpeg 未安裝或未在 PATH 中**: 如果 `librosa.load()` 失敗並提示無法解碼音訊檔案，很可能是因為缺少 `ffmpeg` 或者 `ffmpeg` 不在系統 PATH 中。
*   **中文字體問題**: 如果頻譜圖標題中的中文顯示為方框，請檢查你的系統是否安裝了腳本中指定的任一中文字體，或修改腳本以使用你系統上存在的其他中文字體。
*   **網路問題**: 下載過程依賴穩定的網路連接。
*   **處理時間**: 如果請求的鳥種和國家組合包含大量錄音，腳本可能需要較長時間來下載和處理所有檔案。

## 致謝

*   本腳本使用了 [xeno-canto.org](https://xeno-canto.org) 提供的公共 API。感謝 xeno-canto 社區的貢獻。

---

```markdown
MIT License

Copyright (c) [2025] [KragiKuak]

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
