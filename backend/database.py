from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

client = AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.DB_NAME]

# Collections
users_collection = db.users
organizations_collection = db.organizations
invoices_collection = db.invoices
emission_records_collection = db.emission_records
blockchain_ledger_collection = db.blockchain_ledger
greenwashing_collection = db.greenwashing_analyses
estimations_collection = db.carbon_estimations
reports_collection = db.esg_reports
tasks_collection = db.tasks

async def get_db():
    return db

async def get_database():
    return db
