import json
import os
from pathlib import Path
import resource
import subprocess
import time

source = Path("/data/input.txt")
output = Path("/data/sorted.txt")
scratch = Path("/data/scratch")
scratch.mkdir(exist_ok=True)

limit = int(Path("/sys/fs/cgroup/memory.max").read_text())
buffer = limit // 2
environment = dict(os.environ, LC_ALL="C")

if output.exists():
    output.unlink()

# Request removal of cached input pages before timing.
with source.open("rb") as file:
    os.posix_fadvise(file.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)

command = [
    "sort",
    "--parallel=1",
    f"--buffer-size={buffer}b",
    f"--temporary-directory={scratch}",
    "-o", str(output),
    str(source),
]

start = time.perf_counter()
subprocess.run(command, env=environment, check=True)

# Include flushing the output to storage in elapsed time.
with output.open("rb") as file:
    os.fsync(file.fileno())

elapsed = time.perf_counter() - start
usage = resource.getrusage(resource.RUSAGE_CHILDREN)

# Check correctness outside the timed interval.
subprocess.run(
    ["sort", "--check=quiet", str(output)],
    env=environment,
    check=True,
)
assert output.stat().st_size == source.stat().st_size

results = {
    "memory_gib": limit / 1024**3,
    "sort_buffer_mib": buffer / 1024**2,
    "elapsed_seconds": round(elapsed, 3),
    "throughput_mib_per_second": round(2048 / elapsed, 2),
    "cpu_seconds": round(usage.ru_utime + usage.ru_stime, 3),
    "peak_sort_memory_mib": round(usage.ru_maxrss / 1024, 2),
    "filesystem_input_blocks": usage.ru_inblock,
    "filesystem_output_blocks": usage.ru_oublock,
    "sorted_check_passed": True,
}
print(json.dumps(results, indent=2))
