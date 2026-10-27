#!/bin/bash
# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title DeepMentor
# @raycast.mode fullOutput
# @raycast.packageName DeepMentor
# @raycast.icon 🧭
# @raycast.argument1 {"type": "text", "placeholder": "问题，或 board / stress-test / interview + 问题"}
set -euo pipefail
: "${DEEPMENTOR_PYTHON:?请设置已安装 DeepMentor 的 Python 绝对路径}"
exec "$DEEPMENTOR_PYTHON" -c '
import sys
from contextlib import closing
from deepmentor.bot import compact_reply, consult
from deepmentor.library import Library
with closing(Library()) as library:
    print(compact_reply(consult(library, sys.argv[1])))
' "${1:?请输入问题}"
