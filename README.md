# Scholarly Log

## Setting your Gemini API key (for "Chat with Meeting")

The chat feature now uses **Google Gemini**. You only need to set the key once.

### Option 1: Put it in a `.env` file (recommended)

1. In the **same folder** as `app.py`, open the `.env` file.
2. Add or edit this line (no quotes, no spaces around the `=`):
   ```env
   GEMINI_API_KEY=your-gemini-key-here
   ```
3. **Save** the file.
4. **Restart the app**: stop Streamlit completely (e.g. press `Ctrl+C` in the terminal where it's running), then run:
   ```bash
   .venv/bin/streamlit run app.py
   ```

The app reads `.env` when it **starts**, so you must restart after changing it.

### Option 2: Set it in your environment before starting

If you prefer to set environment variables in your terminal or system:

1. Set `GEMINI_API_KEY` to your key **before** you run Streamlit, for example:
   ```bash
   export GEMINI_API_KEY=your-gemini-key-here
   .venv/bin/streamlit run app.py
   ```
2. The app will use that value when it starts.

### Where to get a Gemini key

Create or copy your Gemini API key from: https://aistudio.google.com/
