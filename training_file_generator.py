import asyncio
import os
import time
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

from label_generator import generate_labels_batch
from serializer import read_data, write_data, shuffle_data
from input_generator import generate_inputs_batch
from app_config import APP_CONFIG
import sys
import threading
from functools import partial

STAY_SIZE = APP_CONFIG["STAY_SIZE"]
PREDICTION_SIZE = APP_CONFIG["PREDICTION_SIZE"]
MAX_PROCS = os.cpu_count() or 4
executor = ThreadPoolExecutor(max_workers=MAX_PROCS)
training_meta: dict
training_locks: dict
done_event = asyncio.Event()

prev_intervals: dict[str, list[dict]] = {}


async def log_progress(training_meta: dict[str, int], time_anchor: float, done_event: asyncio.Event) -> None:
    """
    Every 5 seconds, print how many batches each symbol has completed.
    Stops when done_event is set.
    """
    BAR_WIDTH = 30
    first_iteration = True

    print()

    while not done_event.is_set():
        try:
            # wake early if done_event is set, or after 5s
            await asyncio.wait_for(done_event.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass

        # Elapsed time
        time_now = time.monotonic()
        elapsed = time_now - time_anchor
        elapsed_str = str(timedelta(seconds=int(elapsed)))

        total = training_meta.get("total", 0)

        # print status
        lines = []
        for symbol, count in training_meta.items():
            done_str = "\n"
            if count >= total:
                done_str = f"  → Done! Time elapsed: {elapsed_str}\n"

            # Calculate fill
            frac_b = min(count / total, 1.0)
            filled_b = int(frac_b * BAR_WIDTH)

            # Build bar strings
            bar_b = "█" * filled_b + "-" * (BAR_WIDTH - filled_b)
            lines.append(f"{symbol} → Batches completed: [{bar_b}] {count}/{total} ({frac_b*100:5.1f}%)" + done_str)

        status = "\n".join(lines) + "\n"
        if first_iteration:
            sys.stdout.write(status)
            first_iteration = False
        else:
            up = len(training_meta)
            sys.stdout.write(f"\033[{up}A\033[J{status}")
        sys.stdout.flush()
    
    sys.stdout.write(f"\nDone! Total time: {elapsed_str}\n")
    sys.stdout.flush()


def generate_training_file_batch(symbol: str, read_fname: str, start_index: int, batch_size: int, write_fname: str, NATURAL_MIN: float, write_lock: threading.Lock) -> None:
    new_bar_data = read_data(read_fname, start_index, batch_size + STAY_SIZE)

    global prev_intervals

    bar_data = prev_intervals[symbol] + new_bar_data
    prev_intervals[symbol] = bar_data[-STAY_SIZE + 1:]

    training_data = []

    label_data = generate_labels_batch(bar_data, start_index, batch_size, NATURAL_MIN)
    input_data = generate_inputs_batch(bar_data, start_index, batch_size)

    output_size = len(label_data)

    for idx in range(output_size):
        training_data.append({
            "inputs":    input_data[idx],
            "labels":    label_data[idx],
        })

    with write_lock:
        write_data(write_fname, training_data)
        training_meta[symbol] += 1


def generate_training_file(symbol: str, batch_size: int, NATURAL_MIN: float, pending_calls: list[partial]) -> None:
    print(symbol)
    fname_h = f'historical_files/historical_data_{symbol}.jsonl'
    fname_t = f'training_files/training_data_{symbol}.jsonl'

    if not os.path.exists(fname_h):
        raise FileNotFoundError(f"ERROR: {fname_h} file does not exist yet!")

    if batch_size < PREDICTION_SIZE + STAY_SIZE:
        raise ValueError(f"ERROR: Batch size is too small given lookback and lookahead periods!"
                         f"Batch_size ({batch_size}) must be >= STAY_SIZE+PREDICTION_SIZE "
                         f"({STAY_SIZE + PREDICTION_SIZE})"
        )

    write_lock = threading.Lock()
    batch_idx = 0

    global prev_intervals

    prev_intervals[symbol] = []
    while batch_idx <= 100000:
        # schedule the batch‐generation to run in a separate thread
        pending_calls.append(
            partial(
                generate_training_file_batch,
                symbol,
                fname_h,
                batch_idx,
                batch_size,
                fname_t,
                NATURAL_MIN,
                write_lock
            )
        )

        batch_idx += batch_size

    # finally, shuffle if the training file exists
    #if os.path.exists(fname_t):
        #shuffle_data(fname_t)
    #else:
        #raise FileNotFoundError(f"ERROR: No {fname_t} was created! Make sure {fname_h} is not empty.")


async def generate_training_files(SYMBOLS: list[str], batch_size: int, NATURAL_MIN: float) -> None:
    global training_meta, training_locks, done_event, executor
    training_meta = {s: 0 for s in SYMBOLS}
    training_meta["total"] = batch_size
    training_locks = {s: asyncio.Lock() for s in SYMBOLS}
    done_event = asyncio.Event()
    executor = ThreadPoolExecutor(max_workers=MAX_PROCS)

    # run all file‐gen tasks concurrently
    loop = asyncio.get_running_loop()
    pending_calls: list[partial] = []

    # 2) run all the file-gen coroutines in parallel
    logger_task = asyncio.create_task(log_progress(training_meta, time.monotonic(), done_event))

    for symbol in SYMBOLS:
        generate_training_file(symbol, batch_size, NATURAL_MIN, pending_calls) 

    pending_jobs = [
        loop.run_in_executor(executor, call)
        for call in pending_calls
    ]
    await asyncio.gather(*pending_jobs)

    # signal logger to wrap up, then wait for it
    done_event.set()
    await logger_task
    executor.shutdown(wait=True)
