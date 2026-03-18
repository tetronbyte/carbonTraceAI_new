"""Webhook receivers for real-time ERP updates."""
import hmac
import hashlib
from fastapi import APIRouter, Request, Header, HTTPException
from ..workers.extraction_worker import enqueue_extraction
from ..services.database import db_service
import uuid

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/odoo/{tenant_id}")
async def odoo_webhook(
    tenant_id: str,
    request: Request,
    x_odoo_signature: str = Header(None)
):
    """
    Receive webhook from Odoo.
    
    Odoo sends webhooks for events like:
    - account.move/create (new invoice)
    - mrp.production/write (production updated)
    """
    body = await request.body()
    
    # Verify HMAC signature
    config = await db_service.get_erp_config(tenant_id, "odoo")
    if not config:
        raise HTTPException(status_code=404, detail="Tenant ERP config not found")
    
    from ..models.credentials import CredentialManager
    cred_manager = CredentialManager()
    credentials = cred_manager.decrypt_credentials(config.credentials_enc)
    
    webhook_secret = credentials.get("webhook_secret", "").encode()
    if webhook_secret:
        expected = hmac.new(webhook_secret, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, x_odoo_signature or ""):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    
    payload = await request.json()
    event_type = payload.get("event")  # e.g., "account.move/create"
    
    # Map event to module
    module_map = {
        "account.move": "energy",
        "mrp.production": "production",
        "purchase.order": "procurement"
    }
    
    module = None
    for key, mod in module_map.items():
        if key in event_type:
            module = mod
            break
    
    if module:
        # Enqueue incremental extraction for this module
        job_id = str(uuid.uuid4())
        await enqueue_extraction(
            job_id=job_id,
            tenant_id=tenant_id,
            erp_type="odoo",
            modules=[module],
            from_date=None,  # Will use watermark
            to_date=None,
            force_full_sync=False
        )
    
    return {"status": "queued", "event": event_type}


@router.post("/dynamics/{tenant_id}")
async def dynamics_webhook(
    tenant_id: str,
    request: Request
):
    """
    Receive webhook from Microsoft Dynamics 365 BC.
    
    Dynamics uses a different event notification schema.
    """
    payload = await request.json()
    
    # Dynamics webhook structure:
    # {
    #   "subscriptionId": "...",
    #   "clientState": "...",
    #   "expirationDateTime": "...",
    #   "resource": "companies(...)/purchaseInvoices(...)",
    #   "changeType": "created"
    # }
    
    resource = payload.get("resource", "")
    change_type = payload.get("changeType")
    
    # Map resource to module
    module = None
    if "purchaseInvoices" in resource:
        module = "energy"
    elif "productionOrders" in resource:
        module = "production"
    
    if module and change_type in ["created", "updated"]:
        job_id = str(uuid.uuid4())
        await enqueue_extraction(
            job_id=job_id,
            tenant_id=tenant_id,
            erp_type="dynamics365",
            modules=[module],
            from_date=None,
            to_date=None,
            force_full_sync=False
        )
    
    return {"status": "queued"}


@router.post("/syspro/{tenant_id}")
async def syspro_webhook(
    tenant_id: str,
    request: Request
):
    """
    Receive webhook from SYSPRO.
    
    Note: SYSPRO typically doesn't have native webhooks,
    but you can set up SQL triggers or custom integrations.
    """
    payload = await request.json()
    
    # Custom webhook structure - depends on your SYSPRO integration
    table_name = payload.get("table")
    operation = payload.get("operation")  # INSERT, UPDATE
    
    module_map = {
        "APInvoice": "energy",
        "WipJob": "production",
        "PorMaster": "procurement"
    }
    
    module = module_map.get(table_name)
    
    if module:
        job_id = str(uuid.uuid4())
        await enqueue_extraction(
            job_id=job_id,
            tenant_id=tenant_id,
            erp_type="syspro",
            modules=[module],
            from_date=None,
            to_date=None,
            force_full_sync=False
        )
    
    return {"status": "queued"}
