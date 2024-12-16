from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from application import api
import uvicorn

from paymentserver.domain.payment_service import PaymentService

app = FastAPI()

app.include_router(api.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://paymentappfrontend.s3-website.us-east-2.amazonaws.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
async def load_initial_data():
    csv_path = "../payment_information.csv"
    PaymentService.add_data_from_file(csv_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
