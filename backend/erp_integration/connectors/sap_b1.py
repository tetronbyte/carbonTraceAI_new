"""SAP Business One connector using SQL Server."""
import aioodbc
from typing import List, Dict, Any
from datetime import datetime, timezone
from .base import SQLConnector, RawERPRecord


class SAPBusinessOneConnector(SQLConnector):
    """Connector for SAP Business One (Egypt, South Africa)."""
    
    def __init__(self, tenant_id: str, credentials: Dict[str, Any], connection_string: str):
        super().__init__(tenant_id, credentials, connection_string)
        self.dsn = None
    
    async def authenticate(self) -> None:
        """Establish connection to SAP B1 database."""
        try:
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
                        raise ConnectionError("Failed to query SAP B1 database")
        
        except Exception as e:
            raise ConnectionError(f"Failed to connect to SAP B1: {str(e)}")
    
    async def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
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
        Extract energy invoices from SAP B1.
        
        Tables:
        - OPDN: Goods Receipt PO
        - PDN1: Goods Receipt PO Lines
        """
        query = """
        SELECT 
            T0.DocNum,
            T0.DocDate,
            T0.CardName,
            T0.DocTotal,
            T0.DocCur,
            T1.ItemCode,
            T1.Quantity,
            T1.UnitMsr,
            T1.LineTotal,
            T2.ItemName
        FROM OPDN T0
        INNER JOIN PDN1 T1 ON T0.DocEntry = T1.DocEntry
        LEFT JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
        WHERE T0.DocDate >= ?
          AND T0.DocDate <= ?
          AND (T2.ItmsGrpCod IN (SELECT ItmsGrpCod FROM OITB WHERE ItmsGrpNam LIKE '%Energy%' OR ItmsGrpNam LIKE '%Utility%')
               OR T1.ItemCode LIKE 'ENRG%'
               OR T1.ItemCode LIKE 'ELEC%')
        ORDER BY T0.DocDate
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            # Group by document
            docs = {}
            for row in results:
                doc_num = row["DocNum"]
                if doc_num not in docs:
                    docs[doc_num] = {
                        "DocNum": doc_num,
                        "DocDate": row["DocDate"].isoformat() if hasattr(row["DocDate"], "isoformat") else str(row["DocDate"]),
                        "CardName": row["CardName"],
                        "DocTotal": float(row["DocTotal"]) if row["DocTotal"] else 0,
                        "DocCur": row["DocCur"],
                        "LineItems": []
                    }
                
                docs[doc_num]["LineItems"].append({
                    "ItemCode": row["ItemCode"],
                    "Quantity": float(row["Quantity"]) if row["Quantity"] else 0,
                    "UnitMsr": row["UnitMsr"],
                    "LineTotal": float(row["LineTotal"]) if row["LineTotal"] else 0,
                    "ItemName": row["ItemName"]
                })
            
            return [
                RawERPRecord(
                    source_erp="sap_b1",
                    source_module="accounts_payable",
                    source_record_id=str(doc_num),
                    raw_payload=doc_data,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for doc_num, doc_data in docs.items()
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract energy data from SAP B1: {str(e)}")
    
    async def extract_production_output(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """
        Extract production orders from SAP B1.
        
        Tables:
        - OWOR: Production Orders
        - WOR1: Production Order Components
        """
        query = """
        SELECT 
            T0.DocNum,
            T0.PostDate,
            T0.ItemCode,
            T0.PlannedQty,
            T0.CmpltQty,
            T0.Status,
            T1.ItemName
        FROM OWOR T0
        LEFT JOIN OITM T1 ON T0.ItemCode = T1.ItemCode
        WHERE T0.PostDate >= ?
          AND T0.PostDate <= ?
          AND T0.Status = 'L'
        ORDER BY T0.PostDate
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            return [
                RawERPRecord(
                    source_erp="sap_b1",
                    source_module="manufacturing",
                    source_record_id=str(row["DocNum"]),
                    raw_payload={
                        "DocNum": row["DocNum"],
                        "PostDate": row["PostDate"].isoformat() if hasattr(row["PostDate"], "isoformat") else str(row["PostDate"]),
                        "ItemCode": row["ItemCode"],
                        "PlannedQty": float(row["PlannedQty"]) if row["PlannedQty"] else 0,
                        "CmpltQty": float(row["CmpltQty"]) if row["CmpltQty"] else 0,
                        "ItemName": row["ItemName"]
                    },
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for row in results
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract production data from SAP B1: {str(e)}")
    
    async def extract_procurement(self, from_date: str, to_date: str) -> List[RawERPRecord]:
        """Extract purchase orders from SAP B1."""
        query = """
        SELECT 
            T0.DocNum,
            T0.DocDate,
            T0.CardName,
            T1.ItemCode,
            T1.Quantity,
            T1.UnitMsr,
            T1.LineTotal,
            T2.ItemName
        FROM OPOR T0
        INNER JOIN POR1 T1 ON T0.DocEntry = T1.DocEntry
        LEFT JOIN OITM T2 ON T1.ItemCode = T2.ItemCode
        WHERE T0.DocDate >= ?
          AND T0.DocDate <= ?
          AND T0.DocStatus = 'C'
        ORDER BY T0.DocDate
        """
        
        try:
            results = await self._execute_query(query, (from_date, to_date))
            
            pos = {}
            for row in results:
                doc_num = row["DocNum"]
                if doc_num not in pos:
                    pos[doc_num] = {
                        "DocNum": doc_num,
                        "DocDate": row["DocDate"].isoformat() if hasattr(row["DocDate"], "isoformat") else str(row["DocDate"]),
                        "CardName": row["CardName"],
                        "LineItems": []
                    }
                
                pos[doc_num]["LineItems"].append({
                    "ItemCode": row["ItemCode"],
                    "Quantity": float(row["Quantity"]) if row["Quantity"] else 0,
                    "UnitMsr": row["UnitMsr"],
                    "LineTotal": float(row["LineTotal"]) if row["LineTotal"] else 0,
                    "ItemName": row["ItemName"]
                })
            
            return [
                RawERPRecord(
                    source_erp="sap_b1",
                    source_module="procurement",
                    source_record_id=str(doc_num),
                    raw_payload=po_data,
                    extracted_at=datetime.now(timezone.utc).isoformat()
                )
                for doc_num, po_data in pos.items()
            ]
        
        except Exception as e:
            raise RuntimeError(f"Failed to extract procurement data from SAP B1: {str(e)}")
    
    async def close(self):
        """Close database connection."""
        if self.dsn:
            self.dsn.close()
            await self.dsn.wait_closed()
