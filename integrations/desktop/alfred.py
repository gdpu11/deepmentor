"""Alfred Script Filter: run with the Python environment containing DeepMentor."""
import json
import sys
from contextlib import closing

from deepmentor.bot import compact_reply, consult
from deepmentor.library import Library

try:
    with closing(Library()) as library:
        result = consult(library, sys.argv[1] if len(sys.argv) > 1 else "")
    reply = compact_reply(result)
    items = [{"title": "DeepMentor · " + result["status"], "subtitle": "回车复制带出处的完整结果", "arg": reply,
              "text": {"copy": reply, "largetype": reply}}]
except (ValueError, OSError) as exc:
    items = [{"title": "DeepMentor 无法取得资料", "subtitle": str(exc), "valid": False}]
print(json.dumps({"items": items}, ensure_ascii=False))
