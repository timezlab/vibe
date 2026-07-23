#!/bin/sh
# Stub variant: hangs past the extraction cap — capture must time out,
# note it on stderr, and still exit 0.
cat > /dev/null
sleep 30
echo '{"type":"result","result":"{}"}'
