from fastapi import FastAPI
import sys

app = FastAPI()

@app.get("/")
@app.head("/")
def read_root():
    return {
        "message": "Hello from Octave!", 
        "python_version": sys.version,
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "python": sys.version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 