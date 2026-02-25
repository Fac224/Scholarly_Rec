import os
from datetime import date
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
import streamlit as st
from supabase import Client, create_client
import requests

# Load environment variables from .env at startup (override any existing so .env wins)
_load_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_load_env_path, override=True)


STATUSES = ["To Record", "Recorded", "Action Items", "Archived"]

# Hard-wired Supabase fallback config so the app always works
# (env vars can still override these if you prefer).
SUPABASE_URL_DEFAULT = "https://mcmydalfofsrmnfplfqx.supabase.co"
SUPABASE_KEY_DEFAULT = "sb_publishable_7EtA8LB2OxcxTnrmW0rJEA_xs47zLe-"


@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    """
    Create and cache a Supabase client.

    Uses, in order of priority:
    1. Environment variables SUPABASE_URL / SUPABASE_KEY (if set)
    2. The known-good fallback values baked into this app.
    """
    supabase_url = os.getenv("SUPABASE_URL") or SUPABASE_URL_DEFAULT
    supabase_key = os.getenv("SUPABASE_KEY") or SUPABASE_KEY_DEFAULT

    return create_client(supabase_url.strip(), supabase_key.strip())


@st.cache_resource(show_spinner=False)
def get_gemini_api_key() -> Optional[str]:
    """
    Get the Gemini API key from `GEMINI_API_KEY` or Streamlit secrets.
    """
    api_key: Optional[str] = os.getenv("GEMINI_API_KEY")

    # Optionally override with Streamlit secrets if configured
    try:
        if "gemini" in st.secrets:
            api_key = st.secrets["gemini"].get("api_key", api_key)
    except Exception:
        pass

    if not api_key or not api_key.strip():
        return None

    return api_key.strip()


def fetch_meetings(supabase: Client) -> List[Dict[str, Any]]:
    """Fetch all meetings ordered by date descending."""
    resp = supabase.table("Meetings").select("*").order("date", desc=True).execute()
    return resp.data or []


def insert_meeting(
    supabase: Client,
    title: str,
    meeting_date: date,
    category: str,
    summarized_transcript: str,
    status: str,
) -> None:
    supabase.table("Meetings").insert(
        {
            "title": title,
            "date": meeting_date.isoformat(),
            "category": category,
            "summarized_transcript": summarized_transcript,
            "status": status,
        }
    ).execute()


