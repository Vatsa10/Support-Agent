from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import generate_api_key, hash_api_key, require_admin
from config import config
from db.pool import sys_conn, tenant_conn
from vector_db.ingestion import load_knowledge_base
from vector_db.retrieval import retriever

router = APIRouter()


class CreateTenantRequest(BaseModel):
    name: str
    plan: Optional[str] = "free"


class CreateTenantResponse(BaseModel):
    tenant_id: str
    name: str
    api_key: str
    plan: str


@router.post("/tenants", response_model=CreateTenantResponse)
async def create_tenant(
    req: CreateTenantRequest, _admin: bool = Depends(require_admin)
):
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)

    async with sys_conn() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tenants (name, api_key_hash, plan)
            VALUES ($1, $2, $3)
            RETURNING id, name, plan
            """,
            req.name,
            key_hash,
            req.plan,
        )
        await conn.execute(
            """
            INSERT INTO tenant_settings (tenant_id, rate_limit_per_min)
            VALUES ($1, $2)
            ON CONFLICT (tenant_id) DO NOTHING
            """,
            row["id"],
            config.RATE_LIMIT_PER_MIN,
        )

    return CreateTenantResponse(
        tenant_id=str(row["id"]),
        name=row["name"],
        api_key=api_key,
        plan=row["plan"],
    )


@router.post("/tenants/{tenant_id}/kb/reindex")
async def reindex_kb(tenant_id: str, _admin: bool = Depends(require_admin)):
    chunks = load_knowledge_base(config.KB_PATH, tenant_id=tenant_id)
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail=f"No KB files for tenant at {config.KB_PATH}/{tenant_id}/",
        )
    n = await retriever.index_documents(tenant_id, chunks)
    return {"tenant_id": tenant_id, "chunks_indexed": n}


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: str, _admin: bool = Depends(require_admin)):
    async with sys_conn() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, plan, status, created_at FROM tenants WHERE id = $1",
            tenant_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "plan": row["plan"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat(),
    }
