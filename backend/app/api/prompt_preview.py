"""Prompt preview API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.errors import cost_ceiling_response
from app.api.gateway import GatewayFactory, get_gateway_factory
from app.config import get_settings
from app.db import get_db
from app.gateway.base import CostCeilingExceededError, GatewayError
from app.schemas.prompt import PromptPreviewRequest, PromptPreviewResponse
from app.services.prompt_errors import (
    PromptRenderError,
    PromptTemplateInvalidError,
    PromptVariableMissingError,
)
from app.services.prompt_preview_service import PromptPreviewModelError, preview_prompt
from app.services.prompt_validation import REQUIRED_VARIABLES_BY_TASK

router = APIRouter()


@router.get("/contracts", response_model=dict[str, list[str]])
async def prompt_contracts_route() -> dict[str, list[str]]:
    """Return prompt variable contracts per task."""
    return {
        task: sorted(required_variables)
        for task, required_variables in REQUIRED_VARIABLES_BY_TASK.items()
    }


@router.post("/preview", response_model=PromptPreviewResponse)
async def preview_prompt_route(
    payload: PromptPreviewRequest,
    db: Session = Depends(get_db),
    gateway_factory: GatewayFactory = Depends(get_gateway_factory),
) -> PromptPreviewResponse | JSONResponse:
    """Run a draft prompt template without creating specs or inspections."""
    try:
        result = await preview_prompt(
            db=db,
            task=payload.task,
            template=payload.template,
            variables=payload.variables,
            model_id=payload.model_id,
            gateway_factory=gateway_factory,
            settings=get_settings(),
        )
    except PromptTemplateInvalidError as error:
        return _prompt_invalid_response(error.reason)
    except PromptVariableMissingError as error:
        return _prompt_invalid_response(f"missing variable value: {error.variable_name}")
    except PromptRenderError as error:
        return _prompt_invalid_response(error.reason)
    except PromptPreviewModelError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except CostCeilingExceededError as error:
        return cost_ceiling_response(error)
    except GatewayError as error:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Gateway failure: {error}") from error
    return PromptPreviewResponse(**result.__dict__)


def _prompt_invalid_response(reason: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "prompt_template_invalid", "reason": reason},
    )
