from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from providers.base import ToolCall
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Vin Researcher — Lab 04",
    page_icon="🤖",
    layout="wide",
)

def execute_tool_call(call: ToolCall) -> dict[str, Any]:
    func = TOOL_FUNCTIONS.get(call.name)
    if not func:
        return {
            "tool": call.name,
            "args": call.args,
            "result": {"error": "unknown_tool", "message": f"No implementation for {call.name}"},
        }
    try:
        result = func(**call.args)
    except Exception as exc:
        result = {"error": type(exc).__name__, "message": str(exc)}
    return {"tool": call.name, "args": call.args, "result": result}


def assistant_tool_message(response_text: str | None, calls: list[ToolCall]) -> dict[str, str]:
    call_summary = [{"name": call.name, "args": call.args} for call in calls]
    content = response_text or "I will call the selected tool(s)."
    return {
        "role": "assistant",
        "content": f"{content}\n\nTOOL_CALLS_JSON:\n{json.dumps(call_summary, ensure_ascii=False, indent=2)}",
    }


def tool_results_message(events: list[dict[str, Any]]) -> dict[str, str]:
    return {
        "role": "user",
        "content": (
            "TOOL_RESULTS_JSON:\n"
            f"{json.dumps(events, ensure_ascii=False, indent=2)}\n\n"
            "Use only these tool results. If the user asked for a digest and the items are ready, "
            "call the formatting tool. Otherwise answer the user directly with cited sources when available."
        ),
    }


def run_agent_loop(
    provider: Any,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int = 4,
) -> dict[str, Any]:
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    all_tool_events: list[dict[str, Any]] = []

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(working_messages, tools, model=model, temperature=0.0)
        calls = response.tool_calls
        round_record: dict[str, Any] = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
            "tool_results": [],
        }

        if not calls:
            rounds.append(round_record)
            return {
                "status": "answered",
                "assistant_text": response.text or "",
                "rounds": rounds,
                "tool_events": all_tool_events,
            }

        working_messages.append(assistant_tool_message(response.text, calls))
        non_clarification_events: list[dict[str, Any]] = []

        for call in calls:
            event = execute_tool_call(call)
            round_record["tool_results"].append(event)
            all_tool_events.append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                question = result.get("question") or call.args.get("question") or "Bạn bổ sung thêm thông tin nhé."
                rounds.append(round_record)
                return {
                    "status": "waiting_for_user",
                    "assistant_text": question,
                    "rounds": rounds,
                    "tool_events": all_tool_events,
                }

            non_clarification_events.append(event)

        rounds.append(round_record)
        working_messages.append(tool_results_message(non_clarification_events))

    return {
        "status": "max_tool_rounds",
        "assistant_text": f"Stopped after {max_tool_rounds} tool rounds.",
        "rounds": rounds,
        "tool_events": all_tool_events,
    }


def main():
    st.title("🤖 Vin Researcher — Academic & Technical Agent")
    st.caption("Lab 04: Prompt Engineering & Tool Calling Agent")

    # Sidebar setup
    with st.sidebar:
        st.header("⚙️ Configuration")
        provider_name = st.selectbox("Model Provider", ["gemini", "openrouter", "openai", "anthropic"], index=0)
        version_label = st.text_input("Artifact Version Label", value="v3")
        
        system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
        tools_path = ARTIFACTS_DIR / "tools.yaml"
        
        if system_prompt_path.exists() and tools_path.exists():
            art_ver = build_artifact_version(version_label, system_prompt_path, tools_path)
            st.success(f"**Artifact Version**: `{art_ver.artifact_version}`")
            st.info(f"**Prompt Hash**: `{art_ver.prompt_hash[:12]}`")
            st.info(f"**Tools Hash**: `{art_ver.tools_hash[:12]}`")
        
        st.divider()
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.session_state.history = []
            st.rerun()

    # Load agent prompt & tools
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    provider = make_provider(provider_name)
    selected_model = getattr(provider, "default_model", None)

    # Session state initialization
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "history" not in st.session_state:
        st.session_state.history = []

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "tool_events" in msg and msg["tool_events"]:
                with st.expander("🛠️ Tool Trace Details"):
                    for idx, event in enumerate(msg["tool_events"], 1):
                        st.json({
                            "tool_name": event.get("tool"),
                            "arguments": event.get("args"),
                            "result": event.get("result"),
                        })

    # Chat Input
    if user_input := st.chat_input("Hỏi Vin Researcher..."):
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Prepare messages for LLM
        history_context = st.session_state.history[-10:] if st.session_state.history else []
        input_messages = [
            {"role": "system", "content": system_prompt},
            *history_context,
            {"role": "user", "content": user_input},
        ]

        # Run Agent Loop
        with st.chat_message("assistant"):
            with st.spinner("Agent đang suy nghĩ & gọi tool..."):
                res = run_agent_loop(
                    provider=provider,
                    messages=input_messages,
                    tools=openai_tools,
                    model=selected_model,
                )

            assistant_text = res.get("assistant_text", "")
            st.markdown(assistant_text)

            # Display Tool Trace if tools were executed
            tool_events = res.get("tool_events", [])
            if tool_events:
                with st.expander("🛠️ Tool Trace Details"):
                    for event in tool_events:
                        st.json({
                            "tool_name": event.get("tool"),
                            "arguments": event.get("args"),
                            "result": event.get("result"),
                        })

            # Append to session state
            st.session_state.messages.append({
                "role": "assistant",
                "content": assistant_text,
                "tool_events": tool_events,
            })
            st.session_state.history.append({"role": "user", "content": user_input})
            st.session_state.history.append({"role": "assistant", "content": assistant_text})


if __name__ == "__main__":
    main()
