# Scholarly Record

## Setting your OpenAI API key (for "Chat with Meeting")

You can set the key in **one** of these ways. Use whichever is easiest for you.

---

### Option 1: Paste it in the app (easiest)

1. In the **left sidebar**, find the section called **"OpenAI API Key"**.
2. Click in the box and **paste** your key (it will look like `sk-proj-...`).
3. The app uses it right away. You don’t need to restart anything.

Your key is only kept in memory for that browser session. It is not saved to a file.

---

### Option 2: Put it in a `.env` file

1. In the **same folder** as `app.py`, create or open a file named exactly **`.env`** (starts with a dot).
2. Add one line (no quotes, no spaces around the `=`):
   ```env
   OPENAI_API_KEY=sk-proj-yourActualKeyHere
   ```
3. **Save** the file.
4. **Restart the app**: stop Streamlit completely (e.g. press `Ctrl+C` in the terminal where it’s running), then run `streamlit run app.py` again from this folder.

The app only reads `.env` when it **starts**. So if you change `.env` while the app is running, you must restart for it to take effect.

---

### Option 3: Set it in your environment before starting

If you prefer to set environment variables in your terminal or system:

1. Set `OPENAI_API_KEY` to your key **before** you run Streamlit (e.g. `export OPENAI_API_KEY=sk-proj-...` in the same terminal, then run `streamlit run app.py`).
2. The app will use that value when it starts.

---

### Where to get a key

Create or copy your API key at: https://platform.openai.com/account/api-keys
