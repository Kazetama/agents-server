"""
core/agent.py
─────────────
Main AI agent loop. Handles:
  - Calling Ollama with tool definitions
  - Executing tool calls natively
  - Fallback parsing for leaked JSON tool calls
  - Sanitizing final output (stripping raw JSON blobs)
"""
import re
import json as _json
import ollama
from config.settings import OLLAMA_MODEL
from core.memory import memory
from skills.registry import AVAILABLE_TOOLS, TOOL_FUNCTIONS
from utils.logger import logger


# ─── JSON Leak Sanitizer ─────────────────────────────────────────────────────
_JSON_LEAK_RE = re.compile(
    r'\{[\s\S]*?"name"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{[\s\S]*?\}\s*\}',
    re.DOTALL
)

def _sanitize(text: str) -> str:
    """Strip any raw JSON tool-call blobs that leaked into model text output."""
    return _JSON_LEAK_RE.sub("", text).strip()


# ─── Tool Execution ───────────────────────────────────────────────────────────
def _execute_tool_calls(tool_calls: list, user_id: str) -> bool:
    """Run a list of native tool_calls objects. Returns True if any ran."""
    if not tool_calls:
        return False

    ran_any = False
    for call in tool_calls:
        fn_name = call["function"]["name"]
        fn_args = call["function"].get("arguments", {})
        logger.info(f"[Tool] {fn_name}({fn_args})")

        result = (
            TOOL_FUNCTIONS[fn_name](**fn_args)
            if fn_name in TOOL_FUNCTIONS
            else f"⚠️ Unknown tool: {fn_name}"
        )
        if fn_name not in TOOL_FUNCTIONS:
            logger.warning(f"Unknown tool called: {fn_name}")

        memory.append_raw(user_id, {"role": "tool", "content": str(result)})
        ran_any = True

    return ran_any


# ─── Fallback: Leaked JSON Parser ────────────────────────────────────────────
def _fallback_execute(content: str, user_id: str) -> bool:
    """
    If the model leaked raw JSON tool calls inside its text,
    parse and execute them manually. Returns True if any executed.
    """
    matches = _JSON_LEAK_RE.findall(content)
    if not matches:
        return False

    memory.append_raw(user_id, {"role": "assistant", "content": content})
    ran_any = False

    for raw in matches:
        try:
            data = _json.loads(re.sub(r"\s+", " ", raw))
            fn_name = data.get("name")
            fn_args = data.get("parameters", {})
            if fn_name in TOOL_FUNCTIONS:
                logger.info(f"[Fallback Tool] {fn_name}({fn_args})")
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
                memory.append_raw(user_id, {"role": "tool", "content": str(result)})
                ran_any = True
        except Exception as e:
            logger.error(f"Fallback JSON parse error: {e}")

    return ran_any


# ─── Main Entry ──────────────────────────────────────────────────────────────
def process_message(user_id: str, user_input: str) -> str:
    """
    Full agent loop:
      1. Add user message to memory
      2. Call Ollama with tools
      3. Handle native tool calls OR fallback parse leaked JSON
      4. If tools ran → re-call Ollama for final human-readable response
      5. Sanitize & return
    """
    uid = str(user_id)
    memory.add_message(uid, "user", user_input)

    try:
        # ── Step 1: First Ollama call ─────────────────────────────────────
        resp = ollama.chat(
            model=OLLAMA_MODEL,
            messages=memory.get_history(uid),
            tools=AVAILABLE_TOOLS,
        )
        msg = resp.get("message", {})

        # ── Step 2: Native tool calling ───────────────────────────────────
        native_calls = msg.get("tool_calls", [])
        used_tool = False

        if native_calls:
            memory.append_raw(uid, msg)
            used_tool = _execute_tool_calls(native_calls, uid)
        else:
            # ── Step 3: Fallback for leaked JSON ─────────────────────────
            raw_content = msg.get("content", "")
            if '{"name"' in raw_content:
                used_tool = _fallback_execute(raw_content, uid)

        # ── Step 4: Re-call Ollama for final response if tool was used ────
        if used_tool:
            final = ollama.chat(
                model=OLLAMA_MODEL,
                messages=memory.get_history(uid),
            )
            output = _sanitize(final["message"].get("content", ""))
        else:
            output = _sanitize(msg.get("content", ""))

        memory.add_message(uid, "assistant", output)
        return output

    except Exception as e:
        logger.error(f"Agent error: {e}")
        return f"⚠️ Error: {e}"
