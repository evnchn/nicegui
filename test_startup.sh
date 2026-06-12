#!/usr/bin/env bash

set -euo pipefail

request() {
    local url="$1" code
    # NOTE servers with reload=True log their URL before the socket accepts connections, so retry refused connections
    code=$(curl --silent --location --retry 5 --retry-connrefused --retry-delay 1 --output /dev/null --write-out '%{http_code}' --max-time 5 "$url" || true)
    if [[ $code -lt 200 || $code -ge 500 ]]; then
        echo "Request to $url failed with HTTP status $code"
        return 1
    fi
}

run() {
    pwd
    local output_file
    output_file=$(mktemp)
    local exitcode=0
    # NOTE keep stdin open for examples which read from it (e.g. threaded_nicegui); a no-op for all other examples
    # NOTE no brace group, so $pid is the timeout process itself, which forwards SIGTERM to the server's process group
    timeout 10 uv run --no-sync ./"$1" "${@:2}" < <(sleep 15) > "$output_file" 2>&1 &
    local pid=$!

    local ready=0
    for _ in {1..50}; do
        if grep -qE "NiceGUI ready to go|Uvicorn running on http://127.0.0.1:8000" "$output_file"; then
            ready=1
            break
        fi
        if ! kill -0 "$pid" 2>/dev/null; then
            break
        fi
        sleep 0.2
    done

    local request_output=""
    if [[ $ready -eq 1 ]]; then
        local url
        url=$(grep -Eo "http://(127\.0\.0\.1|localhost):[0-9]+" "$output_file" | head -n 1 || true)
        if request_output=$(request "${url:-http://127.0.0.1:8080}/" 2>&1); then
            kill "$pid" 2>/dev/null || true # NOTE stop the server right after a successful request instead of waiting out the timeout
        else
            exitcode=1
        fi
    else
        exitcode=1
    fi

    local process_exit=0
    wait "$pid" 2>/dev/null || process_exit=$? # NOTE suppress the asynchronous "Terminated" job notification after stopping the server early
    [[ $process_exit -eq 124 ]] && process_exit=0 # exitcode 124 is coming from "timeout command above"
    [[ $process_exit -eq 143 ]] && process_exit=0 # exitcode 143 (SIGTERM) is coming from stopping the server early after a successful request
    [[ $process_exit -ne 0 ]] && exitcode=$process_exit
    local output
    output=$(cat "$output_file")
    rm "$output_file"
    [[ -n $request_output ]] && output+=$'\n'"$request_output" # NOTE append the request failure reason so it shows up in the failure dump
    echo "$output" | grep -qE "NiceGUI ready to go|Uvicorn running on http://127.0.0.1:8000" || exitcode=1
    echo "$output" | grep -qE "Traceback|Error" && exitcode=1
    if [[ $exitcode -ne 0 ]]; then
        echo "Wrong exit code $exitcode. Output was:"
        echo "$output"
        return 1
    fi
}

check() {
    echo "Checking $1 ----------"
    pushd "$(dirname "$1")" >/dev/null

    max_attempts=3
    for attempt in $(seq 1 $max_attempts); do
        if run "$(basename "$1")" "${@:2}"; then
            echo "OK --------"
            popd > /dev/null
            return 0
        elif [ $attempt -eq $max_attempts ]; then
            echo "FAILED after $max_attempts attempts -------"
            popd > /dev/null
            return 1
        else
            echo "Attempt $attempt failed. Retrying..."
        fi
    done
}

check main.py || exit 1
for path in examples/*
do
    # Skip examples/generate_pdf
    if [[ $path == "examples/generate_pdf" ]]; then
        continue # until https://github.com/pygobject/pycairo/issues/387 is fixed
    fi

    # Skip examples/ai_interface for Python 3.14
    if [[ $(uv run python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2) =~ ^3.14$ ]] && [[ $path == "examples/ai_interface" ]]; then
        continue # It still uses Pydantic V1, which breaks horribly with Python 3.14
    fi

    # skip if path is examples/pyserial
    if test $path = "examples/pyserial"; then
        continue # because there is no serial port in github actions
    fi

    # install all requirements except nicegui
    if test -f $path/requirements.txt; then
        sed '/^nicegui/d' $path/requirements.txt > $path/requirements.tmp.txt || exit 1 # remove nicegui from requirements.txt
        uv pip install -r $path/requirements.tmp.txt || exit 1
        rm $path/requirements.tmp.txt || exit 1
    fi

    # run start.sh or main.py
    if test -f $path/start.sh; then
        check $path/start.sh dev || exit 1
    elif test -f $path/main.py; then
        check $path/main.py || exit 1
    fi
    if pytest -q --collect-only $path >/dev/null 2>&1; then
        echo "running tests for $path"
        uv run --no-sync pytest $path || exit 1
    fi
done

exit 0
