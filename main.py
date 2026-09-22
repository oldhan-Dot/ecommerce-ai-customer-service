import uvicorn

from oldhan.conf.config import  settings


def main():
    uvicorn.run(
        "oldhan.api.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
if __name__ == "__main__":
    main()