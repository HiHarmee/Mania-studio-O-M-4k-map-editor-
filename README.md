# Mania Studio

osu!mania 譜面編輯器與本機 AI Timing 工具。

## 專案內容

- `index.html`：Mania Studio 網頁版譜面編輯器前端。
- `ai_timing_server.py`：本機 AI Timing 伺服器，使用 Beat This! 模型進行節拍與強拍分析。
- `AI_TIMING_SETUP.md`：本機 AI Timing 環境建置與使用說明。
- `setup_ai_timing.bat`：一鍵安裝 PyTorch 與 Beat This! 虛擬環境腳本。
- `start_ai_timing.bat`：啟動本機 AI Timing 服務腳本。

## 快速開始

1. 直接在瀏覽器中開啟 `index.html` 即可使用編輯器。
2. 如需使用「AI 自動 Timing」功能，請參考 [AI_TIMING_SETUP.md](AI_TIMING_SETUP.md) 執行 `setup_ai_timing.bat` 與 `start_ai_timing.bat`。
