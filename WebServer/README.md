Web API for Eink Frames

- uses uv in dev
- need to `uv export` the uv lock to `requirements.txt`

### Test on local - no docker
- make sure to have `.env` file with `PHOTO_DIR` set to the directory of images on local
- `PHOTO_SRC` will not be used
```bash
uv run src/main.py
```

### Production
- you need both `PHOTO_DIR` and `PHOTO_SRC` set in `.env`

### Alembic
- `uv run alembic revision -m "message"`
- `uv run alembic upgrade head`

TODO
- try to store index of images once and append new images periodically
