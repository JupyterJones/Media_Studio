#!/usr/bin/env python3
"""
jsonl2text.py
-------------
Converts Antigravity / Agent transcript JSONL files into clean, human-readable text logs.
Parses user prompts, model reasoning (thinking), tool executions, tool outputs,
and assistant replies into structured, easy-to-read sections.

Usage:
    python3 jsonl2text.py [input.jsonl] [output.txt]
    python3 jsonl2text.py 42515a6fe9a4_transcript_full.jsonl
    python3 jsonl2text.py --help
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime

SEPARATOR_DOUBLE = "=" * 80
SEPARATOR_SINGLE = "-" * 80
SEPARATOR_SUB    = "~" * 60

def format_timestamp(ts_str):
    """Parses ISO timestamp into readable string."""
    if not ts_str:
        return ""
    try:
        # Handles 2026-09-02T06:41:40+08:00 or Z
        clean_ts = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_ts)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ts_str

def clean_user_input(raw_content):
    """Extracts actual user request and any notable settings change."""
    if not raw_content:
        return ""

    user_req_match = re.search(r'<USER_REQUEST>(.*?)</USER_REQUEST>', raw_content, re.DOTALL)
    if user_req_match:
        request_text = user_req_match.group(1).strip()
    else:
        # If no XML tags, clean out metadata blocks if present
        request_text = re.sub(r'<ADDITIONAL_METADATA>.*?</ADDITIONAL_METADATA>', '', raw_content, flags=re.DOTALL)
        request_text = re.sub(r'<CONTEXT_SUMMARY>.*?</CONTEXT_SUMMARY>', '', request_text, flags=re.DOTALL)
        request_text = request_text.strip()

    # Check for settings change
    settings_match = re.search(r'<USER_SETTINGS_CHANGE>(.*?)</USER_SETTINGS_CHANGE>', raw_content, re.DOTALL)
    settings_note = ""
    if settings_match:
        settings_note = f"\n[Settings: {settings_match.group(1).strip()}]"

    return request_text + settings_note

def clean_system_message(raw_content):
    """Strips boilerplate wrapper from system notification messages."""
    if not raw_content:
        return ""
    match = re.search(r'<SYSTEM_MESSAGE>\s*(.*?)\s*</SYSTEM_MESSAGE>', raw_content, re.DOTALL)
    if match:
        inner = match.group(1).strip()
        # Clean out redundant "[Message] timestamp=... sender=..." line if present
        inner = re.sub(r'^\[Message\][^\n]*\n?', '', inner).strip()
        return inner
    return raw_content.strip()

def format_tool_call(call):
    """Formats a single tool invocation into a clean human-readable block."""
    name = call.get('name', 'unknown_tool')
    args = call.get('args', {})

    lines = [f"Tool Call: {name}"]

    # Specialized formatting for common tools
    if name == 'run_command':
        cmd = args.get('CommandLine', '')
        cwd = args.get('Cwd', '')
        summary = args.get('toolSummary', '')
        action = args.get('toolAction', '')
        if summary:
            lines.append(f"  Summary : {summary} ({action})")
        if cwd:
            lines.append(f"  Working Dir : {cwd}")
        lines.append(f"  Command :\n    $ {cmd}")

    elif name == 'view_file':
        path = args.get('AbsolutePath', '')
        start = args.get('StartLine')
        end = args.get('EndLine')
        summary = args.get('toolSummary', '')
        line_info = f" (Lines {start}-{end})" if start is not None and end is not None else ""
        lines.append(f"  File : {path}{line_info}")
        if summary:
            lines.append(f"  Summary : {summary}")

    elif name in ('write_to_file', 'replace_file_content'):
        target = args.get('TargetFile', '')
        desc = args.get('Description', '') or args.get('Instruction', '')
        summary = args.get('toolSummary', '')
        lines.append(f"  Target File : {target}")
        if desc:
            lines.append(f"  Description : {desc}")
        elif summary:
            lines.append(f"  Summary : {summary}")

    elif name == 'manage_task':
        action = args.get('Action', '')
        task_id = args.get('TaskId', '')
        lines.append(f"  Action  : {action}")
        if task_id:
            lines.append(f"  Task ID : {task_id}")

    elif name == 'schedule':
        dur = args.get('DurationSeconds')
        prompt = args.get('Prompt', '')
        cond = args.get('TimerCondition', 'never')
        lines.append(f"  Duration  : {dur}s (condition: {cond})")
        if prompt:
            lines.append(f"  Wakeup Prompt : {prompt}")

    else:
        # Generic tool arguments
        for k, v in args.items():
            if k in ('toolSummary', 'toolAction'):
                continue
            val_str = json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            if len(val_str) > 120:
                val_str = val_str[:120] + "..."
            lines.append(f"  {k} : {val_str}")

    return "\n".join(lines)

def process_transcript(input_path, output_path, include_thinking=True, include_tools=True, max_output_lines=150):
    """Reads JSONL transcript and writes formatted text file."""
    if not os.path.exists(input_path):
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return False

    stats = {
        "steps": 0,
        "user_requests": 0,
        "assistant_replies": 0,
        "tool_calls": 0,
        "system_messages": 0,
        "start_time": None,
        "end_time": None,
    }

    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                records.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON decode error at line {line_num}: {e}", file=sys.stderr)

    if not records:
        print("Error: No valid JSON records found in input file.", file=sys.stderr)
        return False

    stats["steps"] = len(records)
    stats["start_time"] = records[0].get("created_at")
    stats["end_time"] = records[-1].get("created_at")

    out_lines = []

    # Write Header
    out_lines.append(SEPARATOR_DOUBLE)
    out_lines.append("TRANSCRIPT LOG: " + os.path.basename(input_path))
    out_lines.append(SEPARATOR_DOUBLE)
    out_lines.append(f"Source File : {os.path.abspath(input_path)}")
    out_lines.append(f"Total Steps : {stats['steps']}")
    if stats["start_time"]:
        out_lines.append(f"Start Time  : {format_timestamp(stats['start_time'])}")
    if stats["end_time"]:
        out_lines.append(f"End Time    : {format_timestamp(stats['end_time'])}")
    out_lines.append(f"Generated   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    out_lines.append(SEPARATOR_DOUBLE)
    out_lines.append("")

    for item in records:
        step_idx = item.get("step_index", "?")
        step_type = item.get("type", "UNKNOWN")
        source = item.get("source", "")
        ts = format_timestamp(item.get("created_at", ""))
        time_tag = f" | {ts}" if ts else ""

        # -------------------------------------------------------------
        # 1. USER_INPUT
        # -------------------------------------------------------------
        if step_type == "USER_INPUT":
            stats["user_requests"] += 1
            raw_content = item.get("content", "")
            user_text = clean_user_input(raw_content)

            out_lines.append(SEPARATOR_DOUBLE)
            out_lines.append(f"[STEP {step_idx}] USER REQUEST{time_tag}")
            out_lines.append(SEPARATOR_DOUBLE)
            out_lines.append(user_text)
            out_lines.append("")

        # -------------------------------------------------------------
        # 2. PLANNER_RESPONSE (Model turn)
        # -------------------------------------------------------------
        elif step_type == "PLANNER_RESPONSE":
            thinking = item.get("thinking")
            tool_calls = item.get("tool_calls") or []
            content = item.get("content")

            # A. Model internal reasoning (Thinking)
            if thinking and include_thinking:
                out_lines.append(SEPARATOR_SINGLE)
                out_lines.append(f"[STEP {step_idx}] ASSISTANT REASONING (Thinking){time_tag}")
                out_lines.append(SEPARATOR_SINGLE)
                out_lines.append(thinking.strip())
                out_lines.append("")

            # B. Tool Calls
            if tool_calls and include_tools:
                stats["tool_calls"] += len(tool_calls)
                out_lines.append(SEPARATOR_SINGLE)
                out_lines.append(f"[STEP {step_idx}] TOOL EXECUTION ({len(tool_calls)} action{'s' if len(tool_calls) > 1 else ''}){time_tag}")
                out_lines.append(SEPARATOR_SINGLE)
                for call in tool_calls:
                    out_lines.append(format_tool_call(call))
                    out_lines.append("")

            # C. Assistant Message Content (User-facing response)
            if content:
                stats["assistant_replies"] += 1
                out_lines.append(SEPARATOR_DOUBLE)
                out_lines.append(f"[STEP {step_idx}] ASSISTANT RESPONSE{time_tag}")
                out_lines.append(SEPARATOR_DOUBLE)
                out_lines.append(content.strip())
                out_lines.append("")

        # -------------------------------------------------------------
        # 3. GENERIC (Tool Output)
        # -------------------------------------------------------------
        elif step_type == "GENERIC":
            if not include_tools:
                continue

            content = item.get("content", "")
            out_lines.append(f"[STEP {step_idx}] TOOL OUTPUT{time_tag}")
            out_lines.append(SEPARATOR_SUB)

            if not content:
                out_lines.append("(No output or empty result)")
            else:
                lines = content.strip().splitlines()
                if max_output_lines > 0 and len(lines) > max_output_lines:
                    head_count = max_output_lines - 10
                    out_lines.extend(lines[:head_count])
                    out_lines.append(f"... [{len(lines) - max_output_lines} lines omitted] ...")
                    out_lines.extend(lines[-10:])
                else:
                    out_lines.extend(lines)

            out_lines.append(SEPARATOR_SUB)
            out_lines.append("")

        # -------------------------------------------------------------
        # 4. SYSTEM_MESSAGE
        # -------------------------------------------------------------
        elif step_type == "SYSTEM_MESSAGE":
            stats["system_messages"] += 1
            if not include_tools:
                continue

            raw_content = item.get("content", "")
            sys_text = clean_system_message(raw_content)

            out_lines.append(f"[STEP {step_idx}] SYSTEM NOTIFICATION{time_tag}")
            out_lines.append(SEPARATOR_SUB)
            out_lines.append(sys_text)
            out_lines.append(SEPARATOR_SUB)
            out_lines.append("")

        # -------------------------------------------------------------
        # 5. OTHER UNKNOWN STEPS
        # -------------------------------------------------------------
        else:
            out_lines.append(f"[STEP {step_idx}] {step_type} ({source}){time_tag}")
            if item.get("content"):
                out_lines.append(str(item.get("content")).strip())
            out_lines.append("")

    # Write Footer Summary
    out_lines.append(SEPARATOR_DOUBLE)
    out_lines.append("SUMMARY OF CONVERSATION")
    out_lines.append(SEPARATOR_DOUBLE)
    out_lines.append(f"Total Steps Processed : {stats['steps']}")
    out_lines.append(f"User Requests         : {stats['user_requests']}")
    out_lines.append(f"Assistant Responses   : {stats['assistant_replies']}")
    out_lines.append(f"Tool Invocations      : {stats['tool_calls']}")
    out_lines.append(f"System Notifications  : {stats['system_messages']}")
    out_lines.append(SEPARATOR_DOUBLE)

    full_output = "\n".join(out_lines) + "\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_output)

    print(f"Successfully converted '{input_path}' -> '{output_path}'")
    print(f"Processed {stats['steps']} steps ({stats['user_requests']} user requests, {stats['assistant_replies']} assistant replies, {stats['tool_calls']} tool calls).")
    print(f"Output size: {len(full_output.encode('utf-8')):,} bytes ({len(out_lines):,} lines).")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Convert Antigravity transcript JSONL into a clean human-readable text document."
    )
    parser.add_argument(
        "pos_input",
        nargs="?",
        default=None,
        help="Path to input JSONL file (positional)"
    )
    parser.add_argument(
        "pos_output",
        nargs="?",
        default=None,
        help="Path to output text file (positional)"
    )
    parser.add_argument(
        "-i", "--input",
        dest="opt_input",
        default=None,
        help="Path to input JSONL file"
    )
    parser.add_argument(
        "-o", "--output",
        dest="opt_output",
        default=None,
        help="Path to output text file"
    )
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Exclude model internal reasoning/thinking blocks"
    )
    parser.add_argument(
        "--no-tools",
        action="store_true",
        help="Exclude tool executions, outputs, and system messages for a conversation-only view"
    )
    parser.add_argument(
        "--max-output-lines",
        type=int,
        default=150,
        help="Max lines of tool output to display before truncating (default: 150, 0 = unlimited)"
    )

    args = parser.parse_args()

    input_file = args.opt_input or args.pos_input or "42515a6fe9a4_transcript_full.jsonl"
    output_file = args.opt_output or args.pos_output

    if not output_file:
        if input_file.lower().endswith(".jsonl"):
            output_file = input_file[:-6] + ".txt"
        else:
            output_file = input_file + ".txt"

    success = process_transcript(
        input_path=input_file,
        output_path=output_file,
        include_thinking=not args.no_thinking,
        include_tools=not args.no_tools,
        max_output_lines=args.max_output_lines
    )

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
