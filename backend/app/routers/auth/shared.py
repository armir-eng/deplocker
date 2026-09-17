from fastapi import Depends, status
from fastapi.responses import JSONResponse

from app.utils.auth.shared import get_current_session

from . import router


@router.get("/session/check")
async def validate_session(
    session: dict = Depends(get_current_session),
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=session,
    )
