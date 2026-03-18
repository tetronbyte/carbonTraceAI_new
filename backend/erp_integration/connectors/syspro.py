"""SYSPRO ERP connector using SQL Server."""
import aioodbc
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import SQLConnector, RawERPRecord


class SYSPROConnector(SQLConnector):
    """Connector for SYSPRO ERP (South Africa, Zimbabwe)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], connection_string: str):
        super().__init__(tenant_id, credentials, connection_string)
        self.dsn = None
    
    async def authenticate(self) -> None:
        """Establish SQL Server connection to SYSPRO."""
        try:
            # Build DSN from connection string
            # Format: Driver={ODBC Driver 17 for SQL Server};Server=...;Database=...;UID=...;PWD=...
            self.dsn = aioodbc.create_pool(
                dsn=self.connection_string,
                minsize=1,
                maxsize=5
            )
            await self.dsn
            
            # Test connection
            async with self.dsn.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT @@VERSION")
                    result = await cursor.fetchone()
                    if not result:
                        raise ConnectionError("Failed to query SQL Server")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SYSPRO SQL Server: {str(e)}")
    
    async def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dicts."""
        if not self.dsn:
            await self.authenticate()
        
        async with self.dsn.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                columns = [column[0] for column in cursor.description]
                results = []
                async for row in cursor:
                    results.append(dict(zip(columns, row)))
                return results
    
    async def extract_energy_data(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract energy invoices from SYSPRO AP tables.
        
        Tables:
        - APInvoice: Invoice headers
        - APInvoiceDetail: Invoice line items
        
        Filters for StockCode patterns like 'ENRG%', 'UTIL%', 'ELEC%'
        """
        query = """
        SELECT 
            I.Invoice,
            I.InvoiceDate,
            I.Supplier,
            I.InvTotal,
            I.Currency,
            D.StockCode,
            D.InvQty,
            D.UnitOfMeasure,
            D.InvPrice,
            D.InvLineValue,
            S.Description as ItemDescription
        FROM APInvoice I
        INNER JOIN APInvoiceDetail D ON I.Invoice = D.Invoice
        LEFT JOIN InvMaster S ON D.StockCode = S.StockCode
        WHERE I.InvoiceDate >= ?
          AND I.InvoiceDate <= ?
          AND (D.StockCode LIKE 'ENRG%' 
               OR D.StockCode LIKE 'UTIL%'
               OR D.StockCode LIKE 'ELEC%'
               OR D.StockCode LIKE 'GAS%'
               OR S.ProductClass IN ('ENERGY', 'UTILITIES'))
        ORDER BY I.InvoiceDate
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            # Group by invoice number
            invoices = {}
            for row in results:
                inv_num = row["Invoice"]
                if inv_num not in invoices:
                    invoices[inv_num] = {
                        "Invoice": inv_num,
                        "InvoiceDate": row["InvoiceDate"].isoformat() if hasattr(row["InvoiceDate"], "isoformat") else str(row["InvoiceDate"]),
                        "Supplier": row["Supplier"],
                        "InvTotal": float(row["InvTotal"]) if row["InvTotal"] else 0,
                        "Currency": row["Currency"],
                        "LineItems": []
                    }
                
                invoices[inv_num]["LineItems"].append({
                    "StockCode": row["StockCode"],
                    "InvQty": float(row["InvQty"]) if row["InvQty"] else 0,
                    "UnitOfMeasure": row["UnitOfMeasure"],
                    "InvPrice": float(row["InvPrice"]) if row["InvPrice"] else 0,
                    "InvLineValue": float(row["InvLineValue"]) if row["InvLineValue"] else 0,
                    "ItemDescription": row["ItemDescription"]
                })
            
            return [
                RawERPRecord(
                    source_erp="syspro",
                    source_module="accounts_payable",
                    source_record_id=inv_num,
                    raw_payload=inv_data,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for inv_num, inv_data in invoices.items()
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from SYSPRO: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract production data from SYSPRO WIP tables.
        
        Tables:
        - WipJob: Work order headers
        - WipJobAllMaterials: Materials used
        """
        query = """
        SELECT 
            J.Job,
            J.DateReleased,
            J.DateCompleted,
            J.StockCode,
            J.QtyManufactured,
            J.UoM,
            S.Description as ProductDescription,
            S.ProductClass
        FROM WipJob J
        LEFT JOIN InvMaster S ON J.StockCode = S.StockCode
        WHERE J.DateCompleted >= ?
          AND J.DateCompleted <= ?
          AND J.JobStatus = 'C'
        ORDER BY J.DateCompleted
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            return [
                RawERPRecord(
                    source_erp="syspro",
                    source_module="manufacturing",
                    source_record_id=row["Job"],
                    raw_payload={
                        "Job": row["Job"],
                        "DateReleased": row["DateReleased"].isoformat() if hasattr(row["DateReleased"], "isoformat") else str(row["DateReleased"]),
                        "DateCompleted": row["DateCompleted"].isoformat() if hasattr(row["DateCompleted"], "isoformat") else str(row["DateCompleted"]),
                        "StockCode": row["StockCode"],
                        "QtyManufactured": float(row["QtyManufactured"]) if row["QtyManufactured"] else 0,
                        "UoM": row["UoM"],
                        "ProductDescription": row["ProductDescription"],
                        "ProductClass": row["ProductClass"]
                    },
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for row in results
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from SYSPRO: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract procurement data from SYSPRO PO tables.
        
        For CBAM Scope 3 upstream emissions.
        """
        query = """
        SELECT 
            P.PurchaseOrder,
            P.OrderDate,
            P.Supplier,
            D.StockCode,
            D.OrderQty,
            D.OrderUom,
            D.OrderPrice,
            D.OrderValue,
            S.Description as ItemDescription
        FROM PorMaster P
        INNER JOIN PorDetail D ON P.PurchaseOrder = D.PurchaseOrder
        LEFT JOIN InvMaster S ON D.StockCode = S.StockCode
        WHERE P.OrderDate >= ?
          AND P.OrderDate <= ?
          AND P.OrderStatus IN ('F', 'C')
        ORDER BY P.OrderDate
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            # Group by PO number
            purchase_orders = {}
            for row in results:
                po_num = row["PurchaseOrder"]
                if po_num not in purchase_orders:
                    purchase_orders[po_num] = {
                        "PurchaseOrder": po_num,
                        "OrderDate": row["OrderDate"].isoformat() if hasattr(row["OrderDate"], "isoformat") else str(row["OrderDate"]),
                        "Supplier": row["Supplier"],
                        "LineItems": []
                    }
                
                purchase_orders[po_num]["LineItems"].append({
                    "StockCode": row["StockCode"],
                    "OrderQty": float(row["OrderQty"]) if row["OrderQty"] else 0,
                    "OrderUom": row["OrderUom"],
                    "OrderPrice": float(row["OrderPrice"]) if row["OrderPrice"] else 0,
                    "OrderValue": float(row["OrderValue"]) if row["OrderValue"] else 0,
                    "ItemDescription": row["ItemDescription"]
                })
            
            return [
                RawERPRecord(
                    source_erp="syspro",
                    source_module="procurement",
                    source_record_id=po_num,
                    raw_payload=po_data,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for po_num, po_data in purchase_orders.items()
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from SYSPRO: {str(e)}")
    
    async def close(self):
        """Close database connection pool."""
        if self.dsn:
            self.dsn.close()
            await self.dsn.wait_closed()
