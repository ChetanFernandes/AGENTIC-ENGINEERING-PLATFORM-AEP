import asyncio
import uvicorn


if __name__ == "__main__":
    loop = asyncio.SelectorEventLoop()
    asyncio.set_event_loop(loop)

    uvicorn.run(
        "fast_api.api_layer:app",
        host="0.0.0.0",
        port=8000,
        reload=False)
    