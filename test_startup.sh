#!/usr/bin/env bash

set -euo pipefail

run() {
    pwd
    # Sidecar (#6079): poll 8080/8000 (NiceGUI default + examples/fastapi's
    # raw uvicorn.run), fire one GET / once a port answers, persist the code.
    status_file=$(mktemp)
    (
        for _ in $(seq 1 100); do
            for port in 8080 8000; do
                if curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$port/" 2>/dev/null; then
                    curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:$port/" > "$status_file" 2>/dev/null || true
                    exit 0
                fi
            done
            sleep 0.1
        done
    ) &
    sidecar_pid=$!
    output=$({ timeout 10 uv run --no-sync ./"$1" "${@:2}"; } 2>&1)
    exitcode=$?
    [[ $exitcode -eq 124 ]] && exitcode=0 # exitcode 124 is coming from "timeout command above"
    kill "$sidecar_pid" 2>/dev/null || true
    wait "$sidecar_pid" 2>/dev/null || true
    http_status=$(cat "$status_file" 2>/dev/null); rm -f "$status_file"
    echo "$output" | grep -qE "NiceGUI ready to go|Uvicorn running on http://127.0.0.1:8000" || exitcode=1
    echo "$output" | grep -qE "Traceback|Error" && exitcode=1
    [[ "$http_status" =~ ^5[0-9][0-9]$ ]] && exitcode=1 # 500 even without a logged traceback (handler returned cleanly)
    if [[ $exitcode -ne 0 ]]; then
        echo "Wrong exit code $exitcode (HTTP status: ${http_status:-000}). Output was:"
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
