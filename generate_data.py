import random
from pathlib import Path

output = Path("/data/input.txt")
rng = random.Random(548)

with output.open("wb") as file:
    for block in range(2048):
        data = rng.randbytes(63 * 8192).hex().encode("ascii")
        records = [
            data[i:i + 126] + b" \n"
            for i in range(0, len(data), 126)
        ]
        file.write(b"".join(records))

        if (block + 1) % 512 == 0:
            print(f"Generated {block + 1} MiB", flush=True)

print(f"Finished: {output.stat().st_size:,} bytes")
