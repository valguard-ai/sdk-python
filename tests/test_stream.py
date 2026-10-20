from valguard.stream import iter_chat_completion_stream


def test_iter_chat_completion_stream_tool_calls():
    raw = (
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"function":{"name":"fn"}}]}}]}\n\n'
        "data: [DONE]\n\n"
    )
    events = list(iter_chat_completion_stream(iter([raw])))
    assert len(events) == 2
    assert events[0]["type"] == "chunk"
    assert events[0]["delta"]["tool_calls"] is not None
    assert events[1]["type"] == "done"


def test_iter_chat_completion_stream_content():
    raw = 'data: {"choices":[{"delta":{"content":"ping"}}]}\n\n'
    events = list(iter_chat_completion_stream(iter([raw])))
    assert events[0]["delta"]["content"] == "ping"
