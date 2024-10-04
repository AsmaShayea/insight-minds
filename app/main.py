from fastapi import FastAPI
from .scraping_service import scrape_reviews
from .database import close_database_connection

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World1"}

@app.get("/scrape-reviews")
def scrape_google_reviews():
    try:
        result = scrape_reviews()
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.on_event("shutdown")
def shutdown_event():
    """
    Close MongoDB connection when shutting down the app.
    """
    close_database_connection()
