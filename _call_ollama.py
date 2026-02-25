# Ollama provider function to insert into core/model_router.py

def _call_ollama(
    messages: List[Dict[str, str]],
    system: str,
    model: str,
    endpoint: str,
    timeout_ms: int,
    max_tokens: int,
) -> Dict[str, Any]:
    with trace_llm_call(
        provider="ollama",
        model=model,
        operation="chat",
        max_tokens=max_tokens,
        message_count=len(messages) + (1 if system else 0),
        has_system_prompt=bool(system),
    ) as span:
        url = f"{endpoint}/api/chat"

        full_messages = ([{"role": "system", "content": system}] + messages) if system else messages
        body = json.dumps(
            {
                "model": model,
                "messages": full_messages,
                "stream": False,
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")

        t0 = time.monotonic()
        try:
            timeout_s = max(timeout_ms / 1000, 5)
            resp = urllib.request.urlopen(req, timeout=timeout_s)
            data = json.loads(resp.read().decode("utf-8"))
            latency = int((time.monotonic() - t0) * 1000)

            text = data.get("message", {}).get("content", "")

            usage = {
                "input": 0,
                "output": 0,
            }

            if span:
                span.set_attribute("llm.latency_ms", latency)

            return _ok_response(text, usage, "ollama", model, latency)

        except urllib.error.HTTPError as e:
            latency = int((time.monotonic() - t0) * 1000)
            detail = ""
            try:
                detail = e.read().decode("utf-8")[:500]
            except Exception:
                pass
            return _err_response(
                f"Ollama HTTP {e.code}: {detail}", "ollama", model, latency
            )
        except Exception as e:
            latency = int((time.monotonic() - t0) * 1000)
            return _err_response(f"Ollama error: {str(e)}", "ollama", model, latency)