def get_active_meeting(meetings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    active_id = st.session_state.get("active_meeting_id")
    if active_id is None:
        return None
    for m in meetings:
        if m.get("id") == active_id:
            return m
    return None


def set_active_meeting(meeting_id: Any) -> None:
    st.session_state["active_meeting_id"] = meeting_id
    # Initialize chat history per meeting
    chats = st.session_state.setdefault("meeting_chats", {})
    chats.setdefault(str(meeting_id), [])


def render_global_css() -> None:
    card_css = """
    <style>
    .kanban-column {
        background-color: #f5f5f7;
        border-radius: 8px;
        padding: 0.75rem;
        min-height: 400px;
    }
    .kanban-header {
        font-weight: 700;
        font-size: 1rem;
        margin-bottom: 0.5rem;
        color: #1f2933;
    }
    .meeting-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        border: 1px solid #e5e7eb;
        cursor: pointer;
        transition: box-shadow 0.15s ease, transform 0.15s ease, border-color 0.15s ease;
    }
    .meeting-card:hover {
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        transform: translateY(-1px);
        border-color: #6366f1;
    }
    .meeting-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
        color: #111827;
    }
    .meeting-meta {
        font-size: 0.8rem;
        color: #6b7280;
    }
    .meeting-category {
        display: inline-block;
        padding: 0.1rem 0.45rem;
        border-radius: 999px;
        background: #eef2ff;
        color: #4f46e5;
        font-size: 0.75rem;
        margin-top: 0.35rem;
    }
    </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)


def render_sidebar_new_meeting(supabase: Optional[Client]) -> None:
    """Render the sidebar new-meeting form and meeting selector."""
    st.sidebar.markdown("---")
    st.sidebar.header("New Meeting")

    with st.sidebar.form("new_meeting_form", clear_on_submit=True):
        title = st.text_input("Title", placeholder="e.g. Weekly product sync")
        meeting_date = st.date_input("Date", value=date.today())
        category = st.text_input("Category", placeholder="e.g. Product, Hiring, Strategy")
        status = st.selectbox("Status", options=STATUSES, index=1)  # default "Recorded"
        summarized_transcript = st.text_area(
            "Summarized Transcript",
            height=200,
            placeholder="Paste your pre-summarized transcript here...",
        )

        submitted = st.form_submit_button("Save to Supabase")

        if submitted:
            if not title or not summarized_transcript:
                st.warning("Please provide at least a title and summarized transcript.")
            else:
                try:
                    insert_meeting(
                        supabase=supabase,
                        title=title,
                        meeting_date=meeting_date,
                        category=category or "General",
                        summarized_transcript=summarized_transcript,
                        status=status,
                    )
                    st.success("Meeting saved.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving meeting: {e}")

    # Optional: list of meetings in sidebar for quick selection
    st.sidebar.markdown("---")
    st.sidebar.subheader("Meetings")
    try:
        meetings = fetch_meetings(supabase)
        if meetings:
            options = {f"{m['title']} ({m['status']})": m["id"] for m in meetings}
            selected_label = st.sidebar.selectbox(
                "Open meeting", ["-"] + list(options.keys()),
                index=0,
            )
            if selected_label != "-":
                set_active_meeting(options[selected_label])
        else:
            st.sidebar.caption("No meetings yet.")
    except Exception:
        st.sidebar.caption("Unable to load meetings list.")


def render_kanban(meetings: List[Dict[str, Any]]) -> None:
    st.subheader("Meetings")
    cols = st.columns(len(STATUSES))

    for idx, status in enumerate(STATUSES):
        with cols[idx]:
            st.markdown(
                f'<div class="kanban-column">'
                f'<div class="kanban-header">{status}</div>',
                unsafe_allow_html=True,
            )

            status_meetings = [m for m in meetings if m.get("status") == status]
            if not status_meetings:
                st.caption("No meetings.")
            else:
                for m in status_meetings:
                    with st.container():
                        card_key = f"card_{status}_{m['id']}"
                        # Use a button to make the card clickable
                        if st.button(
                            f"{m['title']}",
                            key=card_key,
                            help="Open chat for this meeting",
                        ):
                            set_active_meeting(m["id"])

                        # Render the styled card just below the button label
                        st.markdown(
                            f"""
                            <div class="meeting-card">
                                <div class="meeting-title">{m['title']}</div>
                                <div class="meeting-meta">
                                    {m.get('date', '')} · {m.get('user_id', '')}
                                </div>
                                <div class="meeting-category">{m.get('category', 'General')}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

            st.markdown("</div>", unsafe_allow_html=True)


def render_chat_interface(gemini_api_key: str, active_meeting: Dict[str, Any]) -> None:
    st.subheader("Chat with Meeting")

    transcript = active_meeting.get("summarized_transcript", "") or ""
    if not transcript:
        st.info("This meeting has no summarized transcript yet.")
        return

    system_prompt = (
        "You are an assistant helping Stefano. Use ONLY the following summarized "
        "transcript to answer his questions:\n\n"
        f"{transcript}\n\n"
        "If the answer isn't there, say you don't know."
    )

    meeting_id_str = str(active_meeting.get("id"))
    chats: Dict[str, List[Dict[str, str]]] = st.session_state.setdefault(
        "meeting_chats", {}
    )
    chats.setdefault(meeting_id_str, [])

    # Display existing messages
    for msg in chats[meeting_id_str]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask something about this meeting...")
    if not user_input:
        return

    # Append user message
    chats[meeting_id_str].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call Gemini via HTTP API
    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                conversation_lines: List[str] = []
                for msg in chats[meeting_id_str]:
                    role = msg["role"]
                    prefix = "User" if role == "user" else "Assistant"
                    conversation_lines.append(f"{prefix}: {msg['content']}")

                full_prompt = (
                    system_prompt
                    + "\n\nConversation so far:\n"
                    + "\n".join(conversation_lines)
                    + "\nAssistant:"
                )

                url = (
                    "https://generativelanguage.googleapis.com/v1beta/"
                    "models/gemini-1.5-flash-latest:generateContent"
                )
                resp = requests.post(
                    url,
                    params={"key": gemini_api_key},
                    json={
                        "contents": [
                            {
                                "parts": [
                                    {
                                        "text": full_prompt,
                                    }
                                ]
                            }
                        ]
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                answer = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    or "I wasn't able to generate an answer from Gemini."
                )
                st.markdown(answer)

        chats[meeting_id_str].append({"role": "assistant", "content": answer})
    except Exception as e:
        st.error(f"Error calling Gemini: {e}")


def main() -> None:
    st.set_page_config(
        page_title="Scholarly Log 🎓 – Meetings",
        page_icon="📚",
        layout="wide",
    )

    render_global_css()

    st.title("Scholarly Log 🎓")
    st.caption("Manage and chat with your summarized meetings.")

    supabase = get_supabase_client()
    # Sidebar: new meeting + selector
    render_sidebar_new_meeting(supabase)
    gemini_api_key = get_gemini_api_key()

    # Main Kanban
    try:
        meetings = fetch_meetings(supabase)
    except Exception as e:
        st.error(f"Error loading meetings from Supabase: {e}")
        meetings = []

    render_kanban(meetings)

    st.markdown("---")
    active_meeting = get_active_meeting(meetings)
    if active_meeting:
        if gemini_api_key is not None:
            render_chat_interface(gemini_api_key, active_meeting)
        else:
            st.warning(
                "Gemini API key is missing. Add `GEMINI_API_KEY=...` to your `.env` file and restart the app."
            )
    else:
        st.info("Select a meeting card or choose one from the sidebar to start chatting.")


if __name__ == "__main__":
    main()
