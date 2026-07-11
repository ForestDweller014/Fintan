import json
import random
from typing import Optional
import tempfile
import os


def read_data(filename: str, read_index: Optional[int] = 0, batch_size: Optional[int] = None) -> list[dict]:
    """
    Read records from a JSONL file as a list of dicts.

    :param batch_size: Number of records to read; if None, read all remaining.
    :param read_index: Starting index in the file's record list.
    :param file_path: Path to the JSONL file.
    :return: List of dicts representing the records.
    """
    try:
        with open(filename, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    total = len(lines)
    if read_index is None:
        read_index = 0
    if read_index >= total:
        return []

    # Determine slice of lines to parse
    if batch_size is None:
        batch_lines = lines[read_index:]
    else:
        if batch_size <= 0:
            return []
        end_index = min(read_index + batch_size, total)
        batch_lines = lines[read_index:end_index]

    return [json.loads(line) for line in batch_lines]

def write_data(file_path: str, data: list) -> None:
    with open(file_path, 'a') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')

def shuffle_data(file_path: str) -> None:
    """
    Shuffle a JSONL file in-place without loading all lines into memory.
    This function builds an index of byte offsets, shuffles that list,
    then writes lines in the new order to a temp file before replacing.
    """
    # 1) Build list of line offsets
    offsets = []
    with open(file_path, 'rb') as f:
        pos = f.tell()
        for line in f:
            offsets.append(pos)
            pos += len(line)

    if not offsets:
        return  # empty file, nothing to do

    # 2) Shuffle the offsets list in memory (int list only)
    random.shuffle(offsets)

    # 3) Write shuffled lines to a temporary file in same directory
    dir_name = os.path.dirname(file_path)
    tmp = tempfile.NamedTemporaryFile('wb', delete=False, dir=dir_name)
    tmp_path = tmp.name
    try:
        with open(file_path, 'rb') as source:
            for off in offsets:
                source.seek(off)
                tmp.write(source.readline())
    finally:
        tmp.close()

    # 4) Replace the original file with the shuffled temp
    os.replace(tmp_path, file_path)