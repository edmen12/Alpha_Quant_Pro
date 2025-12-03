# Alpha Quant Pro - User Manual

## 1. Introduction
Alpha Quant Pro is an advanced algorithmic trading terminal designed for MetaTrader 5. It leverages Reinforcement Learning (RL) and real-time macroeconomic data to execute high-probability trades. Unlike traditional EAs, it adapts to market regimes using AI.

## 2. Installation
1. **Prerequisites**:
   - Windows 10 or 11 (64-bit).
   - MetaTrader 5 (MT5) terminal installed and logged in.
   - "Algo Trading" enabled in MT5 (Tools > Options > Expert Advisors > Allow Algorithmic Trading).

2. **Setup**:
   - Run `AlphaQuantPro_Setup.exe`.
   - Follow the installation wizard.
   - Accept the EULA.
   - Launch "Alpha Quant Pro" from the desktop shortcut.

## 3. Getting Started
1. **First Launch**:
   - You will see a "Risk Disclosure" popup. Read carefully and click "I ACCEPT THE RISKS".
   - The main dashboard will appear.

2. **Configuration (Settings Tab)**:
   - **Symbol**: The asset to trade (e.g., `EURUSD`, `XAUUSD`). Must match MT5 Market Watch.
   - **Lot Size**: Fixed trading volume (e.g., `0.01`).
   - **Risk %**: Percentage of balance to risk per trade (Dynamic Lot Sizing).
   - **Timeframe**: Chart timeframe (e.g., `M15`, `H1`).

## 4. Remote Control & Monitoring
### Telegram Notifications (Your Mobile Remote)
1. Create a bot via `@BotFather` on Telegram to get a **Bot Token**.
2. Get your **Chat ID** from `@userinfobot`.
3. Enter these in the Settings tab and enable the switch.
4. **Commands**: You can send commands to your bot:
   - `/status`: Get current profit, open trades, and engine status.
   - `/stop`: Emergency stop the engine.
   - `/close_all`: Liquidate all positions immediately.

### Web Dashboard & Ngrok (Anywhere Access)
1. **Web Dashboard**: Enable to view charts and logs in a browser (`http://localhost:8000`). Set a password for security.
2. **Remote Tunnel (Ngrok)**:
   - Register at `dashboard.ngrok.com` to get a free **Auth Token**.
   - Paste the token in the "Ngrok Auth Token" field in Settings.
   - Enable "Ngrok Tunnel".
   - The public URL (e.g., `https://xxxx.ngrok-free.app`) will be sent to your Telegram automatically.
   - **Usage**: You can now monitor your terminal from your phone anywhere!

## 5. Key Features Explained
### 🛡️ Risk Guard (Equity Protection)
- The bot monitors your account equity in real-time.
- If the daily loss exceeds your `Max Daily Loss` setting (default $500), it will **automatically stop trading** for the day.
- This prevents "account blowups" during extreme volatility.

### 📰 News Filter (Macro Awareness)
- The bot is aware of high-impact economic events (NFP, CPI, FOMC).
- It will **pause trading 30 minutes before** and after these events.
- You can see the next news event countdown in the "News" tab.

### 🧠 Smart Entry & Exit
- **AI Confirmation**: Uses the `The_Alpha_v1` model to validate entries based on price action and macro data.
- **Trailing Stops**: Automatically moves Stop Loss to break-even and then follows the price to lock in profits.
- **Partial Close**: Takes 50% profit at the first target (TP1) to secure gains early.

## 6. Operation
- **Start Engine**: Click the "START ENGINE" button on the Dashboard. The status badge will turn GREEN.
- **Stop Engine**: Click "STOP". The engine will cease analyzing, but open trades will remain managed by MT5.
- **Close All**: Use the "CLOSE ALL" button to immediately liquidate all positions managed by the bot.

## 7. Troubleshooting
- **"Engine Stopped" immediately**: Check if MT5 is running and Algo Trading is enabled. Check `Logs` tab for details.
- **"Frontend not found"**: Reinstall the application using the latest installer.
- **No Trades**: The market might be in a "Dead Zone" or high-impact news event (check Logs).

## 8. Support
For technical support, please contact: support@alphaquant.pro
