import os
Import("env")

env_file = os.path.join(env.get("PROJECT_DIR"), ".env")
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            val = val.strip().strip('"').strip("'")
            env.Append(BUILD_FLAGS=[f'-D{key.strip()}="\\"{val}\\""'])
