# Alpha Quant Pro - User Manual

## 1. Introduction
Alpha Quant Pro is an advanced algorithmic trading terminal designed for MetaTrader 5. It leverages Reinforcement Learning (RL) and real-time macroeconomic data to execute high-probability trades.

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

3. **Telegram Notifications (Optional)**:
   - Create a bot via `@BotFather` on Telegram.
   - Enter the **Bot Token** and your **Chat ID** in the Settings tab.
   - Toggle "Enable Telegram".

4. **Web Dashboard (Optional)**:
   - Set a secure password in the Settings tab.
   - Toggle "Enable Web Dashboard".
   - Access via `http://localhost:8000` or the Ngrok URL (if enabled).

## 4. Operation
- **Start Engine**: Click the "START ENGINE" button on the Dashboard. The status badge will turn GREEN.
- **Stop Engine**: Click "STOP". The engine will cease analyzing, but open trades will remain managed by MT5.
- **Close All**: Use the "CLOSE ALL" button to immediately liquidate all positions managed by the bot.

## 5. Troubleshooting
- **"Engine Stopped" immediately**: Check if MT5 is running and Algo Trading is enabled. Check `Logs` tab for details.
- **"Frontend not found"**: Reinstall the application using the latest installer.
- **No Trades**: The market might be in a "Dead Zone" or high-impact news event (check Logs).

## 6. Support
For technical support, please contact: support@alphaquant.pro
