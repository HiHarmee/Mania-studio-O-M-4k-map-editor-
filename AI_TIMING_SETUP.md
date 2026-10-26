# Mania Studio 本機 AI Timing

Timing 分析使用 [Beat This!](https://github.com/CPJKU/beat_this) 的已訓練 `small0` 節拍／強拍追蹤模型。音訊由瀏覽器轉成單聲道 WAV，傳送到本機 `127.0.0.1` 服務進行推論，不會上傳音訊到第三方。第一次啟動模型時會從 Beat This! 官方權重空間下載約 8.1 MB 的模型檔。

## 首次安裝

1. 建議安裝 Python 3.11 或 3.12（需包含 Python Launcher）。安裝器會依序尋找已安裝的 3.12、3.11、3.13 或其他 Python 3 執行環境；即使沒有 3.11 也會繼續嘗試。
2. 執行 `setup_ai_timing.bat`。它會建立此資料夾內的虛擬環境，安裝 CPU 版 PyTorch、torchaudio 與 Beat This!；下載量較大，請確認網路與磁碟空間。
3. 執行 `start_ai_timing.bat`，等待命令視窗顯示模型已就緒。
4. 開啟 `index.html`，到 Timing 分頁按「AI 自動 Timing」。服務視窗需保持開啟。

若已開啟編輯器才啟動服務，可在 Timing 頁按「AI 自動 Timing」重試。服務只監聽本機回環位址，按 Ctrl+C 可停止。

## Timing 與 osu! 格式

模型輸出 beat 與 downbeat 時間。第一個偵測到的 downbeat 作為第一段 Offset；持續 BPM 改變會切成新段，並以該段附近偵測到的 downbeat 自動校準 Offset。Timing 清單中每段都可直接手動編輯 Offset（毫秒），且會維持 Timing 點順序。拍號採用 Timing 頁目前設定的拍號；Beat This! 本身不輸出拍號。自動分段是估計結果，仍建議用波形、節拍器及 Offset 微調確認。

匯出沿用 `.osu` 的 `[TimingPoints]` 欄位：`time,beatLength,meter,sampleSet,sampleIndex,volume,uninherited,effects`。每段都是合法的 uninherited timing point，按時間排序；`beatLength = 60000 / BPM`。

## 參考

- [Beat This! 原始碼與推論說明](https://github.com/CPJKU/beat_this) — MIT 授權；`small0` 權重約 8.1 MB，提供 beats 與 downbeats。
- [Beat This! 論文（ISMIR 2024）](https://arxiv.org/abs/2407.21658)
- [osu! Timing 官方說明](https://osu.ppy.sh/wiki/en/Beatmapping/Timing) — Offset 應對準歌曲第一個 downbeat；不同 BPM 使用不同 timing sections。
- [.osu 檔案格式官方說明](https://osu.ppy.sh/wiki/en/Client/File_formats/osu_%28file_format%29)
