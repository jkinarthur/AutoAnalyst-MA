from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("autoanalyst_ma.api:app", reload=True)


if __name__ == "__main__":
    main()
